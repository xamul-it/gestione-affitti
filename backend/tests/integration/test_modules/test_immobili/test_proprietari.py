"""
Integration tests for the soggetto-based Proprietario role.

Calls route functions directly (db=pg_session) rather than through
TestClient/HTTP/JWT — same established pattern as
test_conduttori_spese_ricorrenti.py. Real PostgreSQL (pg_session), not
the SQLite db_session fixture, which is documented-broken for any
row-creating test in this repo.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto

from immobili.models import DirittoImmobile, Proprietario, UnitaImmobiliare
from immobili.routes.proprietari import (
    create_proprietario,
    delete_proprietario,
    get_proprietari,
    update_proprietario,
)
from immobili.routes.diritti_immobile import create_diritto
from immobili.schemas import DirittoImmobileCreate, ProprietarioCreate, ProprietarioUpdate

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    from app.core.database import SessionLocal
    session = SessionLocal()
    try:
        session.execute(text(f"SET search_path TO {TENANT}, public"))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def soggetto_proprietario(pg_session):
    s = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Giulia",
        cognome="Proprietaria",
        codice_fiscale="PRPGLI80A01H501Y",
    )
    pg_session.add(s)
    pg_session.commit()
    try:
        yield s
    finally:
        pg_session.query(SoggettoAnagrafico).filter_by(id=s.id).delete()
        pg_session.commit()


@pytest.fixture
def unita(pg_session):
    u = UnitaImmobiliare(
        codice="TEST-PROP-001",
        tipo="Appartamento",
        indirizzo="Via Test 2",
        citta="Testville",
    )
    pg_session.add(u)
    pg_session.commit()
    try:
        yield u
    finally:
        pg_session.query(UnitaImmobiliare).filter_by(id=u.id).delete()
        pg_session.commit()


def test_create_proprietario_requires_soggetto_id(pg_session, soggetto_proprietario):
    proprietario = None
    try:
        proprietario = create_proprietario(
            ProprietarioCreate(soggetto_id=soggetto_proprietario.id, note_proprietario="test"),
            db=pg_session,
        )
        assert proprietario.id is not None
        assert proprietario.soggetto_id == soggetto_proprietario.id
        assert proprietario.note_proprietario == "test"
    finally:
        pg_session.rollback()
        if proprietario:
            pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
        pg_session.commit()


def test_create_proprietario_rejects_duplicate_soggetto(pg_session, soggetto_proprietario):
    proprietario = None
    try:
        proprietario = create_proprietario(
            ProprietarioCreate(soggetto_id=soggetto_proprietario.id),
            db=pg_session,
        )
        with pytest.raises(HTTPException) as exc_info:
            create_proprietario(
                ProprietarioCreate(soggetto_id=soggetto_proprietario.id),
                db=pg_session,
            )
        assert exc_info.value.status_code == 400
    finally:
        pg_session.rollback()
        if proprietario:
            pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
        pg_session.commit()


def test_update_proprietario_note_only(pg_session, soggetto_proprietario):
    proprietario = None
    try:
        proprietario = create_proprietario(
            ProprietarioCreate(soggetto_id=soggetto_proprietario.id, note_proprietario="iniziale"),
            db=pg_session,
        )
        aggiornato = update_proprietario(
            proprietario.id,
            ProprietarioUpdate(note_proprietario="aggiornata"),
            db=pg_session,
        )
        assert aggiornato.note_proprietario == "aggiornata"
        assert aggiornato.soggetto_id == soggetto_proprietario.id
    finally:
        pg_session.rollback()
        if proprietario:
            pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
        pg_session.commit()


def test_get_proprietari_does_not_crash(pg_session, soggetto_proprietario):
    """Regression test: get_all() used to filter on a deprecated Integer
    'attivo' column against a Python bool, raising
    'operator does not exist: integer = boolean' in Postgres."""
    proprietario = None
    try:
        proprietario = create_proprietario(
            ProprietarioCreate(soggetto_id=soggetto_proprietario.id),
            db=pg_session,
        )
        risultati = get_proprietari(db=pg_session)
        assert any(p.id == proprietario.id for p in risultati)
    finally:
        pg_session.rollback()
        if proprietario:
            pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
        pg_session.commit()


def test_delete_proprietario_cascades_diritti(pg_session, soggetto_proprietario, unita):
    proprietario = None
    try:
        proprietario = create_proprietario(
            ProprietarioCreate(soggetto_id=soggetto_proprietario.id),
            db=pg_session,
        )
        diritto = create_diritto(
            DirittoImmobileCreate(
                unita_immobiliare_id=unita.id,
                proprietario_id=proprietario.id,
                tipo_diritto="PROPRIETARIO",
                quota_percentuale=100,
            ),
            db=pg_session,
        )
        diritto_id = diritto.id

        delete_proprietario(proprietario.id, db=pg_session)

        assert pg_session.query(Proprietario).filter_by(id=proprietario.id).first() is None
        assert pg_session.query(DirittoImmobile).filter_by(id=diritto_id).first() is None
        proprietario = None  # already deleted by the route under test
    finally:
        pg_session.rollback()
        if proprietario:
            pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
            pg_session.commit()
