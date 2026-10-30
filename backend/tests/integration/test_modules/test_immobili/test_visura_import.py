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
from immobili.services.visura_import_service import (
    VisuraImportError,
    apply_proposal,
    build_proposal,
)
from app.core.platform.models import Documento, EntityType, TipoDocumentoEnum

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


# --- Task 5: apply_proposal -------------------------------------------------

@pytest.fixture
def storage(tmp_path, monkeypatch):
    from app.core.file_storage import file_storage
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    return file_storage


@pytest.fixture
def pdf_sintetica():
    return (FIXTURES / "sintetica.pdf").read_bytes()


@pytest.fixture
def pdf_analitica():
    return (FIXTURES / "analitica.pdf").read_bytes()


def _apply(pg_session, proposta, pdf):
    seed_tipi_documento(pg_session)
    return apply_proposal(pg_session, proposta, pdf, "visura.pdf", TENANT)


def _find_unit(pg_session, particella, sub):
    return pg_session.query(UnitaImmobiliare).filter_by(
        foglio="99", particella=particella, subalterno=sub
    ).one_or_none()


def test_apply_creates_everything(pg_session, storage, sintetica, pdf_sintetica):
    result = _apply(pg_session, build_proposal(pg_session, sintetica), pdf_sintetica)
    assert len(result.unita_create) == 9
    assert result.soggetti_creati == 3
    assert result.diritti_creati == 18
    assert result.documenti_allegati == 9

    u = _find_unit(pg_session, "666", "19")
    assert u.rendita_catastale == 1316.97
    assert u.superficie_mq == 294
    assert u.codice
    assert "--- Dati catastali (da visura T234664/2025 del 16/12/2025) ---" in u.note
    docs = pg_session.query(Documento).filter_by(entity_type=EntityType.IMMOBILE, entity_id=u.id).all()
    assert len(docs) == 1
    assert docs[0].tipo_documento == TipoDocumentoEnum.VISURA_CATASTALE
    assert docs[0].metadata_parsato["numero_visura"] == "T234664/2025"
    assert (storage.base_path / docs[0].file_path).exists()

    luigi = pg_session.query(SoggettoAnagrafico).filter_by(codice_fiscale="ZNDLMT73E17F205F").one()
    assert (luigi.cognome, luigi.nome) == ("ZANDERIGHI", "Luigi Matteo Massimiliano")
    u592 = _find_unit(pg_session, "592", "2")
    tipi = sorted(d.tipo_diritto.value for d in u592.diritti)
    assert tipi == ["PROPRIETARIO", "USO"]


def test_reimport_is_noop(pg_session, storage, sintetica, pdf_sintetica):
    _apply(pg_session, build_proposal(pg_session, sintetica), pdf_sintetica)
    proposta = build_proposal(pg_session, sintetica)
    assert all(u.azione == "invariato" for u in proposta.unita)
    assert all(s.azione == "invariato" for s in proposta.soggetti)
    assert all(d.azione == "invariato" for u in proposta.unita for d in u.diritti)
    result = _apply(pg_session, proposta, pdf_sintetica)
    assert result.diritti_creati == 0
    assert result.documenti_allegati == 0
    assert result.unita_create == []


def test_analitica_after_sintetica_attaches_new_document_only(
    pg_session, storage, sintetica, analitica, pdf_sintetica, pdf_analitica
):
    _apply(pg_session, build_proposal(pg_session, sintetica), pdf_sintetica)
    proposta = build_proposal(pg_session, analitica)
    assert not any(u.azione == "crea" for u in proposta.unita)
    result = _apply(pg_session, proposta, pdf_analitica)
    assert result.unita_create == []
    assert result.documenti_allegati == 9


def test_apply_rejects_missing_tipo(pg_session, storage, sintetica, pdf_sintetica):
    proposta = build_proposal(pg_session, sintetica)
    proposta.unita[0].tipo = None
    with pytest.raises(VisuraImportError):
        _apply(pg_session, proposta, pdf_sintetica)
    assert _find_unit(pg_session, "666", "19") is None


def test_apply_respects_deselection(pg_session, storage, sintetica, pdf_sintetica):
    unit = UnitaImmobiliare(
        codice="TEST-VIS-020", tipo="Appartamento", indirizzo="x", citta="Bologna",
        foglio="99", particella="666", subalterno="20", rendita_catastale=1.0,
    )
    pg_session.add(unit)
    pg_session.flush()
    proposta = build_proposal(pg_session, sintetica)
    skip = next(u for u in proposta.unita if u.subalterno == "21")
    skip.selezionato = False
    upd = next(u for u in proposta.unita if u.subalterno == "20")
    for m in upd.modifiche:
        if m.campo == "rendita_catastale":
            m.selezionato = False
    _apply(pg_session, proposta, pdf_sintetica)
    assert _find_unit(pg_session, "666", "21") is None
    pg_session.refresh(unit)
    assert unit.rendita_catastale == 1.0
    assert unit.indirizzo == "VIA EMILIA PONENTE n. 356"


