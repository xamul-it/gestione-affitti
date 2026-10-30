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
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema
from app.core.file_storage import file_storage

from ..schemas.visura_import import VisuraApplyRequest, VisuraImportResult, VisuraProposta
from ..services.visura import VisuraFormatError, parse_visura
from ..services.visura_import_service import VisuraImportError, apply_proposal, build_proposal

router = APIRouter(prefix="/unita-immobiliari/import-visura", tags=["Import visura catastale"])
logger = logging.getLogger(__name__)

TIPI_DOCUMENTO_SUPPORTATI = {"VISURA_CATASTALE"}
MAX_SIZE = 10 * 1024 * 1024
TEMP_TTL_SECONDS = 24 * 3600
_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
EXPIRED_MSG = "Upload scaduto o non trovato, ricarica la visura"


def _temp_root(tenant_schema: str) -> Path:
    return file_storage._get_tenant_path(tenant_schema) / "temp_uploads"


def _purge_old_uploads(tenant_schema: str) -> None:
    root = _temp_root(tenant_schema)
    if not root.exists():
        return
    cutoff = time.time() - TEMP_TTL_SECONDS
    for d in root.iterdir():
        if d.is_dir() and _TOKEN_RE.match(d.name) and d.stat().st_mtime < cutoff:
            shutil.rmtree(d, ignore_errors=True)


def _token_dir(tenant_schema: str, token: str) -> Optional[Path]:
    if not _TOKEN_RE.match(token or ""):
        return None
    d = _temp_root(tenant_schema) / token
    return d if d.is_dir() else None


def _require_tenant(tenant_schema: Optional[str]) -> str:
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant schema mancante")
    return tenant_schema


@router.post("/preview", response_model=VisuraProposta)
async def preview_import_visura(
    file: UploadFile = File(...),
    tipo_documento: str = Form("VISURA_CATASTALE"),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("documenti.write")),
):
    tenant_schema = _require_tenant(tenant_schema)
    if tipo_documento not in TIPI_DOCUMENTO_SUPPORTATI:
        raise HTTPException(status_code=422, detail="Tipo documento non supportato per l'import")
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Carica un file PDF")
    content = await file.read(MAX_SIZE + 1)
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
    current_user: User = Depends(require_permission("documenti.write")),
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
    proposta = body.proposta
    if visura.numero != proposta.numero_visura or visura.formato != proposta.formato:
        raise HTTPException(status_code=422, detail="La proposta non corrisponde alla visura caricata")

    filename = f"visura_{proposta.formato.value.lower()}_{visura.numero.replace('/', '-')}.pdf"
    try:
        result = apply_proposal(db, proposta, content, filename, tenant_schema)
    except VisuraImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    shutil.rmtree(token_dir, ignore_errors=True)
    return VisuraImportResult(**vars(result))
