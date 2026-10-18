"""Create public tables for esempio_componenti module

Revision ID: esem_001
Revises:
Create Date: 2026-01-18

Creates tables in PUBLIC schema:
- categorie_esempio: Example categories for classification
- priorita_esempio: Example priorities for urgency
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'esem_001'
down_revision = None
branch_labels = ('esem',)
depends_on = None

# Target schema for this migration
target_schema = "public"


def upgrade():
    # Create esem_categorie_esempio table
    op.create_table(
        'esem_categorie_esempio',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codice', sa.String(20), nullable=False),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('descrizione', sa.Text(), nullable=True),
        sa.Column('colore', sa.String(7), nullable=True, server_default='#3498db'),
        sa.Column('icona', sa.String(50), nullable=True),
        sa.Column('ordine', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attivo', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codice'),
        schema='public'
    )
    op.create_index(
        'ix_esem_categorie_esempio_codice',
        'esem_categorie_esempio',
        ['codice'],
        schema='public'
    )

    # Create esem_priorita_esempio table
    op.create_table(
        'esem_priorita_esempio',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codice', sa.String(10), nullable=False),
        sa.Column('nome', sa.String(50), nullable=False),
        sa.Column('livello', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('colore', sa.String(7), nullable=True, server_default='#95a5a6'),
        sa.Column('attivo', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codice'),
        schema='public'
    )
    op.create_index(
        'ix_esem_priorita_esempio_codice',
        'esem_priorita_esempio',
        ['codice'],
        schema='public'
    )


def downgrade():
    op.drop_index('ix_esem_priorita_esempio_codice', table_name='esem_priorita_esempio', schema='public')
    op.drop_table('esem_priorita_esempio', schema='public')
    op.drop_index('ix_esem_categorie_esempio_codice', table_name='esem_categorie_esempio', schema='public')
    op.drop_table('esem_categorie_esempio', schema='public')
