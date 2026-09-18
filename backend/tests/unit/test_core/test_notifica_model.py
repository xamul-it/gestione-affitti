"""
Uses real PostgreSQL (not the SQLite db_session fixture) because
core_notifiche is a tenant-scoped table (search_path-based) and, more
fundamentally, because db_session/SQLite is currently broken for any
test that creates/queries rows in this repo: Tenant declares
__table_args__ = {'schema': 'public'}, and conftest.py's fixture chain
unconditionally registers Tenant on Base.metadata for every test
session, which SQLite's create_all() cannot handle ("unknown database
public"). Same pg_session pattern as
tests/integration/test_tenant_module_routes.py, with an explicit
search_path since that file's tables are all public-schema and this
one isn't.

Also shadows conftest.py's autouse `override_get_db(db_session)` for
this module only, same as test_tenant_module_routes.py does: that
fixture is autouse, so it runs (and pulls in the broken SQLite
db_session/db_engine chain) for every test regardless of whether the
test itself requests db_session. Without this shadow, both tests below
still ERROR at setup with "sqlite3.OperationalError: unknown database
public" from Base.metadata.create_all() trying to create
public.core_tenants.
"""
import pytest
from datetime import datetime
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.auth.models import User
from app.core.platform.models import Notifica, CanaleNotifica, StatoEmailNotifica


@pytest.fixture(autouse=True)
def override_get_db():
    yield


@pytest.fixture
def pg_session():
    session = SessionLocal()
    try:
        session.execute(text("SET search_path TO tenant_qa_test, public"))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def superuser(pg_session):
    """Reuse the existing admin superuser already present in the dev DB (same pattern as test_tenant_module_routes.py)."""
    user = pg_session.query(User).filter_by(is_superuser=True).first()
    assert user is not None, "a superuser must exist in the dev DB for this test"
    return user


def test_notifica_defaults(pg_session, superuser):
    n = Notifica(
        user_id=superuser.id,
        tipo="test.evento",
        titolo="Titolo di prova",
        corpo="Corpo di prova",
    )
    pg_session.add(n)
    pg_session.commit()
    pg_session.refresh(n)
    try:
        assert n.id is not None
        assert n.canali == CanaleNotifica.ENTRAMBI.value
        assert n.stato_email == StatoEmailNotifica.NON_RICHIESTA.value
        assert n.letta is False
        assert n.letta_il is None
        assert isinstance(n.creata_il, datetime)
    finally:
        pg_session.query(Notifica).filter_by(id=n.id).delete()
        pg_session.commit()


def test_notifica_with_entity_link(pg_session, superuser):
    n = Notifica(
        user_id=superuser.id,
        tipo="scadenza.reminder",
        titolo="Scadenza in avvicinamento",
        corpo="La scadenza X è in scadenza tra 3 giorni",
        entity_type="scadenza",
        entity_id=42,
        link_url="/scadenze/42",
        canali=CanaleNotifica.EMAIL.value,
    )
    pg_session.add(n)
    pg_session.commit()
    pg_session.refresh(n)
    try:
        assert n.entity_type == "scadenza"
        assert n.entity_id == 42
        assert n.link_url == "/scadenze/42"
        assert n.canali == CanaleNotifica.EMAIL.value
    finally:
        pg_session.query(Notifica).filter_by(id=n.id).delete()
        pg_session.commit()
