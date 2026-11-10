"""
Relation providers of the affitti_lungo module (fonte MODULO): see
immobili/relations.py for the column contract.
"""
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .models.affittuari import Affittuario
from .models.tecnici import Tecnico


def _has_table(db: Session, schema: str, table: str) -> bool:
    return inspect(db.get_bind()).has_table(table, schema=schema)


def affittuari(db: Session, tenant_schema: str) -> Optional[sa.Select]:
    if not _has_table(db, tenant_schema, "affittuari"):
        return None
    a = Affittuario.__table__.c
    return sa.select(
        a.soggetto_id.label("soggetto_id"),
        sa.cast(sa.null(), sa.String).label("entity_type"),
        sa.cast(sa.null(), sa.Integer).label("entity_id"),
        sa.cast(sa.null(), sa.String).label("descrizione"),
        sa.cast(sa.null(), sa.Date).label("data_inizio"),
        sa.cast(sa.null(), sa.Date).label("data_fine"),
        a.id.label("record_id"),
    ).where(a.soggetto_id.isnot(None))


def tecnici(db: Session, tenant_schema: str) -> Optional[sa.Select]:
    if not _has_table(db, tenant_schema, "tecnici"):
        return None
    t = Tecnico.__table__.c
    return sa.select(
        t.soggetto_id.label("soggetto_id"),
        sa.cast(sa.null(), sa.String).label("entity_type"),
        sa.cast(sa.null(), sa.Integer).label("entity_id"),
        sa.cast(t.specializzazione, sa.String).label("descrizione"),
        sa.cast(sa.null(), sa.Date).label("data_inizio"),
        # An inactive technician counts as ended.
        sa.case((t.attivo.is_(False), sa.cast(sa.func.coalesce(t.updated_at, t.created_at), sa.Date)),
                else_=None).label("data_fine"),
        t.id.label("record_id"),
    ).where(t.soggetto_id.isnot(None))
