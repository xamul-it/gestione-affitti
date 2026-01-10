"""add ruoli_azienda_tipi_overrides table

Revision ID: 2025122702
Revises: 2025122701
Create Date: 2025-12-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2025122702"
down_revision = "2025122701"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS ruoli_azienda_tipi SET SCHEMA public")

    op.create_table(
        "ruoli_azienda_tipi_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "ruolo_tipo_id",
            sa.Integer(),
            sa.ForeignKey("public.ruoli_azienda_tipi.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(length=100), nullable=True),
        sa.Column("descrizione", sa.String(length=500), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )

    op.create_index(
        "ix_ruoli_azienda_tipi_overrides_tenant_id",
        "ruoli_azienda_tipi_overrides",
        ["tenant_id"],
        schema="public",
    )
    op.create_index(
        "ix_ruoli_azienda_tipi_overrides_ruolo_tipo_id",
        "ruoli_azienda_tipi_overrides",
        ["ruolo_tipo_id"],
        schema="public",
    )
    op.create_index(
        "ix_ruoli_azienda_tipi_overrides_is_deleted",
        "ruoli_azienda_tipi_overrides",
        ["is_deleted"],
        schema="public",
    )
    op.create_index(
        "ix_ruoli_azienda_tipi_overrides_tenant_ruolo",
        "ruoli_azienda_tipi_overrides",
        ["tenant_id", "ruolo_tipo_id"],
        unique=True,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ruoli_azienda_tipi_overrides_tenant_ruolo",
        table_name="ruoli_azienda_tipi_overrides",
        schema="public",
    )
    op.drop_index(
        "ix_ruoli_azienda_tipi_overrides_is_deleted",
        table_name="ruoli_azienda_tipi_overrides",
        schema="public",
    )
    op.drop_index(
        "ix_ruoli_azienda_tipi_overrides_ruolo_tipo_id",
        table_name="ruoli_azienda_tipi_overrides",
        schema="public",
    )
    op.drop_index(
        "ix_ruoli_azienda_tipi_overrides_tenant_id",
        table_name="ruoli_azienda_tipi_overrides",
        schema="public",
    )
    op.drop_table("ruoli_azienda_tipi_overrides", schema="public")
