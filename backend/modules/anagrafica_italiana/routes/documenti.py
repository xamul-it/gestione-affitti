"""
API routes for Soggetto Anagrafico Documents.

Uses platform services:
- DocumentService for file upload/download/management
- ScadenzarioService for deadline tracking
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User
from app.core.platform_services import ScadenzarioService

# Import models and services from modules
import sys, os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from affitti_lungo.models.documenti import Documento
from affitti_lungo.services.document_service import DocumentService
from anagrafica_italiana.models import SoggettoAnagrafico, TipoDocumento

router = APIRouter(prefix="/anagrafica/documenti", tags=["documenti-anagrafica"])


@router.post("/upload")
async def upload_documento(
    soggetto_id: int = Form(...),
    tipo_documento_id: int = Form(...),
    file: UploadFile = File(...),
    data_scadenza: Optional[str] = Form(None),  # Format: YYYY-MM-DD
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Upload a document for an anagrafica subject.

    Uses platform DocumentService for secure file handling.

    Args:
        soggetto_id: Soggetto anagrafico ID
        tipo_documento_id: TipoDocumento ID (from tipi_documento table)
        file: File to upload
        data_scadenza: Optional expiration date (YYYY-MM-DD)
        note: Optional notes

    Returns:
        Uploaded documento metadata
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Verify tipo documento
    tipo_doc = db.query(TipoDocumento).filter(
        TipoDocumento.id == tipo_documento_id
    ).first()
    if not tipo_doc or not tipo_doc.attivo:
        raise HTTPException(status_code=404, detail="Tipo documento non trovato o non attivo")

    # Validate expiration date if tipo requires it
    parsed_scadenza = None
    if data_scadenza:
        from datetime import datetime
        try:
            parsed_scadenza = datetime.strptime(data_scadenza, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato data non valido (usa YYYY-MM-DD)")
    elif tipo_doc.richiede_scadenza:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo documento '{tipo_doc.nome}' richiede data di scadenza"
        )

    # Use DocumentService to upload file
    doc_service = DocumentService(db)

    try:
        # Note: DocumentService expects 'tipo' as string, but we'll store tipo_documento_id separately
        # We use tipo_documento.codice as fallback for the enum field
        documento_data = doc_service.upload(
            file=file,
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=soggetto_id,
            filename=file.filename,
            tipo=tipo_doc.codice,  # Use codice for enum compatibility
            descrizione=note,
            validate=True
        )

        # Update documento with anagrafica-specific fields
        documento = db.query(Documento).filter(Documento.id == documento_data["id"]).first()
        if documento:
            documento.tipo_documento_id = tipo_documento_id
            documento.data_scadenza = parsed_scadenza
            documento.note = note
            db.commit()
            db.refresh(documento)

        return {
            "id": documento.id,
            "nome_file": documento.nome_file,
            "tipo_documento": {
                "id": tipo_doc.id,
                "codice": tipo_doc.codice,
                "nome": tipo_doc.nome,
                "categoria": tipo_doc.categoria
            },
            "data_scadenza": parsed_scadenza.isoformat() if parsed_scadenza else None,
            "file_size": documento.dimensione,
            "note": documento.note,
            "created_at": documento.created_at.isoformat() if documento.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il caricamento: {str(e)}"
        )


@router.get("/soggetto/{soggetto_id}")
def list_documenti_soggetto(
    soggetto_id: int,
    categoria: Optional[str] = None,  # Filter by categoria (identita, fiscale, etc.)
    scaduti: bool = False,  # Show only expired docs
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    List all documents for an anagrafica subject.

    Args:
        soggetto_id: Soggetto ID
        categoria: Optional filter by tipo documento categoria
        scaduti: If True, show only expired documents

    Returns:
        List of documents with metadata
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Query documents
    query = db.query(Documento).filter(
        Documento.entity_type == "SOGGETTO_ANAGRAFICO",
        Documento.entity_id == soggetto_id
    )

    # Filter by categoria if specified
    if categoria:
        query = query.join(TipoDocumento, Documento.tipo_documento_id == TipoDocumento.id).filter(
            TipoDocumento.categoria == categoria
        )

    # Filter scaduti
    if scaduti:
        today = date.today()
        query = query.filter(
            Documento.data_scadenza.isnot(None),
            Documento.data_scadenza < today
        )

    documenti = query.order_by(Documento.created_at.desc()).all()

    # Format response with tipo documento info
    result = []
    today = date.today()

    for doc in documenti:
        tipo_doc_info = None
        if doc.tipo_documento_id:
            tipo_doc = db.query(TipoDocumento).filter(
                TipoDocumento.id == doc.tipo_documento_id
            ).first()
            if tipo_doc:
                tipo_doc_info = {
                    "id": tipo_doc.id,
                    "codice": tipo_doc.codice,
                    "nome": tipo_doc.nome,
                    "categoria": tipo_doc.categoria
                }

        result.append({
            "id": doc.id,
            "nome_file": doc.nome_file,
            "tipo_documento": tipo_doc_info,
            "data_scadenza": doc.data_scadenza.isoformat() if doc.data_scadenza else None,
            "is_scaduto": doc.data_scadenza < today if doc.data_scadenza else False,
            "days_to_expiry": (doc.data_scadenza - today).days if doc.data_scadenza else None,
            "dimensione": doc.dimensione,
            "note": doc.note,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        })

    return result


@router.get("/{documento_id}/download")
def download_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Download a document file.

    Uses platform DocumentService for secure file access.
    """
    doc_service = DocumentService(db)

    try:
        # Get file path (includes permission check)
        file_path = doc_service.get_file_path(documento_id)

        # Get documento for filename
        documento = doc_service.get_or_404(documento_id)

        # Verify it's an anagrafica document
        if documento.entity_type != "SOGGETTO_ANAGRAFICO":
            raise HTTPException(
                status_code=403,
                detail="Questo documento non appartiene al modulo anagrafica"
            )

        return FileResponse(
            path=str(file_path),
            filename=documento.nome_file,
            media_type=documento.mime_type or "application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il download: {str(e)}"
        )


