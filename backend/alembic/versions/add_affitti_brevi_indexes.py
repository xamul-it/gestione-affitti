"""add affitti_brevi performance indexes

Revision ID: affitti_brevi_indexes_001
Revises:
Create Date: 2025-12-28

Performance indexes for Affitti Brevi module:
- Prenotazioni: Composite indexes for date range queries
- Prenotazioni: Booking code uniqueness
- Scadenze: Deadline queries
- TassaPrenotazione: Booking lookup
- ComunicazionePolizia: Status queries
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'affitti_brevi_indexes_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes"""

    # Prenotazioni indexes
    # Composite index for date range queries (most common query pattern)
    op.create_index(
        'idx_prenotazioni_immobile_dates',
        'prenotazioni',
        ['unita_immobiliare_id', 'data_checkin', 'data_checkout'],
        unique=False
    )

    # Composite index for booking code uniqueness per platform
    op.create_index(
        'idx_prenotazioni_code_platform',
        'prenotazioni',
        ['portale_origine', 'codice_prenotazione'],
        unique=False  # Not unique because could be same code on different platforms
    )

    # Index for status queries
    op.create_index(
        'idx_prenotazioni_stato',
        'prenotazioni',
        ['stato'],
        unique=False
    )

    # Scadenze indexes
    # Composite index for deadline queries (most common: not completed + by date)
    op.create_index(
        'idx_scadenze_completata_data',
        'scadenze',
        ['completata', 'data_scadenza'],
        unique=False
    )

    # Index for deadline type filtering
    op.create_index(
        'idx_scadenze_tipo_stato',
        'scadenze',
        ['tipo_scadenza', 'stato'],
        unique=False
    )

    # TassaPrenotazione indexes
    # Already has unique index on prenotazione_id from model definition
    # Add index for config lookup
    op.create_index(
        'idx_tassa_prenotazione_config',
        'tasse_prenotazioni',
        ['config_id'],
        unique=False
    )

    # ComunicazionePolizia indexes
    # Index for status queries (finding pending/error communications)
    op.create_index(
        'idx_comunicazioni_polizia_stato',
        'comunicazioni_polizia',
        ['stato'],
        unique=False
    )

    # Index for date queries (finding overdue communications)
    op.create_index(
        'idx_comunicazioni_polizia_created',
        'comunicazioni_polizia',
        ['created_at'],
        unique=False
    )

    # CalendarioIcal indexes
    # Index for immobile lookup
    op.create_index(
        'idx_calendari_ical_immobile',
        'calendari_ical',
        ['unita_immobiliare_id'],
        unique=False
    )

    # Index for active calendars
    op.create_index(
        'idx_calendari_ical_attivo',
        'calendari_ical',
        ['attivo'],
        unique=False
    )

    # BloccoCalendario indexes
    # Composite index for date range queries
    op.create_index(
        'idx_blocco_calendario_immobile_dates',
        'blocchi_calendario',
        ['unita_immobiliare_id', 'data_inizio', 'data_fine'],
        unique=False
    )

    print("✅ Added performance indexes for Affitti Brevi module")


def downgrade():
    """Remove performance indexes"""

    # Remove in reverse order
    op.drop_index('idx_blocco_calendario_immobile_dates', table_name='blocchi_calendario')
    op.drop_index('idx_calendari_ical_attivo', table_name='calendari_ical')
    op.drop_index('idx_calendari_ical_immobile', table_name='calendari_ical')
    op.drop_index('idx_comunicazioni_polizia_created', table_name='comunicazioni_polizia')
    op.drop_index('idx_comunicazioni_polizia_stato', table_name='comunicazioni_polizia')
    op.drop_index('idx_tassa_prenotazione_config', table_name='tasse_prenotazioni')
    op.drop_index('idx_scadenze_tipo_stato', table_name='scadenze')
    op.drop_index('idx_scadenze_completata_data', table_name='scadenze')
    op.drop_index('idx_prenotazioni_stato', table_name='prenotazioni')
    op.drop_index('idx_prenotazioni_code_platform', table_name='prenotazioni')
    op.drop_index('idx_prenotazioni_immobile_dates', table_name='prenotazioni')

    print("✅ Removed performance indexes for Affitti Brevi module")
