"""
Relations of a bene (rights, tenancies, assignments) on top of the core
relations (core_relazioni, entity_type IMMOBILE). The rules (shares, duplicates,
dates, module gate) live in RelazioneService; here only what is specific to
beni: which types apply, the registration data of a comodato, the warning on
shares above the whole, and the per-bene-type visibility hook.
"""
from datetime import date
from fractions import Fraction
from typing import Dict, List, Optional, Tuple, Union

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform.models import Relazione
from app.core.platform_services.quote import parse_quota
from app.core.platform_services.relazione_service import RelazioneService, e_corrente

from ..models import Bene

ENTITY_TYPE = "IMMOBILE"
MODULO = "immobili"
FAMIGLIE = ("diritti_reali", "godimento", "incarichi")

# Units are seen with immobile.view, land parcels with terreno.view.
# Writes need the ".edit" counterpart (immobile.edit / terreno.edit).
PERMESSO_PER_TIPO = {"UNITA": "immobile.view", "TERRENO": "terreno.view"}

# Registration of a comodato: keys of `dati`.
_REGISTRAZIONE = ("registrazione_data", "registrazione_ufficio", "registrazione_numero")


def permessi_vista(db: Session, tenant_schema: Optional[str]) -> sa.Select:
    """Hook object_permissions of the manifest: (entity_id, permesso) of every bene, in one select."""
    b = Bene.__table__.c
    permesso = sa.case(*[(b.tipo_bene == tipo, p) for tipo, p in PERMESSO_PER_TIPO.items()], else_=None)
    return sa.select(b.id.label("entity_id"), permesso.label("permesso")).where(permesso.isnot(None))


def _tipo_del_bene(svc: RelazioneService, codice: str) -> RuoloDisponibile:
    try:
        tipo = svc.tipo(codice)
    except LookupError:
        raise ValueError(f"Tipo di relazione '{codice}' non valido per un bene")
    if tipo.modulo_id != MODULO or tipo.famiglia not in FAMIGLIE or ENTITY_TYPE not in (tipo.entity_types or []):
        raise ValueError(f"Il tipo '{tipo.nome_display}' non si applica a un bene")
    return tipo


def _valida_dati(tipo: RuoloDisponibile, dati: Optional[dict]) -> Optional[dict]:
    """Registration of a comodato: ISO date, office and number as text."""
    if tipo.codice != "comodatario" or not dati:
        return dati
    data = dati.get("registrazione_data")
    if data not in (None, ""):
        try:
            date.fromisoformat(str(data))
        except ValueError:
            raise ValueError("La data di registrazione deve essere nel formato AAAA-MM-GG")
    for chiave in _REGISTRAZIONE[1:]:
        if dati.get(chiave) is not None and not isinstance(dati[chiave], (str, int)):
            raise ValueError(f"'{chiave}' non è valido")
    return dati


def somma_quote_aperte(db: Session, bene_id: int, tipo: str) -> Fraction:
    """Exact sum of the shares of the open relations of a type on a bene."""
    righe = (
        db.query(Relazione)
        .join(RuoloDisponibile, RuoloDisponibile.id == Relazione.ruolo_id)
        .filter(RuoloDisponibile.codice == tipo, RuoloDisponibile.modulo_id == MODULO,
                Relazione.entity_type == ENTITY_TYPE, Relazione.entity_id == bene_id,
                Relazione.quota_numeratore.isnot(None))
        .all()
    )
    return sum((r.quota_frazione for r in righe if e_corrente(r.data_fine)), Fraction(0))


def crea_relazione_bene(
    db: Session, tenant_schema: str, user_id: Optional[int], bene_id: int, soggetto_id: int, tipo: str, *,
    quota: Union[str, Tuple[int, int], None] = None, data_inizio: Optional[date] = None,
    data_fine: Optional[date] = None, note: Optional[str] = None, dati: Optional[dict] = None,
) -> Tuple[Relazione, List[str]]:
    """Creates the relation (flush only) and returns it with the warnings (shares above the whole).
    ValueError: invalid input; LookupError: bene or anagrafica not found."""
    svc = RelazioneService(db, tenant_schema, user_id)
    tipo_row = _tipo_del_bene(svc, tipo)
    dati = _valida_dati(tipo_row, dati)
    if isinstance(quota, str):
        quota = parse_quota(quota)
    rel = svc.crea(
        soggetto_id, tipo, entity_type=ENTITY_TYPE, entity_id=bene_id, data_inizio=data_inizio,
        data_fine=data_fine, note=note, dati=dati, quota=quota,
    )
    avvisi: List[str] = []
    if rel.quota_numeratore is not None and e_corrente(rel.data_fine):
        somma = somma_quote_aperte(db, bene_id, tipo)
        if somma > 1:
            avvisi.append(f"Le quote di {tipo_row.nome_display} sul bene superano l'intero ({somma})")
    return rel, avvisi


def relazioni_del_bene(db: Session, tenant_schema: Optional[str], bene_id: int,
                       solo_correnti: bool = False) -> Dict[str, List[dict]]:
    """Relations of a bene grouped by family (every family present, possibly empty)."""
    out: Dict[str, List[dict]] = {f: [] for f in FAMIGLIE}
    query = (
        db.query(Relazione, RuoloDisponibile)
        .join(RuoloDisponibile, RuoloDisponibile.id == Relazione.ruolo_id)
        .filter(Relazione.entity_type == ENTITY_TYPE, Relazione.entity_id == bene_id,
                RuoloDisponibile.modulo_id == MODULO, RuoloDisponibile.famiglia.in_(FAMIGLIE))
    )
    righe = [(r, t) for r, t in query.all() if not solo_correnti or e_corrente(r.data_fine)]
    if not righe:
        return out
    ids = sorted({r.soggetto_id for r, _ in righe})
    nomi = {
        s.id: RelazioneService._nome(s)
        for s in db.execute(
            text("SELECT id, nome, cognome, ragione_sociale FROM anag_soggetti_anagrafici WHERE id = ANY(:ids)"),
            {"ids": ids},
        )
    }
    # Open first, then the most recent start; id for a stable order.
    righe.sort(key=lambda rt: (not e_corrente(rt[0].data_fine), -(rt[0].data_inizio.toordinal() if rt[0].data_inizio else 0), rt[0].id))
    for r, t in righe:
        out[t.famiglia].append({
            "id": r.id, "tipo": t.codice, "tipo_nome": t.nome_display,
            "soggetto_id": r.soggetto_id, "soggetto_nome": nomi.get(r.soggetto_id, f"Anagrafica {r.soggetto_id}"),
            "quota_numeratore": r.quota_numeratore, "quota_denominatore": r.quota_denominatore,
            "quota": r.quota, "data_inizio": r.data_inizio, "data_fine": r.data_fine,
            "note": r.note, "dati": r.dati,
        })
    return out
