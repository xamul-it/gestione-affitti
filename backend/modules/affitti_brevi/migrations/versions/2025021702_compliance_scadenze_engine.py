"""compliance scadenze engine

Drop the never-executed AttivitaSchedulata/Log tables (superseded by the
compliance scheduler's per-tenant APScheduler job) and add
Comunicazione.scadenza_id (link to the core Scadenza this Comunicazione
was generated for).

Revision ID: 2025021702
Revises: 2025021701
Create Date: 2026-09-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025021702'
down_revision = '2025021701'
branch_labels = None
depends_on = None

# Target schema: tenant schemas only
target_schema = "tenant"


def upgrade():
    op.execute("DROP TABLE IF EXISTS ab_attivita_schedulate_log")
    op.execute("DROP TABLE IF EXISTS ab_attivita_schedulate")

    op.execute("ALTER TABLE ab_comunicazioni ADD COLUMN IF NOT EXISTS scadenza_id INTEGER")
    op.execute("COMMENT ON COLUMN ab_comunicazioni.scadenza_id IS 'FK logica a core_scadenze.id'")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ab_comunicazioni_scadenza_id ON ab_comunicazioni (scadenza_id)")


def downgrade():
    op.drop_index('ix_ab_comunicazioni_scadenza_id', table_name='ab_comunicazioni')
    op.drop_column('ab_comunicazioni', 'scadenza_id')

    op.create_table(
        'ab_attivita_schedulate',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('descrizione', sa.Text(), nullable=True),
        sa.Column('unita_immobiliare_id', sa.Integer(),
                  sa.ForeignKey('immo_unita_immobiliari.id', ondelete='SET NULL'), nullable=True),
        sa.Column('canale_id', sa.Integer(),
                  sa.ForeignKey('ab_canali.id', ondelete='SET NULL'), nullable=True),
        sa.Column('periodicita', sa.String(30), nullable=False, server_default='SINGOLA'),
        sa.Column('ora_esecuzione', sa.String(5), nullable=True, server_default='06:00'),
        sa.Column('giorno_settimana', sa.Integer(), nullable=True),
        sa.Column('giorno_mese', sa.Integer(), nullable=True),
        sa.Column('prossima_esecuzione', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ultima_esecuzione', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stato', sa.String(30), nullable=False, server_default='PIANIFICATA'),
        sa.Column('attiva', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('esito_ultima_esecuzione', sa.Text(), nullable=True),
        sa.Column('errore_ultima_esecuzione', sa.Text(), nullable=True),
        sa.Column('esecuzioni_totali', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('esecuzioni_successo', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('esecuzioni_fallite', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('precondizioni', sa.Text(), nullable=True),
        sa.Column('output_tipo', sa.String(50), nullable=True),
        sa.Column('output_destinatari', sa.Text(), nullable=True),
        sa.Column('notifica_completamento', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notifica_errore', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('notifica_scadenza', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('creato_da', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ab_attivita_prossima_esec', 'ab_attivita_schedulate',
                     ['prossima_esecuzione', 'attiva'])
    op.create_index('ix_ab_attivita_tipo_stato', 'ab_attivita_schedulate', ['tipo', 'stato'])

    op.create_table(
        'ab_attivita_schedulate_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attivita_id', sa.Integer(),
                  sa.ForeignKey('ab_attivita_schedulate.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_esecuzione', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_completamento', sa.DateTime(timezone=True), nullable=True),
        sa.Column('durata_secondi', sa.Integer(), nullable=True),
        sa.Column('stato', sa.String(30), nullable=False),
        sa.Column('esito', sa.Text(), nullable=True),
        sa.Column('errore', sa.Text(), nullable=True),
        sa.Column('elementi_processati', sa.Integer(), server_default='0'),
        sa.Column('elementi_successo', sa.Integer(), server_default='0'),
        sa.Column('elementi_errore', sa.Integer(), server_default='0'),
        sa.Column('elementi_saltati', sa.Integer(), server_default='0'),
        sa.Column('eseguito_da', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
