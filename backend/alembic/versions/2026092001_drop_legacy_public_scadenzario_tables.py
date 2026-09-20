"""Drop legacy public copies of scadenzario tables.

Now that core_scadenze/core_scadenza_destinatari/core_scadenza_log are
correctly created per-tenant (2026091801) and excluded from
create_core_tables() (see TENANT_ONLY_CORE_TABLES in app/main.py), the
original copies left behind in `public` are dead weight that silently
masks a missing per-tenant migration: a new tenant that never ran
`alembic -x schema=<new> upgrade head` would have its core_scadenze
queries quietly resolve via search_path fallback to this leftover EMPTY
public table instead of erroring loudly. Dropping it converts that into
an obvious failure.

Verified 0 rows in public.core_scadenze, core_scadenza_destinatari,
core_scadenza_log, and public.core_document_jobs (whose scadenza_id FK
points at core_scadenze) in every environment before writing this
migration — see the task's own pre-flight psql checks.

Revision ID: 2026092001
Revises: 2026091802
Create Date: 2026-09-20
"""
from alembic import op
import sqlalchemy as sa

revision = "2026092001"
down_revision = "2026091802"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    # NOTE: alembic's op.drop_table(..., if_exists=True) does NOT actually
    # emit "DROP TABLE IF EXISTS" — if_exists is silently absorbed as an
    # (invalid) dialect keyword on the underlying sa.Table(), and the DDL
    # still comes out as a plain DROP TABLE that errors if the table is
    # absent (verified directly against alembic 1.12.1 / SQLAlchemy 2.0.51
    # while writing this migration). Use raw "IF EXISTS" SQL instead so
    # this is genuinely defensive on both an already-migrated DB (where
    # the FK/tables still exist from before 2026012801 was corrected) and
    # a brand-new bootstrap (where they never existed).
    bind = op.get_bind()
    bind.execute(sa.text(
        "ALTER TABLE core_document_jobs "
        "DROP CONSTRAINT IF EXISTS core_document_jobs_scadenza_id_fkey"
    ))
    bind.execute(sa.text("DROP TABLE IF EXISTS core_scadenza_log"))
    bind.execute(sa.text("DROP TABLE IF EXISTS core_scadenza_destinatari"))
    bind.execute(sa.text("DROP TABLE IF EXISTS core_scadenze"))


def downgrade() -> None:
    # Deliberately not restored: these tables were a historical accident
    # (an unfiltered create_core_tables() run, never a real migration),
    # verified empty, and the whole point of this migration is that they
    # should not exist. If you genuinely need to roll back this specific
    # revision for some other reason, recreate the three tables manually
    # from 2026091801's DDL (applied to `public` instead of a tenant
    # schema) and re-add the core_document_jobs FK — there is no
    # meaningful "undo" for dropping tables that were already empty and
    # actively harmful to keep around.
    pass
