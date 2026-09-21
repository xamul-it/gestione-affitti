"""Rename the public-schema document-type reference tables from anag_* to
core_*, since the document registry (Documento/DocumentoFile/TipoDocumento/
StatoDocumento) moved to app/core/platform/models — it is a core platform
service, not anagrafica_italiana's, per
docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md.

A plain rename preserves the existing seeded rows (tipi/stati documento are
reference data, not user data, but there is no reason to drop and reseed
when a rename is simpler and safer). Companion migration
2026092102_rename_document_registry_tenant_tables.py handles the
tenant-scoped counterparts (anag_documenti, anag_documenti_files, and the
two override tables).

Uses a defensive IF-old-exists-AND-new-doesn't-THEN-rename guard (same
pattern as 2026011506_rename_documenti.py in anagrafica_italiana's own
chain) rather than a bare op.rename_table(), because a bare rename hard-
fails on a database that never had anag_tipi_documento in the first place
(a fresh bootstrap that reaches this migration before anagrafica_italiana
has ever been registered) — see the independent review of an earlier,
non-defensive version of this migration for the full failure analysis.

Revision ID: 2026092101
Revises: 2026092001
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "2026092101"
down_revision = "2026092001"
branch_labels = None
depends_on = None

target_schema = "public"

_RENAMES = [
    ("anag_tipi_documento", "core_tipi_documento"),
    ("anag_stati_documento", "core_stati_documento"),
]


def _rename_if_needed(old_name: str, new_name: str) -> None:
    # op.execute (not a raw bind.execute) so this goes through env.py's
    # schema gate and only actually fires while migrating `public` — a
    # raw bind.execute would run unconditionally on every schema pass of
    # `-x schema=all`/`-x schema=<tenant>`, and since this SQL explicitly
    # qualifies `public.*`, it would rename the shared reference tables as
    # a side effect of migrating a single tenant schema (verified: this
    # bug was caught by actually running `-x schema=tenant_qa_test
    # downgrade` against an earlier bind.execute-based version of this
    # migration, which renamed public.core_tipi_documento back to
    # anag_tipi_documento even though only one tenant was targeted).
    op.execute(sa.text(f"""
        DO $$
        BEGIN
            IF to_regclass('public.{old_name}') IS NOT NULL
               AND to_regclass('public.{new_name}') IS NULL THEN
                ALTER TABLE public.{old_name} RENAME TO {new_name};
            END IF;
        END $$;
    """))


def upgrade() -> None:
    for old_name, new_name in _RENAMES:
        _rename_if_needed(old_name, new_name)


def downgrade() -> None:
    for old_name, new_name in reversed(_RENAMES):
        _rename_if_needed(new_name, old_name)
