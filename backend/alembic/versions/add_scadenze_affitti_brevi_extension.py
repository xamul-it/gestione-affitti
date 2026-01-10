"""add scadenze_affitti_brevi extension table

Revision ID: scadenze_extension_001
Revises: affitti_brevi_indexes_001
Create Date: 2025-12-29

Adds extension table for affitti_brevi-specific scadenza metadata.

This module uses the core platform scadenza system (app.core.platform.models.scadenza)
with an extension table for module-specific metadata:
- tipo_scadenza: Affitti Brevi specific types (COMUNICAZIONE_POLIZIA, REPORT_ISTAT, ALTRO)
- ricorrente: Recurrence flag for monthly ISTAT reports
- frequenza_giorni: Days between recurrences
- prossima_ricorrenza: Next recurrence date

The core scadenze table handles:
- modulo: "affitti_brevi"
- entity_type: "prenotazione", "report_istat", etc.
- entity_id: FK to entity
- titolo, descrizione, data_scadenza, priorita, stato
- User tracking: creato_da, completato_da, completato_il
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'scadenze_extension_001'
down_revision = 'affitti_brevi_indexes_001'
branch_labels = None
depends_on = None


def upgrade():
    """Create scadenze_affitti_brevi_ext table"""

    # Create enum type for TipoScadenzaAffittiBrevi
    tipo_scadenza_enum = postgresql.ENUM(
        'COMUNICAZIONE_POLIZIA',
        'REPORT_ISTAT',
        'ALTRO',
        name='tiposcadenzaaffittibrevi'
    )
    tipo_scadenza_enum.create(op.get_bind(), checkfirst=True)

    # Create extension table
    op.create_table(
        'scadenze_affitti_brevi_ext',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scadenza_id', sa.Integer(), nullable=False, comment='FK to core scadenze table'),
        sa.Column('tipo_scadenza', tipo_scadenza_enum, nullable=False, comment='Affitti Brevi deadline type'),
        sa.Column('ricorrente', sa.Boolean(), nullable=False, server_default='false', comment='True if recurring deadline'),
        sa.Column('frequenza_giorni', sa.Integer(), nullable=True, comment='Days between recurrences (e.g., 30 for monthly)'),
        sa.Column('prossima_ricorrenza', sa.Date(), nullable=True, comment='Next recurrence date'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['scadenza_id'],
            ['scadenze.id'],
            ondelete='CASCADE'
        ),
        sa.UniqueConstraint('scadenza_id', name='uq_scadenze_ext_scadenza_id')
    )

    # Create indexes
    op.create_index(
        'ix_scadenze_ext_scadenza_id',
        'scadenze_affitti_brevi_ext',
        ['scadenza_id'],
        unique=False
    )
    op.create_index(
        'ix_scadenze_ext_tipo_scadenza',
        'scadenze_affitti_brevi_ext',
        ['tipo_scadenza'],
        unique=False
    )


def downgrade():
    """Drop scadenze_affitti_brevi_ext table"""

    # Drop indexes
    op.drop_index('ix_scadenze_ext_tipo_scadenza', table_name='scadenze_affitti_brevi_ext')
    op.drop_index('ix_scadenze_ext_scadenza_id', table_name='scadenze_affitti_brevi_ext')

    # Drop table
    op.drop_table('scadenze_affitti_brevi_ext')

    # Drop enum type
    tipo_scadenza_enum = postgresql.ENUM(
        'COMUNICAZIONE_POLIZIA',
        'REPORT_ISTAT',
        'ALTRO',
        name='tiposcadenzaaffittibrevi'
    )
    tipo_scadenza_enum.drop(op.get_bind(), checkfirst=True)