def test_apply_rolls_back_on_error(pg_session, storage, sintetica, pdf_sintetica, monkeypatch):
    saved, deleted = [], []
    real_save = storage.save_file

    def flaky_save(*args, **kwargs):
        if len(saved) == 2:
            raise OSError("disk full")
        path = real_save(*args, **kwargs)
        saved.append(path)
        return path

    monkeypatch.setattr(storage, "save_file", flaky_save)
    monkeypatch.setattr(storage, "delete_file", lambda path, *a, **k: deleted.append(path) or True)
    proposta = build_proposal(pg_session, sintetica)
    with pytest.raises(OSError):
        _apply(pg_session, proposta, pdf_sintetica)
    assert _find_unit(pg_session, "666", "19") is None
    assert pg_session.query(SoggettoAnagrafico).filter_by(codice_fiscale="ZNDLMT73E17F205F").first() is None
    assert sorted(deleted) == sorted(saved)


def test_existing_user_fields_untouched(pg_session, storage, sintetica, pdf_sintetica):
    unit = UnitaImmobiliare(
        codice="TEST-VIS-018", tipo="Villa", indirizzo="vecchio", citta="Bologna",
        foglio="99", particella="666", subalterno="18",
        classe_energetica="B", descrizione="mia", note="nota utente",
    )
    pg_session.add(unit)
    pg_session.flush()
    _apply(pg_session, build_proposal(pg_session, sintetica), pdf_sintetica)
    pg_session.refresh(unit)
    assert (unit.tipo, unit.classe_energetica, unit.descrizione, unit.codice) == ("Villa", "B", "mia", "TEST-VIS-018")
    assert unit.note.startswith("nota utente")
    assert "--- Dati catastali" in unit.note


# --- Task 6: routes -------------------------------------------------------------

import asyncio
import inspect
import io

from fastapi import HTTPException, UploadFile

from immobili.routes.visura_import import apply_import_visura, preview_import_visura
from immobili.schemas.visura_import import VisuraApplyRequest


def _upload(name: str) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO((FIXTURES / name).read_bytes()))


def _call(fn, **kwargs):
    result = fn(**kwargs)
    return asyncio.run(result) if inspect.isawaitable(result) else result


def _preview(pg_session, name):
    return _call(
        preview_import_visura, file=_upload(name), tipo_documento="VISURA_CATASTALE",
        db=pg_session, tenant_schema=TENANT, current_user=None,
    )


def test_preview_returns_token_and_proposal(pg_session, storage):
    proposta = _preview(pg_session, "sintetica.pdf")
    assert len(proposta.unita) == 9
    assert len(proposta.upload_token) == 32
    assert all(c in "0123456789abcdef" for c in proposta.upload_token)


def test_preview_rejects_riepilogo_imu(pg_session, storage):
    with pytest.raises(HTTPException) as exc:
        _preview(pg_session, "riepilogo_imu.pdf")
    assert exc.value.status_code == 422
    assert "Formato non supportato" in exc.value.detail


def test_preview_rejects_other_tipo_documento(pg_session, storage):
    with pytest.raises(HTTPException) as exc:
        _call(
            preview_import_visura, file=_upload("sintetica.pdf"), tipo_documento="CARTA_IDENTITA",
            db=pg_session, tenant_schema=TENANT, current_user=None,
        )
    assert exc.value.status_code == 422


def test_apply_unknown_token_404(pg_session, storage):
    proposta = _preview(pg_session, "sintetica.pdf")
    with pytest.raises(HTTPException) as exc:
        apply_import_visura(
            body=VisuraApplyRequest(upload_token="0" * 32, proposta=proposta),
            db=pg_session, tenant_schema=TENANT, current_user=None,
        )
    assert exc.value.status_code == 404


def test_apply_token_must_be_hex(pg_session, storage):
    proposta = _preview(pg_session, "sintetica.pdf")
    with pytest.raises(HTTPException) as exc:
        apply_import_visura(
            body=VisuraApplyRequest(upload_token="../../etc", proposta=proposta),
            db=pg_session, tenant_schema=TENANT, current_user=None,
        )
    assert exc.value.status_code == 404


