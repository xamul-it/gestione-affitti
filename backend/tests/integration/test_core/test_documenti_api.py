"""
Integration tests for the generic entity-polymorphic document registry
(app/core/routes/documenti.py) — moved here from affitti_lungo in e812186.

Uses real PostgreSQL (pg_session), not the SQLite db_session fixture — see
tests/unit/test_core/test_notifica_model.py for why db_session is broken
for any row-creating test in this repo.

This is the first automated coverage for this endpoint. It exists because
a real, previously-undetected bug was found while wiring immobili's forms
to it: upload_documento() called file_storage.save_file() without the
required tenant_schema argument. save_file()'s TypeError was caught by the
route's own try/except and re-raised as HTTPException(500), so the failure
was an opaque 500 rather than a crash, but every single upload failed.
test_upload_creates_documento_and_saves_file guards against that bug
reappearing.
"""
import io

import pytest
from fastapi import UploadFile
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType
from app.core.routes.documenti import (
    delete_documento,
    download_documento,
    get_documenti,
    upload_documento,
)

pytestmark = pytest.mark.integration

TENANT = "tenant_qa_test"


@pytest.fixture(autouse=True)
def override_get_db():
    """Shadow conftest.py's autouse override_get_db(db_session) for this module only — see test_notifica_model.py for rationale."""
    yield


@pytest.fixture
def pg_session():
    session = SessionLocal()
    try:
        session.execute(text(f"SET search_path TO {TENANT}, public"))
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


def _make_upload_file(filename="test.pdf", content=b"%PDF-1.4 fake content"):
    return UploadFile(file=io.BytesIO(content), filename=filename)


def _cleanup(pg_session, documento_ids):
    ids = [i for i in documento_ids if i]
    if not ids:
        return
    # A prior assertion failure can leave the session's transaction aborted;
    # roll back first so the cleanup query itself doesn't raise and mask it.
    pg_session.rollback()
    documenti = pg_session.query(Documento).filter(Documento.id.in_(ids)).all()
    for d in documenti:
        file_storage.delete_file(d.file_path)
    pg_session.query(Documento).filter(Documento.id.in_(ids)).delete(synchronize_session=False)
    pg_session.commit()


@pytest.mark.asyncio
async def test_upload_creates_documento_and_saves_file(pg_session):
    """Regression test for the TypeError bug: save_file() requires
    tenant_schema, which upload_documento() previously never passed."""
    documento = None
    try:
        documento = await upload_documento(
            file=_make_upload_file(),
            entity_type=EntityType.IMMOBILE,
            entity_id=4242,
            tipo_documento="PLANIMETRIA",
            descrizione="Planimetria unità 4242",
            note=None,
            db=pg_session,
            tenant_schema=TENANT,
        )
        assert documento.id is not None
        assert documento.entity_type == EntityType.IMMOBILE
        assert documento.entity_id == 4242
        assert documento.nome_file == "test.pdf"
        assert documento.file_path.startswith(f"{TENANT}/")

        saved_path = file_storage.get_file_path(documento.file_path)
        assert saved_path.exists()
        assert documento.dimensione == saved_path.stat().st_size
    finally:
        _cleanup(pg_session, [documento.id if documento else None])


@pytest.mark.asyncio
async def test_upload_accepts_condominio_entity_type(pg_session):
    """EntityType.CONDOMINIO was added alongside this move (e812186) for
    building-level documents (regolamento condominiale, verbali assemblea)."""
    documento = None
    try:
        documento = await upload_documento(
            file=_make_upload_file(filename="regolamento.pdf"),
            entity_type=EntityType.CONDOMINIO,
            entity_id=7,
            tipo_documento="ALTRO",
            descrizione=None,
            note=None,
            db=pg_session,
            tenant_schema=TENANT,
        )
        assert documento.entity_type == EntityType.CONDOMINIO
    finally:
        _cleanup(pg_session, [documento.id if documento else None])


@pytest.mark.asyncio
async def test_get_documenti_filters_by_entity(pg_session):
    first = second = None
    try:
        first = await upload_documento(
            file=_make_upload_file(filename="a.pdf"),
            entity_type=EntityType.IMMOBILE,
            entity_id=100,
            tipo_documento="ALTRO",
            descrizione=None,
            note=None,
            db=pg_session,
            tenant_schema=TENANT,
        )
        second = await upload_documento(
            file=_make_upload_file(filename="b.pdf"),
            entity_type=EntityType.PROPRIETARIO,
            entity_id=200,
            tipo_documento="ALTRO",
            descrizione=None,
            note=None,
            db=pg_session,
            tenant_schema=TENANT,
        )

        only_immobile = get_documenti(
            entity_type=EntityType.IMMOBILE, entity_id=100, db=pg_session
        )
        ids = {d.id for d in only_immobile}
        assert first.id in ids
        assert second.id not in ids
    finally:
        _cleanup(pg_session, [first.id if first else None, second.id if second else None])


@pytest.mark.asyncio
async def test_download_documento_returns_existing_file(pg_session):
    documento = None
    try:
        documento = await upload_documento(
            file=_make_upload_file(),
            entity_type=EntityType.IMMOBILE,
            entity_id=555,
            tipo_documento="ALTRO",
            descrizione=None,
            note=None,
            db=pg_session,
            tenant_schema=TENANT,
        )

        response = await download_documento(documento.id, db=pg_session)
        assert response.path.exists()
        assert response.filename == "test.pdf"
    finally:
        _cleanup(pg_session, [documento.id if documento else None])


@pytest.mark.asyncio
async def test_delete_documento_removes_file_and_record(pg_session):
    documento = await upload_documento(
        file=_make_upload_file(),
        entity_type=EntityType.IMMOBILE,
        entity_id=999,
        tipo_documento="ALTRO",
        descrizione=None,
        note=None,
        db=pg_session,
        tenant_schema=TENANT,
    )
    try:
        saved_path = file_storage.get_file_path(documento.file_path)
        assert saved_path.exists()

        delete_documento(documento.id, db=pg_session)

        assert not saved_path.exists()
        assert pg_session.query(Documento).filter(Documento.id == documento.id).first() is None
    finally:
        _cleanup(pg_session, [documento.id])
