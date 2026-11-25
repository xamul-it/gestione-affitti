"""Document tables of a new tenant under their core_* names, with current columns.

In a new tenant the core chain runs first, so its rename anag_* -> core_*
(2026092102) and the history columns (2026110902) find nothing; then this
module creates the tables under the old anag_* names (2026011503/05) and the
code, which uses core_documenti, finds no table. This migration re-applies
those two core migrations, both idempotent: in existing tenants (core_*
already there, columns already added) it changes nothing.
Found by scripts/tenant_prova.py nuovo (2026-11-25).

Revision ID: 2026112501
Revises: 2026092101
"""
import importlib.util
from pathlib import Path

from alembic import op

revision = "2026112501"
down_revision = "2026092101"
branch_labels = None
depends_on = None

target_schema = "tenant"

_CORE = Path(__file__).resolve().parents[4] / "alembic" / "versions"


def _core(nome: str):
    spec = importlib.util.spec_from_file_location(f"core_{nome}", _CORE / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    modulo.op = op  # the same migration context (or the test's stand-in)
    return modulo


def upgrade() -> None:
    _core("2026092102_rename_document_registry_tenant_tables").upgrade()
    _core("2026110902_documenti_storico").upgrade()


def downgrade() -> None:
    pass
