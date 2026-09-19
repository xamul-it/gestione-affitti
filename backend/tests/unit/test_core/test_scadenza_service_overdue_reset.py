"""
Uses real PostgreSQL (pg_session), not the SQLite db_session fixture —
see tests/unit/test_core/test_notifica_model.py for why db_session is
broken for any row-creating test in this repo. core_scadenze /
core_scadenza_destinatari are tenant-scoped (Task 1), hence the explicit
search_path.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.auth.models import User
from app.core.auth.security import get_password_hash
from app.core.platform.models import Scadenza, ScadenzaDestinatario, StatoScadenza
from app.core.platform_services import ScadenzaService


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
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
def user_a(pg_session):
    user = User(
        email="scad-reset-test-a@example.com",
        username="scad_reset_test_a",
        full_name="Scad Reset Test A",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False,
    )
    pg_session.add(user)
    pg_session.commit()
    pg_session.refresh(user)
    try:
        yield user
    finally:
        pg_session.query(User).filter_by(id=user.id).delete()
        pg_session.commit()


def test_update_overdue_status_resets_notificato_flag(pg_session, user_a):
    scadenza = Scadenza(
        titolo="Test",
        data_scadenza=date.today() - timedelta(days=1),
        stato=StatoScadenza.ATTIVA,
        creato_da=user_a.id,
    )
    pg_session.add(scadenza)
    pg_session.flush()

    destinatario = ScadenzaDestinatario(scadenza_id=scadenza.id, user_id=user_a.id, notificato=True)
    pg_session.add(destinatario)
    pg_session.commit()

    try:
        ScadenzaService(pg_session).update_overdue_status()

        pg_session.refresh(scadenza)
        pg_session.refresh(destinatario)
        assert scadenza.stato == StatoScadenza.SCADUTA
        assert destinatario.notificato is False
    finally:
        pg_session.query(ScadenzaDestinatario).filter_by(id=destinatario.id).delete()
        pg_session.query(Scadenza).filter_by(id=scadenza.id).delete()
        pg_session.commit()


def test_update_overdue_status_does_not_touch_already_scaduta(pg_session, user_a):
    scadenza = Scadenza(
        titolo="Test",
        data_scadenza=date.today() - timedelta(days=5),
        stato=StatoScadenza.SCADUTA,
        creato_da=user_a.id,
    )
    pg_session.add(scadenza)
    pg_session.flush()
    destinatario = ScadenzaDestinatario(scadenza_id=scadenza.id, user_id=user_a.id, notificato=True)
    pg_session.add(destinatario)
    pg_session.commit()

    try:
        ScadenzaService(pg_session).update_overdue_status()

        pg_session.refresh(destinatario)
        assert destinatario.notificato is True  # untouched: was already SCADUTA before this call
    finally:
        pg_session.query(ScadenzaDestinatario).filter_by(id=destinatario.id).delete()
        pg_session.query(Scadenza).filter_by(id=scadenza.id).delete()
        pg_session.commit()
