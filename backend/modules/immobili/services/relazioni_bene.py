"""
Relations of a bene (rights, tenancies, assignments) on top of the core
relations (core_relazioni, entity_type IMMOBILE). The rules (shares, duplicates,
dates, module gate) live in RelazioneService; here only what is specific to
beni: which types apply, the registration data of a comodato, the warning on
shares above the whole, and the per-bene-type visibility hook.

Tenancies and assignments can also sit on a raggruppamento (entity_type
RAGGRUPPAMENTO, phase 4a): they hold for every bene below it.
relazioni_effettive() is the one place that adds them to the bene's own.
"""
from dataclasses import dataclass
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

from ..models import Bene, Raggruppamento
from .raggruppamenti import antenati

ENTITY_TYPE = "IMMOBILE"
ENTITY_TYPE_RAMO = "RAGGRUPPAMENTO"
MODULO = "immobili"
FAMIGLIE = ("diritti_reali", "godimento", "incarichi")

# Units are seen with immobile.view, land parcels with terreno.view.
# Writes need the ".edit" counterpart (immobile.edit / terreno.edit).
PERMESSO_PER_TIPO = {"UNITA": "immobile.view", "TERRENO": "terreno.view"}

# Right type of the old rights table (TipoDiritto name) -> relation type of the diritti_reali family.
# A co-owner is just an owner with a share.
MAPPA_TIPO_DIRITTO: Dict[str, str] = {
    "PROPRIETARIO": "proprieta",
    "COMPROPRIETARIO": "proprieta",
    "NUDA_PROPRIETA": "nuda_proprieta",
    "USUFRUTTUARIO": "usufrutto",
    "USO": "uso",
    "ABITAZIONE": "abitazione",
    "SUPERFICIE": "superficie",
    "ENFITEUSI": "enfiteusi",
    "ALTRO": "diritto_reale_altro",
}

# Registration of a comodato: keys of `dati`.
_REGISTRAZIONE = ("registrazione_data", "registrazione_ufficio", "registrazione_numero")


def permessi_vista(db: Session, tenant_schema: Optional[str]) -> sa.Select:
    """Hook object_permissions of the manifest: (entity_id, permesso) of every bene, in one select."""
    b = Bene.__table__.c
    permesso = sa.case(*[(b.tipo_bene == tipo, p) for tipo, p in PERMESSO_PER_TIPO.items()], else_=None)
    return sa.select(b.id.label("entity_id"), permesso.label("permesso")).where(permesso.isnot(None))


# (ramo, view permission) for every bene type found in the ramo's subtree; a ramo with no beni
# below is seen with either view permission.
_VISTA_RAMI_SQL = """
    WITH RECURSIVE giu(radice, id, livello) AS (
        SELECT id, id, 0 FROM immo_raggruppamenti
        UNION ALL
        SELECT giu.radice, r.id, giu.livello + 1
        FROM immo_raggruppamenti r JOIN giu ON r.padre_id = giu.id
        WHERE giu.livello < 100
    ),
    tipi AS (
        SELECT DISTINCT giu.radice, b.tipo_bene FROM giu JOIN immo_beni b ON b.raggruppamento_id = giu.id
    )
    SELECT radice AS entity_id,
           CASE tipo_bene WHEN 'UNITA' THEN 'immobile.view' WHEN 'TERRENO' THEN 'terreno.view' END AS permesso
    FROM tipi
    UNION ALL
    SELECT r.id, p.permesso
    FROM immo_raggruppamenti r CROSS JOIN (VALUES ('immobile.view'), ('terreno.view')) AS p(permesso)
    WHERE NOT EXISTS (SELECT 1 FROM tipi WHERE tipi.radice = r.id)
"""


def permessi_vista_raggruppamenti(db: Session, tenant_schema: Optional[str]):
    """Hook object_permissions for RAGGRUPPAMENTO: a ramo's relations hold for its beni, so they are
    seen with the view permission of at least one bene type below it (either one for an empty ramo)."""
    return sa.text(_VISTA_RAMI_SQL).columns(entity_id=sa.Integer, permesso=sa.String)


