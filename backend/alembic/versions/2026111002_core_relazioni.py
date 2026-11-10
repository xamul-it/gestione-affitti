"""Tenant table core_relazioni: role relations soggetto -> object.

Spec docs/superpowers/specs/2026-11-10-relazioni-ruoli-soggetti-design.md.
Create-only; public.core_soggetti_ruoli (shared, empty) is left untouched.

Revision ID: 2026111002
Revises: 2026111001
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

revision = "2026111002"
down_revision = "2026111001"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS core_relazioni (
            id SERIAL PRIMARY KEY,
            soggetto_id INTEGER NOT NULL,
            ruolo_id INTEGER NOT NULL REFERENCES public.core_ruoli_disponibili(id),
            entity_type VARCHAR(50),
            entity_id INTEGER,
            sottotipo VARCHAR(100),
            data_inizio DATE,
            data_fine DATE,
            data_scadenza DATE,
            scadenza_id INTEGER REFERENCES core_scadenze(id) ON DELETE SET NULL,
            note TEXT,
            dati JSON,
            creato_da INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS ix_core_relazioni_soggetto ON core_relazioni (soggetto_id);
        CREATE INDEX IF NOT EXISTS ix_core_relazioni_oggetto ON core_relazioni (entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS ix_core_relazioni_ruolo ON core_relazioni (ruolo_id);
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS core_relazioni"))
