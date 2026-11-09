from datetime import date, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.file_storage import file_storage
from app.core.platform.models import Documento, DocumentoFile, EntityType, TipoDocumento as TipoDocumentoModel
from app.core.platform_services.documento_service import DocumentoService, FileInput
from app.core.schemas.documenti import DocumentoOut, DocumentoResponse, DocumentoUpdate, TipoDocumentoOut
import logging
import mimetypes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documenti", tags=["Documenti"])

MAX_LIMIT = 500

# Legacy TipoDocumentoEnum values that have a typed equivalent.
_LEGACY_ALIASES = {"PLANIMETRIA": "PLANIMETRIA_CATASTALE", "CERTIFICATO_ENERGETICO": "APE"}


def _user_id(current_user) -> Optional[int]:
    return getattr(current_user, "id", None) if isinstance(current_user, User) else None


def _tenant(tenant_schema) -> Optional[str]:
    return tenant_schema if isinstance(tenant_schema, str) else None


def to_out(documento: Documento, service: Optional[DocumentoService] = None) -> DocumentoOut:
    tipo = documento.tipo
    service = service or DocumentoService(None, None, None)
    files = [
        {"id": f.id, "nome_file": f.nome_file, "mime_type": f.mime_type} for f in documento.files
    ] or ([{"id": None, "nome_file": documento.nome_file, "mime_type": documento.mime_type}]
          if documento.file_path else [])
    return DocumentoOut(
        id=documento.id,
        entity_type=documento.entity_type,
        entity_id=documento.entity_id,
        tipo_documento=documento.tipo_documento.value if documento.tipo_documento is not None else None,
        tipo_documento_id=documento.tipo_documento_id,
        tipo_codice=tipo.codice if tipo else None,
        tipo_nome=tipo.nome if tipo else None,
        regime=tipo.regime if tipo else None,
        descrizione=documento.descrizione,
        note=documento.note,
        nome_file=documento.nome_file,
        file_path=documento.file_path,
        mime_type=documento.mime_type,
        dimensione=documento.dimensione,
        data_riferimento=documento.data_riferimento,
        stato=documento.stato or "CORRENTE",
        sostituito_da_id=documento.sostituito_da_id,
        sottotipo=documento.sottotipo,
        dati=documento.dati,
        data_scadenza=documento.data_scadenza,
        data_scadenza_effettiva=service.scadenza_effettiva(documento),
        files=files,
        created_at=documento.created_at,
        updated_at=documento.updated_at,
    )


