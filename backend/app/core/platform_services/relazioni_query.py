"""
All role relations of a tenant as one query: core relations (core_relazioni,
fonte CORE) plus those derived by the module providers (fonte MODULO), see
docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md.

A provider is "module.path:function" in the catalog; it returns a select with
soggetto_id, entity_type, entity_id, descrizione, data_inizio, data_fine,
record_id, or None when the module tables are missing in the tenant.
"""
import importlib
import logging
from datetime import date
from typing import Dict, Iterable, List, Optional

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.models import RuoloDisponibile
from app.core.platform.models import Relazione
from app.core.platform_services.relazioni_moduli import moduli_attivi

logger = logging.getLogger(__name__)

# Readable name of the object of a core relation, per entity type.
_DESCRIZIONI_CORE = {
    "CONDOMINIO": ("immo_condomini", "COALESCE(NULLIF(o.nome, ''), concat_ws(', ', o.indirizzo, o.citta))"),
    "IMMOBILE": ("immo_unita_immobiliari", "concat_ws(', ', o.indirizzo, o.citta)"),
    "SOGGETTO_ANAGRAFICO": (
        "anag_soggetti_anagrafici",
        "COALESCE(NULLIF(o.ragione_sociale, ''), concat_ws(' ', o.cognome, o.nome))",
    ),
}


def _provider(path: str):
    module_name, func_name = path.split(":")
    return getattr(importlib.import_module(module_name), func_name)


def _tipi(db: Session, tenant_schema: Optional[str], tipo: Optional[str]) -> List[RuoloDisponibile]:
    """Active types of the modules enabled in the tenant."""
    q = db.query(RuoloDisponibile).filter(RuoloDisponibile.attivo.is_(True))
    attivi = moduli_attivi(db, tenant_schema)
    if attivi is not None:
        q = q.filter(RuoloDisponibile.modulo_id.in_(list(attivi)))
    if tipo:
        q = q.filter(RuoloDisponibile.codice == tipo)
    return q.order_by(RuoloDisponibile.id).all()


def _descrizione_core(db: Session, tenant_schema: str):
    inspector = inspect(db.get_bind())
    rami = []
    for entity_type, (tabella, expr) in _DESCRIZIONI_CORE.items():
        if inspector.has_table(tabella, schema=tenant_schema):
            rami.append(
                f"WHEN r.entity_type = '{entity_type}' THEN "
                f"(SELECT {expr} FROM {tabella} o WHERE o.id = r.entity_id)"
            )
    if not rami:
        return sa.cast(sa.null(), sa.String)
    return sa.literal_column(f"(CASE {' '.join(rami)} END)", sa.String)


def relazioni_select(db: Session, tenant_schema: str, *, tipo: Optional[str] = None) -> Optional[sa.Select]:
    """UNION ALL of core and module relations; None if there is nothing to select."""
    tipi = _tipi(db, tenant_schema, tipo)
    parti = []

    core = [t for t in tipi if t.fonte == "CORE"]
    if core and inspect(db.get_bind()).has_table("core_relazioni", schema=tenant_schema):
        r = sa.table(
            "core_relazioni", *(sa.column(c) for c in (
                "id", "soggetto_id", "ruolo_id", "entity_type", "entity_id", "sottotipo",
                "data_inizio", "data_fine", "data_scadenza",
            )),
        ).alias("r")
        k = RuoloDisponibile.__table__.c
        parti.append(
            sa.select(
                r.c.soggetto_id.label("soggetto_id"),
                k.codice.label("tipo"),
                k.nome_display.label("tipo_nome"),
                k.modulo_id.label("modulo"),
                k.fonte.label("fonte"),
                k.permesso_oggetto.label("permesso_oggetto"),
                r.c.id.label("relazione_id"),
                r.c.entity_type.label("entity_type"),
                r.c.entity_id.label("entity_id"),
                r.c.sottotipo.label("sottotipo"),
                _descrizione_core(db, tenant_schema).label("descrizione"),
                r.c.data_inizio.label("data_inizio"),
                r.c.data_fine.label("data_fine"),
                r.c.data_scadenza.label("data_scadenza"),
                sa.cast(sa.null(), sa.Integer).label("record_id"),
            )
            .select_from(r.join(RuoloDisponibile.__table__, k.id == r.c.ruolo_id))
            .where(k.id.in_([t.id for t in core]))
        )

    for t in tipi:
        if t.fonte != "MODULO" or not t.provider:
            continue
        try:
            sel = _provider(t.provider)(db, tenant_schema)
        except (ImportError, AttributeError, ValueError):
            logger.exception("Provider di relazione non valido: %s", t.provider)
            continue
        if sel is None:
            continue
        p = sel.subquery()
        parti.append(sa.select(
            p.c.soggetto_id,
            sa.literal(t.codice, sa.String).label("tipo"),
            sa.literal(t.nome_display, sa.String).label("tipo_nome"),
            sa.literal(t.modulo_id, sa.String).label("modulo"),
            sa.literal("MODULO", sa.String).label("fonte"),
            sa.literal(t.permesso_oggetto, sa.String).label("permesso_oggetto"),
            sa.cast(sa.null(), sa.Integer).label("relazione_id"),
            sa.cast(p.c.entity_type, sa.String).label("entity_type"),
            p.c.entity_id,
            sa.cast(sa.null(), sa.String).label("sottotipo"),
            sa.cast(p.c.descrizione, sa.String).label("descrizione"),
            p.c.data_inizio,
            p.c.data_fine,
            sa.cast(sa.null(), sa.Date).label("data_scadenza"),
            p.c.record_id,
        ))

    if not parti:
        return None
    return parti[0] if len(parti) == 1 else sa.union_all(*parti)


