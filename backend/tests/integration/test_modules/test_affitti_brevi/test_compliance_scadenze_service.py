"""
Test per ComplianceScadenzeService — motore scadenze compliance
(docs/superpowers/specs/2026-09-28-affitti-brevi-motore-scadenze-compliance-design.md).

Usa pg_session bound a singola Connection (pattern stabilito in questa
sessione, vedi test_ical_sync.py per il razionale).
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, TipoComunicazione, Prenotazione, Soggiorno
from affitti_brevi.services.compliance_scadenze_service import ComplianceScadenzeService
from app.core.platform_services import ScadenzaService
from immobili.models import UnitaImmobiliare

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
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
def soggiorno(pg_session):
    unita = UnitaImmobiliare(
        codice="TEST-COMPL-001",
        tipo="Appartamento",
        indirizzo="Via Test 1",
        citta="Testville",
    )
    pg_session.add(unita)
    pg_session.flush()

    checkin = date.today() + timedelta(hours=6)
    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione="TEST-COMPL-PREN-001",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=3),
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    s = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=3),
    )
    pg_session.add(s)
    pg_session.commit()

    yield s

    pg_session.query(Comunicazione).filter_by(soggiorno_id=s.id).delete()
    pg_session.query(Soggiorno).filter_by(id=s.id).delete()
    pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
    pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()
    pg_session.commit()


def test_genera_scadenza_polizia_crea_comunicazione_e_scadenza(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)

    comunicazione = service.genera_scadenza_polizia(soggiorno)

    assert comunicazione is not None
    assert comunicazione.tipo == TipoComunicazione.POLIZIA.value
    assert comunicazione.scadenza_id is not None

    scadenza = ScadenzaService(pg_session).get_scadenza(comunicazione.scadenza_id)
    assert scadenza is not None
    assert scadenza.modulo == "affitti_brevi"
    assert scadenza.entity_type == "comunicazione"
    assert scadenza.entity_id == comunicazione.id
    # 24h dal check-in
    assert scadenza.data_scadenza == soggiorno.data_checkin + timedelta(days=1)


def test_genera_scadenza_polizia_idempotente(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)

    primo = service.genera_scadenza_polizia(soggiorno)
    secondo = service.genera_scadenza_polizia(soggiorno)

    assert primo is not None
    assert secondo is None  # no-op, già esisteva

    count = pg_session.query(Comunicazione).filter_by(
        soggiorno_id=soggiorno.id, tipo=TipoComunicazione.POLIZIA.value
    ).count()
    assert count == 1


def test_genera_scadenza_tassa_crea_comunicazione_con_data_checkin(pg_session, soggiorno):
    service = ComplianceScadenzeService(pg_session)

    comunicazione = service.genera_scadenza_tassa(soggiorno)

    assert comunicazione is not None
    assert comunicazione.tipo == TipoComunicazione.TASSA_DICHIARAZIONE.value

    scadenza = ScadenzaService(pg_session).get_scadenza(comunicazione.scadenza_id)
    assert scadenza.data_scadenza == soggiorno.data_checkin