@router.get("/tipi", response_model=List[TipoDocumentoOut])
def get_tipi(
    entity_type: EntityType,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Tipologie applicabili a un tipo di entità (con le personalizzazioni del tenant)."""
    service = DocumentoService(db, _tenant(tenant_schema), None)
    return [TipoDocumentoOut(**t) for t in service.tipi_per_entita(entity_type)]


@router.get("/", response_model=List[DocumentoOut])
def get_documenti(
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[int] = None,
    tipo_codice: Optional[str] = None,
    modulo: Optional[str] = None,
    includi_sostituiti: bool = False,
    scadenza_entro_giorni: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Documenti con filtri; di default solo quelli in vigore."""
    query = db.query(Documento)
    if entity_type:
        query = query.filter(Documento.entity_type == entity_type)
    if entity_id:
        query = query.filter(Documento.entity_id == entity_id)
    if tipo_codice or modulo:
        query = query.join(TipoDocumentoModel, TipoDocumentoModel.id == Documento.tipo_documento_id)
        if tipo_codice:
            query = query.filter(TipoDocumentoModel.codice == tipo_codice)
        if modulo:
            query = query.filter(TipoDocumentoModel.modulo == modulo)
    if not includi_sostituiti:
        query = query.filter(Documento.stato == "CORRENTE")
    if scadenza_entro_giorni is not None:
        soglia = date.today() + timedelta(days=scadenza_entro_giorni)
        # Effective scadenza = min(data_scadenza, dati.decaduto_il): <= soglia iff either is.
        query = query.filter(or_(
            Documento.data_scadenza <= soglia,
            Documento.dati.op("->>")("decaduto_il") <= soglia.isoformat(),
        ))
    documenti = (
        query.options(selectinload(Documento.files), joinedload(Documento.tipo))
        .order_by(Documento.data_riferimento.desc().nullslast(), Documento.created_at.desc(), Documento.id.desc())
        .offset(max(skip, 0))
        .limit(max(1, min(limit, MAX_LIMIT)))
        .all()
    )
    service = DocumentoService(db, None, None)
    return [to_out(d, service) for d in documenti]


@router.get("/files/{file_id}/view")
def view_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Un file del documento, da mostrare in anteprima (inline)."""
    f = db.get(DocumentoFile, file_id)
    if f is None:
        raise HTTPException(status_code=404, detail="File non trovato")
    return _inline(f.file_path, f.nome_file, f.mime_type)


# Types shown inline in the preview, detected from the file's first bytes
# (the stored/uploaded content type is client-controlled). Anything else is
# served as an attachment.
_PREVIEW_SIGNATURES = (
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)
_SAFE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "sandbox; default-src 'none'; img-src 'self'; object-src 'self'",
}


def _preview_type(path) -> Optional[str]:
    with open(path, "rb") as fh:
        head = fh.read(16)
    for signature, mime in _PREVIEW_SIGNATURES:
        if head.startswith(signature):
            return mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def _inline(relative_path: str, nome_file: Optional[str], mime_type: Optional[str]) -> FileResponse:
    path = file_storage.get_file_path(relative_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File non trovato sul filesystem")
    preview = _preview_type(path)
    return FileResponse(
        path=path,
        filename=nome_file,
        media_type=preview or "application/octet-stream",
        content_disposition_type="inline" if preview else "attachment",
        headers=_SAFE_HEADERS,
    )


@router.get("/{documento_id}/view")
def view_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Primo file del documento in anteprima (anche per i documenti a file singolo storici)."""
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    if documento.files:
        f = documento.files[0]
        return _inline(f.file_path, f.nome_file, f.mime_type)
    if not documento.file_path:
        raise HTTPException(status_code=404, detail="Il documento non ha file")
    return _inline(documento.file_path, documento.nome_file, documento.mime_type)


@router.get("/{documento_id}/storico", response_model=List[DocumentoOut])
def get_storico(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Tutte le versioni dello stesso documento (stessa entità, tipologia e sottotipo), dalla più recente."""
    service = DocumentoService(db, None, None)
    return [to_out(d, service) for d in service.storico(documento_id)]


@router.get("/{documento_id}", response_model=DocumentoOut)
def get_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Ottieni dettagli di un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {documento_id} non trovato"
        )
    return to_out(documento)


def _legacy_tipo_codice(db: Session, tipo_documento: str, entity_type: EntityType) -> str:
    service = DocumentoService(db, None, None)
    applicabili = {t["codice"] for t in service.tipi_per_entita(entity_type)}
    for candidate in (_LEGACY_ALIASES.get(tipo_documento), tipo_documento):
        if candidate and candidate in applicabili:
            return candidate
    if entity_type == EntityType.IMMOBILE and "ALTRO_IMMOBILE" in applicabili:
        return "ALTRO_IMMOBILE"
    return "DOCUMENTO_GENERICO"


@router.post("/upload", response_model=DocumentoOut, status_code=status.HTTP_201_CREATED)
async def upload_documento(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    entity_type: EntityType = Form(...),
    entity_id: int = Form(...),
    tipo_codice: Optional[str] = Form(None),
    tipo_documento: Optional[str] = Form(None),
    data_riferimento: Optional[date] = Form(None),
    sottotipo: Optional[str] = Form(None),
    data_scadenza: Optional[date] = Form(None),
    dati: Optional[str] = Form(None),
    descrizione: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("documenti.write")),
):
    """
    Carica un documento tipizzato (uno o più file).

    - **files**: i file del documento (es. fronte/retro, pagine)
    - **tipo_codice**: codice della tipologia (vedi GET /documenti/tipi)
    - **data_riferimento**: data del documento (default oggi)
    - **data_scadenza**: obbligatoria per le tipologie a scadenza manuale
    - **dati**: JSON con i dati del form della tipologia
    - **file** / **tipo_documento**: forma precedente a file singolo, ancora accettata
    """
    tenant = _tenant(tenant_schema)
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")
    uploads = [f for f in (files or []) if f is not None] or ([file] if file is not None else [])
    if not uploads:
        raise HTTPException(status_code=422, detail="Nessun file caricato")
    if not tipo_codice:
        if not tipo_documento:
            raise HTTPException(status_code=422, detail="Tipologia documento mancante")
        tipo_codice = _legacy_tipo_codice(db, tipo_documento, entity_type)
    try:
        dati_dict = json.loads(dati) if dati else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Campo dati non è un JSON valido")

    inputs = []
    for u in uploads:
        content = await u.read()
        inputs.append(FileInput(
            content=content, filename=u.filename,
            mime_type=u.content_type or mimetypes.guess_type(u.filename or "")[0],
        ))

    service = DocumentoService(db, tenant, _user_id(current_user))
    try:
        documento = service.crea(
            entity_type=entity_type, entity_id=entity_id, tipo_codice=tipo_codice, files=inputs,
            data_riferimento=data_riferimento, sottotipo=sottotipo or None, data_scadenza=data_scadenza,
            dati=dati_dict, descrizione=descrizione, note=note,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    db.commit()
    db.refresh(documento)
    return to_out(documento, service)


@router.get("/{documento_id}/download")
async def download_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Download di un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {documento_id} non trovato"
        )

    file_path = file_storage.get_file_path(documento.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File non trovato sul filesystem"
        )

    return FileResponse(
        path=file_path,
        filename=documento.nome_file,
        media_type=documento.mime_type
    )


@router.put("/{documento_id}", response_model=DocumentoResponse)
def update_documento(
    documento_id: int,
    documento_update: DocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.write")),
):
    """Aggiorna metadata di un documento"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {documento_id} non trovato"
        )

    for field, value in documento_update.model_dump(exclude_unset=True).items():
        setattr(documento, field, value)

    db.commit()
    db.refresh(documento)
    return to_out(documento)


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("documenti.delete")),
):
    """Elimina un documento (file + record). Per le tipologie sostitutive torna in vigore il precedente."""
    service = DocumentoService(db, _tenant(tenant_schema), _user_id(current_user))
    try:
        service.elimina(documento_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {documento_id} non trovato"
        )
    db.commit()
    return None
