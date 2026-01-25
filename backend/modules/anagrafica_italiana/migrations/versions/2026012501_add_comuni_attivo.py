"""add attivo column to comuni

Revision ID: 2026012501_add_comuni_attivo
Revises: 2026011506_rename_documenti
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa

revision = "2026012501_add_comuni_attivo"
down_revision = "2026011506_rename_documenti"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE public.anag_comuni_italia ADD COLUMN IF NOT EXISTS attivo BOOLEAN DEFAULT TRUE")
    op.execute("UPDATE public.anag_comuni_italia SET attivo = TRUE WHERE attivo IS NULL")


def downgrade():
    op.execute("ALTER TABLE public.anag_comuni_italia DROP COLUMN IF EXISTS attivo")
