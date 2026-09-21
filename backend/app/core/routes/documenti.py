from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.file_storage import file_storage
from app.core.platform.models import Documento, EntityType, TipoDocumentoEnum as TipoDocumento
from app.core.schemas.documenti import DocumentoResponse, DocumentoUpdate
import logging
import mimetypes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documenti", tags=["Documenti"])


@router.get("/", response_model=List[DocumentoResponse])
def get_documenti(
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Ottieni lista documenti con filtri opzionali"""
    query = db.query(Documento)

    if entity_type:
        query = query.filter(Documento.entity_type == entity_type)
    if entity_id:
        query = query.filter(Documento.entity_id == entity_id)

    documenti = query.order_by(Documento.created_at.desc()).offset(skip).limit(limit).all()
    return documenti


@router.get("/{documento_id}", response_model=DocumentoResponse)
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
    return documento


@router.post("/upload", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
async def upload_documento(
    file: UploadFile = File(...),
    entity_type: EntityType = Form(...),
    entity_id: int = Form(...),
    tipo_documento: TipoDocumento = Form(...),
    descrizione: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("documenti.write")),
):
    """
    Upload di un documento

    - **file**: File da caricare
    - **entity_type**: Tipo entità (IMMOBILE, CONTRATTO, ecc.)
    - **entity_id**: ID dell'entità
    - **tipo_documento**: Tipo documento
    - **descrizione**: Descrizione opzionale
    - **note**: Note opzionali
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    # Salva il file
    try:
        file_path = file_storage.save_file(
            file.file,
            entity_type.value,
            entity_id,
            file.filename,
            tenant_schema=tenant_schema,
        )
    except Exception as e:
        logger.exception("Errore nel salvataggio del documento (entity_type=%s, entity_id=%s)", entity_type, entity_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore nel salvataggio del file"
        )

    # Determina MIME type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]

    # Crea record nel database
    documento = Documento(
        entity_type=entity_type,
        entity_id=entity_id,
        tipo_documento=tipo_documento,
        nome_file=file.filename,
        file_path=file_path,
        mime_type=mime_type,
        dimensione=file_storage.get_file_size(file_path),
        descrizione=descrizione,
        note=note
    )

    db.add(documento)
    db.commit()
    db.refresh(documento)

    return documento


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
    return documento


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.delete")),
):
    """Elimina un documento (file + record database)"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {documento_id} non trovato"
        )

    # Elimina file dal filesystem
    file_storage.delete_file(documento.file_path)

    # Elimina record dal database
    db.delete(documento)
    db.commit()

    return None
