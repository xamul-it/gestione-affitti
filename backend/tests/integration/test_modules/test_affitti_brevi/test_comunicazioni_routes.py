"""
Test di integrazione per le route /comunicazioni — vedi
test_compliance_scadenze_service.py per i test della logica di dominio
sottostante; qui si verifica solo il livello HTTP/route.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from affitti_brevi.models import Comunicazione, Prenotazione, Soggiorno
from affitti_brevi.services.compliance_scadenze_service import ComplianceScadenzeService
from affitti_brevi.routes.comunicazioni import router as comunicazioni_router
from immobili.models import UnitaImmobiliare
from app.core.database import get_db
from app.core.platform.models import Scadenza, ScadenzaDestinatario
from fastapi import FastAPI

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
def client(pg_session):
    app = FastAPI()
    app.include_router(comunicazioni_router, prefix="/api/v1/affitti-brevi")
    app.dependency_overrides[get_db] = lambda: pg_session
    return TestClient(app)


@pytest.fixture
def comunicazione(pg_session):
    unita = UnitaImmobiliare(codice="TEST-ROUTE-001", tipo="Appartamento", indirizzo="Via Test 1", citta="Testville")
    pg_session.add(unita)
    pg_session.flush()

    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione="TEST-ROUTE-PREN-001",
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
    )
    pg_session.add(soggiorno)
    pg_session.commit()

    c = ComplianceScadenzeService(pg_session).genera_scadenza_polizia(soggiorno)

    yield c

    # Le Comunicazioni generate da genera_scadenza_polizia possono aver
    # creato una Scadenza core collegata (ScadenzaService.create_scadenza).
    # Vive nella stessa connessione/schema tenant ma non è coperta da
    # cascade su Comunicazione/Soggiorno — va ripulita esplicitamente
    # (stessa lezione di test_compliance_scadenze_service.py).
    scadenza_ids = [
        row[0] for row in
        pg_session.query(Comunicazione.scadenza_id)
        .filter(Comunicazione.soggiorno_id == soggiorno.id, Comunicazione.scadenza_id.isnot(None))
        .all()
    ]

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


def test_get_comunicazione(client, comunicazione):
    response = client.get(f"/api/v1/affitti-brevi/comunicazioni/{comunicazione.id}")
    assert response.status_code == 200
    assert response.json()["tipo"] == "POLIZIA"


def test_get_comunicazione_404(client):
    response = client.get("/api/v1/affitti-brevi/comunicazioni/999999")
    assert response.status_code == 404


def test_segna_completata(client, comunicazione):
    response = client.post(
        f"/api/v1/affitti-brevi/comunicazioni/{comunicazione.id}/segna-completata",
        json={"note": "Inviato a mano allo sportello"},
    )
    assert response.status_code == 200
    assert response.json()["stato"] == "INVIATA"
