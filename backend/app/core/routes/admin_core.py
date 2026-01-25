"""
Admin routes for core maintenance.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import require_permission
from app.core.services.tenant_service import TenantService

router = APIRouter(prefix="/admin/core", tags=["Admin - Core"])


@router.post("/cleanup")
def cleanup_non_core_tables(
    schema_name: str = "public",
    force: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("platform.admin")),
):
    """
    Drop all non-core tables in a schema (default: public).
    """
    try:
        terminated = TenantService.terminate_db_connections(db) if force else 0
        dropped = TenantService.clear_non_core_tables(db, schema_name=schema_name, force=force)
        return {
            "status": "cleared",
            "schema": schema_name,
            "terminated_connections": terminated,
            "tables_dropped": dropped,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
