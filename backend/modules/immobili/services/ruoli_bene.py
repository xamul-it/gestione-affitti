"""
Roles on a bene at a date and the "who pays what" summary.

Spec: docs/superpowers/specs/2026-11-10-beni-catastali-design.md, section
"Titolari, usufrutto e conduttore". The costs and income register
(2026-11-12-costi-ricavi-design.md) reuses ruoli_alla_data for its shares:
keep the names stable. No amount is ever computed here.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Iterable, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform.models import Relazione

from ..models import Bene

ENTITY_TYPE = "IMMOBILE"
MODULO = "immobili"
GODIMENTO = ("usufrutto", "uso", "abitazione", "enfiteusi", "superficie")
PIENA_PROPRIETA = ("proprieta",)
PROPRIETA = ("nuda_proprieta", "proprieta")
# Rights where extraordinary repairs stay with the owners (c.c. artt. 1005,
# 1026). The enfiteuta bears them himself (art. 960), the superficiario owns
# the building (art. 952).
STRAORDINARIE_AI_PROPRIETARI = ("usufrutto", "uso", "abitazione")
# Personal enjoyment of the bene: whoever holds it bears the ordinary costs.
GODIMENTO_PERSONALE = ("conduttore", "affittuario_agrario", "comodatario", "godimento_altro")
# Who farms the land and gathers the fruits: the agrarian income follows them
# (TUIR artt. 32, 33). A plain lease ("conduttore") is not an agricultural use.
CONDUZIONE_AGRICOLA = ("affittuario_agrario", "comodatario", "godimento_altro")
CENTO = Decimal(100)
UNO = Fraction(1)

AVVISO_TERRENO_LOCATO = (
    "Terreno locato: se l'uso è agricolo registra il conduttore come affittuario agrario; "
    "se non è agricolo il terreno non produce reddito agrario e il canone è un reddito diverso (TUIR artt. 32, 67)"
)
AVVISO_GODIMENTO_ALTRO = "Titolo di godimento non specificato: verificare che conduca il fondo"


@dataclass
class RigaRelazione:
    """One relation of a bene, as read from core_relazioni."""
    soggetto_id: int
    nome: str
    tipo: str  # relation type code ("proprieta", "usufrutto", "conduttore"...)
    quota: Optional[Fraction]
    data_inizio: Optional[date]
    data_fine: Optional[date]


@dataclass
class Soggetto:
    """A subject of a "who pays what" item.

    Every computation (allocations, sums, checks) uses `quota_esatta`, the exact
    Fraction: the costs and income register splits with it. `quota` is the
    rounded percentage (3 x 33.33 = 99.99) and `quota_frazione` the text
    ("1/3"): both are for presentation only, never to be summed or multiplied.
    """
    soggetto_id: int
    nome: str
    ruolo: str  # code of the relation type
    quota: Optional[Decimal]
    quota_esatta: Optional[Fraction] = None
    quota_frazione: Optional[str] = None


@dataclass
class RuoliBene:
    titolari_godimento: list[Soggetto]
    proprietari: list[Soggetto]
    conduttori: list[Soggetto]  # open personal enjoyments (GODIMENTO_PERSONALE)
    usufrutto: bool  # a right of enjoyment other than ownership exists
    straordinarie_ai_proprietari: bool = False  # usufruct, use or habitation
    avvisi: list[str] = field(default_factory=list)


@dataclass
class Voce:
    codice: str
    etichetta: str
    soggetti: list[Soggetto]
    norma: str
    avvisi: list[str] = field(default_factory=list)


@dataclass
class RiepilogoBene:
    data: date
    voci: list[Voce]
    avvisi: list[str]


def _vale(riga: RigaRelazione, giorno: date) -> bool:
    return (riga.data_inizio is None or riga.data_inizio <= giorno) and (
        riga.data_fine is None or riga.data_fine >= giorno)


def _soggetto(riga: RigaRelazione, quota: Optional[Fraction]) -> Soggetto:
    percento = None if quota is None else (Decimal(quota.numerator) * CENTO / Decimal(quota.denominator)
                                           ).quantize(Decimal("0.01"), ROUND_HALF_UP)
    frazione = None if quota is None else f"{quota.numerator}/{quota.denominator}"
    return Soggetto(soggetto_id=riga.soggetto_id, nome=riga.nome, ruolo=riga.tipo, quota=percento,
                    quota_esatta=quota, quota_frazione=frazione)


def _percentuale(frazione: Fraction) -> str:
    valore = (Decimal(frazione.numerator) * CENTO / Decimal(frazione.denominator)).quantize(Decimal("0.01"))
    return f"{valore.normalize():f}"


def _gruppo(righe: list[RigaRelazione], nome: str, avvisi: list[str]) -> list[Soggetto]:
    quote = [r.quota for r in righe]
    if len(righe) > 1 and any(q is None for q in quote):
        avvisi.append(f"Quote mancanti per {nome}")
    elif len(righe) > 1:
        totale = sum(quote, Fraction(0))
        if totale != UNO:
            avvisi.append(f"Le quote di {nome} sommano a {_percentuale(totale)}%")
    return [_soggetto(r, UNO if r.quota is None and len(righe) == 1 else r.quota) for r in righe]


def _quota_conduttori(righe: list[RigaRelazione]) -> list[Soggetto]:
    quota = UNO if len(righe) == 1 else None
    return [_soggetto(r, quota) for r in righe]


def _quote_distinte(godimento: list[RigaRelazione], piena: list[RigaRelazione]) -> bool:
    """True when full owners hold other shares than the rights of enjoyment.

    E.g. succession: usufruct 50 on the deceased's half, co-owner 50 in full:
    the co-owner keeps enjoying his half. With overlapping rights (owner 100
    and enfiteusi 100) or missing shares the owner is the burdened one.
    """
    if not godimento or not piena:
        return False
    quote = [x.quota for x in godimento + piena]
    return all(q is not None for q in quote) and sum(quote, Fraction(0)) <= UNO


def ruoli_da_righe(relazioni: Iterable[RigaRelazione], d: date) -> RuoliBene:
    """Roles from the relation rows valid on day d; no DB access.

    Rows of other types (incarichi: manutentore, terzo responsabile...) are ignored.
    """
    validi = [x for x in relazioni if _vale(x, d)]
    avvisi: list[str] = []
    for x in validi:
        if x.tipo == "diritto_reale_altro":
            avvisi.append(f"Diritto 'ALTRO' di {x.nome}: ripartizione da decidere a mano")

    godimento = [x for x in validi if x.tipo in GODIMENTO]
    usufrutto = bool(godimento)
    piena = [x for x in validi if x.tipo in PIENA_PROPRIETA]
    titolari_righe = (godimento + piena) if _quote_distinte(godimento, piena) else (godimento or piena)
    titolari = _gruppo(titolari_righe, "titolari del godimento", avvisi)
    proprieta_righe = [x for x in validi if x.tipo in PROPRIETA]
    # Without a separate right of enjoyment the owners are the holders: one check only.
    proprietari = _gruppo(proprieta_righe, "proprietari", avvisi if usufrutto else [])
    if not titolari:
        avvisi.append("Nessun titolare registrato alla data")

    conduttori = _quota_conduttori([x for x in validi if x.tipo in GODIMENTO_PERSONALE])
    return RuoliBene(
        titolari_godimento=titolari, proprietari=proprietari, conduttori=conduttori,
        usufrutto=usufrutto, avvisi=avvisi,
        straordinarie_ai_proprietari=any(x.tipo in STRAORDINARIE_AI_PROPRIETARI for x in godimento),
    )


def ruoli_alla_data(db: Session, bene_id: int, d: date) -> RuoliBene:
    tipi = GODIMENTO + PROPRIETA + GODIMENTO_PERSONALE + ("diritto_reale_altro",)
    rel = (
        db.query(Relazione, RuoloDisponibile.codice)
        .join(RuoloDisponibile, RuoloDisponibile.id == Relazione.ruolo_id)
        .filter(Relazione.entity_type == ENTITY_TYPE, Relazione.entity_id == bene_id,
                RuoloDisponibile.modulo_id == MODULO, RuoloDisponibile.codice.in_(tipi))
        .order_by(Relazione.id)
        .all()
    )
    nomi = {}
    if rel:
        ids = sorted({r.soggetto_id for r, _ in rel})
        nomi = {
            row.id: (" ".join(p for p in (row.nome, row.cognome) if p) or row.ragione_sociale
                     or f"Anagrafica {row.id}")
            for row in db.execute(
                text("SELECT id, nome, cognome, ragione_sociale "
                     "FROM anag_soggetti_anagrafici WHERE id = ANY(:ids)"), {"ids": ids})
        }
    righe = [
        RigaRelazione(r.soggetto_id, nomi.get(r.soggetto_id, f"Anagrafica {r.soggetto_id}"), codice,
                      r.quota_frazione, r.data_inizio, r.data_fine)
        for r, codice in rel
    ]
    return ruoli_da_righe(righe, d)


def voci_riepilogo(ruoli: RuoliBene, tipo_bene: str) -> list[Voce]:
    titolari = ruoli.titolari_godimento
    terreno = tipo_bene == "TERRENO"
    voci = [Voce("RENDITA", "Reddito dominicale" if terreno else "Rendita catastale", titolari,
                 "TUIR artt. 26, 27")]
    if terreno:
        # Whoever farms the parcel, even a co-owner farming the whole of it
        # (own share plus the rented one, TUIR art. 33). A plain lease is not
        # farming: the income stays with the holders, with a warning.
        agricoli = [c for c in ruoli.conduttori if c.ruolo in CONDUZIONE_AGRICOLA]
        avvisi = []
        if any(c.ruolo == "godimento_altro" for c in agricoli):
            avvisi.append(AVVISO_GODIMENTO_ALTRO)
        elif not agricoli and any(c.ruolo == "conduttore" for c in ruoli.conduttori):
            avvisi.append(AVVISO_TERRENO_LOCATO)
        voci.append(Voce("REDDITO_AGRARIO", "Reddito agrario", agricoli or titolari,
                         "TUIR artt. 32, 33", avvisi))
    voci += [
        Voce("IMU", "IMU", titolari, "L. 160/2019, c. 743"),
        Voce("SPESE_ORDINARIE", "Spese ordinarie", ruoli.conduttori or titolari, "c.c. art. 1004"),
        Voce("SPESE_STRAORDINARIE", "Spese straordinarie",
             ruoli.proprietari if ruoli.straordinarie_ai_proprietari else titolari, "c.c. art. 1005"),
        Voce("CANONE", "Canone d'affitto", titolari, "chi concede il godimento (modulo affitti)"),
    ]
    return voci


def riepilogo_bene(db: Session, bene: Bene, d: date) -> RiepilogoBene:
    ruoli = ruoli_alla_data(db, bene.id, d)
    voci = voci_riepilogo(ruoli, bene.tipo_bene)
    return RiepilogoBene(data=d, voci=voci, avvisi=ruoli.avvisi + [a for v in voci for a in v.avvisi])
