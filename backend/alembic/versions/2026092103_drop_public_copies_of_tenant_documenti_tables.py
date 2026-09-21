"""Drop the accidental public-schema copies of the four tenant-scoped
document-registry tables created by 2026092101/2026092102's rename.

Root cause: core_documenti, core_documenti_files, core_tipi_documento_overrides
and core_stati_documento_overrides are tenant-scoped, but their new core_*
names made them match create_core_tables()'s `startswith("core_")` filter
in app/main.py, which runs unconditionally at every boot against the
public schema. They weren't in TENANT_ONLY_CORE_TABLES yet (fixed in the
same change as this migration), so every boot after the rename silently
created empty copies of these four tables in `public` — exactly the
tenant-isolation hazard 2026092001 already fixed once for the scadenzario
tables (search_path fallback to a shared public table instead of an error
on a tenant missing its own copy).

Verified 0 rows in all four public.core_documenti*/core_*_documento_overrides
tables in this environment before writing this migration (they had only
just been created by this same session's own boot tests).

Revision ID: 2026092103
Revises: 2026092102
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "2026092103"
down_revision = "2026092102"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    # See 2026092001 for why raw "IF EXISTS" SQL is used instead of
    # op.drop_table(if_exists=True) (which doesn't actually emit IF EXISTS).
    #
    # Two things matter here, both verified the hard way while writing the
    # companion rename migrations: (1) op.execute, not a raw bind.execute,
    # so this only actually fires while migrating `public` — a raw
    # bind.execute bypasses env.py's schema gate and runs on every schema
    # pass of `-x schema=all`; (2) explicit "public." qualification, so
    # that even if the gate were somehow bypassed, an unqualified DROP
    # TABLE IF EXISTS core_documenti_files run during a TENANT schema pass
    # would resolve via search_path to that tenant's own real
    # core_documenti_files table — created by 2026092102's rename — and
    # destroy it. Both mistakes were present in an earlier draft of this
    # migration; this is not a hypothetical.
    op.execute(sa.text("DROP TABLE IF EXISTS public.core_documenti_files"))
    op.execute(sa.text("DROP TABLE IF EXISTS public.core_documenti"))
    op.execute(sa.text("DROP TABLE IF EXISTS public.core_tipi_documento_overrides"))
    op.execute(sa.text("DROP TABLE IF EXISTS public.core_stati_documento_overrides"))


def downgrade() -> None:
    # Deliberately not restored — see 2026092001's downgrade() for the same
    # reasoning: these were a boot-time accident, verified empty, and
    # actively harmful to keep in public. The real per-tenant tables
    # (created by 2026092102's rename inside each tenant schema) are
    # untouched by this migration.
    pass
