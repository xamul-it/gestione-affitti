"""Share (quota) on core_relazioni, stored as a fraction.

quota_numeratore / quota_denominatore are both set or both null; the share
is positive and at most 1 (numerator <= denominator). Skipped in schemas
without core_relazioni. Idempotent.

Revision ID: 2026112502
Revises: 2026112501
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "2026112502"
down_revision = "2026112501"
branch_labels = None
depends_on = None

target_schema = "tenant"

_CHECK = """
    CHECK ((quota_numeratore IS NULL) = (quota_denominatore IS NULL)
           AND (quota_numeratore IS NULL
                OR (quota_numeratore > 0 AND quota_numeratore <= quota_denominatore)))
"""


def upgrade() -> None:
    op.execute(sa.text(f"""
        DO $$
        BEGIN
            IF to_regclass('core_relazioni') IS NULL THEN
                RETURN;
            END IF;
            ALTER TABLE core_relazioni ADD COLUMN IF NOT EXISTS quota_numeratore INTEGER;
            ALTER TABLE core_relazioni ADD COLUMN IF NOT EXISTS quota_denominatore INTEGER;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                 WHERE conname = 'ck_core_relazioni_quota'
                   AND conrelid = to_regclass('core_relazioni')
            ) THEN
                ALTER TABLE core_relazioni ADD CONSTRAINT ck_core_relazioni_quota {_CHECK};
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE IF EXISTS core_relazioni DROP CONSTRAINT IF EXISTS ck_core_relazioni_quota"))
    op.execute(sa.text("ALTER TABLE IF EXISTS core_relazioni DROP COLUMN IF EXISTS quota_denominatore"))
    op.execute(sa.text("ALTER TABLE IF EXISTS core_relazioni DROP COLUMN IF EXISTS quota_numeratore"))
