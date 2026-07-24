"""
Integration tests for per-tenant module version tracking.

Uses a real Postgres session (the same SessionLocal the running app uses,
bound to settings.DATABASE_URL) rather than the SQLite-backed db_session
fixture — sync_module_tables_for_tenant/get_tenant_modules run raw
Postgres-only SQL (pg_attribute, pg_indexes) that does not exist on
SQLite. A throwaway tenant schema is created and dropped per test,
regardless of outcome.
"""
import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.models.tenant import Tenant, TenantModule
from app.core.module_system.models import Module
from app.core.services.tenant_module_service import TenantModuleService

TEST_SCHEMA = "tenant_pytest_version_check"


@pytest.fixture(autouse=True)
def override_get_db():
    """
    Shadow conftest.py's autouse `override_get_db(db_session)` fixture for
    this module only. That global fixture unconditionally pulls in the
    SQLite-backed `db_session`/`db_engine` fixtures (via its dependency),
    which fail at CREATE TABLE time because several models (e.g. Tenant)
    declare `__table_args__ = {'schema': 'public'}` — a Postgres-only
    construct SQLite's dialect rejects. This test module talks to
    Postgres directly through `pg_session` and never touches the FastAPI
    TestClient, so the override is unnecessary here; redefining the
    fixture under the same name overrides it for tests in this file only,
    per normal pytest fixture resolution, without touching the shared
    conftest.py fixture used by the rest of the suite.
    """
    yield


@pytest.fixture
def pg_session():
    """A real session against the actual dev Postgres database."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def throwaway_tenant(pg_session):
    """A real tenant row pointing at a throwaway schema name. The schema
    itself is never physically CREATEd — sufficient for version-tracking
    logic, which reads/writes core_tenant_modules and core_modules only."""
    tenant = Tenant(
        schema_name=TEST_SCHEMA,
        nome_display="Pytest Version Check",
        active=True,
    )
    pg_session.add(tenant)
    pg_session.commit()
    pg_session.refresh(tenant)
    try:
        yield tenant
    finally:
        pg_session.query(TenantModule).filter_by(tenant_id=tenant.id).delete()
        pg_session.query(Tenant).filter_by(id=tenant.id).delete()
        pg_session.commit()


@pytest.mark.tenant
def test_register_module_sets_installed_version(pg_session, throwaway_tenant):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    assert module is not None, "esempio_componenti must be registered for this test to run"

    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=module.version)

    tm = pg_session.query(TenantModule).filter_by(
        tenant_id=throwaway_tenant.id, module_id="esempio_componenti"
    ).first()
    assert tm is not None
    assert tm.installed_version == module.version


@pytest.mark.tenant
def test_needs_update_false_when_versions_match(pg_session, throwaway_tenant):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=module.version)

    modules_payload = TenantModuleService.get_tenant_modules(throwaway_tenant.id, pg_session)
    entry = next(m for m in modules_payload if m["module_id"] == "esempio_componenti")
    assert entry["installed_version"] == module.version
    assert entry["needs_update"] is False


@pytest.mark.tenant
def test_needs_update_true_when_versions_differ(pg_session, throwaway_tenant):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version="0000000000")

    modules_payload = TenantModuleService.get_tenant_modules(throwaway_tenant.id, pg_session)
    entry = next(m for m in modules_payload if m["module_id"] == "esempio_componenti")
    assert entry["installed_version"] == "0000000000"
    assert entry["needs_update"] is True


@pytest.mark.tenant
def test_needs_update_false_when_installed_version_unknown(pg_session, throwaway_tenant):
    """A row with installed_version still NULL (shouldn't happen after the
    Task 2 backfill, but defensively) must not be treated as needing an
    update — there's nothing to compare against."""
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=None)

    modules_payload = TenantModuleService.get_tenant_modules(throwaway_tenant.id, pg_session)
    entry = next(m for m in modules_payload if m["module_id"] == "esempio_componenti")
    assert entry["installed_version"] is None
    assert entry["needs_update"] is False
