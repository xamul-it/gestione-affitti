"""
API routes for document parsing orchestration.

Endpoints:
- POST /document-parsing/upload-and-parse: Upload document and start parsing
- GET /document-parsing/status/{job_uuid}: Check job status
- POST /document-parsing/callback/{job_uuid}: Callback from parsing service (no auth)
- GET /document-parsing/my-jobs: Get user's parsing jobs
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status as http_status
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform.models import JobStatus
from app.core.platform_services import DocumentParsingService

router = APIRouter(prefix="/document-parsing", tags=["document-parsing"])
logger = logging.getLogger(__name__)


@router.post("/upload-and-parse")
async def upload_and_parse_document(
    file: UploadFile = File(...),
    document_type_key: str = Form(...),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[int] = Form(None),
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload document and initiate asynchronous parsing.

    Workflow:
        1. Upload document to temp storage
        2. Create DocumentJob record
        3. Submit to parsing service
        4. Return job_uuid for status polling

    Args:
        file: Document file to parse
        document_type_key: Full document type key (e.g., "anagrafica_italiana.CARTA_IDENTITA")
        entity_type: Optional target entity type
        entity_id: Optional target entity ID
        tenant_schema: Tenant schema (injected)
        current_user: Current authenticated user (injected)
        db: Database session (injected)

    Returns:
        {
            "job_uuid": "...",
            "status": "QUEUED",
            "polling_url": "/api/v1/document-parsing/status/{job_uuid}",
            "message": "Documento in elaborazione..."
        }

    Raises:
        400: Invalid document type or missing tenant
        500: Upload or submission failure
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    logger.info(
        f"[DocumentParsing][Upload] User {current_user.id} uploading {file.filename} "
        f"for {document_type_key} in tenant {tenant_schema}"
    )

    parsing_service_override = None
    parsing_config_override = None
    callback_url_override = None
    if document_type_key.startswith("anagrafica_italiana."):
        document_code = document_type_key.split(".", 1)[1]
        try:
            from anagrafica_italiana.models import TipoDocumento
            tipo_doc = db.query(TipoDocumento).filter(
                TipoDocumento.codice == document_code
            ).first()
            if tipo_doc:
                parsing_service_override = tipo_doc.parsing_service
                parsing_config_override = tipo_doc.parsing_config
                callback_url_override = tipo_doc.parsing_callback_url
        except Exception:
            logger.debug(
                "[DocumentParsing][Upload] Unable to load TipoDocumento overrides for %s",
                document_type_key
            )

    # Create service and upload
    service = DocumentParsingService(db, tenant_schema)

    try:
        job = service.upload_and_parse(
            file=file,
            document_type_key=document_type_key,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=current_user.id,
            parsing_service_override=parsing_service_override,
            parsing_config_override=parsing_config_override,
            callback_url_override=callback_url_override,
        )

        return {
            "job_uuid": job.job_uuid,
            "status": job.status.value,
            "polling_url": f"/api/v1/document-parsing/status/{job.job_uuid}",
            "message": "Documento in elaborazione. Riceverai una notifica al completamento.",
            "document_type": document_type_key,
            "original_filename": job.original_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[DocumentParsing][Upload] Failed for user {current_user.id}, "
            f"file {file.filename}, type {document_type_key}"
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'upload: {str(e)}"
        )


@router.get("/status/{job_uuid}")
def get_parsing_status(
    job_uuid: str,
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check status of a parsing job.

    Args:
        job_uuid: Job UUID
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)
        db: Database session (injected)

    Returns:
        Full job details including parsing_result if completed

    Raises:
        404: Job not found
        403: User doesn't own the job
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    service = DocumentParsingService(db, tenant_schema)
    job = service.get_job_or_404(job_uuid)

    # Verify ownership
    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Non hai accesso a questo job"
        )

    return job.to_dict()


@router.post("/callback/{job_uuid}")
async def parsing_callback(
    job_uuid: str,
    callback_data: dict,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint for external parsing services.

    IMPORTANT: This endpoint does NOT require user authentication.
    It's called by external services (MRZ service, OCR service, etc.).

    Expected payload:
    {
        "job_id": "uuid",
        "status": "finished" | "failed",
        "result": {...} | null,
        "error": "..." | null
    }

    Args:
        job_uuid: Job UUID from URL path
        callback_data: Callback payload from service
        db: Database session (injected)

    Returns:
        {"message": "Callback processed", "job_status": "..."}

    Raises:
        404: Job not found

    Security Notes:
        - TODO: Add HMAC signature validation
        - TODO: Add IP whitelist for parsing services
    """
    logger.info(f"[DocumentParsing][Callback] Received callback for job {job_uuid}")
    logger.debug(f"[DocumentParsing][Callback] Payload: {callback_data}")

    # Import DocumentJob here to avoid circular import
    from app.core.platform.models import DocumentJob

    # Validate job exists (tenant validation happens in service)
    job = db.query(DocumentJob).filter(
        DocumentJob.job_uuid == job_uuid
    ).first()

    if not job:
        logger.error(f"[DocumentParsing][Callback] Job not found: {job_uuid}")
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job non trovato: {job_uuid}"
        )

    # Use service to handle callback
    service = DocumentParsingService(db, job.tenant_schema)

    try:
        updated_job = service.handle_callback(job_uuid, callback_data)

        return {
            "message": "Callback processed successfully",
            "job_status": updated_job.status.value,
            "job_uuid": updated_job.job_uuid
        }

    except Exception as e:
        logger.exception(f"[DocumentParsing][Callback] Error processing callback for job {job_uuid}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore elaborazione callback: {str(e)}"
        )


