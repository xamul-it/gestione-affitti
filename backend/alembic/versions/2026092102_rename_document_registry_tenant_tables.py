"""Rename the tenant-scoped document-registry tables from anag_* to core_*,
companion to 2026092101 (which handles the public-schema reference tables).
Same rationale: Documento/DocumentoFile and the two per-tenant override
tables are now app/core/platform/models, not anagrafica_italiana's.

All four tables are empty of real data in every tenant checked during this
change (anag_documenti/anag_documenti_files: the generic document-upload
endpoint they back had a bug that made every upload fail until fixed in
750aaba, so nothing was ever successfully stored; the two override tables
have simply never been used) — a rename is still used over drop+recreate
for consistency with the public-schema migration and because it works
identically regardless of whether a given tenant has rows.

Revision ID: 2026092102
Revises: 2026092101
Create Date: 2026-09-21
"""
from alembic import op

revision = "2026092102"
down_revision = "2026092101"
branch_labels = None
depends_on = None

target_schema = "tenant"


def upgrade() -> None:
    op.rename_table("anag_documenti", "core_documenti")
    op.rename_table("anag_documenti_files", "core_documenti_files")
    op.rename_table("anag_tipi_documento_overrides", "core_tipi_documento_overrides")
    op.rename_table("anag_stati_documento_overrides", "core_stati_documento_overrides")


def downgrade() -> None:
    op.rename_table("core_stati_documento_overrides", "anag_stati_documento_overrides")
    op.rename_table("core_tipi_documento_overrides", "anag_tipi_documento_overrides")
    op.rename_table("core_documenti_files", "anag_documenti_files")
    op.rename_table("core_documenti", "anag_documenti")
