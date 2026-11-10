"""Manifest-owned fields on public.core_ruoli_disponibili.

Relation types are declared by modules in their manifest (relation_types)
and synced by app.core.platform_services.relation_type_sync (spec
docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md).
Add-column only.

Revision ID: 2026111001
Revises: 2026110902
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

revision = "2026111001"
down_revision = "2026110902"
branch_labels = None
depends_on = None

target_schema = "public"

_COLUMNS = (
    ("entity_types", "JSON"),
    ("fonte", "VARCHAR(10) NOT NULL DEFAULT 'CORE'"),
    ("provider", "VARCHAR(200)"),
    ("scadenza", "JSON"),
    ("promemoria_giorni", "JSON"),
    ("sottotipi_fonte", "VARCHAR(100)"),
    ("unico_per_oggetto", "BOOLEAN NOT NULL DEFAULT false"),
    ("permesso_oggetto", "VARCHAR(100)"),
)


def upgrade() -> None:
    for name, ddl in _COLUMNS:
        op.execute(sa.text(f"ALTER TABLE public.core_ruoli_disponibili ADD COLUMN IF NOT EXISTS {name} {ddl}"))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.execute(sa.text(f"ALTER TABLE public.core_ruoli_disponibili DROP COLUMN IF EXISTS {name}"))
