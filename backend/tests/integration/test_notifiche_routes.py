"""
Calls the route functions directly (db=pg_session, current_user=<real
User>) rather than through TestClient/HTTP/JWT — same established
pattern as test_tenant_module_routes.py. This sidesteps two problems:
(1) db_session/SQLite is currently broken for any row-creating test in
this repo (see test_notification_service.py for the full rationale),
and this also means every fixture that transitively touches db_session
(test_user, test_tenant, and therefore auth_client) is broken too;
(2) it avoids needing to construct a valid JWT for a throwaway user.

The one exception is test_notifiche_require_auth, which specifically
tests HTTP-layer behavior (a request with no Authorization header) that
only exists when going through a real request — it uses a plain
TestClient with no dependency overrides, since the request should be
rejected by the auth dependency before ever touching the database.
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.auth.models import User
from app.core.auth.security import get_password_hash
from app.core.platform.models import Notifica, CanaleNotifica
from app.core.platform_services import NotificationService
from app.core.routes.notifiche import list_notifiche, segna_letta, segna_tutte_lette, badge


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for the full rationale."""
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


def _make_throwaway_user(pg_session, suffix):
    user = User(
        email=f"notif-route-test-{suffix}@example.com",
        username=f"notif_route_test_{suffix}",
        full_name=f"Notif Route Test {suffix}",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False,
    )
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    return user


@pytest.fixture
def user_a(pg_session):
    user = _make_throwaway_user(pg_session, "a")
    try:
        yield user
    finally:
        pg_session.query(User).filter_by(id=user.id).delete()
        pg_session.commit()


@pytest.fixture
def user_b(pg_session):
    user = _make_throwaway_user(pg_session, "b")
    try:
        yield user
    finally:
        pg_session.query(User).filter_by(id=user.id).delete()
        pg_session.commit()


def _create_notifica(pg_session, user_id, titolo="Titolo"):
    return NotificationService(pg_session).notify(
        user_ids=[user_id], tipo="test.evento", titolo=titolo, corpo="Corpo",
        canali=CanaleNotifica.IN_APP,
    )[0]


def _cleanup(pg_session, notifiche):
    ids = [n.id for n in notifiche]
    if ids:
        pg_session.query(Notifica).filter(Notifica.id.in_(ids)).delete(synchronize_session=False)
    pg_session.commit()


def test_list_notifiche_returns_only_own(pg_session, user_a, user_b):
    n1 = _create_notifica(pg_session, user_a.id, "Mia")
    n2 = _create_notifica(pg_session, user_b.id, "Non mia")
    try:
        result = list_notifiche(solo_non_lette=False, skip=0, limit=50, db=pg_session, current_user=user_a)
        assert len(result) == 1
        assert result[0].titolo == "Mia"
    finally:
        _cleanup(pg_session, [n1, n2])


def test_list_notifiche_solo_non_lette(pg_session, user_a):
    n1 = _create_notifica(pg_session, user_a.id, "Prima")
    segna_letta(n1.id, db=pg_session, current_user=user_a)
    n2 = _create_notifica(pg_session, user_a.id, "Seconda")
    try:
        result = list_notifiche(solo_non_lette=True, skip=0, limit=50, db=pg_session, current_user=user_a)
        assert len(result) == 1
        assert result[0].titolo == "Seconda"
    finally:
        _cleanup(pg_session, [n1, n2])


def test_segna_letta(pg_session, user_a):
    n = _create_notifica(pg_session, user_a.id)
    try:
        result = segna_letta(n.id, db=pg_session, current_user=user_a)
        assert result.letta is True
    finally:
        _cleanup(pg_session, [n])


def test_segna_letta_altrui_raises_404(pg_session, user_a, user_b):
    n = _create_notifica(pg_session, user_b.id)
    try:
        with pytest.raises(HTTPException) as exc_info:
            segna_letta(n.id, db=pg_session, current_user=user_a)
        assert exc_info.value.status_code == 404
    finally:
        _cleanup(pg_session, [n])


def test_segna_tutte_lette(pg_session, user_a):
    n1 = _create_notifica(pg_session, user_a.id, "Uno")
    n2 = _create_notifica(pg_session, user_a.id, "Due")
    try:
        result = segna_tutte_lette(db=pg_session, current_user=user_a)
        assert result.count == 2
    finally:
        _cleanup(pg_session, [n1, n2])


def test_badge(pg_session, user_a):
    n = _create_notifica(pg_session, user_a.id)
    try:
        result = badge(db=pg_session, current_user=user_a)
        assert result.count_non_lette == 1
    finally:
        _cleanup(pg_session, [n])


def test_notifiche_require_auth():
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/v1/notifiche")
    assert response.status_code == 403
