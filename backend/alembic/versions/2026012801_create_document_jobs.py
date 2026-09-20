"""Create document_jobs table for async parsing.

Revision ID: 2026012801
Revises: 2026011501
Create Date: 2026-01-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2026012801"
down_revision = "2026011501"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    # Create JobStatus enum explicitly first (checkfirst=True). The column
    # below MUST use create_type=False, or Alembic's create_table DDL will
    # try to CREATE TYPE jobstatus a second time and fail with
    # "type already exists" the first time this migration ever runs for
    # real against a schema that doesn't already have it (verified via a
    # standalone repro against this exact pattern).
    jobstatus_enum = postgresql.ENUM(
        'PENDING',
        'QUEUED',
        'PROCESSING',
        'COMPLETED',
        'FAILED',
        'TIMEOUT',
        'CANCELLED',
        name='jobstatus',
        create_type=True
    )
    jobstatus_enum.create(op.get_bind(), checkfirst=True)

    # Create core_document_jobs table
    op.create_table(
        'core_document_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_uuid', sa.String(length=36), nullable=False),
        sa.Column('tenant_schema', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('document_type_key', sa.String(length=100), nullable=False),
        sa.Column('parsing_service', sa.String(length=50), nullable=False),
        sa.Column('parsing_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM(
            'PENDING',
            'QUEUED',
            'PROCESSING',
            'COMPLETED',
            'FAILED',
            'TIMEOUT',
            'CANCELLED',
            name='jobstatus',
            create_type=False,
        ), nullable=False, server_default='PENDING'),
        sa.Column('parsing_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('needs_review', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('queued_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('scadenza_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['core_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_document_jobs_tenant', 'core_document_jobs', ['tenant_schema'])
    op.create_index('idx_document_jobs_status', 'core_document_jobs', ['status'])
    op.create_index('idx_document_jobs_entity', 'core_document_jobs', ['entity_type', 'entity_id'])
    op.create_index('idx_document_jobs_created', 'core_document_jobs', ['created_at'])
    op.create_index('idx_document_jobs_creator', 'core_document_jobs', ['created_by'])
    op.create_index(op.f('ix_core_document_jobs_id'), 'core_document_jobs', ['id'])

    # Create unique constraint on job_uuid
    op.create_unique_constraint('uq_document_jobs_uuid', 'core_document_jobs', ['job_uuid'])


def downgrade() -> None:
    # Drop table
    op.drop_table('core_document_jobs')

    # Drop enum
    jobstatus_enum = postgresql.ENUM(name='jobstatus')
    jobstatus_enum.drop(op.get_bind(), checkfirst=True)
