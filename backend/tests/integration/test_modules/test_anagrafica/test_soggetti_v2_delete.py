"""
Regression tests for DELETE /anagrafica/soggetti-v2/{id} when the soggetto
has an active role (Proprietario/Affittuario/Tecnico) linked to it.

Before this fix, delete_soggetto_v2 had no guard and went straight to
db.delete()/commit(). SoggettoAnagrafico.proprietari (and .tecnici) have
no cascade/passive_deletes configured, and immo_proprietari has no real
FK constraint in the DB at all, so deleting a soggetto already registered
as a Proprietario crashed with a NotNullViolation instead of the intended
"can't delete, has active roles" 400 (the v1 soggetti.py router — not
mounted — already implements this exact guard; v2, the live route, never
had it).

Uses real PostgreSQL (pg_session), same pattern as test_public_api.py.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto
from anagrafica_italiana.routes.soggetti_v2 import delete_soggetto_v2

from immobili.models import Proprietario
from immobili.routes.proprietari import create_proprietario
from immobili.schemas import ProprietarioCreate

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
def soggetto(pg_session):
    s = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Delete",
        cognome="Guard",
        codice_fiscale="DLTGRD80A01H501G",
    )
    pg_session.add(s)
    pg_session.commit()
    yield s
    pg_session.rollback()
    pg_session.query(SoggettoAnagrafico).filter_by(id=s.id).delete()
    pg_session.commit()


def test_delete_soggetto_blocked_when_registered_as_proprietario(pg_session, soggetto):
    proprietario = create_proprietario(ProprietarioCreate(soggetto_id=soggetto.id), db=pg_session)
    try:
        with pytest.raises(HTTPException) as exc_info:
            delete_soggetto_v2(soggetto.id, db=pg_session)
        assert exc_info.value.status_code == 400

        # Blocked, not silently cascaded: both rows must still exist.
        assert pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto.id).first() is not None
        assert pg_session.query(Proprietario).filter_by(id=proprietario.id).first() is not None
    finally:
        pg_session.rollback()
        pg_session.query(Proprietario).filter_by(id=proprietario.id).delete()
        pg_session.commit()


def test_delete_soggetto_succeeds_without_roles(pg_session, soggetto):
    soggetto_id = soggetto.id

    delete_soggetto_v2(soggetto_id, db=pg_session)

    assert pg_session.query(SoggettoAnagrafico).filter_by(id=soggetto_id).first() is None
