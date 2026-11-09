"""
Core documents API on top of DocumentoService: types per entity, typed
multi-file upload, history listing, preview. Route functions are called
directly inside the rolled-back integration db_session.
"""
import io
import json
from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, UploadFile

from app.core.file_storage import file_storage
from app.core.platform.models import EntityType
from app.core.platform_services.document_type_sync import sync_document_types
from app.core.routes.documenti import (
    get_documenti,
    get_storico,
    get_tipi,
    upload_documento,
    view_file,
)
from anagrafica_italiana.__manifest__ import manifest as anagrafica_manifest
from immobili.__manifest__ import manifest as immobili_manifest

pytestmark = pytest.mark.integration

TENANT = "tenant_qa_test"
UNIT = 991001


@pytest.fixture(autouse=True)
def setup(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(file_storage, "base_path", tmp_path)
    sync_document_types(db_session, {"immobili": immobili_manifest, "anagrafica_italiana": anagrafica_manifest})


def _file(name="a.pdf"):
    return UploadFile(file=io.BytesIO(b"%PDF-1.4 x"), filename=name, headers={"content-type": "application/pdf"})


async def _upload(db, **kw):
    params = dict(
        files=[_file()], file=None, entity_type=EntityType.IMMOBILE, entity_id=UNIT,
        tipo_codice=None, tipo_documento=None, data_riferimento=None, sottotipo=None,
        data_scadenza=None, dati=None, descrizione=None, note=None,
        db=db, tenant_schema=TENANT, current_user=None,
    )
    params.update(kw)
    return await upload_documento(**params)


@pytest.mark.asyncio
async def test_upload_ape_defaults_today_and_computes_scadenza(db_session):
    out = await _upload(db_session, tipo_codice="APE", dati=json.dumps({"classe": "B"}))
    assert out.tipo_codice == "APE"
    assert out.data_riferimento == date.today()
    assert out.data_scadenza_effettiva == date.today() + relativedelta(years=10)
    assert out.dati == {"classe": "B"}
    assert out.stato == "CORRENTE"
    assert len(out.files) == 1


@pytest.mark.asyncio
async def test_upload_multiple_files(db_session):
    out = await _upload(db_session, tipo_codice="TITOLO_EDILIZIO", files=[_file("p1.pdf"), _file("p2.pdf")])
    assert [f.nome_file for f in out.files] == ["p1.pdf", "p2.pdf"]


@pytest.mark.asyncio
async def test_legacy_single_file_upload(db_session):
    out = await _upload(db_session, files=None, file=_file("plan.pdf"), tipo_documento="PLANIMETRIA")
    assert out.tipo_codice == "PLANIMETRIA_CATASTALE"
    legacy = await _upload(db_session, files=None, file=_file("x.pdf"), tipo_documento="FOTO",
                           entity_type=EntityType.CONDOMINIO, entity_id=7)
    assert legacy.tipo_codice == "DOCUMENTO_GENERICO"


@pytest.mark.asyncio
async def test_invalid_dati_json_is_422(db_session):
    with pytest.raises(HTTPException) as exc:
        await _upload(db_session, tipo_codice="APE", dati="{not json")
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_service_error_is_422(db_session):
    with pytest.raises(HTTPException) as exc:
        await _upload(db_session, tipo_codice="POLIZZA_FABBRICATO")
    assert exc.value.status_code == 422
    assert "Scadenza obbligatoria" in exc.value.detail


@pytest.mark.asyncio
async def test_list_hides_superseded_by_default(db_session):
    old = await _upload(db_session, tipo_codice="APE", data_riferimento=date(2014, 1, 1))
    new = await _upload(db_session, tipo_codice="APE", data_riferimento=date(2024, 1, 1))
    common = dict(entity_type=EntityType.IMMOBILE, entity_id=UNIT, tipo_codice=None, modulo=None,
                  scadenza_entro_giorni=None, skip=0, limit=100, db=db_session)
    ids = {d.id for d in get_documenti(includi_sostituiti=False, **common)}
    assert new.id in ids and old.id not in ids
    all_ids = {d.id for d in get_documenti(includi_sostituiti=True, **common)}
    assert {old.id, new.id} <= all_ids
    assert [d.id for d in get_storico(old.id, db=db_session)] == [new.id, old.id]


@pytest.mark.asyncio
async def test_list_filters_modulo_and_scadenza(db_session):
    ape = await _upload(db_session, tipo_codice="APE", data_riferimento=date(2016, 6, 1))
    await _upload(db_session, tipo_codice="TITOLO_EDILIZIO")
    res = get_documenti(entity_type=EntityType.IMMOBILE, entity_id=None, tipo_codice=None, modulo="immobili",
                        includi_sostituiti=False, scadenza_entro_giorni=365 * 3, skip=0, limit=500, db=db_session)
    ids = {d.id for d in res}
    assert ape.id in ids
    assert all(d.data_scadenza_effettiva is not None for d in res)


def test_tipi_for_immobile(db_session):
    codes = {t.codice for t in get_tipi(entity_type=EntityType.IMMOBILE, db=db_session, tenant_schema=TENANT)}
    assert "APE" in codes and "CARTA_IDENTITA" not in codes and "DOCUMENTO_GENERICO" in codes


@pytest.mark.asyncio
async def test_view_file_inline(db_session):
    out = await _upload(db_session, tipo_codice="ALTRO_IMMOBILE")
    response = view_file(out.files[0].id, db=db_session, tenant_schema=TENANT)
    assert response.headers["content-disposition"].startswith("inline")


@pytest.mark.asyncio
async def test_view_unsafe_type_is_attachment(db_session):
    html = UploadFile(file=io.BytesIO(b"<script>alert(1)</script>"), filename="x.html",
                      headers={"content-type": "text/html"})
    out = await _upload(db_session, tipo_codice="ALTRO_IMMOBILE", files=[html])
    response = view_file(out.files[0].id, db=db_session, tenant_schema=TENANT)
    assert response.headers["content-disposition"].startswith("attachment")
    assert response.media_type == "application/octet-stream"
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_view_pdf_inline_is_sandboxed(db_session):
    out = await _upload(db_session, tipo_codice="ALTRO_IMMOBILE")
    response = view_file(out.files[0].id, db=db_session, tenant_schema=TENANT)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in response.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_list_limit_is_capped(db_session, monkeypatch):
    import app.core.routes.documenti as routes
    monkeypatch.setattr(routes, "MAX_LIMIT", 1)
    await _upload(db_session, tipo_codice="TITOLO_EDILIZIO")
    await _upload(db_session, tipo_codice="TITOLO_EDILIZIO")
    res = get_documenti(entity_type=EntityType.IMMOBILE, entity_id=UNIT, tipo_codice=None, modulo=None,
                        includi_sostituiti=False, scadenza_entro_giorni=None, skip=0, limit=100, db=db_session)
    assert len(res) == 1


@pytest.mark.asyncio
async def test_view_rejects_other_tenant_file(db_session, tmp_path):
    from app.core.platform.models import DocumentoFile
    out = await _upload(db_session, tipo_codice="ALTRO_IMMOBILE")
    (tmp_path / "tenant_principale").mkdir(exist_ok=True)
    (tmp_path / "tenant_principale" / "s.pdf").write_bytes(b"%PDF-1.4 secret")
    f = db_session.get(DocumentoFile, out.files[0].id)
    f.file_path = "tenant_principale/s.pdf"
    db_session.flush()
    with pytest.raises(HTTPException) as exc:
        view_file(f.id, db=db_session, tenant_schema=TENANT)
    assert exc.value.status_code == 404
