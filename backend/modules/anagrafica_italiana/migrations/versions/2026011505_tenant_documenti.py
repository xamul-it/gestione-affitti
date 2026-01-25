"""anagrafica tenant documenti

Revision ID: 2026011505_tenant_documenti
Revises: 2026011504_public_domain_fix
Create Date: 2026-01-21
"""

from alembic import op, context
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "2026011505_tenant_documenti"
down_revision = "2026011504_public_domain_fix"
branch_labels = None
depends_on = None

# Run only in tenant schemas
target_schema = "tenant"


def upgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS anag_documenti (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INTEGER NOT NULL,
            tipo_documento VARCHAR(50) NOT NULL,
            nome_file VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            mime_type VARCHAR(100),
            dimensione BIGINT,
            descrizione VARCHAR(500),
            note VARCHAR(500),
            data_scadenza DATE,
            tipo_documento_id INTEGER REFERENCES public.anag_tipi_documento(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """))

    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_documenti_entity_type ON anag_documenti(entity_type)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_documenti_entity_id ON anag_documenti(entity_id)"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_anag_documenti_data_scadenza ON anag_documenti(data_scadenza)"))


def downgrade() -> None:
    schema = context.get_x_argument(as_dictionary=True).get("schema")
    if not schema or schema == "public":
        return
    op.execute(text("DROP TABLE IF EXISTS anag_documenti CASCADE"))
