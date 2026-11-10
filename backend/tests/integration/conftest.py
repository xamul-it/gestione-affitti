"""
Integration fixtures: real PostgreSQL, nothing left behind.

Overrides the SQLite fixtures of tests/fixtures/ for everything under
tests/integration/. db_session runs inside an outer transaction that is
rolled back at the end: commit() in the code under test only releases a
SAVEPOINT, so tests can create users, tenants' rows and documents freely
without leaving rows in the dev database.

Tenant-scoped data goes to the existing test tenant (tenant_qa_test); the
"other tenant" for isolation tests is tenant_principale. Both only ever see
writes that are rolled back.
"""
import uuid
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine, get_db, get_public_db, get_tenant_schema
from app.core.models.tenant import Tenant

TEST_TENANT = "tenant_qa_test"
OTHER_TENANT = "tenant_principale"


@pytest.fixture
def db_session():
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    # Remembered by the search_path listener in app.core.database and
    # re-applied after every commit.
    session.execute(text(f"SET search_path TO {TEST_TENANT}, public"))
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def tenant_db_session(db_session, test_tenant):
    db_session.execute(text(f"SET search_path TO {test_tenant.schema_name}, public"))
    yield db_session


@pytest.fixture
def test_tenant(db_session):
    return db_session.query(Tenant).filter_by(schema_name=TEST_TENANT).one()


@pytest.fixture
def another_tenant(db_session):
    return db_session.query(Tenant).filter_by(schema_name=OTHER_TENANT).one()


@pytest.fixture
def override_get_db(db_session):
    """API calls share the test transaction, so they see the fixtures' rows
    and their writes are rolled back too. Each request still runs in the
    tenant of its token, like the real get_db; the test's own search_path
    is restored afterwards."""
    from fastapi import Depends
    from app.main import app

    def _with_search_path(path):
        previous = db_session.info.get("search_path", "public")
        db_session.execute(text(f"SET search_path TO {path}"))
        try:
            yield db_session
        finally:
            db_session.execute(text(f"SET search_path TO {previous}"))

    def _test_db(tenant_schema: Optional[str] = Depends(get_tenant_schema)):
        yield from _with_search_path(f"{tenant_schema}, public" if tenant_schema else "public")

    def _test_public_db():
        yield from _with_search_path("public")

    app.dependency_overrides[get_db] = _test_db
    app.dependency_overrides[get_public_db] = _test_public_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def unique_suffix():
    return uuid.uuid4().hex[:8]


@pytest.fixture(autouse=True)
def _ripristina_registro_tipi_documento():
    """Some tests register fake document types and then clear the global
    registry, wiping the types the app registered at startup (e.g.
    immobili.ALTRO_IMMOBILE) for every later test. Restore it after each test."""
    import copy
    from app.core.platform_services.document_type_registry import document_type_registry as reg
    attrs = ("_types", "_by_module", "_by_category", "_by_parsing_service")
    snapshot = {a: copy.deepcopy(getattr(reg, a)) for a in attrs}
    yield
    for a in attrs:
        current = getattr(reg, a)
        current.clear()
        current.update(snapshot[a])
