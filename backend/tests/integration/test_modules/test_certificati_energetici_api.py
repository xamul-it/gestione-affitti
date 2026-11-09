"""
/certificati-energetici endpoints after the move of energy certificates to
core APE documents: reads come from the CORRENTE APE documents, writes are
gone (410) in favour of /documenti.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.core.file_storage import file_storage
from app.core.platform.models import EntityType
from app.core.platform_services.document_type_sync import sync_document_types
from app.core.platform_services.documento_service import DocumentoService, FileInput
from immobili.__manifest__ import manifest as immobili_manifest
from immobili.routes.certificati_energetici import (
    create_certificato,
    get_certificati,
    get_certificati_by_unita_immobiliare,
    get_certificato,
    get_certificato_valido_by_unita_immobiliare,
)

pytestmark = pytest.mark.integration

UNIT = 992001


@pytest.fixture
def service(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    sync_document_types(db_session, {"immobili": immobili_manifest})
    return DocumentoService(db_session, "tenant_qa_test", None)


def _ape(service, emissione, classe="C", unit=UNIT, **dati):
    return service.crea(
        entity_type=EntityType.IMMOBILE, entity_id=unit, tipo_codice="APE",
        files=[FileInput(b"%PDF-1.4", "ape.pdf", "application/pdf")], data_riferimento=emissione,
        dati={"classe": classe, "ep_gl_nren": 88.5, "codice_identificativo": "X-1", "tecnico_id": 3, **dati},
    )


def test_by_unita_returns_current_ape_as_certificate(db_session, service):
    _ape(service, date(2014, 1, 1), "G")
    new = _ape(service, date(2024, 3, 15), "C")
    res = get_certificati_by_unita_immobiliare(UNIT, db=db_session)
    assert len(res) == 1
    c = res[0]
    assert (c.id, c.unita_immobiliare_id, c.classe_energetica) == (new.id, UNIT, "C")
    assert (c.data_emissione, c.data_scadenza) == (date(2024, 3, 15), date(2034, 3, 15))
    assert (c.indice_prestazione_energetica, c.numero_protocollo, c.tecnico_id) == (88.5, "X-1", 3)


def test_get_single_and_list(db_session, service):
    doc = _ape(service, date(2024, 3, 15))
    assert get_certificato(doc.id, db=db_session).classe_energetica == "C"
    assert doc.id in {c.id for c in get_certificati(skip=0, limit=100, validi_solo=False, db=db_session)}
    with pytest.raises(HTTPException) as exc:
        get_certificato(999999999, db=db_session)
    assert exc.value.status_code == 404


def test_valido_uses_effective_scadenza(db_session, service):
    _ape(service, date(2024, 3, 15), decaduto_il="2025-12-31")
    with pytest.raises(HTTPException) as exc:
        get_certificato_valido_by_unita_immobiliare(UNIT, db=db_session)
    assert exc.value.status_code == 404
    ok = _ape(service, date(2024, 3, 15), unit=UNIT + 1)
    assert get_certificato_valido_by_unita_immobiliare(UNIT + 1, db=db_session).id == ok.id


def test_create_is_gone(db_session):
    with pytest.raises(HTTPException) as exc:
        create_certificato()
    assert exc.value.status_code == 410


def test_requires_authentication():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as http:
        assert http.get("/api/v1/certificati-energetici/").status_code in (401, 403)
        assert http.get("/api/v1/certificati-energetici/unita-immobiliare/1").status_code in (401, 403)
