"""
DocumentoService (app/core/platform_services/documento_service.py): typed
document creation, history rules (CORRENTE/SOSTITUITO) and the linked core
scadenza. Real PostgreSQL, rolled back; files go to a temporary storage.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType, Scadenza
from app.core.platform.models.tipo_documento_override import TipoDocumentoOverride
from app.core.platform_services.document_type_sync import sync_document_types
from app.core.platform_services.documento_service import DocumentoService, FileInput
from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from immobili.__manifest__ import manifest as immobili_manifest

pytestmark = pytest.mark.integration

UNIT = 990001


@pytest.fixture
def service(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    sync_document_types(db_session, {"immobili": immobili_manifest, "anagrafica_italiana": anagrafica_manifest})
    user_id = db_session.execute(text("SELECT min(id) FROM public.core_users")).scalar()
    return DocumentoService(db_session, "tenant_qa_test", user_id)


def _pdf(name="doc.pdf"):
    return [FileInput(content=b"%PDF-1.4 test", filename=name, mime_type="application/pdf")]


def _crea(service, codice, **kw):
    return service.crea(entity_type=EntityType.IMMOBILE, entity_id=kw.pop("entity_id", UNIT),
                        tipo_codice=codice, files=kw.pop("files", _pdf()), **kw)


def test_cumulativo_always_corrente(service):
    a = _crea(service, "TITOLO_EDILIZIO", data_riferimento=date(2020, 1, 1))
    b = _crea(service, "TITOLO_EDILIZIO", data_riferimento=date(2022, 1, 1))
    assert (a.stato, b.stato) == ("CORRENTE", "CORRENTE")
    assert len(b.files) == 1 and b.nome_file == "doc.pdf"


def test_sostitutivo_newer_supersedes(service, db_session):
    old = _crea(service, "APE", data_riferimento=date(2014, 3, 15), dati={"classe": "G"})
    new = _crea(service, "APE", data_riferimento=date(2024, 3, 15), dati={"classe": "C"})
    db_session.refresh(old)
    assert new.stato == "CORRENTE"
    assert old.stato == "SOSTITUITO" and old.sostituito_da_id == new.id
    assert db_session.get(Scadenza, old.scadenza_id).stato.value == "COMPLETATA"
    assert db_session.get(Scadenza, new.scadenza_id).stato.value == "ATTIVA"


def test_sostitutivo_older_goes_to_storico(service, db_session):
    current = _crea(service, "APE", data_riferimento=date(2024, 3, 15))
    older = _crea(service, "APE", data_riferimento=date(2019, 6, 1))
    db_session.refresh(current)
    assert older.stato == "SOSTITUITO" and older.sostituito_da_id == current.id
    assert older.scadenza_id is None
    assert current.stato == "CORRENTE"
    assert db_session.get(Scadenza, current.scadenza_id).stato.value == "ATTIVA"


def test_sottotipo_groups_independently(service):
    el = _crea(service, "CONFORMITA_IMPIANTO", sottotipo="ELETTRICO", data_riferimento=date(2020, 1, 1))
    gas = _crea(service, "CONFORMITA_IMPIANTO", sottotipo="GAS", data_riferimento=date(2021, 1, 1))
    assert (el.stato, gas.stato) == ("CORRENTE", "CORRENTE")


def test_sottotipo_must_be_declared(service):
    with pytest.raises(ValueError, match="Sottotipo"):
        _crea(service, "CONFORMITA_IMPIANTO", sottotipo="FOGNARIO")


def test_ape_scadenza_calcolata(service, db_session):
    ape = _crea(service, "APE", data_riferimento=date(2024, 3, 15))
    assert ape.data_scadenza == date(2034, 3, 15)
    scad = db_session.get(Scadenza, ape.scadenza_id)
    assert scad.data_scadenza == date(2034, 3, 15)
    assert scad.entity_type == "IMMOBILE" and scad.entity_id == UNIT
    assert scad.modulo == "immobili"
    assert scad.titolo == "Attestato di prestazione energetica in scadenza"


def test_ape_decaduto_anticipa_scadenza(service, db_session):
    ape = _crea(service, "APE", data_riferimento=date(2024, 3, 15), dati={"decaduto_il": "2026-12-31"})
    assert service.scadenza_effettiva(ape) == date(2026, 12, 31)
    assert db_session.get(Scadenza, ape.scadenza_id).data_scadenza == date(2026, 12, 31)


def test_manual_scadenza_required(service):
    with pytest.raises(ValueError, match="Scadenza obbligatoria"):
        _crea(service, "POLIZZA_FABBRICATO")
    pol = _crea(service, "POLIZZA_FABBRICATO", data_scadenza=date(2027, 1, 31))
    assert service.scadenza_effettiva(pol) == date(2027, 1, 31)


def test_unknown_or_inactive_type_rejected(service, db_session):
    with pytest.raises(ValueError, match="Tipologia"):
        _crea(service, "NON_ESISTE")
    with pytest.raises(ValueError, match="non si applica"):
        _crea(service, "CARTA_IDENTITA", data_scadenza=date(2030, 1, 1))


def test_default_data_riferimento_today(service):
    doc = _crea(service, "ALTRO_IMMOBILE")
    assert doc.data_riferimento == date.today()


def test_elimina_corrente_ripromuove(service, db_session):
    first = _crea(service, "APE", data_riferimento=date(2010, 1, 1))
    second = _crea(service, "APE", data_riferimento=date(2014, 1, 1))
    third = _crea(service, "APE", data_riferimento=date(2024, 1, 1))
    service.elimina(third.id)
    db_session.refresh(second)
    db_session.refresh(first)
    assert db_session.get(Documento, third.id) is None
    assert second.stato == "CORRENTE" and second.sostituito_da_id is None
    assert first.stato == "SOSTITUITO" and first.sostituito_da_id == second.id
    scad = db_session.get(Scadenza, second.scadenza_id)
    assert scad.stato.value == "ATTIVA" and scad.data_scadenza == date(2024, 1, 1)


def test_elimina_ultimo_chiude_scadenza(service, db_session):
    ape = _crea(service, "APE", data_riferimento=date(2024, 1, 1))
    scadenza_id = ape.scadenza_id
    service.elimina(ape.id)
    assert db_session.get(Scadenza, scadenza_id).stato.value in ("COMPLETATA", "CANCELLATA")


def test_storico_newest_first(service):
    a = _crea(service, "APE", data_riferimento=date(2010, 1, 1))
    b = _crea(service, "APE", data_riferimento=date(2024, 1, 1))
    _crea(service, "APE", data_riferimento=date(2024, 1, 1), entity_id=UNIT + 1)
    assert [d.id for d in service.storico(a.id)] == [b.id, a.id]


def test_tipi_per_entita_filters_and_overrides(service, db_session):
    ape_id = db_session.execute(text("SELECT id FROM public.core_tipi_documento WHERE codice='APE'")).scalar()
    db_session.add(TipoDocumentoOverride(tipo_documento_id=ape_id, nome="APE (mio)"))
    db_session.flush()
    tipi = {t["codice"]: t for t in service.tipi_per_entita(EntityType.IMMOBILE)}
    assert "CARTA_IDENTITA" not in tipi
    assert tipi["APE"]["nome"] == "APE (mio)"
    assert tipi["APE"]["regime"] == "SOSTITUTIVO"


def test_failed_create_removes_saved_files(service, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("db down")
    monkeypatch.setattr(service, "_applica_storico", boom)
    with pytest.raises(RuntimeError):
        _crea(service, "ALTRO_IMMOBILE")
    assert not [p for p in tmp_path.rglob("*") if p.is_file()]


def test_elimina_keeps_files_until_commit(service, tmp_path):
    doc = _crea(service, "ALTRO_IMMOBILE")
    paths = service.elimina(doc.id)
    assert paths and all((tmp_path / p).exists() for p in paths)
    service.elimina_file(paths)
    assert not any((tmp_path / p).exists() for p in paths)


def test_empty_decaduto_is_ignored(service):
    ape = _crea(service, "APE", data_riferimento=date(2024, 3, 15), dati={"decaduto_il": ""})
    assert "decaduto_il" not in ape.dati
    assert service.scadenza_effettiva(ape) == date(2034, 3, 15)
