"""
Verifies that tenant-only core tables (scadenzario, notifiche) are never
created in the public schema by create_core_tables() — they must only
exist per-tenant, via their dedicated Alembic migrations.
"""
import pytest
from sqlalchemy import MetaData

from app.core.database import Base
from app.main import TENANT_ONLY_CORE_TABLES, create_core_tables


@pytest.fixture(autouse=True)
def override_get_db():
    """
    Shadow conftest.py's autouse `override_get_db(db_session)` fixture for
    this module only. That global fixture unconditionally builds
    `db_session`/`db_engine` (SQLite), which runs an unfiltered
    `Base.metadata.create_all()` — this fails because `Tenant` declares
    `__table_args__ = {'schema': 'public'}`, which SQLite's dialect
    rejects. This test never touches the database, so the override is
    unnecessary here; redefining the fixture under the same name shadows
    it for tests in this file only (same pattern already used in
    tests/integration/test_tenant_module_routes.py).
    """
    yield


def test_tenant_only_tables_excluded_from_public_creation():
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
    assert "core_scadenze" in TENANT_ONLY_CORE_TABLES
    assert "core_scadenza_destinatari" in TENANT_ONLY_CORE_TABLES
    assert "core_scadenza_log" in TENANT_ONLY_CORE_TABLES
