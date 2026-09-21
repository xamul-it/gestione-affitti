"""Rename the tenant-scoped document-registry tables from anag_* to core_*,
companion to 2026092101 (which handles the public-schema reference tables).
Same rationale: Documento/DocumentoFile and the two per-tenant override
tables are now app/core/platform/models, not anagrafica_italiana's.

All four tables were empty of real data in every tenant checked when this
migration was written (anag_documenti/anag_documenti_files: the generic
document-upload endpoint they back had a bug that made every upload fail
until fixed in 750aaba, so nothing was ever successfully stored; the two
override tables have simply never been used) — a rename is still used
over drop+recreate for consistency with the public-schema migration and
because it works identically regardless of whether a given tenant has rows.

Uses a defensive IF-old-exists-AND-new-doesn't-THEN-rename guard (same
pattern as 2026011506_rename_documenti.py in anagrafica_italiana's own
chain, and the same reasoning as 2026092101) instead of a bare
op.rename_table(): a brand new tenant schema, or one where
anagrafica_italiana hasn't been installed yet, has none of these four
tables at all, and a bare rename would hard-fail on it. anagrafica_
italiana's own migrations (2026011503/2026011505) still create these
tables under their original anag_* names for every tenant (with their FK
targets updated to point at the already-renamed public tables) — this
migration's job is only to rename them to core_* wherever they exist,
whenever it runs relative to that tenant's own anagrafica_italiana
install.

Revision ID: 2026092102
Revises: 2026092101
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "2026092102"
down_revision = "2026092101"
branch_labels = None
depends_on = None

target_schema = "tenant"

_RENAMES = [
    ("anag_documenti", "core_documenti"),
    ("anag_documenti_files", "core_documenti_files"),
    ("anag_tipi_documento_overrides", "core_tipi_documento_overrides"),
    ("anag_stati_documento_overrides", "core_stati_documento_overrides"),
]


def _rename_if_needed(old_name: str, new_name: str) -> None:
    # op.execute (not a raw bind.execute) so this only actually fires while
    # migrating a tenant schema — see 2026092101's identical comment for
    # why bypassing the gate is a real bug, not just belt-and-suspenders,
    # verified against that migration's public-schema equivalent.
    op.execute(sa.text(f"""
        DO $$
        BEGIN
            IF to_regclass('{old_name}') IS NOT NULL
               AND to_regclass('{new_name}') IS NULL THEN
                ALTER TABLE {old_name} RENAME TO {new_name};
            END IF;
        END $$;
    """))


def upgrade() -> None:
    # documenti_files first: renaming documenti while a still-anag_-named
    # documenti_files' FK constraint points at it is fine either order
    # (Postgres FKs are tracked by OID, not name), but keep the
    # parent-then-child intuition anyway for readability.
    for old_name, new_name in _RENAMES:
        _rename_if_needed(old_name, new_name)


def downgrade() -> None:
    for old_name, new_name in reversed(_RENAMES):
        _rename_if_needed(new_name, old_name)
