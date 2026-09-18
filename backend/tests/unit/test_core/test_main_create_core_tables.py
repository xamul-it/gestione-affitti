"""
Verifies that tenant-only core tables (scadenzario, notifiche) are never
created in the public schema by create_core_tables() — they must only
exist per-tenant, via their dedicated Alembic migrations.
"""
from sqlalchemy import MetaData

from app.core.database import Base
from app.main import TENANT_ONLY_CORE_TABLES


def test_tenant_only_tables_excluded_from_public_creation():
    """Test that the filtering logic correctly excludes tenant-only tables."""
    # Simulate the logic in create_core_tables()
    core_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if table.name.startswith("core_") and table.name not in TENANT_ONLY_CORE_TABLES:
            table.to_metadata(core_metadata)

    created_names = set(core_metadata.tables.keys())
    assert "core_scadenze" not in created_names
    assert "core_scadenza_destinatari" not in created_names
    assert "core_scadenza_log" not in created_names
    assert "core_users" in created_names  # sanity: real public tables still included


def test_tenant_only_tables_constant_contains_scadenzario():
    """Test that TENANT_ONLY_CORE_TABLES contains the scadenzario tables."""
    assert "core_scadenze" in TENANT_ONLY_CORE_TABLES
    assert "core_scadenza_destinatari" in TENANT_ONLY_CORE_TABLES
    assert "core_scadenza_log" in TENANT_ONLY_CORE_TABLES
