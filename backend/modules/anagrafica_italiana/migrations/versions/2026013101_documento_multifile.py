"""documento_multifile

Add support for multi-file documents:
- Add metadata_parsato and confidence_score to Documento
- Make legacy fields nullable
- Create DocumentoFile table for individual files

Revision ID: 2026013101
Revises: 2026012802
Create Date: 2026-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026013101'
down_revision = '2026012802'  # Last anagrafica migration
branch_labels = None
depends_on = None

# Target schema: tenant schemas only
target_schema = "tenant"


def upgrade():
    """
    Upgrade tenant schemas to support multi-file documents.

    This migration:
    1. Adds new fields to anag_documenti for parsed metadata
    2. Makes legacy single-file fields nullable
    3. Creates anag_documenti_files table
    """
    # 1. Add new fields to Documento
    op.add_column(
        'anag_documenti',
        sa.Column('metadata_parsato', postgresql.JSON, nullable=True,
                  comment='Aggregated parsed data from all files')
    )
    op.add_column(
        'anag_documenti',
        sa.Column('confidence_score', sa.Integer, nullable=True,
                  comment='Average confidence score (0-100) from all parsed files')
    )

    # 2. Make legacy fields nullable for backward compatibility
    op.alter_column(
        'anag_documenti',
        'nome_file',
        existing_type=sa.String(255),
        nullable=True
    )
    op.alter_column(
        'anag_documenti',
        'file_path',
        existing_type=sa.String(500),
        nullable=True
    )
    op.alter_column(
        'anag_documenti',
        'mime_type',
        existing_type=sa.String(100),
        nullable=True
    )
    op.alter_column(
        'anag_documenti',
        'dimensione',
        existing_type=sa.BigInteger,
        nullable=True
    )

    # 3. Create DocumentoFile table
    op.create_table(
        'anag_documenti_files',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('documento_id', sa.Integer, nullable=False),

        # File information
        sa.Column('file_path', sa.String(500), nullable=False,
                  comment='Relative path to original file (includes tenant prefix)'),
        sa.Column('nome_file', sa.String(255), nullable=False,
                  comment='Original filename'),
        sa.Column('mime_type', sa.String(100), nullable=True,
                  comment='MIME type (image/jpeg, application/pdf, etc.)'),
        sa.Column('dimensione', sa.BigInteger, nullable=True,
                  comment='File size in bytes'),

        # Display and organization
        sa.Column('ordine', sa.Integer, nullable=False, server_default='1',
                  comment='Display order (1, 2, 3, ...)'),
        sa.Column('tipo_pagina', sa.String(50), nullable=True,
                  comment='Page type: fronte, retro, pagina_1, etc.'),

        # Normalized file (cache)
        sa.Column('file_normalizzato_path', sa.String(500), nullable=True,
                  comment='Path to normalized JPEG file'),
        sa.Column('normalizzato_width', sa.Integer, nullable=True,
                  comment='Width of normalized image in pixels'),
        sa.Column('normalizzato_height', sa.Integer, nullable=True,
                  comment='Height of normalized image in pixels'),

        # Parsing information (optional per file)
        sa.Column('parsing_job_id', sa.Integer, nullable=True,
                  comment='FK to public.core_document_jobs if parsing performed'),
        sa.Column('parsing_result', postgresql.JSON, nullable=True,
                  comment='Parsed data extracted from this specific file'),
        sa.Column('confidence_score', sa.Integer, nullable=True,
                  comment='Parsing confidence for this file (0-100)'),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('NOW()'), nullable=False),

        # Foreign keys
        sa.ForeignKeyConstraint(
            ['documento_id'],
            ['anag_documenti.id'],
            name='fk_anag_documenti_files_documento',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['parsing_job_id'],
            ['public.core_document_jobs.id'],
            name='fk_anag_documenti_files_parsing_job',
            ondelete='SET NULL'
        ),

        # Constraints
        sa.CheckConstraint('ordine > 0', name='check_ordine_positive'),
        sa.CheckConstraint(
            'confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 100)',
            name='check_confidence_range'
        )
    )

    # 4. Create indexes for performance
    op.create_index(
        'ix_anag_documenti_files_documento_id',
        'anag_documenti_files',
        ['documento_id']
    )
    op.create_index(
        'ix_anag_documenti_files_parsing_job_id',
        'anag_documenti_files',
        ['parsing_job_id'],
        postgresql_where=sa.text('parsing_job_id IS NOT NULL')
    )
    op.create_index(
        'ix_anag_documenti_files_ordine',
        'anag_documenti_files',
        ['documento_id', 'ordine']
    )


def downgrade():
    """
    Downgrade: Remove multi-file support.

    WARNING: This will lose DocumentoFile data!
    Use with extreme caution.
    """
    # Drop indexes
    op.drop_index('ix_anag_documenti_files_ordine', table_name='anag_documenti_files')
    op.drop_index('ix_anag_documenti_files_parsing_job_id', table_name='anag_documenti_files')
    op.drop_index('ix_anag_documenti_files_documento_id', table_name='anag_documenti_files')

    # Drop DocumentoFile table
    op.drop_table('anag_documenti_files')

    # Remove new fields from Documento
    op.drop_column('anag_documenti', 'confidence_score')
    op.drop_column('anag_documenti', 'metadata_parsato')

    # Restore NOT NULL constraints on legacy fields
    # WARNING: This will fail if there are documents with NULL values
    op.alter_column(
        'anag_documenti',
        'nome_file',
        existing_type=sa.String(255),
        nullable=False
    )
    op.alter_column(
        'anag_documenti',
        'file_path',
        existing_type=sa.String(500),
        nullable=False
    )
