"""Add documento identità fields to SoggettoAnagrafico.

Adds tipo_documento_identita / numero_documento_identita /
stato_rilascio_documento so SimilarityMatchingService can match soggetti
by identity document, not just codice_fiscale — needed because affitti_brevi
guests are frequently foreign tourists without an Italian codice fiscale.

Revision ID: 2026092101
Revises: 2026013101
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "2026092101"
down_revision = "2026013101"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    op.add_column(
        "anag_soggetti_anagrafici",
        sa.Column("tipo_documento_identita", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "anag_soggetti_anagrafici",
        sa.Column("numero_documento_identita", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "anag_soggetti_anagrafici",
        sa.Column("stato_rilascio_documento", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_anag_soggetti_tipo_documento_identita",
        "anag_soggetti_anagrafici",
        ["tipo_documento_identita"],
    )
    op.create_index(
        "ix_anag_soggetti_numero_documento_identita",
        "anag_soggetti_anagrafici",
        ["numero_documento_identita"],
    )


def downgrade() -> None:
    op.drop_index("ix_anag_soggetti_numero_documento_identita", table_name="anag_soggetti_anagrafici")
    op.drop_index("ix_anag_soggetti_tipo_documento_identita", table_name="anag_soggetti_anagrafici")
    op.drop_column("anag_soggetti_anagrafici", "stato_rilascio_documento")
    op.drop_column("anag_soggetti_anagrafici", "numero_documento_identita")
    op.drop_column("anag_soggetti_anagrafici", "tipo_documento_identita")
