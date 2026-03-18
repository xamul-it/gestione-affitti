"""
API routes for "Create Anagrafica from Document" workflow.

Workflow:
1. User uploads identity document (carta d'identità, passaporto)
2. Document parsed by MRZ service asynchronously
3. User receives notification when parsing complete
4. User reviews parsed data and completes anagrafica creation
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status as http_status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, date
import logging

from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User
from app.core.file_storage import file_storage
from app.core.platform_services import DocumentParsingService, ScadenzaService
from app.core.platform.models import JobStatus, StatoScadenza

from ..models import SoggettoAnagrafico, TipoSoggetto, Documento, TipoDocumento
from ..schemas import CompleteSoggettoFromDocument
from ..services.document_service import DocumentService

router = APIRouter(
    prefix="/anagrafica/from-document",
    tags=["anagrafica-from-document"]
)
logger = logging.getLogger(__name__)


@router.post("/upload-identity-document")
async def upload_identity_document(
    file: UploadFile = File(...),
    document_type: str = Form("CARTA_IDENTITA"),
    db: Session = Depends(get_db),
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.create"))
):
    """
    Step 1: Upload identity document for parsing.

    Supports:
    - CARTA_IDENTITA (Italian ID card)
    - PASSAPORTO (Passport)
    - PATENTE_GUIDA (Driver's license)
    - PERMESSO_SOGGIORNO (Residence permit)

    Workflow:
        1. Upload document to temp storage
        2. Submit to MRZ parsing service
        3. Service calls callback when done
        4. Callback creates Scadenza notification
        5. User sees notification and proceeds to step 2

    Args:
        file: Identity document image
        document_type: Type code (CARTA_IDENTITA, PASSAPORTO, etc.)
        db: Database session (injected)
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)

    Returns:
        {
            "job_uuid": "...",
            "status": "QUEUED",
            "message": "Documento in elaborazione...",
            "polling_url": "/api/v1/document-parsing/status/{job_uuid}"
        }

    Raises:
        400: Invalid document type or missing tenant
        500: Upload failure
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    # Build full document type key
    document_type_key = f"anagrafica_italiana.{document_type}"

    logger.info(
        f"[AnagraficaFromDoc][Upload] User {current_user.id} uploading identity document "
        f"{file.filename} (type={document_type})"
    )

    # Use DocumentParsingService to upload and parse
    parsing_service = DocumentParsingService(db, tenant_schema)

    try:
        tipo_doc = db.query(TipoDocumento).filter(
            TipoDocumento.codice == document_type
        ).first()

        job = parsing_service.upload_and_parse(
            file=file,
            document_type_key=document_type_key,
            entity_type=None,  # No entity yet (will be created in step 2)
            entity_id=None,
            user_id=current_user.id,
            parsing_service_override=tipo_doc.parsing_service if tipo_doc else None,
            parsing_config_override=tipo_doc.parsing_config if tipo_doc else None,
            callback_url_override=tipo_doc.parsing_callback_url if tipo_doc else None,
        )

        return {
            "job_uuid": job.job_uuid,
            "status": job.status.value,
            "message": (
                "Documento inviato al servizio di elaborazione. "
                "Riceverai una notifica quando il parsing sarà completato."
            ),
            "polling_url": f"/api/v1/document-parsing/status/{job.job_uuid}",
            "document_type": document_type,
            "original_filename": job.original_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AnagraficaFromDoc][Upload] Failed for user {current_user.id}, "
            f"file {file.filename}, type {document_type}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'upload: {str(e)}"
        )


@router.get("/pending-documents")
def get_pending_documents(
    db: Session = Depends(get_db),
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get documents pending completion (parsed but not yet linked to anagrafica).

    Returns documents with:
    - status = COMPLETED
    - entity_id = NULL (not yet linked to soggetto)
    - created_by = current_user

    Args:
        db: Database session (injected)
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)

    Returns:
        List of:
        {
            "job": {...},  # Full DocumentJob data
            "parsed_data": {...},  # Extracted data from MRZ
            "notification": {...}  # Linked Scadenza if exists
        }

    Raises:
        400: Missing tenant
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    parsing_service = DocumentParsingService(db, tenant_schema)
    pending_jobs = parsing_service.get_pending_documents(user_id=current_user.id)

    result = []
    for job in pending_jobs:
        # Get linked notification if exists
        notification = None
        if job.scadenza_id:
            from app.core.platform.models import Scadenza
            scadenza = db.query(Scadenza).filter(
                Scadenza.id == job.scadenza_id
            ).first()
            if scadenza:
                notification = scadenza.to_dict()

        result.append({
            "job": job.to_dict(),
            "parsed_data": job.parsing_result,
            "notification": notification
        })

    return result


