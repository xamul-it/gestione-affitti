"""merge_scadenze_and_condomini_migrations

Revision ID: a46db514c861
Revises: 2025122601, scadenze_extension_001
Create Date: 2025-12-29 13:17:42.596863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a46db514c861'
down_revision: Union[str, None] = ('2025122601', 'scadenze_extension_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
