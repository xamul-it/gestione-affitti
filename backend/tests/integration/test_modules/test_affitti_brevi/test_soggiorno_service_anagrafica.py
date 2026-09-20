"""
Integration test: SoggiornoService.registra_ospite() links each guest to
the shared anagrafica registry (creating or reusing a SoggettoAnagrafico),
via anagrafica_client -> anagrafica_italiana.services.public_api.

Uses real PostgreSQL (pg_session), not the SQLite db_session fixture — see
tests/unit/test_core/test_notifica_model.py for why db_session is broken
for any row-creating test in this repo.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.core.database import SessionLocal
from anagrafica_italiana.models import SoggettoAnagrafico
from immobili.models import UnitaImmobiliare
from affitti_brevi.models import Prenotazione, Soggiorno, OspiteSoggiorno
from affitti_brevi.services.soggiorno_service import SoggiornoService


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
def soggiorno(pg_session):
    """A minimal, valid Soggiorno with the real FK chain it requires
    (UnitaImmobiliare -> Prenotazione -> Soggiorno), with explicit cleanup
    in reverse FK order."""
    unita = UnitaImmobiliare(
        codice="TEST-ANAG-001",
        tipo="Appartamento",
        indirizzo="Via di Prova 1",
        citta="Roma",
    )
    pg_session.add(unita)
    pg_session.flush()

    prenotazione = Prenotazione(
        unita_immobiliare_id=unita.id,
        codice_prenotazione="TEST-BOOKING-001",
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=3),
        numero_ospiti=1,
    )
    pg_session.add(prenotazione)
    pg_session.flush()

    stay = Soggiorno(
        prenotazione_id=prenotazione.id,
        unita_immobiliare_id=unita.id,
        data_checkin=date.today(),
        data_checkout=date.today() + timedelta(days=3),
        numero_ospiti_previsti=1,
    )
    pg_session.add(stay)
    pg_session.commit()

    try:
        yield stay
    finally:
        pg_session.query(OspiteSoggiorno).filter_by(soggiorno_id=stay.id).delete()
        pg_session.query(Soggiorno).filter_by(id=stay.id).delete()
        pg_session.query(Prenotazione).filter_by(id=prenotazione.id).delete()
        pg_session.query(UnitaImmobiliare).filter_by(id=unita.id).delete()
        pg_session.commit()


def test_registra_ospite_creates_and_links_new_soggetto(pg_session, soggiorno):
    service = SoggiornoService(pg_session)

    ospite = service.registra_ospite(
        soggiorno_id=soggiorno.id,
        dati_ospite={
            "nome": "Jean",
            "cognome": "Dupont",
            "data_nascita": date(1988, 7, 4),
            "tipo_documento": "PASSAPORTO",
            "numero_documento": "FR999888",
            "stato_rilascio": "FRANCIA",
        },
    )

    try:
        assert ospite.soggetto_anagrafico_id is not None
        soggetto = pg_session.query(SoggettoAnagrafico).filter_by(id=ospite.soggetto_anagrafico_id).first()
        assert soggetto is not None
        assert soggetto.nome == "Jean"
        assert soggetto.numero_documento_identita == "FR999888"
    finally:
        soggetto_id = ospite.soggetto_anagrafico_id
        pg_session.query(OspiteSoggiorno).filter_by(id=ospite.id).delete()
        pg_session.commit()
        if soggetto_id:
            pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto_id).delete()
            pg_session.commit()


def test_registra_ospite_reuses_soggetto_for_returning_guest(pg_session, soggiorno):
    """A guest who stayed before (same passport) gets linked to the SAME
    registry entry on a new stay, not a duplicate one."""
    service = SoggiornoService(pg_session)

    dati_ospite = {
        "nome": "Hans",
        "cognome": "Muller",
        "data_nascita": date(1975, 11, 2),
        "tipo_documento": "CARTA_IDENTITA",
        "numero_documento": "DE555444",
        "stato_rilascio": "GERMANIA",
    }

    primo_ospite = service.registra_ospite(soggiorno_id=soggiorno.id, dati_ospite=dati_ospite, principale=True)
    secondo_ospite = service.registra_ospite(soggiorno_id=soggiorno.id, dati_ospite=dict(dati_ospite))

    try:
        assert primo_ospite.soggetto_anagrafico_id is not None
        assert secondo_ospite.soggetto_anagrafico_id == primo_ospite.soggetto_anagrafico_id

        count = (
            pg_session.query(SoggettoAnagrafico)
            .filter(SoggettoAnagrafico.numero_documento_identita == "DE555444")
            .count()
        )
        assert count == 1
    finally:
        soggetto_id = primo_ospite.soggetto_anagrafico_id
        pg_session.query(OspiteSoggiorno).filter(
            OspiteSoggiorno.id.in_([primo_ospite.id, secondo_ospite.id])
        ).delete(synchronize_session=False)
        pg_session.commit()
        if soggetto_id:
            pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto_id).delete()
            pg_session.commit()
