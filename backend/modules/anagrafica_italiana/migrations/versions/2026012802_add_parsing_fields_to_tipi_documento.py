"""add parsing fields to anag_tipi_documento

Revision ID: 2026012802_add_parsing_fields
Revises: 2026012501_add_comuni_attivo
Create Date: 2026-01-28
"""

from alembic import op, context
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "2026012802_add_parsing_fields"
down_revision = "2026012501_add_comuni_attivo"
branch_labels = None
depends_on = None

# Run only in public schema
target_schema = "public"


def upgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if schema != "public":
        return

    op.execute(text("""
        ALTER TABLE public.anag_tipi_documento
        ADD COLUMN IF NOT EXISTS parsing_service VARCHAR(50)
    """))

    op.execute(text("""
        ALTER TABLE public.anag_tipi_documento
        ADD COLUMN IF NOT EXISTS parsing_config JSON
    """))

    op.execute(text("""
        ALTER TABLE public.anag_tipi_documento
        ADD COLUMN IF NOT EXISTS parsing_callback_url VARCHAR(255)
    """))


def downgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if schema != "public":
        return
    # No destructive downgrade for domain data
    pass