def permessi_vista_ramo(db: Session, raggruppamento_id: int) -> set:
    """View permissions that each allow reading the ramo's relations."""
    sub = permessi_vista_raggruppamenti(db, None).subquery()
    return {r[0] for r in db.execute(sa.select(sub.c.permesso).where(sub.c.entity_id == raggruppamento_id)) if r[0]}


# bene type -> permission needed to change what its beni inherit.
PERMESSO_MODIFICA_PER_TIPO = {"UNITA": "immobile.edit", "TERRENO": "terreno.edit"}

# (ramo, edit permission) for every bene type found in the ramo's subtree.
_MODIFICA_RAMI_SQL = """
    WITH RECURSIVE giu(radice, id, livello) AS (
        SELECT id, id, 0 FROM immo_raggruppamenti
        UNION ALL
        SELECT giu.radice, r.id, giu.livello + 1
        FROM immo_raggruppamenti r JOIN giu ON r.padre_id = giu.id
        WHERE giu.livello < 100
    )
    SELECT DISTINCT giu.radice AS entity_id,
           CASE b.tipo_bene WHEN 'UNITA' THEN 'immobile.edit' WHEN 'TERRENO' THEN 'terreno.edit' END AS permesso
    FROM giu JOIN immo_beni b ON b.raggruppamento_id = giu.id
"""


def permessi_modifica_raggruppamenti(db: Session, tenant_schema: Optional[str]):
    """Hook object_edit_permissions for RAGGRUPPAMENTO: all these rows are required to write."""
    return sa.text(_MODIFICA_RAMI_SQL).columns(entity_id=sa.Integer, permesso=sa.String)


def permessi_modifica_ramo(db: Session, raggruppamento_id: int) -> set:
    """Edit permissions of every bene type below the ramo (empty for a ramo with no beni)."""
    sub = permessi_modifica_raggruppamenti(db, None).subquery()
    return {r[0] for r in db.execute(sa.select(sub.c.permesso).where(sub.c.entity_id == raggruppamento_id)) if r[0]}


_OGGETTO = {ENTITY_TYPE: "un bene", ENTITY_TYPE_RAMO: "un raggruppamento"}


def _tipo_del_bene(svc: RelazioneService, codice: str, entity_type: str = ENTITY_TYPE) -> RuoloDisponibile:
    try:
        tipo = svc.tipo(codice)
    except LookupError:
        raise ValueError(f"Tipo di relazione '{codice}' non valido per {_OGGETTO[entity_type]}")
    if tipo.modulo_id != MODULO or tipo.famiglia not in FAMIGLIE or entity_type not in (tipo.entity_types or []):
        raise ValueError(f"Il tipo '{tipo.nome_display}' non si applica a {_OGGETTO[entity_type]}")
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


def crea_relazione_raggruppamento(
    db: Session, tenant_schema: str, user_id: Optional[int], raggruppamento_id: int, soggetto_id: int,
    tipo: str, *, quota: Union[str, Tuple[int, int], None] = None, data_inizio: Optional[date] = None,
    data_fine: Optional[date] = None, note: Optional[str] = None, dati: Optional[dict] = None,
) -> Tuple[Relazione, List[str]]:
    """A tenancy or an assignment on a ramo (rights stay on beni: their types do not list RAGGRUPPAMENTO)."""
    svc = RelazioneService(db, tenant_schema, user_id)
    tipo_row = _tipo_del_bene(svc, tipo, ENTITY_TYPE_RAMO)
    dati = _valida_dati(tipo_row, dati)
    if isinstance(quota, str):
        quota = parse_quota(quota)
    rel = svc.crea(
        soggetto_id, tipo, entity_type=ENTITY_TYPE_RAMO, entity_id=raggruppamento_id, data_inizio=data_inizio,
        data_fine=data_fine, note=note, dati=dati, quota=quota,
    )
    return rel, []


@dataclass
class RelazioneEffettiva:
    relazione: Relazione
    tipo: RuoloDisponibile
    provenienza: Optional[Raggruppamento]  # None = the bene's own relation


