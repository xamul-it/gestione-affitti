"""add stati_documento tables

Revision ID: 2026010902_add_stati_documento
Revises: 2026010901_add_tipi_documento_overrides
Create Date: 2026-01-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026010902_add_stati_documento"
down_revision = "2026010901_add_tipi_documento_overrides"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stati_documento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codice", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descrizione", sa.String(length=255), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("codice"),
        schema="public",
    )

    op.create_table(
        "stati_documento_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stato_documento_id", sa.Integer(), nullable=False, index=True),
        sa.Column("codice", sa.String(length=20), nullable=True),
        sa.Column("nome", sa.String(length=100), nullable=True),
        sa.Column("descrizione", sa.String(length=255), nullable=True),
        sa.Column("attivo", sa.Boolean(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["stato_documento_id"],
            ["public.stati_documento.id"],
            ondelete="CASCADE"
        ),
        sa.UniqueConstraint("stato_documento_id", name="ix_stati_documento_overrides_stato"),
        schema="public",
    )


def downgrade():
    op.drop_table("stati_documento_overrides", schema="public")
    op.drop_table("stati_documento", schema="public")
