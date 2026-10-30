"""
Integration tests for the "import unità immobiliari da visura catastale" flow.

Calls services/route functions directly (db=pg_session) rather than through
TestClient/HTTP/JWT — same established pattern as test_proprietari.py.
Real PostgreSQL (pg_session), not the SQLite db_session fixture.
"""
from decimal import Decimal

import pytest
from sqlalchemy import text

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto, TipoDocumento
from anagrafica_italiana.seeds.seed_tipi_documento import seed_tipi_documento

from immobili.models import DirittoImmobile, Proprietario, UnitaImmobiliare
from immobili.models.diritti_immobile import TipoDiritto

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


def test_diritto_uso_persisted(pg_session):
    s = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Ugo",
        cognome="Usuario",
        codice_fiscale="SURUGO80A01H501Z",
    )
    pg_session.add(s)
    pg_session.flush()
    p = Proprietario(soggetto_id=s.id)
    u = UnitaImmobiliare(codice="TEST-USO-001", tipo="Magazzino", indirizzo="Via Uso 1", citta="Testville")
    pg_session.add_all([p, u])
    pg_session.flush()
    d = DirittoImmobile(
        unita_immobiliare_id=u.id,
        proprietario_id=p.id,
        tipo_diritto=TipoDiritto.USO,
        quota_percentuale=Decimal("100"),
    )
    pg_session.add(d)
    pg_session.flush()
    pg_session.expire_all()

    reloaded = pg_session.query(DirittoImmobile).filter_by(id=d.id).one()
    assert reloaded.tipo_diritto == TipoDiritto.USO
    # rollback in fixture teardown discards everything


def test_tipo_documento_visura_catastale_seeded(pg_session):
    seed_tipi_documento(pg_session)
    tipo = pg_session.query(TipoDocumento).filter_by(codice="VISURA_CATASTALE").first()
    assert tipo is not None
    assert tipo.richiede_scadenza is False