@router.delete("/{documento_id}")
def delete_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.delete"))
):
    """
    Delete a document (file + database record).

    Uses platform DocumentService for safe deletion.
    """
    doc_service = DocumentService(db)

    try:
        # Get documento first to verify ownership
        documento = doc_service.get_or_404(documento_id)

        # Verify it's an anagrafica document
        if documento.entity_type != "SOGGETTO_ANAGRAFICO":
            raise HTTPException(
                status_code=403,
                detail="Questo documento non appartiene al modulo anagrafica"
            )

        # Delete using service
        doc_service.delete(documento_id)

        return {"message": "Documento eliminato con successo"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'eliminazione: {str(e)}"
        )


@router.get("/scadenzario/soggetto/{soggetto_id}")
def get_scadenzario_soggetto(
    soggetto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get deadline summary for a soggetto (expired, expiring soon, upcoming).

    Uses platform ScadenzarioService.
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    scad_service = ScadenzarioService(db)

    # Get documents grouped by deadline status
    scadenze = scad_service.get_by_entity(
        entity_type="SOGGETTO_ANAGRAFICO",
        entity_id=soggetto_id,
        include_expired=True
    )

    # Format response with tipo documento info
    def format_doc(doc):
        tipo_doc_info = None
        if doc.tipo_documento_id:
            tipo_doc = db.query(TipoDocumento).filter(
                TipoDocumento.id == doc.tipo_documento_id
            ).first()
            if tipo_doc:
                tipo_doc_info = {
                    "id": tipo_doc.id,
                    "codice": tipo_doc.codice,
                    "nome": tipo_doc.nome
                }

        days_diff = (doc.data_scadenza - date.today()).days if doc.data_scadenza else 0

        return {
            "id": doc.id,
            "nome_file": doc.nome_file,
            "tipo_documento": tipo_doc_info,
            "data_scadenza": doc.data_scadenza.isoformat() if doc.data_scadenza else None,
            "days_diff": days_diff
        }

    return {
        "expired": [format_doc(doc) for doc in scadenze["expired"]],
        "expiring_soon": [format_doc(doc) for doc in scadenze["expiring_soon"]],
        "upcoming": [format_doc(doc) for doc in scadenze["upcoming"]]
    }


@router.get("/scadenzario/statistics")
def get_scadenzario_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get deadline statistics for all anagrafica documents.

    Uses platform ScadenzarioService.
    """
    scad_service = ScadenzarioService(db)

    stats = scad_service.get_statistics(entity_type="SOGGETTO_ANAGRAFICO")

    return stats
