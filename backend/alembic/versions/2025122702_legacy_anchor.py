"""Legacy anchor to bridge old database revision IDs.

Revision ID: 2025122702
Revises:
Create Date: 2025-12-27 02:00:00.000000
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "2025122702"
down_revision = None
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    # No-op: anchor revision to satisfy existing databases.
    pass


def downgrade() -> None:
    # No-op: anchor revision to satisfy existing databases.
    pass
