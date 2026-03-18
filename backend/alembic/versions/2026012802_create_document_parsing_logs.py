"""create document parsing logs table

Revision ID: 2026012802
Revises: 2026012801
Create Date: 2026-01-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2026012802"
down_revision = "2026012801"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.create_table(
        "core_document_parsing_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_uuid", sa.String(length=36), nullable=True),
        sa.Column("tenant_schema", sa.String(length=100), nullable=True),
        sa.Column("parsing_service", sa.String(length=50), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_doc_parsing_logs_job", "core_document_parsing_logs", ["job_uuid"])
    op.create_index("idx_doc_parsing_logs_tenant", "core_document_parsing_logs", ["tenant_schema"])
    op.create_index("idx_doc_parsing_logs_service", "core_document_parsing_logs", ["parsing_service"])
    op.create_index("idx_doc_parsing_logs_created", "core_document_parsing_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("core_document_parsing_logs")
