"""add terreni and tipologie_terreno tables

Revision ID: 2026010901
Revises: 2025122702
Create Date: 2026-01-09
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026010901"
down_revision = "2025122702"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create tipologie_terreno table in public schema (domain data)
    op.create_table(
        "tipologie_terreno",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codice", sa.String(length=10), nullable=False, unique=True, index=True),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("ordinamento", sa.Integer(), default=0),
        sa.Column("attiva", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True, index=True),  # null = platform, value = tenant-specific
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )

    op.create_index(
        "ix_tipologie_terreno_codice",
        "tipologie_terreno",
        ["codice"],
        schema="public",
    )
    op.create_index(
        "ix_tipologie_terreno_tenant_id",
        "tipologie_terreno",
        ["tenant_id"],
        schema="public",
    )
    op.create_index(
        "ix_tipologie_terreno_attiva",
        "tipologie_terreno",
        ["attiva"],
        schema="public",
    )

    # 2. Create terreni table in public schema (structure for tenant copy)
    op.create_table(
        "terreni",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codice", sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        # FK to public.tipologie_terreno
        sa.Column(
            "tipologia_id",
            sa.Integer(),
            sa.ForeignKey("public.tipologie_terreno.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # Location
        sa.Column("indirizzo", sa.String(length=255), nullable=True),
        sa.Column("comune", sa.String(length=100), nullable=False),
        sa.Column("cap", sa.String(length=10), nullable=True),
        sa.Column("provincia", sa.String(length=2), nullable=False),
        sa.Column("nazione", sa.String(length=100), nullable=True, server_default=sa.text("'Italia'")),
        # Physical characteristics
        sa.Column("superficie", sa.Float(), nullable=False),
        sa.Column("unita_misura_superficie", sa.String(length=10), nullable=True, server_default=sa.text("'mq'")),
        # Cadastral data
        sa.Column("sezione_catastale", sa.String(length=20), nullable=True),
        sa.Column("foglio", sa.String(length=20), nullable=True),
        sa.Column("particella", sa.String(length=20), nullable=True),
        sa.Column("subalterno", sa.String(length=20), nullable=True),
        sa.Column("qualita_coltura", sa.String(length=100), nullable=True),
        sa.Column("classe_catastale", sa.String(length=10), nullable=True),
        # Fiscal values
        sa.Column("reddito_dominicale", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reddito_agrario", sa.Numeric(precision=12, scale=2), nullable=True),
        # Notes and status
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )

    op.create_index(
        "ix_terreni_codice",
        "terreni",
        ["codice"],
        schema="public",
    )
    op.create_index(
        "ix_terreni_tipologia_id",
        "terreni",
        ["tipologia_id"],
        schema="public",
    )
    op.create_index(
        "ix_terreni_attivo",
        "terreni",
        ["attivo"],
        schema="public",
    )
    op.create_index(
        "ix_terreni_comune",
        "terreni",
        ["comune"],
        schema="public",
    )
    op.create_index(
        "ix_terreni_provincia",
        "terreni",
        ["provincia"],
        schema="public",
    )


def downgrade() -> None:
    # Drop terreni indexes and table
    op.drop_index("ix_terreni_provincia", table_name="terreni", schema="public")
    op.drop_index("ix_terreni_comune", table_name="terreni", schema="public")
    op.drop_index("ix_terreni_attivo", table_name="terreni", schema="public")
    op.drop_index("ix_terreni_tipologia_id", table_name="terreni", schema="public")
    op.drop_index("ix_terreni_codice", table_name="terreni", schema="public")
    op.drop_table("terreni", schema="public")

    # Drop tipologie_terreno indexes and table
    op.drop_index("ix_tipologie_terreno_attiva", table_name="tipologie_terreno", schema="public")
    op.drop_index("ix_tipologie_terreno_tenant_id", table_name="tipologie_terreno", schema="public")
    op.drop_index("ix_tipologie_terreno_codice", table_name="tipologie_terreno", schema="public")
    op.drop_table("tipologie_terreno", schema="public")
