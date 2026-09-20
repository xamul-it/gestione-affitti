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


def test_notifies_creator_when_no_explicit_recipients_and_does_not_renotify(pg_session, user_a):
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

            # second run: must NOT re-notify — a ScadenzaDestinatario row
            # for the creator should now exist and be marked notified
            MockService.reset_mock()
            _check_scadenze_in_avvicinamento(pg_session, giorni_prima=3)
            MockService.return_value.notify.assert_not_called()
    finally:
        pg_session.query(ScadenzaDestinatario).filter_by(scadenza_id=scadenza.id).delete()
        pg_session.query(Scadenza).filter_by(id=scadenza.id).delete()
        pg_session.commit()


def test_check_scadenze_scadute_notifies_and_does_not_renotify(pg_session, user_a):
    from app.core.platform_services.scadenza_reminder_job import _check_scadenze_scadute

    scadenza, destinatario = _make_scadenza(pg_session, user_a.id, giorni_da_oggi=-1)
    scadenza.stato = StatoScadenza.SCADUTA
    pg_session.commit()
    try:
        with patch("app.core.platform_services.scadenza_reminder_job.NotificationService") as MockService:
            _check_scadenze_scadute(pg_session)
            MockService.return_value.notify.assert_called_once()

            pg_session.refresh(destinatario)
            assert destinatario.notificato is True

            MockService.reset_mock()
            _check_scadenze_scadute(pg_session)
            MockService.return_value.notify.assert_not_called()
    finally:
        _cleanup(pg_session, [(scadenza, destinatario)])


def test_run_reminder_check_uses_a_single_connection_throughout():
    """
    Regression test for the search_path/connection-pooling bug: proves
    run_reminder_check keeps the SAME physical connection for its entire
    call (bound once, never returned to the pool and re-checked-out
    mid-run), which is what guarantees search_path survives its own
    internal commits without needing to be re-asserted after each one.

    This checks connection IDENTITY rather than a sampled search_path
    string, so it can't false-pass due to pool contamination from other
    tests in this file that also set search_path to tenant_qa_test and
    commit it — a connection-identity check is true regardless of what
    value any given connection happens to carry.

    Patches `Session._connection_for_bind` rather than the public
    `Session.connection()` wrapper: every internal ORM operation (query,
    execute, flush, ...) resolves its connection via
    `_connection_for_bind` directly, never through the public `connection()`
    method, so that's the only hook point that actually observes what
    connection object each statement really used.
    """
    from unittest.mock import patch
    from sqlalchemy.orm import Session as OrmSession
    from app.core.platform_services.scadenza_reminder_job import run_reminder_check

    seen_connection_ids = []
    original_connection_for_bind = OrmSession._connection_for_bind

    def spying_connection_for_bind(self, *args, **kwargs):
        conn = original_connection_for_bind(self, *args, **kwargs)
        seen_connection_ids.append(id(conn))
        return conn

    with patch.object(OrmSession, "_connection_for_bind", spying_connection_for_bind):
        run_reminder_check("tenant_qa_test")

    assert seen_connection_ids, "expected at least one statement to run during the call"
    assert len(set(seen_connection_ids)) == 1, (
        f"run_reminder_check used {len(set(seen_connection_ids))} distinct "
        "connection objects during one call — search_path is not guaranteed "
        "to survive across them"
    )


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