@router.post("/complete")
def complete_anagrafica_from_document(
    data: CompleteSoggettoFromDocument,
    db: Session = Depends(get_db),
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.create"))
):
    """
    Step 2: Complete anagrafica creation with reviewed data.

    Workflow:
        1. Load DocumentJob and verify ownership/status
        2. Create SoggettoAnagrafico with user-reviewed data
        3. Move file from temp to permanent storage
        4. Create Documento record linked to soggetto
        5. Update job.entity_id to link to soggetto
        6. Complete Scadenza notification

    Args:
        data: Reviewed anagrafica data
        db: Database session (injected)
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)

    Returns:
        {
            "soggetto": {...},  # Created SoggettoAnagrafico
            "documento": {...}  # Created Documento
        }

    Raises:
        400: Missing tenant or invalid data
        403: User doesn't own the job
        404: Job not found
        409: Codice fiscale already exists
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    # Ensure tenant search_path
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))

    logger.info(
        f"[AnagraficaFromDoc][Complete] User {current_user.id} completing anagrafica "
        f"from job {data.job_uuid}"
    )

    DocumentService(db, tenant_schema=tenant_schema).ensure_documenti_table()

    # 1. Load and validate DocumentJob
    parsing_service = DocumentParsingService(db, tenant_schema)
    job = parsing_service.get_job_or_404(data.job_uuid)

    # Verify ownership
    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Non hai accesso a questo job"
        )

    # Verify status
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Job non completato. Status attuale: {job.status.value}"
        )

    # Verify not already linked
    if job.entity_id is not None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Questo documento è già stato utilizzato per creare un'anagrafica"
        )

    # 2. Check codice fiscale uniqueness
    existing = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.codice_fiscale == data.codice_fiscale
    ).first()

    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Esiste già un soggetto con codice fiscale {data.codice_fiscale}"
        )

    # 3. Create SoggettoAnagrafico
    try:
        # Parse dates
        data_nascita_parsed = None
        if data.data_nascita:
            data_nascita_parsed = datetime.strptime(data.data_nascita, "%Y-%m-%d").date()

        soggetto = SoggettoAnagrafico(
            tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
            nome=data.nome,
            cognome=data.cognome,
            codice_fiscale=data.codice_fiscale,
            data_nascita=data_nascita_parsed,
            luogo_nascita=data.luogo_nascita,
            email=data.email,
            telefono=data.telefono,
            cellulare=data.cellulare,
            indirizzo=data.indirizzo,
            citta=data.citta,
            cap=data.cap,
            provincia=data.provincia,
            note=data.note,
            attivo=True
        )

        db.add(soggetto)
        db.flush()  # Get soggetto.id

        logger.info(f"[AnagraficaFromDoc][Complete] Created soggetto #{soggetto.id}")

    except Exception as e:
        db.rollback()
        logger.error(f"[AnagraficaFromDoc][Complete] Failed to create soggetto: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore creazione anagrafica: {str(e)}"
        )

    # 4. Move file from temp to permanent storage
    try:
        new_file_path = file_storage.move_from_temp(
            temp_relative_path=job.file_path,
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=soggetto.id,
            tenant_schema=tenant_schema
        )

        logger.info(
            f"[AnagraficaFromDoc][Complete] Moved file from temp to permanent: {new_file_path}"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"[AnagraficaFromDoc][Complete] Failed to move file: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore spostamento file: {str(e)}"
        )

    # 5. Create Documento record
    try:
        # Parse document expiry
        data_scadenza = None
        if data.document_expiry:
            data_scadenza = datetime.strptime(data.document_expiry, "%Y-%m-%d").date()

        # Get TipoDocumento for the document type
        document_type_code = job.document_type_key.split('.')[-1]  # Extract CODE from module.CODE
        tipo_doc = db.query(TipoDocumento).filter(
            TipoDocumento.codice == document_type_code
        ).first()

        documento = Documento(
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=soggetto.id,
            tipo_documento=document_type_code,
            tipo_documento_id=tipo_doc.id if tipo_doc else None,
            nome_file=job.original_filename,
            file_path=new_file_path,
            mime_type=job.mime_type,
            dimensione=file_storage.get_file_size(new_file_path, tenant_schema),
            descrizione=f"Documento d'identità (parsing automatico, confidence {job.confidence_score}%)",
            data_scadenza=data_scadenza,
            note=f"Numero documento: {data.document_number}" if data.document_number else None
        )

        db.add(documento)
        db.flush()

        logger.info(f"[AnagraficaFromDoc][Complete] Created documento #{documento.id}")

    except Exception as e:
        db.rollback()
        logger.error(f"[AnagraficaFromDoc][Complete] Failed to create documento: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore creazione documento: {str(e)}"
        )

    # 6. Update DocumentJob to link to soggetto
    job.entity_type = "SOGGETTO_ANAGRAFICO"
    job.entity_id = soggetto.id

    # 7. Complete Scadenza notification
    if job.scadenza_id:
        try:
            from app.core.platform.models import Scadenza
            scadenza = db.query(Scadenza).filter(Scadenza.id == job.scadenza_id).first()
            if scadenza and scadenza.stato == StatoScadenza.ATTIVA:
                scadenza.stato = StatoScadenza.COMPLETATA
                scadenza.completato_da = current_user.id
                scadenza.completato_il = datetime.utcnow()
                logger.info(f"[AnagraficaFromDoc][Complete] Completed scadenza #{scadenza.id}")
        except Exception as e:
            logger.warning(f"[AnagraficaFromDoc][Complete] Failed to complete scadenza: {e}")

    # Commit all changes
    db.commit()
    # Ensure tenant search_path before ORM refresh (refresh issues a SELECT).
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))
    db.refresh(soggetto)
    db.refresh(documento)

    logger.info(
        f"[AnagraficaFromDoc][Complete] ✓ Completed workflow: "
        f"job={job.job_uuid}, soggetto={soggetto.id}, documento={documento.id}"
    )

    return {
        "soggetto": {
            "id": soggetto.id,
            "tipo_soggetto": soggetto.tipo_soggetto.value,
            "nome": soggetto.nome,
            "cognome": soggetto.cognome,
            "codice_fiscale": soggetto.codice_fiscale,
            "data_nascita": soggetto.data_nascita.isoformat() if soggetto.data_nascita else None,
            "email": soggetto.email,
            "telefono": soggetto.telefono,
            "created_at": soggetto.created_at.isoformat() if soggetto.created_at else None
        },
        "documento": {
            "id": documento.id,
            "nome_file": documento.nome_file,
            "tipo_documento": documento.tipo_documento,
            "data_scadenza": documento.data_scadenza.isoformat() if documento.data_scadenza else None,
            "dimensione": documento.dimensione,
            "created_at": documento.created_at.isoformat() if documento.created_at else None
        },
        "message": "Anagrafica creata con successo da documento"
    }


@router.post("/link-to-existing")
def link_document_to_existing_soggetto(
    job_uuid: str = Form(...),
    soggetto_id: int = Form(...),
    db: Session = Depends(get_db),
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("soggetto.edit"))
):
    """
    Link document from parsing job to existing SoggettoAnagrafico.

    Use Case:
        User uploads identity document, parsing completes, similarity matching
        finds existing anagrafica → user chooses to add document to existing
        record instead of creating new one.

    Workflow:
        1. Load DocumentJob and verify ownership/status
        2. Verify SoggettoAnagrafico exists
        3. Move file from temp to permanent storage
        4. Create Documento record linked to soggetto
        5. Update job.entity_id to link to soggetto
        6. Complete Scadenza notification

    Args:
        job_uuid: DocumentJob UUID
        soggetto_id: Existing SoggettoAnagrafico ID to link document to
        db: Database session (injected)
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)

    Returns:
        {
            "soggetto_id": 45,
            "documento": {...},
            "message": "Documento aggiunto all'anagrafica esistente"
        }

    Raises:
        400: Missing tenant or invalid data
        403: User doesn't own the job
        404: Job or Soggetto not found
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    # Ensure tenant search_path
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))

    logger.info(
        f"[AnagraficaFromDoc][LinkExisting] User {current_user.id} linking job {job_uuid} "
        f"to soggetto {soggetto_id}"
    )

    DocumentService(db, tenant_schema=tenant_schema).ensure_documenti_table()

    # 1. Load and validate DocumentJob
    parsing_service = DocumentParsingService(db, tenant_schema)
    job = parsing_service.get_job_or_404(job_uuid)

    # Verify ownership
    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Non hai accesso a questo job"
        )

    # Verify status
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Job non completato. Status attuale: {job.status.value}"
        )

    # Verify not already linked
    if job.entity_id is not None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Questo documento è già stato utilizzato"
        )

    # 2. Verify SoggettoAnagrafico exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not soggetto:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Soggetto #{soggetto_id} non trovato"
        )

    # 3. Move file from temp to permanent storage
    try:
        new_file_path = file_storage.move_from_temp(
            temp_relative_path=job.file_path,
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=soggetto.id,
            tenant_schema=tenant_schema
        )

        logger.info(
            f"[AnagraficaFromDoc][LinkExisting] Moved file from temp to permanent: {new_file_path}"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"[AnagraficaFromDoc][LinkExisting] Failed to move file: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore spostamento file: {str(e)}"
        )

    # 4. Create Documento record
    try:
        # Get TipoDocumento for the document type
        document_type_code = job.document_type_key.split('.')[-1]  # Extract CODE from module.CODE
        tipo_doc = db.query(TipoDocumento).filter(
            TipoDocumento.codice == document_type_code
        ).first()

        documento = Documento(
            entity_type="SOGGETTO_ANAGRAFICO",
            entity_id=soggetto.id,
            tipo_documento=document_type_code,
            tipo_documento_id=tipo_doc.id if tipo_doc else None,
            nome_file=job.original_filename,
            file_path=new_file_path,
            mime_type=job.mime_type,
            dimensione=file_storage.get_file_size(new_file_path, tenant_schema),
            descrizione=f"Documento d'identità (parsing automatico, confidence {job.confidence_score}%)",
            note=f"Aggiunto da documento parsato"
        )

        db.add(documento)
        db.flush()

        logger.info(f"[AnagraficaFromDoc][LinkExisting] Created documento #{documento.id}")

    except Exception as e:
        db.rollback()
        logger.error(f"[AnagraficaFromDoc][LinkExisting] Failed to create documento: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore creazione documento: {str(e)}"
        )

    # 5. Update DocumentJob to link to soggetto
    job.entity_type = "SOGGETTO_ANAGRAFICO"
    job.entity_id = soggetto.id

    # 6. Complete Scadenza notification
    if job.scadenza_id:
        try:
            from app.core.platform.models import Scadenza
            scadenza = db.query(Scadenza).filter(Scadenza.id == job.scadenza_id).first()
            if scadenza and scadenza.stato == StatoScadenza.ATTIVA:
                scadenza.stato = StatoScadenza.COMPLETATA
                scadenza.completato_da = current_user.id
                scadenza.completato_il = datetime.utcnow()
                logger.info(f"[AnagraficaFromDoc][LinkExisting] Completed scadenza #{scadenza.id}")
        except Exception as e:
            logger.warning(f"[AnagraficaFromDoc][LinkExisting] Failed to complete scadenza: {e}")

    # Commit all changes
    db.commit()
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))
    db.refresh(documento)

    logger.info(
        f"[AnagraficaFromDoc][LinkExisting] ✓ Completed: "
        f"job={job.job_uuid}, soggetto={soggetto.id}, documento={documento.id}"
    )

    return {
        "soggetto_id": soggetto.id,
        "documento": {
            "id": documento.id,
            "nome_file": documento.nome_file,
            "tipo_documento": documento.tipo_documento,
            "dimensione": documento.dimensione,
            "created_at": documento.created_at.isoformat() if documento.created_at else None
        },
        "message": "Documento aggiunto all'anagrafica esistente con successo"
    }
