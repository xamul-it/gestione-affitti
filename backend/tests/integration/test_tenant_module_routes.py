"""
Tests that the force-update and reseed route functions are wired to the
correct service methods and return the expected response shape. Calls the
route functions directly (not via TestClient/HTTP) against a real Postgres
session, for the same reason test_tenant_module_version.py does — the
underlying service calls raw Postgres-only SQL that SQLite can't run.
"""
import pytest

from app.core.database import SessionLocal
from app.core.models.tenant import Tenant, TenantModule
from app.core.auth.models import User
from app.core.module_system.models import Module
from app.core.services.tenant_module_service import TenantModuleService
from app.core.routes.tenants import force_update_module, reseed_module_test_data

TEST_SCHEMA = "tenant_pytest_route_check"


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
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def throwaway_tenant(pg_session):
    tenant = Tenant(
        schema_name=TEST_SCHEMA,
        nome_display="Pytest Route Check",
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


@pytest.fixture
def superuser(pg_session):
    """Reuse the existing admin superuser (id=1) already present in the dev DB."""
    user = pg_session.query(User).filter_by(is_superuser=True).first()
    assert user is not None, "a superuser must exist in the dev DB for this test"
    return user


@pytest.mark.tenant
def test_force_update_route_bumps_installed_version(pg_session, throwaway_tenant, superuser):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version="0000000000")

    result = force_update_module(throwaway_tenant.id, "esempio_componenti", current_user=superuser, db=pg_session)
    assert result["status"] == "updated"

    pg_session.expire_all()
    tm = pg_session.query(TenantModule).filter_by(
        tenant_id=throwaway_tenant.id, module_id="esempio_componenti"
    ).first()
    assert tm.installed_version == module.version


@pytest.mark.tenant
def test_reseed_route_returns_success(pg_session, throwaway_tenant, superuser):
    module = pg_session.query(Module).filter_by(technical_name="esempio_componenti").first()
    TenantModuleService._register_module(throwaway_tenant.id, "esempio_componenti", pg_session, version=module.version)

    result = reseed_module_test_data(throwaway_tenant.id, "esempio_componenti", current_user=superuser, db=pg_session)
    assert result["status"] == "reseeded"