def _corrente(col):
    return sa.or_(col.is_(None), col >= sa.func.current_date())


def _filtrata(db, tenant_schema, *, permessi: set, tipo=None, soggetto_ids=None, entity_type=None,
              entity_id=None, solo_correnti=False):
    """Relations the caller may see: a type with permesso_oggetto needs that permission."""
    sel = relazioni_select(db, tenant_schema, tipo=tipo)
    if sel is None:
        return None
    u = sel.subquery("rel")
    q = sa.select(u)
    if "*" not in permessi:
        q = q.where(sa.or_(u.c.permesso_oggetto.is_(None), u.c.permesso_oggetto.in_(list(permessi))))
    if soggetto_ids is not None:
        q = q.where(u.c.soggetto_id.in_(list(soggetto_ids)))
    if entity_type:
        q = q.where(u.c.entity_type == entity_type)
    if entity_id is not None:
        q = q.where(u.c.entity_id == entity_id)
    if solo_correnti:
        q = q.where(_corrente(u.c.data_fine))
    return q, u


def elenca(db: Session, tenant_schema: str, *, permessi: set, soggetto_ids: Optional[Iterable[int]] = None,
           tipo: Optional[str] = None, entity_type: Optional[str] = None, entity_id: Optional[int] = None,
           solo_correnti: bool = False) -> List[dict]:
    """Relations as dicts, only those of the types the caller may see."""
    built = _filtrata(db, tenant_schema, permessi=permessi, tipo=tipo, soggetto_ids=soggetto_ids, entity_type=entity_type,
                      entity_id=entity_id, solo_correnti=solo_correnti)
    if built is None:
        return []
    q, u = built
    oggi = date.today()
    out = []
    for row in db.execute(q.order_by(u.c.tipo, u.c.soggetto_id, u.c.data_inizio)).mappings():
        r = dict(row)
        r.pop("permesso_oggetto")
        r["corrente"] = r["data_fine"] is None or r["data_fine"] >= oggi
        out.append(r)
    return out


def soggetti_con_ruolo(db: Session, tenant_schema: str, tipo: str, *, permessi: set,
                       solo_correnti: bool = True) -> sa.Select:
    """Select of the soggetto ids having a visible relation of `tipo` (for an IN filter)."""
    built = _filtrata(db, tenant_schema, permessi=permessi, tipo=tipo, solo_correnti=solo_correnti)
    if built is None:
        return sa.select(sa.cast(sa.null(), sa.Integer)).where(sa.false())
    f = built[0].subquery("vis")
    return sa.select(f.c.soggetto_id).distinct()


def ruoli_per_soggetti(db: Session, tenant_schema: str, soggetto_ids: Iterable[int], *,
                       permessi: set) -> Dict[int, List[dict]]:
    """{soggetto_id: [{codice, nome, modulo, n}]} of the visible relations, n = current ones; one query."""
    ids = list(soggetto_ids)
    if not ids:
        return {}
    built = _filtrata(db, tenant_schema, permessi=permessi, soggetto_ids=ids)
    if built is None:
        return {}
    u = built[0].subquery("vis")
    n = sa.func.count().filter(_corrente(u.c.data_fine))
    q = (sa.select(u.c.soggetto_id, u.c.tipo, u.c.tipo_nome, u.c.modulo, n.label("n"))
         .group_by(u.c.soggetto_id, u.c.tipo, u.c.tipo_nome, u.c.modulo)
         .order_by(u.c.soggetto_id, u.c.tipo))
    out: Dict[int, List[dict]] = {}
    for row in db.execute(q):
        out.setdefault(row.soggetto_id, []).append(
            {"codice": row.tipo, "nome": row.tipo_nome, "modulo": row.modulo, "n": row.n}
        )
    return out
