"""add_multifile_config_to_tipo_documento

Add parsing_multi_file_config to TipoDocumento for per-page parsing configuration.

Revision ID: 2026013101
Revises: 2026012803
Create Date: 2026-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026013101'
down_revision = '2026012803'  # Last core migration
branch_labels = None
depends_on = None

# Target schema: public only
target_schema = "public"


def upgrade():
    """
    Add parsing_multi_file_config to anag_tipi_documento.

    This allows configuring different parsing settings for different
    page types (fronte, retro, etc.) within a document type.
    """
    op.add_column(
        'anag_tipi_documento',
        sa.Column(
            'parsing_multi_file_config',
            postgresql.JSON,
            nullable=True,
            comment='Configuration for parsing different file types (fronte, retro, etc.)'
        ),
        schema='public'
    )


def downgrade():
    """Remove parsing_multi_file_config field"""
    op.drop_column('anag_tipi_documento', 'parsing_multi_file_config', schema='public')
