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

revision = "2026092001"
down_revision = "2026091802"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.drop_constraint(
        "core_document_jobs_scadenza_id_fkey", "core_document_jobs", type_="foreignkey"
    )
    op.drop_table("core_scadenza_log")
    op.drop_table("core_scadenza_destinatari")
    op.drop_table("core_scadenze")


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
    raise NotImplementedError(
        "This migration intentionally has no downgrade — see the comment above."
    )
