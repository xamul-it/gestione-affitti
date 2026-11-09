"""Manifest-owned fields on public.core_tipi_documento.

Document types are declared by modules in their manifest (document_types)
and synced into this table by app.core.platform_services.document_type_sync
(spec docs/superpowers/specs/2026-11-09-tipologie-documentali-moduli-design.md).
Add-column only: existing rows and their ids (referenced by documents) stay.

Revision ID: 2026110901
Revises: 2026103001
Create Date: 2026-11-09
"""
from alembic import op
import sqlalchemy as sa

revision = "2026110901"
down_revision = "2026103001"
branch_labels = None
depends_on = None

target_schema = "public"

_COLUMNS = (
    ("modulo", "VARCHAR(100)"),
    ("entity_types", "JSON"),
    ("regime", "VARCHAR(20) NOT NULL DEFAULT 'CUMULATIVO'"),
    ("sottotipi", "JSON"),
    ("scadenza", "JSON"),
    ("promemoria_giorni", "JSON"),
    ("form", "VARCHAR(100)"),
)


def upgrade() -> None:
    for name, ddl in _COLUMNS:
        op.execute(sa.text(f"ALTER TABLE public.core_tipi_documento ADD COLUMN IF NOT EXISTS {name} {ddl}"))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.execute(sa.text(f"ALTER TABLE public.core_tipi_documento DROP COLUMN IF EXISTS {name}"))
