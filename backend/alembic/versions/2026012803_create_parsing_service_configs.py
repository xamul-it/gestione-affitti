"""create parsing service configs table

Revision ID: 2026012803
Revises: 2026012802
Create Date: 2026-01-28
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2026012803"
down_revision = "2026012802"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.create_table(
        "core_parsing_services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_key", sa.String(length=50), nullable=False),
        sa.Column("transport_type", sa.String(length=20), nullable=False, server_default="HTTP"),
        sa.Column("endpoint_url", sa.String(length=500), nullable=True),
        sa.Column("redis_queue", sa.String(length=200), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True, server_default="300"),
        sa.Column("enabled", sa.String(length=5), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_key", name="uq_core_parsing_services_key"),
    )
    op.create_index("idx_core_parsing_services_key", "core_parsing_services", ["service_key"])
    op.create_index("idx_core_parsing_services_transport", "core_parsing_services", ["transport_type"])


def downgrade() -> None:
    op.drop_table("core_parsing_services")
