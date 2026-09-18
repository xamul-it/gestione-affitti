"""
Uses real PostgreSQL (pg_session), not the SQLite db_session fixture —
see tests/unit/test_core/test_notifica_model.py and
tests/integration/test_tenant_module_routes.py for why db_session is
currently broken for any row-creating test in this repo.
"""
import smtplib
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.auth.models import User
from app.core.auth.security import get_password_hash
from app.core.platform.models import CanaleNotifica, StatoEmailNotifica
from app.core.platform_services.notification_service import NotificationService


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see docstring in test_notifica_model.py for the full rationale."""
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
def service(pg_session):
    return NotificationService(pg_session)


def _make_throwaway_user(pg_session, suffix):
    user = User(
        email=f"notif-service-test-{suffix}@example.com",
        username=f"notif_service_test_{suffix}",
        full_name=f"Notif Test {suffix}",
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


def _cleanup_notifiche(pg_session, notifiche):
    from app.core.platform.models import Notifica
    ids = [n.id for n in notifiche]
    if ids:
        pg_session.query(Notifica).filter(Notifica.id.in_(ids)).delete(synchronize_session=False)
    pg_session.commit()


def test_notify_creates_in_app_row_without_email_when_smtp_not_configured(service, pg_session, user_a):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        result = service.notify(
            user_ids=[user_a.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.ENTRAMBI,
        )
    try:
        assert len(result) == 1
        notifica = result[0]
        assert notifica.user_id == user_a.id
        assert notifica.stato_email == StatoEmailNotifica.NON_RICHIESTA.value
        assert notifica.letta is False
    finally:
        _cleanup_notifiche(pg_session, result)


def test_notify_email_only_channel_still_creates_row(service, pg_session, user_a):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        result = service.notify(
            user_ids=[user_a.id],
            tipo="scadenza.reminder",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.EMAIL,
        )
    try:
        assert len(result) == 1
        assert result[0].canali == CanaleNotifica.EMAIL.value
    finally:
        _cleanup_notifiche(pg_session, result)


def test_notify_multiple_recipients(service, pg_session, user_a, user_b):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        result = service.notify(
            user_ids=[user_a.id, user_b.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
        )
    try:
        assert {n.user_id for n in result} == {user_a.id, user_b.id}
    finally:
        _cleanup_notifiche(pg_session, result)


def test_notify_sends_email_and_marks_sent_on_success(service, pg_session, user_a):
    smtp_instance = MagicMock()
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", "smtp.example.com"), \
         patch("app.core.config.settings.NOTIFICHE_SMTP_TLS", "STARTTLS"), \
         patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = smtp_instance
        result = service.notify(
            user_ids=[user_a.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.EMAIL,
        )
    try:
        assert result[0].stato_email == StatoEmailNotifica.SENT.value
        smtp_instance.sendmail.assert_called_once()
    finally:
        _cleanup_notifiche(pg_session, result)


def test_notify_marks_failed_on_smtp_error_but_keeps_in_app_row(service, pg_session, user_a):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", "smtp.example.com"), \
         patch("app.core.config.settings.NOTIFICHE_SMTP_TLS", "STARTTLS"), \
         patch("smtplib.SMTP", side_effect=smtplib.SMTPException("boom")):
        result = service.notify(
            user_ids=[user_a.id],
            tipo="test.evento",
            titolo="Titolo",
            corpo="Corpo",
            canali=CanaleNotifica.EMAIL,
        )
    try:
        assert len(result) == 1
        assert result[0].stato_email == StatoEmailNotifica.FAILED.value
        assert result[0].errore_email is not None
    finally:
        _cleanup_notifiche(pg_session, result)


def test_list_for_user_filters_by_owner(service, pg_session, user_a, user_b):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        r1 = service.notify(user_ids=[user_a.id], tipo="a", titolo="A", corpo="A")
        r2 = service.notify(user_ids=[user_b.id], tipo="b", titolo="B", corpo="B")
    try:
        mine = service.list_for_user(user_a.id)
        assert len(mine) == 1
        assert mine[0].user_id == user_a.id
    finally:
        _cleanup_notifiche(pg_session, r1 + r2)


def test_list_for_user_solo_non_lette(service, pg_session, user_a):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        notifiche = service.notify(user_ids=[user_a.id], tipo="a", titolo="A", corpo="A")
    try:
        service.segna_letta(notifiche[0].id, user_a.id)
        assert service.list_for_user(user_a.id, solo_non_lette=True) == []
        assert len(service.list_for_user(user_a.id, solo_non_lette=False)) == 1
    finally:
        _cleanup_notifiche(pg_session, notifiche)


def test_segna_letta_only_affects_owner(service, pg_session, user_a, user_b):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        notifiche = service.notify(user_ids=[user_a.id], tipo="a", titolo="A", corpo="A")
    try:
        result = service.segna_letta(notifiche[0].id, user_b.id)
        assert result is None  # not the owner, no-op

        result = service.segna_letta(notifiche[0].id, user_a.id)
        assert result.letta is True
        assert result.letta_il is not None
    finally:
        _cleanup_notifiche(pg_session, notifiche)


def test_segna_tutte_lette(service, pg_session, user_a):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        r1 = service.notify(user_ids=[user_a.id], tipo="a", titolo="A", corpo="A")
        r2 = service.notify(user_ids=[user_a.id], tipo="b", titolo="B", corpo="B")
    try:
        count = service.segna_tutte_lette(user_a.id)
        assert count == 2
        assert service.badge_count(user_a.id) == 0
    finally:
        _cleanup_notifiche(pg_session, r1 + r2)


def test_badge_count(service, pg_session, user_a):
    with patch("app.core.config.settings.NOTIFICHE_SMTP_HOST", None):
        r1 = service.notify(user_ids=[user_a.id], tipo="a", titolo="A", corpo="A")
        r2 = service.notify(user_ids=[user_a.id], tipo="b", titolo="B", corpo="B")
    try:
        service.segna_letta(r2[0].id, user_a.id)
        assert service.badge_count(user_a.id) == 1
    finally:
        _cleanup_notifiche(pg_session, r1 + r2)
