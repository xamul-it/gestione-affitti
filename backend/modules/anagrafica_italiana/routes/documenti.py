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
import logging

from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User
from app.core.platform_services import ScadenzarioService, DocumentParsingService
from app.core.platform.models import JobStatus
from app.core.file_storage import file_storage
from app.core.file_normalization import file_normalization

from ..models import SoggettoAnagrafico, TipoDocumento, Documento, DocumentoFile
from ..services.document_service import DocumentService
from ..schemas import CompleteDocumentoParsing

router = APIRouter(prefix="/anagrafica/documenti", tags=["documenti-anagrafica"])
logger = logging.getLogger(__name__)

def _ensure_documenti_table(db: Session, tenant_schema: Optional[str]) -> None:
    DocumentService(db, tenant_schema=tenant_schema).ensure_documenti_table()


@router.post("/upload")
async def upload_documento(
    soggetto_id: int = Form(...),
    tipo_documento_id: int = Form(...),
    file: UploadFile = File(...),
    data_scadenza: Optional[str] = Form(None),  # Format: YYYY-MM-DD
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
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
    _ensure_documenti_table(db, tenant_schema)

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
    doc_service = DocumentService(db, tenant_schema=tenant_schema)

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
        documento = doc_service.get(documento_data["id"])
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
        logger.exception(
            "[ANAG][UPLOAD] Failed to upload documento: soggetto_id=%s tipo_documento_id=%s schema=%s file=%s",
            soggetto_id,
            tipo_documento_id,
            tenant_schema,
            getattr(file, "filename", None),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante il caricamento: {str(e)}"
        )


@router.post("/upload-multi")
async def upload_documento_multi_file(
    soggetto_id: int = Form(...),
    tipo_documento_id: int = Form(...),
    files: List[UploadFile] = File(...),
    tipo_pagina: Optional[List[str]] = Form(None),  # Optional: specify page type for each file
    data_scadenza: Optional[str] = Form(None),  # Format: YYYY-MM-DD
    note: Optional[str] = Form(None),
    descrizione: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Upload multi-file document (e.g., ID card front + back).

    New in v2: Supports multiple files for a single documento entity.

    Args:
        soggetto_id: Soggetto anagrafico ID
        tipo_documento_id: TipoDocumento ID (from tipi_documento table)
        files: List of files to upload
        tipo_pagina: Optional list of page types (fronte, retro, etc.) matching files order
        data_scadenza: Optional expiration date (YYYY-MM-DD)
        note: Optional notes
        descrizione: Optional description

    Returns:
        {
            "documento": {...},
            "parsing_jobs": [...]  # If parsing configured
        }

    Raises:
        400: Invalid input
        404: Soggetto or TipoDocumento not found
        500: Upload/processing failure
    """
    _ensure_documenti_table(db, tenant_schema)

    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="Almeno un file è richiesto")

    logger.info(
        f"[ANAG][UPLOAD-MULTI] User {current_user.id} uploading {len(files)} files "
        f"for soggetto {soggetto_id}, tipo_documento_id={tipo_documento_id}"
    )

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

    # Parse expiration date if provided
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

    # Parse tipo_pagina list
    page_types = tipo_pagina if tipo_pagina else [None] * len(files)
    if len(page_types) != len(files):
        raise HTTPException(
            status_code=400,
            detail=f"tipo_pagina count ({len(page_types)}) must match files count ({len(files)})"
        )

    try:
        # 1. Create Documento parent record
        documento = Documento(
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=soggetto_id,
            tipo_documento_id=tipo_documento_id,
            descrizione=descrizione,
            note=note,
            data_scadenza=parsed_scadenza,
            # metadata_parsato will be populated after parsing
        )
        db.add(documento)
        db.flush()  # Get documento.id

        logger.info(f"[ANAG][UPLOAD-MULTI] Created Documento #{documento.id}")

        # 2. Process each file
        documento_files = []
        parsing_jobs = []

        for idx, (file, page_type) in enumerate(zip(files, page_types), start=1):
            # Determine page type
            if page_type is None:
                if len(files) == 1:
                    page_type = "unico"
                elif idx == 1:
                    page_type = "fronte"
                elif idx == 2:
                    page_type = "retro"
                else:
                    page_type = f"pagina_{idx}"

            logger.info(f"[ANAG][UPLOAD-MULTI] Processing file {idx}/{len(files)}: {file.filename} ({page_type})")

            # a. Save original file
            file_content = file.file
            relative_path = file_storage.save_file(
                file=file_content,
                entity_type="SOGGETTO_ANAGRAFICO",
                entity_id=soggetto_id,
                filename=file.filename,
                tenant_schema=tenant_schema
            )

            # b. Normalize file
            normalized_path = None
            normalized_width = None
            normalized_height = None

            try:
                abs_path = file_storage.get_file_path(relative_path, tenant_schema)
                base_name = relative_path.rsplit('.', 1)[0]
                normalized_relative = f"{base_name}_norm.jpg"
                normalized_abs = file_storage.get_file_path(normalized_relative, tenant_schema)

                norm_path, width, height = file_normalization.normalize_file(
                    input_path=abs_path,
                    output_path=normalized_abs
                )
                normalized_path = normalized_relative
                normalized_width = width
                normalized_height = height

                logger.info(f"[ANAG][UPLOAD-MULTI] Normalized to {normalized_path} ({width}x{height})")

            except Exception as e:
                logger.warning(f"[ANAG][UPLOAD-MULTI] Normalization failed: {e}")
                # Continue without normalization

            # c. Create DocumentoFile record
            doc_file = DocumentoFile(
                documento_id=documento.id,
                file_path=relative_path,
                nome_file=file.filename,
                mime_type=file.content_type,
                dimensione=file_storage.get_file_size(relative_path, tenant_schema),
                ordine=idx,
                tipo_pagina=page_type,
                file_normalizzato_path=normalized_path,
                normalizzato_width=normalized_width,
                normalizzato_height=normalized_height
            )
            db.add(doc_file)
            db.flush()  # Get doc_file.id

            documento_files.append(doc_file)

            # d. Check if parsing required for this page type
            if tipo_doc.parsing_multi_file_config:
                page_config = tipo_doc.parsing_multi_file_config.get(page_type, {})
                if page_config.get("parsing_required", False):
                    # Submit to parsing
                    parsing_service = DocumentParsingService(db, tenant_schema)

                    # Use normalized file for parsing if available
                    parsing_file_path = normalized_path if normalized_path else relative_path

                    # Create temporary UploadFile-like object for parsing service
                    from io import BytesIO
                    with open(file_storage.get_file_path(parsing_file_path, tenant_schema), 'rb') as f:
                        file_bytes = f.read()

                    class TempUploadFile:
                        def __init__(self, filename, content, content_type):
                            self.filename = filename
                            self.file = BytesIO(content)
                            self.content_type = content_type

                    temp_file = TempUploadFile(
                        filename=file.filename,
                        content=file_bytes,
                        content_type="image/jpeg" if normalized_path else file.content_type
                    )

                    job = parsing_service.upload_and_parse(
                        file=temp_file,
                        document_type_key=f"anagrafica_italiana.{tipo_doc.codice}",
                        entity_type="SOGGETTO_ANAGRAFICO",
                        entity_id=soggetto_id,
                        user_id=current_user.id,
                        parsing_service_override=page_config.get("service") or tipo_doc.parsing_service,
                        parsing_config_override=page_config.get("config"),
                    )

                    # Link job to DocumentoFile
                    doc_file.parsing_job_id = job.id
                    parsing_jobs.append(job)

                    logger.info(f"[ANAG][UPLOAD-MULTI] Created parsing job {job.job_uuid} for file {doc_file.id}")

        # 3. Commit all changes
        db.commit()
        db.refresh(documento)

        logger.info(
            f"[ANAG][UPLOAD-MULTI] ✓ Completed: documento={documento.id}, "
            f"files={len(documento_files)}, parsing_jobs={len(parsing_jobs)}"
        )

        return {
            "documento": documento.to_dict(),
            "parsing_jobs": [job.to_dict() for job in parsing_jobs]
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"[ANAG][UPLOAD-MULTI] Failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'upload multi-file: {str(e)}"
        )


@router.get("/soggetto/{soggetto_id}")
def list_documenti_soggetto(
    soggetto_id: int,
    categoria: Optional[str] = None,  # Filter by categoria (identita, fiscale, etc.)
    scaduti: bool = False,  # Show only expired docs
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
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
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    _ensure_documenti_table(db, tenant_schema)

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
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Download a document file.

    Uses platform DocumentService for secure file access.
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    _ensure_documenti_table(db, tenant_schema)

    doc_service = DocumentService(db, tenant_schema=tenant_schema)

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


@router.get("/{documento_id}/view")
def view_documento_complete(
    documento_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get complete document metadata with all files.

    Returns documento parent with all associated files (for multi-file documents)
    or legacy single-file structure for backward compatibility.

    Response format:
    {
        "id": 123,
        "entity_type": "SOGGETTO_ANAGRAFICO",
        "entity_id": 45,
        "tipo_documento": {...},
        "is_legacy": false,
        "files": [
            {
                "id": 1,
                "ordine": 1,
                "tipo_pagina": "fronte",
                "nome_file": "carta_identita_fronte.jpg",
                "file_normalizzato_path": "...",
                "is_parsed": true,
                "parsing_result": {...},
                "confidence_score": 95
            },
            ...
        ],
        "metadata_parsato": {...},  // Aggregated from all files
        "confidence_score": 92       // Average across files
    }
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    _ensure_documenti_table(db, tenant_schema)

    # Get documento
    documento = db.query(Documento).filter(
        Documento.id == documento_id
    ).first()

    if not documento:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    # Verify it's an anagrafica document
    if documento.entity_type != "SOGGETTO_ANAGRAFICO":
        raise HTTPException(
            status_code=403,
            detail="Questo documento non appartiene al modulo anagrafica"
        )

    # Get tipo documento info
    tipo_doc_info = None
    if documento.tipo_documento_id:
        tipo_doc = db.query(TipoDocumento).filter(
            TipoDocumento.id == documento.tipo_documento_id
        ).first()
        if tipo_doc:
            tipo_doc_info = {
                "id": tipo_doc.id,
                "codice": tipo_doc.codice,
                "nome": tipo_doc.nome,
                "categoria": tipo_doc.categoria,
                "richiede_scadenza": tipo_doc.richiede_scadenza
            }

    # Build response
    result = {
        "id": documento.id,
        "entity_type": documento.entity_type,
        "entity_id": documento.entity_id,
        "tipo_documento": tipo_doc_info,
        "descrizione": documento.descrizione,
        "note": documento.note,
        "data_scadenza": documento.data_scadenza.isoformat() if documento.data_scadenza else None,
        "is_legacy": documento.is_legacy,
        "files": documento.get_files_list(),
        "metadata_parsato": documento.metadata_parsato,
        "confidence_score": documento.confidence_score,
        "created_at": documento.created_at.isoformat() if documento.created_at else None,
        "updated_at": documento.updated_at.isoformat() if documento.updated_at else None
    }

    return result


@router.get("/file/{file_id}/view-normalized")
def view_normalized_file(
    file_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    View normalized JPEG file for a DocumentoFile.

    Returns the normalized JPEG version (2048px max, optimized for web viewing).
    If normalization failed or not available, falls back to original file.

    Args:
        file_id: DocumentoFile ID

    Returns:
        FileResponse with JPEG image
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    _ensure_documenti_table(db, tenant_schema)

    # Get DocumentoFile
    doc_file = db.query(DocumentoFile).filter(
        DocumentoFile.id == file_id
    ).first()

    if not doc_file:
        raise HTTPException(status_code=404, detail="File documento non trovato")

    # Verify parent documento exists and is anagrafica
    documento = db.query(Documento).filter(
        Documento.id == doc_file.documento_id
    ).first()

    if not documento or documento.entity_type != "SOGGETTO_ANAGRAFICO":
        raise HTTPException(
            status_code=403,
            detail="Questo file non appartiene al modulo anagrafica"
        )

    # Determine which file to serve
    file_path = doc_file.file_normalizzato_path if doc_file.file_normalizzato_path else doc_file.file_path

    if not file_path:
        raise HTTPException(status_code=404, detail="File path non disponibile")

    # Get absolute path
    abs_path = file_storage.get_file_path(file_path, tenant_schema)

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="File non trovato sul filesystem")

    # Determine media type
    media_type = "image/jpeg" if doc_file.file_normalizzato_path else (doc_file.mime_type or "application/octet-stream")

    return FileResponse(
        path=str(abs_path),
        media_type=media_type,
        filename=doc_file.nome_file
    )


@router.get("/file/{file_id}/thumbnail")
def get_file_thumbnail(
    file_id: int,
    size: int = 320,  # Default 320px
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get thumbnail version of DocumentoFile.

    Generates and caches a thumbnail from the normalized file (or original if normalization unavailable).
    Thumbnail is resized to fit within size x size while maintaining aspect ratio.

    Args:
        file_id: DocumentoFile ID
        size: Maximum dimension in pixels (default 320)

    Returns:
        FileResponse with thumbnail JPEG
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    if size < 50 or size > 1024:
        raise HTTPException(status_code=400, detail="Size deve essere tra 50 e 1024")

    _ensure_documenti_table(db, tenant_schema)

    # Get DocumentoFile
    doc_file = db.query(DocumentoFile).filter(
        DocumentoFile.id == file_id
    ).first()

    if not doc_file:
        raise HTTPException(status_code=404, detail="File documento non trovato")

    # Verify parent documento
    documento = db.query(Documento).filter(
        Documento.id == doc_file.documento_id
    ).first()

    if not documento or documento.entity_type != "SOGGETTO_ANAGRAFICO":
        raise HTTPException(
            status_code=403,
            detail="Questo file non appartiene al modulo anagrafica"
        )

    # Determine source file (prefer normalized)
    source_path = doc_file.file_normalizzato_path if doc_file.file_normalizzato_path else doc_file.file_path

    if not source_path:
        raise HTTPException(status_code=404, detail="File path non disponibile")

    # Check for cached thumbnail
    base_name = source_path.rsplit('.', 1)[0]
    thumbnail_relative = f"{base_name}_thumb_{size}.jpg"
    thumbnail_abs = file_storage.get_file_path(thumbnail_relative, tenant_schema)

    # Generate thumbnail if not cached
    if not thumbnail_abs.exists():
        from PIL import Image
        import io

        source_abs = file_storage.get_file_path(source_path, tenant_schema)

        if not source_abs.exists():
            raise HTTPException(status_code=404, detail="File sorgente non trovato")

        try:
            # Open image and create thumbnail
            with Image.open(source_abs) as img:
                # Convert to RGB if needed (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail((size, size), Image.Resampling.LANCZOS)

                # Save thumbnail
                thumbnail_abs.parent.mkdir(parents=True, exist_ok=True)
                img.save(thumbnail_abs, 'JPEG', quality=85, optimize=True)

                logger.info(f"[ANAG][THUMBNAIL] Generated {size}px thumbnail for file {file_id}")

        except Exception as e:
            logger.error(f"[ANAG][THUMBNAIL] Failed to generate thumbnail: {e}")
            raise HTTPException(status_code=500, detail=f"Errore generazione thumbnail: {str(e)}")

    return FileResponse(
        path=str(thumbnail_abs),
        media_type="image/jpeg",
        filename=f"thumb_{doc_file.nome_file}"
    )


@router.get("/file/{file_id}/download-original")
def download_original_file(
    file_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Download original file (before normalization).

    Returns the original uploaded file in its native format.

    Args:
        file_id: DocumentoFile ID

    Returns:
        FileResponse with original file
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    _ensure_documenti_table(db, tenant_schema)

    # Get DocumentoFile
    doc_file = db.query(DocumentoFile).filter(
        DocumentoFile.id == file_id
    ).first()

    if not doc_file:
        raise HTTPException(status_code=404, detail="File documento non trovato")

    # Verify parent documento
    documento = db.query(Documento).filter(
        Documento.id == doc_file.documento_id
    ).first()

    if not documento or documento.entity_type != "SOGGETTO_ANAGRAFICO":
        raise HTTPException(
            status_code=403,
            detail="Questo file non appartiene al modulo anagrafica"
        )

    # Get original file path
    if not doc_file.file_path:
        raise HTTPException(status_code=404, detail="File path non disponibile")

    # Get absolute path
    abs_path = file_storage.get_file_path(doc_file.file_path, tenant_schema)

    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="File non trovato sul filesystem")

    return FileResponse(
        path=str(abs_path),
        media_type=doc_file.mime_type or "application/octet-stream",
        filename=doc_file.nome_file
    )


@router.post("/complete-parsing")
def complete_parsed_document(
    data: CompleteDocumentoParsing,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Complete a parsed document for an existing soggetto.

    - Moves temp file to permanent storage
    - Creates Documento record
    - Optionally updates soggetto fields
    - Completes linked scadenza notification
    """
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    _ensure_documenti_table(db, tenant_schema)

    parsing_service = DocumentParsingService(db, tenant_schema)
    job = parsing_service.get_job_or_404(data.job_uuid)

    if job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Non hai accesso a questo job")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job non completato. Status attuale: {job.status.value}"
        )

    if job.entity_type != "SOGGETTO_ANAGRAFICO" or not job.entity_id:
        raise HTTPException(
            status_code=400,
            detail="Questo job non è collegato a un soggetto anagrafico"
        )

    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == job.entity_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    if data.apply_to_soggetto:
        if data.nome is not None:
            soggetto.nome = data.nome
        if data.cognome is not None:
            soggetto.cognome = data.cognome
        if data.codice_fiscale is not None:
            soggetto.codice_fiscale = data.codice_fiscale
        if data.luogo_nascita is not None:
            soggetto.luogo_nascita = data.luogo_nascita
        if data.data_nascita:
            from datetime import datetime
            soggetto.data_nascita = datetime.strptime(data.data_nascita, "%Y-%m-%d").date()

    document_type_code = job.document_type_key.split(".")[-1]
    tipo_doc = db.query(TipoDocumento).filter(
        TipoDocumento.codice == document_type_code
    ).first()
    if not tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo documento non trovato")

    try:
        if "temp_uploads" in (job.file_path or ""):
            new_file_path = file_storage.move_from_temp(
                temp_relative_path=job.file_path,
                entity_type="SOGGETTO_ANAGRAFICO",
                entity_id=soggetto.id,
                tenant_schema=tenant_schema
            )
        else:
            new_file_path = job.file_path
    except Exception as e:
        logger.error("[ANAG][PARSING COMPLETE] Failed to move file: %s", e)
        raise HTTPException(status_code=500, detail=f"Errore spostamento file: {str(e)}")

    parsed_scadenza = None
    if data.document_expiry:
        from datetime import datetime
        parsed_scadenza = datetime.strptime(data.document_expiry, "%Y-%m-%d").date()

    note = data.note
    if data.document_number:
        note_prefix = f"Numero documento: {data.document_number}"
        note = f"{note_prefix}. {note}" if note else note_prefix

    documento = Documento(
        entity_type="SOGGETTO_ANAGRAFICO",
        entity_id=soggetto.id,
        tipo_documento=tipo_doc.codice,
        tipo_documento_id=tipo_doc.id,
        nome_file=job.original_filename,
        file_path=new_file_path,
        mime_type=job.mime_type,
        dimensione=file_storage.get_file_size(new_file_path, tenant_schema),
        descrizione=(
            f"Documento d'identità (parsing automatico, confidence {job.confidence_score}%)"
            if job.confidence_score is not None else "Documento d'identità (parsing automatico)"
        ),
        data_scadenza=parsed_scadenza,
        note=note
    )

    db.add(documento)

    if job.scadenza_id:
        from app.core.platform.models import Scadenza, StatoScadenza
        from datetime import datetime
        scadenza = db.query(Scadenza).filter(Scadenza.id == job.scadenza_id).first()
        if scadenza and scadenza.stato == StatoScadenza.ATTIVA:
            scadenza.stato = StatoScadenza.COMPLETATA
            scadenza.completato_da = current_user.id
            scadenza.completato_il = datetime.utcnow()

    db.commit()
    # Ensure tenant search_path before ORM refresh (refresh issues a SELECT).
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))
    db.refresh(documento)
    db.refresh(soggetto)

    return {
        "documento": {
            "id": documento.id,
            "nome_file": documento.nome_file,
            "tipo_documento": tipo_doc.codice,
            "data_scadenza": documento.data_scadenza.isoformat() if documento.data_scadenza else None,
            "created_at": documento.created_at.isoformat() if documento.created_at else None,
        },
        "soggetto": {
            "id": soggetto.id,
            "nome": soggetto.nome,
            "cognome": soggetto.cognome,
            "codice_fiscale": soggetto.codice_fiscale,
            "data_nascita": soggetto.data_nascita.isoformat() if soggetto.data_nascita else None,
            "luogo_nascita": soggetto.luogo_nascita,
        },
        "message": "Documento validato e collegato al soggetto"
    }


@router.delete("/{documento_id}")
def delete_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.delete"))
):
    """
    Delete a document (file + database record).

    Uses platform DocumentService for safe deletion.
    """
    doc_service = DocumentService(db, tenant_schema=tenant_schema)

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
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get deadline summary for a soggetto (expired, expiring soon, upcoming).

    Uses platform ScadenzarioService.
    """
    _ensure_documenti_table(db, tenant_schema)

    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    scad_service = ScadenzarioService(db, model_class=Documento)

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
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get deadline statistics for all anagrafica documents.

    Uses platform ScadenzarioService.
    """
    _ensure_documenti_table(db, tenant_schema)

    scad_service = ScadenzarioService(db, model_class=Documento)

    stats = scad_service.get_statistics(entity_type="SOGGETTO_ANAGRAFICO")

    return stats
