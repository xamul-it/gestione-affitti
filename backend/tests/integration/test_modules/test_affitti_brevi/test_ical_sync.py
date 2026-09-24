"""
Regression tests for the iCal sync pipeline (Booking.com/Airbnb/Vrbo import).

Found broken end-to-end while investigating "I never see the calendar
import" for the affitti_brevi module:

- routes/canali.py ordered by Canale.ordine, a column that doesn't exist
  on the model (only .nome) — GET /canali/ 500'd unconditionally.
- routes/calendari.py's create_calendario duplicate-check referenced
  CalendarioCanale.portale / calendario.portale — fields that don't
  exist since the Canale/CalendarioCanale refactor (it's canale_id now)
  — POST /calendari/ 500'd unconditionally.
- routes/sync.py's sync_single_calendario and sync_calendari_unita
  built SyncResult(**result) / read result.get(...) from
  ICalSyncService.sync_calendario()'s actual return type, a 4-tuple
  (created, updated, skipped, error) — both crashed unconditionally on
  every call.
- services/sync_scheduler.py (the automatic background sync, started at
  app startup but never actually started before, and never actually
  reachable end-to-end) used the *other*, parallel ICalParser/
  ical_parser.py implementation, whose model references (CalendarioIcal.
  portale, Prenotazione.calendario_ical_id/portale_origine,
  OriginePrenotazione) all predate the same refactor and don't exist —
  every automatic sync failed immediately at import time. It's been
  switched to use ICalSyncService instead, the implementation
  routes/sync.py already uses and SyncResult/SyncAllResponse are shaped
  for.

Uses real PostgreSQL (pg_session bound to one explicit Connection —
see the docstring on that fixture for why), same established pattern
as other integration tests this session. Mocks ICalSyncService.fetch_ical
to avoid a real network call.
"""
from unittest.mock import patch

import pytest
from sqlalchemy import text

from affitti_brevi.models import Canale, CalendarioCanale, Prenotazione
from affitti_brevi.routes.canali import get_canali
from affitti_brevi.services.ical_sync_service import ICalSyncService
from immobili.models import UnitaImmobiliare

TENANT = "tenant_qa_test"

SAMPLE_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:TESTREG456@airbnb.com
DTSTART;VALUE=DATE:20270301
DTEND;VALUE=DATE:20270305
SUMMARY:Reserved - TESTREG456
DESCRIPTION:Prezzo totale: EUR 420.00
END:VEVENT
END:VCALENDAR
"""


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    """
    Bound to a single, explicitly-checked-out Connection for the fixture's
    whole lifetime (rather than letting the Session pull from/return to the
    engine's pool per-transaction, as plain SessionLocal() does). A commit
    or rollback ends a *logical* transaction and releases the connection
    back to the pool; the next query can then land on a *different* pooled
    connection that never had this fixture's `SET search_path` applied,
    surfacing as a spurious "relation does not exist" on an otherwise
    correct query.
    """
    from app.core.database import engine
    from sqlalchemy.orm import Session as SASession

    connection = engine.connect()
    connection.execute(text(f"SET search_path TO {TENANT}, public"))
    connection.commit()
    session = SASession(bind=connection)
    try:
        yield session
    finally:
        session.close()
        connection.close()


@pytest.fixture
def unita(pg_session):
    u = UnitaImmobiliare(
        codice="TEST-ICAL-001",
        tipo="Appartamento",
        indirizzo="Via Test 1",
        citta="Testville",
    )
    pg_session.add(u)
    pg_session.commit()
    unita_id = u.id
    yield u
    pg_session.query(Prenotazione).filter_by(unita_immobiliare_id=unita_id).delete()
    pg_session.query(UnitaImmobiliare).filter_by(id=unita_id).delete()
    pg_session.commit()


def test_get_canali_does_not_crash(pg_session):
    """
    Regression test for the Canale.ordine AttributeError: calls the actual
    route function (not just a query shaped like it), since a query that
    merely resembles the route's own would not have caught this.
    """
    response = get_canali(db=pg_session)
    assert response.totale > 0
    assert any(c.codice == "AIRBNB" for c in response.canali)


def test_create_calendario_rejects_duplicate_by_canale(pg_session, unita):
    airbnb = pg_session.query(Canale).filter_by(codice="AIRBNB").first()
    cal = CalendarioCanale(unita_immobiliare_id=unita.id, canale_id=airbnb.id, url_ical="http://example.invalid/a.ics")
    pg_session.add(cal)
    pg_session.commit()
    cal_id = cal.id
    try:
        # Regression test for the .portale AttributeError: this exact
        # query shape is what create_calendario's duplicate-check runs.
        existing = pg_session.query(CalendarioCanale).filter(
            CalendarioCanale.unita_immobiliare_id == unita.id,
            CalendarioCanale.canale_id == airbnb.id,
        ).first()
        assert existing is not None
        assert existing.id == cal_id
    finally:
        pg_session.query(CalendarioCanale).filter_by(id=cal_id).delete()
        pg_session.commit()


def test_sync_calendario_creates_prenotazione(pg_session, unita):
    """
    Regression test for the whole pipeline: ICalSyncService.sync_calendario
    is what both routes/sync.py and the scheduler now call. Verifies it
    returns the documented 4-tuple and actually creates a Prenotazione
    with the current model's real field names (calendario_canale_id, not
    the old calendario_ical_id/portale_origine).
    """
    airbnb = pg_session.query(Canale).filter_by(codice="AIRBNB").first()
    cal = CalendarioCanale(unita_immobiliare_id=unita.id, canale_id=airbnb.id, url_ical="http://example.invalid/a.ics")
    pg_session.add(cal)
    pg_session.commit()
    cal_id = cal.id

    try:
        with patch.object(ICalSyncService, "fetch_ical", return_value=SAMPLE_ICAL):
            created, updated, skipped, error = ICalSyncService(pg_session).sync_calendario(cal_id)

        assert error is None
        assert created == 1
        assert updated == 0
        assert skipped == 0

        prenotazione = pg_session.query(Prenotazione).filter_by(uid_ical="TESTREG456@airbnb.com").first()
        assert prenotazione is not None
        assert prenotazione.calendario_canale_id == cal_id
        assert prenotazione.unita_immobiliare_id == unita.id
        assert str(prenotazione.data_checkin) == "2027-03-01"
        assert str(prenotazione.data_checkout) == "2027-03-05"

        # Re-syncing the same feed must not duplicate the booking.
        with patch.object(ICalSyncService, "fetch_ical", return_value=SAMPLE_ICAL):
            created2, updated2, skipped2, error2 = ICalSyncService(pg_session).sync_calendario(cal_id)
        assert error2 is None
        assert created2 == 0
        assert skipped2 == 1
    finally:
        pg_session.query(Prenotazione).filter_by(calendario_canale_id=cal_id).delete()
        pg_session.query(CalendarioCanale).filter_by(id=cal_id).delete()
        pg_session.commit()