def _valida_il(rel: Relazione, d: date) -> bool:
    return (rel.data_inizio is None or rel.data_inizio <= d) and (rel.data_fine is None or rel.data_fine >= d)


def _relazioni_di(db: Session, oggetti: List[Tuple[str, int]]) -> List[Tuple[Relazione, RuoloDisponibile]]:
    if not oggetti:
        return []
    filtro = sa.or_(*[sa.and_(Relazione.entity_type == et, Relazione.entity_id == eid) for et, eid in oggetti])
    return (
        db.query(Relazione, RuoloDisponibile)
        .join(RuoloDisponibile, RuoloDisponibile.id == Relazione.ruolo_id)
        .filter(filtro, RuoloDisponibile.modulo_id == MODULO, RuoloDisponibile.famiglia.in_(FAMIGLIE))
        .order_by(Relazione.id)
        .all()
    )


def relazioni_effettive(db: Session, bene_id: int, d: Optional[date] = None) -> List[RelazioneEffettiva]:
    """The bene's relations plus those of every ramo above it (today's tree); with d, only those valid on d."""
    bene = db.get(Bene, bene_id)
    if bene is None:
        return []
    rami = {r.id: r for r in antenati(db, bene.raggruppamento_id)} if bene.raggruppamento_id else {}
    oggetti = [(ENTITY_TYPE, bene_id)] + [(ENTITY_TYPE_RAMO, rid) for rid in rami]
    out = [
        RelazioneEffettiva(r, t, rami.get(r.entity_id) if r.entity_type == ENTITY_TYPE_RAMO else None)
        for r, t in _relazioni_di(db, oggetti)
    ]
    return [x for x in out if d is None or _valida_il(x.relazione, d)]


def _per_famiglia(db: Session, righe: List[RelazioneEffettiva], solo_correnti: bool) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {f: [] for f in FAMIGLIE}
    righe = [x for x in righe if not solo_correnti or e_corrente(x.relazione.data_fine)]
    if not righe:
        return out
    ids = sorted({x.relazione.soggetto_id for x in righe})
    nomi = {
        s.id: RelazioneService._nome(s)
        for s in db.execute(
            text("SELECT id, nome, cognome, ragione_sociale FROM anag_soggetti_anagrafici WHERE id = ANY(:ids)"),
            {"ids": ids},
        )
    }
    # Open first, then the most recent start; id for a stable order.
    righe.sort(key=lambda x: (not e_corrente(x.relazione.data_fine),
                              -(x.relazione.data_inizio.toordinal() if x.relazione.data_inizio else 0),
                              x.relazione.id))
    for x in righe:
        r, t, ramo = x.relazione, x.tipo, x.provenienza
        out[t.famiglia].append({
            "id": r.id, "tipo": t.codice, "tipo_nome": t.nome_display,
            "soggetto_id": r.soggetto_id, "soggetto_nome": nomi.get(r.soggetto_id, f"Anagrafica {r.soggetto_id}"),
            "quota_numeratore": r.quota_numeratore, "quota_denominatore": r.quota_denominatore,
            "quota": r.quota, "data_inizio": r.data_inizio, "data_fine": r.data_fine,
            "note": r.note, "dati": r.dati,
            "provenienza": ({"raggruppamento_id": ramo.id, "nome": ramo.nome, "tipo": ramo.tipo} if ramo else None),
        })
    return out


def relazioni_del_bene(db: Session, tenant_schema: Optional[str], bene_id: int,
                       solo_correnti: bool = False) -> Dict[str, List[dict]]:
    """Relations of a bene, own and inherited from its rami, grouped by family (every family present)."""
    return _per_famiglia(db, relazioni_effettive(db, bene_id), solo_correnti)


def relazioni_del_raggruppamento(db: Session, tenant_schema: Optional[str], raggruppamento_id: int,
                                 solo_correnti: bool = False) -> Dict[str, List[dict]]:
    """Own relations of a ramo, grouped by family."""
    righe = [RelazioneEffettiva(r, t, None) for r, t in _relazioni_di(db, [(ENTITY_TYPE_RAMO, raggruppamento_id)])]
    return _per_famiglia(db, righe, solo_correnti)
