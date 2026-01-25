"""rename documenti table to anag_documenti

Revision ID: 2026011506_rename_documenti
Revises: 2026011505_tenant_documenti
Create Date: 2026-01-21
"""

from alembic import op, context
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "2026011506_rename_documenti"
down_revision = "2026011505_tenant_documenti"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return

    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'documenti'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'anag_documenti'
            ) THEN
                EXECUTE format('ALTER TABLE %I.documenti RENAME TO anag_documenti', :schema);
            END IF;
        END $$;
    """).bindparams(schema=schema))


def downgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return

    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'anag_documenti'
            ) AND NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'documenti'
            ) THEN
                EXECUTE format('ALTER TABLE %I.anag_documenti RENAME TO documenti', :schema);
            END IF;
        END $$;
    """).bindparams(schema=schema))
