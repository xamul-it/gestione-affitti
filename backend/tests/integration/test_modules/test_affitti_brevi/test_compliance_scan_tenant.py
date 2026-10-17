"""
Test di integrazione per compliance_scheduler._scan_tenant — verifica il
filtro valido=True/data_checkin sulla query, che ComplianceScadenzeService
da solo non applica (riceve solo il Soggiorno che il chiamante gli passa).

Usa pg_session bound a singola Connection (stesso pattern di
test_compliance_scadenze_service.py / test_ical_sync.py).
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, Prenotazione, Soggiorno
from affitti_brevi.services.compliance_scheduler import _scan_tenant
from app.core.platform.models import Scadenza, ScadenzaDestinatario
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


def _crea_soggiorno(pg_session, codice, valido=True):
    unita = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via Test 1", citta="Testville")
    pg_session.add(unita)
    pg_session.flush()

    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione=f"{codice}-PREN",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    soggiorno = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=2),
        valido=valido,
    )
    pg_session.add(soggiorno)
    pg_session.commit()
    return unita, prenotazione, soggiorno


def test_scan_tenant_ignora_soggiorni_non_validi(pg_session):
    unita_ok, pren_ok, soggiorno_ok = _crea_soggiorno(pg_session, "TEST-SCAN-OK")
    unita_ko, pren_ko, soggiorno_ko = _crea_soggiorno(pg_session, "TEST-SCAN-KO", valido=False)

    try:
        stats = _scan_tenant(TENANT)

        assert stats["errori"] == 0
        comunicazioni_ok = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ok.id).count()
        comunicazioni_ko = pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno_ko.id).count()

        assert comunicazioni_ok == 2  # Polizia + tassa
        assert comunicazioni_ko == 0
    finally:
        # Le Comunicazioni create dalla scan possono aver generato Scadenze
        # core collegate (ComplianceScadenzeService -> ScadenzaService.
        # create_scadenza). Queste vivono nella stessa connessione
        # (search_path già include lo schema tenant) ma non sono coperte da
        # cascade su Comunicazione/Soggiorno — vanno ripulite esplicitamente
        # per evitare accumulo tra run successivi (stessa lezione di
        # test_compliance_scadenze_service.py).
        scadenza_ids = [
            row[0] for row in
            pg_session.query(Comunicazione.scadenza_id)
            .filter(
                Comunicazione.soggiorno_id.in_([soggiorno_ok.id, soggiorno_ko.id]),
                Comunicazione.scadenza_id.isnot(None),
            )
            .all()
        ]

        for unita, prenotazione, soggiorno in [(unita_ok, pren_ok, soggiorno_ok), (unita_ko, pren_ko, soggiorno_ko)]:
            pg_session.query(Comunicazione).filter_by(soggiorno_id=soggiorno.id).delete()
            pg_session.query(Soggiorno).filter_by(id=soggiorno.id).delete()
            pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
            pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()

        if scadenza_ids:
            pg_session.query(ScadenzaDestinatario).filter(
                ScadenzaDestinatario.scadenza_id.in_(scadenza_ids)
            ).delete(synchronize_session=False)
            pg_session.query(Scadenza).filter(
                Scadenza.id.in_(scadenza_ids)
            ).delete(synchronize_session=False)

        pg_session.commit()
