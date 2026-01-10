"""add tenant module config column

Revision ID: add_tenant_module_config
Revises: a46db514c861
Create Date: 2025-12-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'add_tenant_module_config'
down_revision = 'a46db514c861'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns('tenant_modules', schema='public')
    if not any(col['name'] == 'config' for col in columns):
        op.add_column(
            'tenant_modules',
            sa.Column('config', postgresql.JSONB(), nullable=True),
            schema='public'
        )


def downgrade():
    op.drop_column('tenant_modules', 'config', schema='public')
