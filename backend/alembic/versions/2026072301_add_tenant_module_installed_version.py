"""Add installed_version to core_tenant_modules for update-drift tracking.

Revision ID: 2026072301
Revises: 2026013101
Create Date: 2026-07-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2026072301"
down_revision = "2026013101"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.add_column(
        "core_tenant_modules",
        sa.Column("installed_version", sa.String(20), nullable=True),
    )
    # Backfill: this column didn't exist before, so there is no real drift
    # yet for modules already installed on a tenant — treat them as aligned
    # with the module's current version as of this migration.
    op.execute("""
        UPDATE core_tenant_modules tm
        SET installed_version = m.version
        FROM core_modules m
        WHERE m.technical_name = tm.module_id
    """)


def downgrade() -> None:
    op.drop_column("core_tenant_modules", "installed_version")