def test_apply_end_to_end(pg_session, storage):
    seed_tipi_documento(pg_session)
    proposta = _preview(pg_session, "sintetica.pdf")
    result = apply_import_visura(
        body=VisuraApplyRequest(upload_token=proposta.upload_token, proposta=proposta),
        db=pg_session, tenant_schema=TENANT, current_user=None,
    )
    assert len(result.unita_create) == 9
    assert not (storage.base_path / TENANT / "temp_uploads" / proposta.upload_token).exists()


# --- Final review fixes ---------------------------------------------------------

import copy
import inspect
from datetime import date as _date

from immobili.routes import visura_import as visura_import_routes
from immobili.services.visura.models import FabbricatoParsed, FormatoVisura, VisuraParsed
from immobili.services.visura.text import build_intestato
from immobili.services.visura_import_service import merge_client_choices


def test_apply_ignores_tampered_values(pg_session, storage, sintetica, pdf_sintetica):
    server = build_proposal(pg_session, sintetica)
    client = copy.deepcopy(server)
    u = next(x for x in client.unita if x.subalterno == "19")
    u.rendita_catastale = 1.0
    u.foglio = "1"
    u.note_catastali = "hacked"
    u.tipo = "Villa"
    client.soggetti[0].codice_fiscale = "XXXXXX00X00X000X"
    merged = merge_client_choices(build_proposal(pg_session, sintetica), client)
    _apply(pg_session, merged, pdf_sintetica)
    unit = _find_unit(pg_session, "666", "19")
    assert unit.rendita_catastale == 1316.97
    assert unit.tipo == "Villa"
    assert "hacked" not in unit.note
    assert pg_session.query(SoggettoAnagrafico).filter_by(codice_fiscale="XXXXXX00X00X000X").first() is None


def test_apply_ignores_tampered_modifica(pg_session, storage, sintetica, pdf_sintetica):
    unit = UnitaImmobiliare(
        codice="TEST-VIS-T20", tipo="Appartamento", indirizzo="x", citta="Bologna",
        foglio="99", particella="666", subalterno="20", rendita_catastale=1.0,
    )
    pg_session.add(unit)
    pg_session.flush()
    client = build_proposal(pg_session, sintetica)
    upd = next(x for x in client.unita if x.subalterno == "20")
    next(m for m in upd.modifiche if m.campo == "rendita_catastale").nuovo = "not a number"
    merged = merge_client_choices(build_proposal(pg_session, sintetica), client)
    _apply(pg_session, merged, pdf_sintetica)
    pg_session.refresh(unit)
    assert unit.rendita_catastale == 499.67


def test_stale_proposal_rejected(pg_session, storage, sintetica, pdf_sintetica):
    stale = build_proposal(pg_session, sintetica)
    _apply(pg_session, merge_client_choices(build_proposal(pg_session, sintetica), stale), pdf_sintetica)
    with pytest.raises(VisuraImportError, match="ricarica la visura"):
        merge_client_choices(build_proposal(pg_session, sintetica), stale)


def test_company_matched_by_partita_iva(pg_session):
    existing = _soggetto(
        pg_session, tipo_soggetto=TipoSoggetto.PERSONA_GIURIDICA,
        ragione_sociale="Immobiliare Test Srl", partita_iva="01234567890",
    )
    intestato = build_intestato("IMMOBILIARE TEST SRL", "01234567890", None, None, "Proprieta' 1/1")
    visura = VisuraParsed(
        formato=FormatoVisura.SINTETICA, numero="T1/2025", data=_date(2025, 1, 1), soggetto_cf=None,
        fabbricati=[FabbricatoParsed(
            comune="BOLOGNA", codice_catastale_comune="A944", provincia=None, sezione_urbana=None,
            foglio="1", particella="2", subalterno="3", zona_censuaria=None, micro_zona=None,
            categoria="A/3", classe=None, consistenza=None, vani=None, superficie_totale=None,
            superficie_escluse_aree=None, rendita=None, indirizzo="VIA X n. 1", piano=None,
            intestati=[intestato],
        )],
        terreni_count=0,
    )
    proposta = build_proposal(pg_session, visura)
    assert proposta.soggetti[0].soggetto_id == existing.id


def test_routes_require_anagrafica_permissions():
    assert {"documenti.write", "soggetto.create", "soggetto.edit"} <= set(visura_import_routes.REQUIRED_PERMISSIONS)


def test_preview_does_not_block_event_loop():
    assert not inspect.iscoroutinefunction(visura_import_routes.preview_import_visura)
