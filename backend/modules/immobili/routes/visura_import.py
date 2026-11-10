"""
"Carica da documento" for unità immobiliari: import from a catasto visura.

POST /preview  multipart PDF -> editable proposal + upload_token (nothing written)
POST /apply    token + confirmed proposal -> applied in one transaction

The PDF stays in the tenant's temp_uploads/<token>/ between the two calls
and is re-parsed on apply, so the proposal can't be pointed at another
document. Temp uploads older than 24h are purged on each preview.
"""
import io
import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.file_storage import file_storage

from ..schemas.visura_import import VisuraApplyRequest, VisuraImportResult, VisuraProposta
from ..services.upload_temporanei import purge_old_uploads as _purge_old_uploads
from ..services.upload_temporanei import token_dir as _token_dir
from ..services.visura import VisuraFormatError, parse_visura
from ..services.visura_import_service import (
    VisuraImportError,
    apply_proposal,
    build_proposal,
    merge_client_choices,
)

router = APIRouter(prefix="/unita-immobiliari/import-visura", tags=["Import visura catastale"])
logger = logging.getLogger(__name__)

# Apply creates/updates anagrafiche, unità, diritti and attaches documents.
REQUIRED_PERMISSIONS = ["documenti.write", "soggetto.create", "soggetto.edit"]
TIPI_DOCUMENTO_SUPPORTATI = {"VISURA_CATASTALE"}
MAX_SIZE = 10 * 1024 * 1024
EXPIRED_MSG = "Upload scaduto o non trovato, ricarica la visura"


def _require_tenant(tenant_schema: Optional[str]) -> str:
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant schema mancante")
    return tenant_schema


@router.post("/preview", response_model=VisuraProposta)
def preview_import_visura(
    file: UploadFile = File(...),
    tipo_documento: str = Form("VISURA_CATASTALE"),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission(REQUIRED_PERMISSIONS)),
):
    tenant_schema = _require_tenant(tenant_schema)
    if tipo_documento not in TIPI_DOCUMENTO_SUPPORTATI:
        raise HTTPException(status_code=422, detail="Tipo documento non supportato per l'import")
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Carica un file PDF")
    # Plain `def` route: FastAPI runs it in the threadpool, so the pdftotext
    # subprocess and DB work don't block the event loop.
    content = file.file.read(MAX_SIZE + 1)
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=422, detail="File troppo grande (massimo 10 MB)")

    try:
        visura = parse_visura(content)
    except VisuraFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    proposta = build_proposal(db, visura)

    _purge_old_uploads(tenant_schema)
    token = uuid.uuid4().hex
    file_storage.save_temp_file(io.BytesIO(content), token, "visura.pdf", tenant_schema)
    proposta.upload_token = token
    return proposta


@router.post("/apply", response_model=VisuraImportResult)
def apply_import_visura(
    body: VisuraApplyRequest,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission(REQUIRED_PERMISSIONS)),
):
    tenant_schema = _require_tenant(tenant_schema)
    token_dir = _token_dir(tenant_schema, body.upload_token)
    pdfs = sorted(token_dir.glob("*.pdf")) if token_dir else []
    if not pdfs:
        raise HTTPException(status_code=404, detail=EXPIRED_MSG)
    content = pdfs[0].read_bytes()

    try:
        visura = parse_visura(content)
    except VisuraFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    filename = f"visura_{visura.formato.value.lower()}_{visura.numero.replace('/', '-')}.pdf"
    try:
        # Values always come from the PDF re-parsed server-side; the client
        # only contributes its selections and the editable fields.
        proposta = merge_client_choices(build_proposal(db, visura), body.proposta)
        result = apply_proposal(db, proposta, content, filename, tenant_schema)
    except VisuraImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Dati modificati nel frattempo: ricarica la visura")

    shutil.rmtree(token_dir, ignore_errors=True)
    return VisuraImportResult(**vars(result))