@router.get("/my-jobs")
def get_my_parsing_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all parsing jobs created by current user.

    Args:
        status: Optional status filter (PENDING, QUEUED, COMPLETED, etc.)
        limit: Max results (default 50)
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)
        db: Database session (injected)

    Returns:
        List of jobs with metadata

    Raises:
        400: Invalid status or missing tenant
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = JobStatus[status.upper()]
        except KeyError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Status non valido: {status}. Valori: {[s.value for s in JobStatus]}"
            )

    service = DocumentParsingService(db, tenant_schema)
    jobs = service.get_user_jobs(
        user_id=current_user.id,
        status_filter=status_filter,
        limit=limit
    )

    return [job.to_dict() for job in jobs]


@router.get("/pending-documents")
def get_pending_documents(
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get completed jobs pending user action (not yet linked to entity).

    Used in "create from document" workflow.

    Args:
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)
        db: Database session (injected)

    Returns:
        List of completed jobs with status=COMPLETED and entity_id=NULL

    Raises:
        400: Missing tenant
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    service = DocumentParsingService(db, tenant_schema)
    jobs = service.get_pending_documents(user_id=current_user.id)

    return [job.to_dict() for job in jobs]


@router.get("/job/{job_id}")
def get_job_by_id(
    job_id: int,
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get parsing job by numeric ID (for scadenza resolution).
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    service = DocumentParsingService(db, tenant_schema)
    job = service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Job non trovato: {job_id}"
        )

    if job.created_by != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Non hai accesso a questo job"
        )

    return job.to_dict()


@router.get("/entity-jobs")
def get_entity_jobs(
    entity_type: str,
    entity_id: int,
    status: Optional[str] = None,
    pending_only: bool = True,
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get parsing jobs for a specific entity.

    Args:
        entity_type: Target entity type
        entity_id: Target entity ID
        status: Optional status filter
        pending_only: If True, only jobs with active scadenza are returned
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)
        db: Database session (injected)

    Returns:
        List of jobs for the entity
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    status_filter = None
    if status:
        try:
            status_filter = JobStatus[status.upper()]
        except KeyError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Status non valido: {status}. Valori: {[s.value for s in JobStatus]}"
            )

    service = DocumentParsingService(db, tenant_schema)
    jobs = service.get_entity_jobs(
        entity_type=entity_type,
        entity_id=entity_id,
        status_filter=status_filter,
        created_by=current_user.id,
        pending_only=pending_only,
    )

    return [job.to_dict() for job in jobs]
