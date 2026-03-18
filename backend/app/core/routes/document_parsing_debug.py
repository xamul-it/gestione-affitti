"""
Debug routes for document parsing service calls.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.core.auth.dependencies import require_permission
from app.core.platform.models import DocumentParsingLog, DocumentJob, JobStatus

router = APIRouter(prefix="/document-parsing/debug", tags=["document-parsing-debug"])


@router.get("/logs", response_model=List[Dict[str, Any]])
def list_parsing_logs(
    limit: int = Query(200, ge=1, le=500),
    job_uuid: Optional[str] = Query(None),
    tenant_schema: Optional[str] = Query(None),
    parsing_service: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("platform.admin")),
):
    """
    Return recent parsing service logs for debugging.
    """
    query = db.query(DocumentParsingLog)

    if job_uuid:
        query = query.filter(DocumentParsingLog.job_uuid == job_uuid)
    if tenant_schema:
        query = query.filter(DocumentParsingLog.tenant_schema == tenant_schema)
    if parsing_service:
        query = query.filter(DocumentParsingLog.parsing_service == parsing_service)
    if direction:
        query = query.filter(DocumentParsingLog.direction == direction)

    logs = query.order_by(DocumentParsingLog.created_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]


@router.get("/jobs", response_model=List[Dict[str, Any]])
def list_parsing_jobs(
    limit: int = Query(200, ge=1, le=500),
    job_uuid: Optional[str] = Query(None),
    tenant_schema: Optional[str] = Query(None),
    parsing_service: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    created_by: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("platform.admin")),
):
    """
    Return recent parsing jobs for debugging/monitoring.
    """
    query = db.query(DocumentJob)

    if job_uuid:
        query = query.filter(DocumentJob.job_uuid == job_uuid)
    if tenant_schema:
        query = query.filter(DocumentJob.tenant_schema == tenant_schema)
    if parsing_service:
        query = query.filter(DocumentJob.parsing_service == parsing_service)
    if created_by:
        query = query.filter(DocumentJob.created_by == created_by)
    if status:
        try:
            status_enum = JobStatus[status.upper()]
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"Status non valido: {status}") from exc
        query = query.filter(DocumentJob.status == status_enum)

    jobs = query.order_by(DocumentJob.created_at.desc()).limit(limit).all()
    return [job.to_dict() for job in jobs]
