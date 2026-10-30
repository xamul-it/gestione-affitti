"""Add USO, ABITAZIONE, SUPERFICIE, ENFITEUSI to the public.tipodiritto enum.

Needed by the "import da visura catastale" flow: catasto visure list real
rights beyond proprietà/nuda proprietà/usufrutto (e.g. "Uso 1/1 in regime di
separazione dei beni"), and every intestato is imported with its exact right.

Lives in the core chain (not immobili/migrations) because promote.sh runs
`alembic -x schema=all upgrade head` on the core chain only; module public
migrations run once, at first module registration. The PG enum type
`tipodiritto` is in `public` (shared by every tenant's
immo_diritti_immobile.tipo_diritto column), so this only fires on the public
pass — op.execute is gated by env.py on target_schema.

Revision ID: 2026103001
Revises: 2026092103
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "2026103001"
down_revision = "2026092103"
branch_labels = None
depends_on = None

target_schema = "public"

NEW_VALUES = ("USO", "ABITAZIONE", "SUPERFICIE", "ENFITEUSI")


def upgrade() -> None:
    for value in NEW_VALUES:
        op.execute(sa.text(f"ALTER TYPE public.tipodiritto ADD VALUE IF NOT EXISTS '{value}'"))


def downgrade() -> None:
    # PostgreSQL cannot drop enum values; leaving them is harmless.
    pass
