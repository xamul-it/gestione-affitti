"""
Uses real PostgreSQL (pg_session) — see test_scadenza_service_overdue_reset.py
and test_notifica_model.py for why db_session/SQLite is broken here.
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.auth.models import User
from app.core.auth.security import get_password_hash
from app.core.platform.models import Scadenza, ScadenzaDestinatario, StatoScadenza
from app.core.platform_services.scadenza_reminder_job import _check_scadenze_in_avvicinamento


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
        email="reminder-job-test-a@example.com",
        username="reminder_job_test_a",
        full_name="Reminder Job Test A",
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


def _make_scadenza(pg_session, user_id, giorni_da_oggi, notificato=False):
    scadenza = Scadenza(
        titolo=f"Scadenza tra {giorni_da_oggi}gg",
        data_scadenza=date.today() + timedelta(days=giorni_da_oggi),
        stato=StatoScadenza.ATTIVA,
        creato_da=user_id,
    )
    pg_session.add(scadenza)
    pg_session.flush()
    destinatario = ScadenzaDestinatario(scadenza_id=scadenza.id, user_id=user_id, notificato=notificato)
    pg_session.add(destinatario)
    pg_session.commit()
    return scadenza, destinatario


def _cleanup(pg_session, pairs):
    for scadenza, destinatario in pairs:
        pg_session.query(ScadenzaDestinatario).filter_by(id=destinatario.id).delete()
        pg_session.query(Scadenza).filter_by(id=scadenza.id).delete()
    pg_session.commit()


def test_notifies_scadenze_within_threshold(pg_session, user_a):
    scadenza, destinatario = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=2)
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)
        MockService.return_value.notify.assert_called_once()
    finally:
        _cleanup(pg_session, [(scadenza, destinatario)])


def test_does_not_notify_outside_threshold(pg_session, user_a):
    scadenza, destinatario = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=10)
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)
        MockService.return_value.notify.assert_not_called()
    finally:
        _cleanup(pg_session, [(scadenza, destinatario)])


def test_does_not_renotify_already_notified(pg_session, user_a):
    scadenza, destinatario = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=1, notificato=True)
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)
        MockService.return_value.notify.assert_not_called()
    finally:
        _cleanup(pg_session, [(scadenza, destinatario)])


def test_marks_recipients_notified_after_sending(pg_session, user_a):
    scadenza, destinatario = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=1)
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService"):
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)

        pg_session.refresh(destinatario)
        assert destinatario.notificato is True
        assert destinatario.notificato_il is not None
    finally:
        _cleanup(pg_session, [(scadenza, destinatario)])


def test_notifies_creator_when_no_explicit_recipients(pg_session, user_a):
    scadenza = Scadenza(
        titolo="TODO senza destinatari",
        data_scadenza=date.today() + timedelta(days=1),
        stato=StatoScadenza.ATTIVA,
        creato_da=user_a.id,
    )
    pg_session.add(scadenza)
    pg_session.commit()
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)

        _, kwargs = MockService.return_value.notify.call_args
        assert user_a.id in kwargs["user_ids"]
    finally:
        pg_session.query(Scadenza).filter_by(id=scadenza.id).delete()
        pg_session.commit()


def test_one_bad_scadenza_does_not_block_others(pg_session, user_a):
    pair1 = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=1)
    pair2 = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=2)
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
            MockService.return_value.notify.side_effect = [RuntimeError("boom"), None]
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)

        assert MockService.return_value.notify.call_count == 2
    finally:
        _cleanup(pg_session, [pair1, pair2])
