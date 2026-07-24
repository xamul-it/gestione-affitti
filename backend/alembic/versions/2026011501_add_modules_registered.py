"""Add registered fields to modules.

Revision ID: 2026011501
Revises: 
Create Date: 2026-01-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026011501"
down_revision = "2025122702"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.add_column(
        "core_modules",
        sa.Column("registered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "core_modules",
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("core_modules", "registered_at")
    op.drop_column("core_modules", "registered")
