"""
Integration tests for the "import unità immobiliari da visura catastale" flow.

Calls services/route functions directly (db=pg_session) rather than through
TestClient/HTTP/JWT — same established pattern as test_proprietari.py.
Real PostgreSQL (pg_session), not the SQLite db_session fixture.
"""
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto, TipoDocumento
from anagrafica_italiana.seeds.seed_tipi_documento import seed_tipi_documento

from immobili.models import DirittoImmobile, Proprietario, UnitaImmobiliare
from immobili.models.diritti_immobile import TipoDiritto
from immobili.services.visura import parse_visura
from immobili.services.visura_import_service import build_proposal

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    """Real PostgreSQL session wrapped in an outer transaction: service-level
    commit() only releases a SAVEPOINT, and everything is rolled back at the
    end, so tests never leave rows behind in tenant_qa_test."""
    from app.core.database import engine
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        session.execute(text(f"SET LOCAL search_path TO {TENANT}, public"))
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "visure"


@pytest.fixture(scope="module")
def sintetica():
    return parse_visura((FIXTURES / "sintetica.pdf").read_bytes())


@pytest.fixture(scope="module")
def analitica():
    return parse_visura((FIXTURES / "analitica.pdf").read_bytes())


def _unita(proposta, foglio, particella, sub):
    return next(
        u for u in proposta.unita
        if (u.foglio, u.particella, u.subalterno) == (foglio, particella, sub)
    )


def _soggetto(pg_session, **kwargs):
    s = SoggettoAnagrafico(**kwargs)
    pg_session.add(s)
    pg_session.flush()
    return s


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


# --- Task 4: build_proposal -------------------------------------------------

def test_proposal_empty_db_creates_all(pg_session, sintetica):
    proposta = build_proposal(pg_session, sintetica)
    assert len(proposta.unita) == 9
    assert all(u.azione == "crea" for u in proposta.unita)
    assert len(proposta.soggetti) == 3
    assert all(s.azione == "crea" for s in proposta.soggetti)
    cfs = {s.codice_fiscale for s in proposta.soggetti}
    assert cfs == {"ZNDLMT73E17F205F", "ZNDLCN38R19F205K", None}
    demanio = next(s for s in proposta.soggetti if s.codice_fiscale is None)
    assert demanio.persona_giuridica is True

    u = _unita(proposta, "99", "592", "2")
    assert u.tipo == "Magazzino"
    assert u.citta.upper() == "BOLOGNA"
    assert u.provincia == "BO"
    assert [d.tipo_diritto for d in u.diritti] == [TipoDiritto.PROPRIETARIO, TipoDiritto.USO]
    assert all(d.azione == "crea" for d in u.diritti)
    assert "--- Dati catastali (da visura T234664/2025 del 16/12/2025) ---" in u.note_catastali
    assert "Categoria C/2, Classe 2, Consistenza 113 m2" in u.note_catastali


def test_soggetto_matched_by_cf(pg_session, sintetica):
    existing = _soggetto(
        pg_session, tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome="Luciano", cognome="Zanderighi", codice_fiscale="ZNDLCN38R19F205K",
    )
    proposta = build_proposal(pg_session, sintetica)
    p = next(s for s in proposta.soggetti if s.codice_fiscale == "ZNDLCN38R19F205K")
    assert p.azione == "aggiorna"
    assert p.soggetto_id == existing.id
    assert "data_nascita" in p.campi_da_completare
    assert "nome" not in p.campi_da_completare


def test_ente_senza_cf_matched_by_ragione_sociale(pg_session, sintetica):
    existing = _soggetto(
        pg_session, tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA,
        ragione_sociale="Demanio dello Stato - Ramo Ferrovia",
    )
    proposta = build_proposal(pg_session, sintetica)
    p = next(s for s in proposta.soggetti if s.codice_fiscale is None)
    assert p.soggetto_id == existing.id
    assert p.azione == "invariato"


def test_unit_matched_shows_diff(pg_session, sintetica):
    unit = UnitaImmobiliare(
        codice="TEST-VIS-019", tipo="Villa", indirizzo="VIA EMILIA PONENTE n. 354", piano="S1-T - 1",
        citta="Bologna", foglio="99", particella="666", subalterno="19",
        rendita_catastale=1000.0, superficie_mq=294, classe_energetica="B",
    )
    pg_session.add(unit)
    pg_session.flush()
    proposta = build_proposal(pg_session, sintetica)
    u = _unita(proposta, "99", "666", "19")
    assert u.azione == "aggiorna"
    assert u.unita_id == unit.id
    rendita = next(m for m in u.modifiche if m.campo == "rendita_catastale")
    assert (rendita.attuale, rendita.nuovo) == (1000.0, 1316.97)
    assert not any(m.campo in ("tipo", "classe_energetica", "superficie_mq", "indirizzo") for m in u.modifiche)


def test_quota_mismatch_warning(pg_session, sintetica):
    s = _soggetto(
        pg_session, tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA,
        ragione_sociale="DEMANIO DELLO STATO - RAMO FERROVIA",
    )
    p = Proprietario(soggetto_id=s.id)
    unit = UnitaImmobiliare(
        codice="TEST-VIS-592", tipo="Magazzino", indirizzo="VIA EMILIA PONENTE n. 2",
        citta="Bologna", foglio="99", particella="592", subalterno="2",
    )
    pg_session.add_all([p, unit])
    pg_session.flush()
    pg_session.add(DirittoImmobile(
        unita_immobiliare_id=unit.id, proprietario_id=p.id,
        tipo_diritto=TipoDiritto.PROPRIETARIO, quota_percentuale=Decimal("50"),
    ))
    pg_session.flush()
    proposta = build_proposal(pg_session, sintetica)
    u = _unita(proposta, "99", "592", "2")
    assert any("Quota diversa" in a for a in u.avvisi)
    demanio_diritto = next(d for d in u.diritti if d.tipo_diritto == TipoDiritto.PROPRIETARIO)
    assert demanio_diritto.azione == "invariato"
