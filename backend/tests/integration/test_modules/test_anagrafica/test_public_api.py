"""
Integration tests for anagrafica_italiana's public_api (trova_o_crea_soggetto).

Uses real PostgreSQL (pg_session), not the SQLite db_session fixture — see
tests/unit/test_core/test_notifica_model.py for why db_session is broken
for any row-creating test in this repo.
"""
import pytest
from datetime import date
from sqlalchemy import text

from app.core.database import SessionLocal
from anagrafica_italiana.models import SoggettoAnagrafico
from anagrafica_italiana.services.public_api import trova_o_crea_soggetto


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


def _cleanup(pg_session, soggetto_ids):
    ids = [i for i in soggetto_ids if i]
    if ids:
        pg_session.query(SoggettoAnagrafico).filter(SoggettoAnagrafico.id.in_(ids)).delete(synchronize_session=False)
    pg_session.commit()


def test_creates_new_soggetto_when_no_match(pg_session):
    dto = trova_o_crea_soggetto(
        pg_session,
        nome="Anna",
        cognome="Verdi",
        data_nascita=date(1995, 3, 10),
    )
    try:
        assert dto.creato_ora is True
        soggetto = pg_session.query(SoggettoAnagrafico).filter_by(id=dto.id).first()
        assert soggetto is not None
        assert soggetto.nome == "Anna"
        assert soggetto.cognome == "Verdi"
    finally:
        _cleanup(pg_session, [dto.id])


def test_reuses_existing_soggetto_on_exact_codice_fiscale(pg_session):
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Mario",
        cognome="Bianchi",
        codice_fiscale="BNCMRA80A01H501Z",
    )
    try:
        assert first.creato_ora is True

        second = trova_o_crea_soggetto(
            pg_session,
            nome="Mario",
            cognome="Bianchi",
            codice_fiscale="bncmra80a01h501z",  # lowercase — must still match
        )
        assert second.creato_ora is False
        assert second.id == first.id

        count = (
            pg_session.query(SoggettoAnagrafico)
            .filter(SoggettoAnagrafico.codice_fiscale == "BNCMRA80A01H501Z")
            .count()
        )
        assert count == 1
    finally:
        _cleanup(pg_session, [first.id])


def test_reuses_existing_soggetto_on_exact_documento_identita(pg_session):
    """The scenario this whole change exists for: a foreign tourist with no
    codice fiscale, identified by passport number instead."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Jean",
        cognome="Dupont",
        data_nascita=date(1988, 7, 4),
        tipo_documento_identita="PASSAPORTO",
        numero_documento_identita="fr123456",
        stato_rilascio_documento="FRANCIA",
    )
    try:
        assert first.creato_ora is True

        # Same guest, second stay some time later
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Jean",
            cognome="Dupont",
            data_nascita=date(1988, 7, 4),
            tipo_documento_identita="PASSAPORTO",
            numero_documento_identita="FR123456",  # uppercase — must still match
            stato_rilascio_documento="FRANCIA",
        )
        assert second.creato_ora is False
        assert second.id == first.id
    finally:
        _cleanup(pg_session, [first.id])


def test_does_not_merge_different_people_sharing_name_and_birthdate(pg_session):
    """A fuzzy name+DOB coincidence must never trigger an automatic merge —
    only a real identifier (CF or document) counts as a certain match."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Mario",
        cognome="Rossi",
        data_nascita=date(1980, 1, 1),
    )
    try:
        # Same name and birth date, but no shared identifier — must be a
        # DIFFERENT, new soggetto, not silently merged into the first.
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Mario",
            cognome="Rossi",
            data_nascita=date(1980, 1, 1),
        )
        assert second.creato_ora is True
        assert second.id != first.id
    finally:
        _cleanup(pg_session, [first.id, second.id])


def test_different_document_country_does_not_match(pg_session):
    """A document number alone isn't globally unique — the issuing country
    must match too, or it's treated as a different soggetto."""
    first = trova_o_crea_soggetto(
        pg_session,
        nome="Anna",
        cognome="Kowalski",
        tipo_documento_identita="CARTA_IDENTITA",
        numero_documento_identita="XYZ1000",
        stato_rilascio_documento="POLONIA",
    )
    try:
        second = trova_o_crea_soggetto(
            pg_session,
            nome="Anna",
            cognome="Kowalski",
            tipo_documento_identita="CARTA_IDENTITA",
            numero_documento_identita="XYZ1000",
            stato_rilascio_documento="GERMANIA",
        )
        assert second.creato_ora is True
        assert second.id != first.id
    finally:
        _cleanup(pg_session, [first.id, second.id])
