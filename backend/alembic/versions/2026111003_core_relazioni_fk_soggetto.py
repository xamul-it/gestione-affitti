"""core_relazioni.soggetto_id -> anag_soggetti_anagrafici ON DELETE CASCADE.

Safety net against orphan relations when an anagrafica disappears outside the
API (the delete routes refuse anagrafiche that still have relations).
Skipped in schemas without anag_soggetti_anagrafici.

Revision ID: 2026111003
Revises: 2026111002
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

revision = "2026111003"
down_revision = "2026111002"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF to_regclass('anag_soggetti_anagrafici') IS NOT NULL
               AND to_regclass('core_relazioni') IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1 FROM pg_constraint
                    WHERE conname = 'fk_core_relazioni_soggetto'
                      AND conrelid = to_regclass('core_relazioni')
               ) THEN
                DELETE FROM core_relazioni r
                 WHERE NOT EXISTS (SELECT 1 FROM anag_soggetti_anagrafici s WHERE s.id = r.soggetto_id);
                ALTER TABLE core_relazioni
                  ADD CONSTRAINT fk_core_relazioni_soggetto FOREIGN KEY (soggetto_id)
                  REFERENCES anag_soggetti_anagrafici(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE core_relazioni DROP CONSTRAINT IF EXISTS fk_core_relazioni_soggetto"))
