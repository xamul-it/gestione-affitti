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

Revision ID: 2026092101
Revises: 2026092001
Create Date: 2026-09-21
"""
from alembic import op

revision = "2026092101"
down_revision = "2026092001"
branch_labels = None
depends_on = None

target_schema = "public"


def upgrade() -> None:
    op.rename_table("anag_tipi_documento", "core_tipi_documento", schema="public")
    op.rename_table("anag_stati_documento", "core_stati_documento", schema="public")


def downgrade() -> None:
    op.rename_table("core_stati_documento", "anag_stati_documento", schema="public")
    op.rename_table("core_tipi_documento", "anag_tipi_documento", schema="public")
