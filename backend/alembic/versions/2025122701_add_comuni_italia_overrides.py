"""add comuni_italia_overrides table

Revision ID: 2025122701
Revises: add_tenant_module_config
Create Date: 2025-12-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2025122701"
down_revision = "add_tenant_module_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure comuni_italia is in public schema (no-op if already there)
    op.execute("ALTER TABLE IF EXISTS comuni_italia SET SCHEMA public")

    op.create_table(
        "comuni_italia_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("comune_id", sa.Integer(), sa.ForeignKey("public.comuni_italia.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=True),
        sa.Column("nome_normalized", sa.String(length=100), nullable=True),
        sa.Column("codice_istat", sa.String(length=10), nullable=True),
        sa.Column("codice_catastale", sa.String(length=10), nullable=True),
        sa.Column("cap", sa.String(length=10), nullable=True),
        sa.Column("provincia_sigla", sa.String(length=2), nullable=True),
        sa.Column("provincia_nome", sa.String(length=100), nullable=True),
        sa.Column("regione", sa.String(length=100), nullable=True),
        sa.Column("latitudine", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitudine", sa.Numeric(10, 7), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )

    op.create_index(
        "ix_comuni_italia_overrides_tenant_id",
        "comuni_italia_overrides",
        ["tenant_id"],
        schema="public",
    )
    op.create_index(
        "ix_comuni_italia_overrides_comune_id",
        "comuni_italia_overrides",
        ["comune_id"],
        schema="public",
    )
    op.create_index(
        "ix_comuni_italia_overrides_is_deleted",
        "comuni_italia_overrides",
        ["is_deleted"],
        schema="public",
    )
    op.create_index(
        "ix_comuni_italia_overrides_tenant_comune",
        "comuni_italia_overrides",
        ["tenant_id", "comune_id"],
        unique=True,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_comuni_italia_overrides_tenant_comune",
        table_name="comuni_italia_overrides",
        schema="public",
    )
    op.drop_index(
        "ix_comuni_italia_overrides_is_deleted",
        table_name="comuni_italia_overrides",
        schema="public",
    )
    op.drop_index(
        "ix_comuni_italia_overrides_comune_id",
        table_name="comuni_italia_overrides",
        schema="public",
    )
    op.drop_index(
        "ix_comuni_italia_overrides_tenant_id",
        table_name="comuni_italia_overrides",
        schema="public",
    )
    op.drop_table("comuni_italia_overrides", schema="public")
