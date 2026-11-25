"""
Roles on a bene at a date and the "who pays what" summary.

Spec: docs/superpowers/specs/2026-11-10-beni-catastali-design.md, section
"Titolari, usufrutto e conduttore". The costs and income register
(2026-11-12-costi-ricavi-design.md) reuses ruoli_alla_data for its shares:
keep the names stable. No amount is ever computed here.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy.orm import Session, joinedload

from ..models import AssegnazioneConduttore, Bene, Conduttore, DirittoImmobile, Proprietario

GODIMENTO = ("USUFRUTTUARIO", "USO", "ABITAZIONE", "ENFITEUSI", "SUPERFICIE")
PIENA_PROPRIETA = ("PROPRIETARIO", "COMPROPRIETARIO")
PROPRIETA = ("NUDA_PROPRIETA",) + PIENA_PROPRIETA
# Rights where extraordinary repairs stay with the owners (c.c. artt. 1005,
# 1026). The enfiteuta bears them himself (art. 960), the superficiario owns
# the building (art. 952).
STRAORDINARIE_AI_PROPRIETARI = ("USUFRUTTUARIO", "USO", "ABITAZIONE")
CENTO = Decimal(100)


@dataclass
class Soggetto:
    soggetto_id: int
    nome: str
    ruolo: str  # tipo_diritto, or "CONDUTTORE"
    quota: Optional[Decimal]


@dataclass
class RuoliBene:
    titolari_godimento: list[Soggetto]
    proprietari: list[Soggetto]
    conduttori: list[Soggetto]
    usufrutto: bool  # a right of enjoyment other than ownership exists
    straordinarie_ai_proprietari: bool = False  # usufruct, use or habitation
    avvisi: list[str] = field(default_factory=list)


@dataclass
class Voce:
    codice: str
    etichetta: str
    soggetti: list[Soggetto]
    norma: str


@dataclass
class RiepilogoBene:
    data: date
    voci: list[Voce]
    avvisi: list[str]


def _testo(valore) -> Optional[str]:
    """Rights keep dates as 'YYYY-MM-DD' strings, assignments as dates."""
    if valore is None or valore == "":
        return None
    return valore.isoformat() if isinstance(valore, date) else str(valore)[:10]


def _vale(riga, giorno: str) -> bool:
    inizio, fine = _testo(riga.data_inizio), _testo(riga.data_fine)
    return (inizio is None or inizio <= giorno) and (fine is None or fine >= giorno)


def _tipo(diritto) -> str:
    return getattr(diritto.tipo_diritto, "value", diritto.tipo_diritto)


def _gruppo(diritti: list, nome: str, avvisi: list[str]) -> list[Soggetto]:
    quote = [d.quota_percentuale for d in diritti]
    if len(diritti) > 1 and any(q is None for q in quote):
        avvisi.append(f"Quote mancanti per {nome}")
    elif len(diritti) > 1:
        totale = sum(Decimal(q) for q in quote)
        if totale != CENTO:
            avvisi.append(f"Le quote di {nome} sommano a {totale.normalize():f}%")
    soggetti = []
    for d in diritti:
        quota = d.quota_percentuale
        if quota is None and len(diritti) == 1:
            quota = CENTO
        soggetti.append(Soggetto(
            soggetto_id=d.proprietario.soggetto_id,
            nome=d.proprietario.soggetto.nome_completo,
            ruolo=_tipo(d),
            quota=None if quota is None else Decimal(quota),
        ))
    return soggetti


def _quota_conduttori(righe: list) -> list[Soggetto]:
    quota = CENTO if len(righe) == 1 else None
    return [Soggetto(soggetto_id=a.conduttore.soggetto_id, nome=a.conduttore.soggetto.nome_completo,
                     ruolo="CONDUTTORE", quota=quota) for a in righe]


def ruoli_da_righe(diritti: Iterable, assegnazioni: Iterable, d: date) -> RuoliBene:
    """Roles from right and tenant-assignment rows valid on day d; no DB access."""
    giorno = d.isoformat()
    validi = [x for x in diritti if _vale(x, giorno)]
    avvisi: list[str] = []
    for x in validi:
        if _tipo(x) == "ALTRO":
            avvisi.append(f"Diritto 'ALTRO' di {x.proprietario.soggetto.nome_completo}: "
                          "ripartizione da decidere a mano")

    godimento = [x for x in validi if _tipo(x) in GODIMENTO]
    usufrutto = bool(godimento)
    titolari_righe = godimento or [x for x in validi if _tipo(x) in PIENA_PROPRIETA]
    titolari = _gruppo(titolari_righe, "titolari del godimento", avvisi)
    proprieta_righe = [x for x in validi if _tipo(x) in PROPRIETA]
    # Without a separate right of enjoyment the owners are the holders: one check only.
    proprietari = _gruppo(proprieta_righe, "proprietari", avvisi if usufrutto else [])
    if not titolari:
        avvisi.append("Nessun titolare registrato alla data")

    conduttori = _quota_conduttori([a for a in assegnazioni if _vale(a, giorno)])
    return RuoliBene(
        titolari_godimento=titolari, proprietari=proprietari, conduttori=conduttori,
        usufrutto=usufrutto, avvisi=avvisi,
        straordinarie_ai_proprietari=any(_tipo(x) in STRAORDINARIE_AI_PROPRIETARI for x in godimento),
    )


def ruoli_alla_data(db: Session, bene_id: int, d: date) -> RuoliBene:
    diritti = (
        db.query(DirittoImmobile)
        .options(joinedload(DirittoImmobile.proprietario).joinedload(Proprietario.soggetto))
        .filter(DirittoImmobile.bene_id == bene_id)
        .order_by(DirittoImmobile.id)
        .all()
    )
    assegnazioni = (
        db.query(AssegnazioneConduttore)
        .options(joinedload(AssegnazioneConduttore.conduttore).joinedload(Conduttore.soggetto))
        .filter(AssegnazioneConduttore.bene_id == bene_id)
        .order_by(AssegnazioneConduttore.id)
        .all()
    )
    return ruoli_da_righe(diritti, assegnazioni, d)


def voci_riepilogo(ruoli: RuoliBene, tipo_bene: str) -> list[Voce]:
    titolari = ruoli.titolari_godimento
    terreno = tipo_bene == "TERRENO"
    voci = [Voce("RENDITA", "Reddito dominicale" if terreno else "Rendita catastale", titolari,
                 "TUIR artt. 26, 27")]
    if terreno:
        # Whoever farms the parcel, even a co-owner farming the whole of it
        # (own share plus the rented one, TUIR art. 33).
        voci.append(Voce("REDDITO_AGRARIO", "Reddito agrario",
                         ruoli.conduttori or titolari, "TUIR artt. 32, 33"))
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
    return RiepilogoBene(data=d, voci=voci_riepilogo(ruoli, bene.tipo_bene), avvisi=ruoli.avvisi)
