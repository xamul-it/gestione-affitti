"""add tipi_documento_overrides table

Revision ID: 2026010901_add_tipi_documento_overrides
Revises: add_tenant_module_config
Create Date: 2026-01-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026010901_add_tipi_documento_overrides"
down_revision = "add_tenant_module_config"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tipi_documento_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo_documento_id", sa.Integer(), nullable=False, index=True),
        sa.Column("codice", sa.String(length=50), nullable=True),
        sa.Column("nome", sa.String(length=100), nullable=True),
        sa.Column("descrizione", sa.String(length=255), nullable=True),
        sa.Column("categoria", sa.String(length=50), nullable=True),
        sa.Column("richiede_scadenza", sa.Boolean(), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tipo_documento_id"],
            ["public.tipi_documento.id"],
            ondelete="CASCADE"
        ),
        sa.UniqueConstraint("tipo_documento_id", name="ix_tipi_documento_overrides_tipo"),
        schema="public",
    )


def downgrade():
    op.drop_table("tipi_documento_overrides", schema="public")
