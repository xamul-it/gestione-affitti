"""Relation type families on public.core_ruoli_disponibili.

Adds `famiglia` (grouping of the types: diritti_reali, godimento, incarichi),
`ammette_quota` (the relation may carry a share) and `solo_beni` (the type
applies to beni only), declared by modules in the manifest relation_types
(app.core.platform_services.relation_type_sync). Add-column only.

Revision ID: 2026112501
Revises: 2026111003
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "2026112501"
down_revision = "2026111003"
branch_labels = None
depends_on = None

target_schema = "public"

_COLUMNS = (
    ("famiglia", "VARCHAR(30)"),
    ("ammette_quota", "BOOLEAN NOT NULL DEFAULT false"),
    ("solo_beni", "BOOLEAN NOT NULL DEFAULT false"),
)


def upgrade() -> None:
    for name, ddl in _COLUMNS:
        op.execute(sa.text(f"ALTER TABLE public.core_ruoli_disponibili ADD COLUMN IF NOT EXISTS {name} {ddl}"))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.execute(sa.text(f"ALTER TABLE public.core_ruoli_disponibili DROP COLUMN IF EXISTS {name}"))
