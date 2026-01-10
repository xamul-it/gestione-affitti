"""make nome field optional in condomini

Revision ID: 2025122601
Revises:
Create Date: 2025-12-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025122601'
down_revision = None  # Set this to the latest migration ID if there are existing migrations
branch_labels = None
depends_on = None


def upgrade():
    """
    Make 'nome' field optional (nullable=True) in condomini table.

    The 'nome' field is not the primary identifier - 'codice' is.
    This allows automatic codice generation without requiring manual nome input.
    """
    # Make nome nullable in condomini
    op.alter_column('condomini', 'nome',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade():
    """
    Revert 'nome' field to required (nullable=False) in condomini table.

    WARNING: This will fail if there are existing records with NULL nome values.
    """
    # Make nome non-nullable in condomini
    op.alter_column('condomini', 'nome',
                    existing_type=sa.String(length=255),
                    nullable=False)
