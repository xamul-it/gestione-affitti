"""
Admin routes for Comuni Italia management.

Provides endpoints for:
- Update comuni from external sources
- View update status
- Manual CAP lookup
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from pydantic import BaseModel
from typing import Optional, Literal

import sys, os

router = APIRouter(prefix="/admin/comuni", tags=["Admin - Comuni"])


class UpdateRequest(BaseModel):
    """Request body for update endpoint."""
    mode: Literal["incremental", "full"] = "incremental"
    force: bool = False


class UpdateResponse(BaseModel):
    """Response from update endpoint."""
    success: bool
    source: str
    mode: str
    total_fetched: int
    added: int
    updated: int
    skipped: int
    errors: int
    duration_sec: Optional[float] = None
    error_details: Optional[list] = None


@router.post("/update", response_model=UpdateResponse)
def update_comuni(
    request: UpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update comuni_italia table from GitHub repository.

    **Modes:**
    - `incremental` (default): Add only missing comuni
    - `full`: Delete all and re-import (requires force=true)

    **Example:**
    ```json
    POST /api/v1/admin/comuni/update
    {
        "mode": "incremental",
        "force": false
    }
    ```

    **Response:**
    ```json
    {
        "success": true,
        "source": "github",
        "total_fetched": 7904,
        "added": 7820,
        "skipped": 84,
        "errors": 0,
        "duration_sec": 3.2
    }
    ```

    **Warning:** Full sync with ~8,000 comuni takes ~10-15 seconds.
    """
    # Import ComuniUpdaterService lazily to avoid loading module models at startup
    modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)
    from immobili.services.comuni_updater_service import ComuniUpdaterService
    service = ComuniUpdaterService(db)

    # Safety check for full sync
    if request.mode == "full" and not request.force:
        raise HTTPException(
            status_code=400,
            detail="Full sync requires force=true to prevent accidental data loss"
        )

    result = service.update_from_github(
        mode=request.mode,
        force=request.force
    )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {result.get('error_details', 'Unknown error')}"
        )

    return result


@router.get("/status")
def get_comuni_status(db: Session = Depends(get_db)):
    """
    Get current database status and coverage.

    **Response:**
    ```json
    {
        "total_comuni": 7904,
        "total_regioni": 20,
        "total_province": 107,
        "missing_cap": 0,
        "coverage_percent": 100.0,
        "data_quality": {
            "complete": 7904,
            "incomplete": 0
        }
    }
    ```
    """
    service = ComuniUpdaterService(db)
    return service.get_update_status()


@router.get("/lookup-cap/{cap}")
def lookup_city_by_cap(cap: str, db: Session = Depends(get_db)):
    """
    Lookup city information by CAP (postal code).

    Uses external API (Zippopotam.us) for real-time validation.

    **Example:**
    ```
    GET /api/v1/admin/comuni/lookup-cap/20100
    ```

    **Response:**
    ```json
    {
        "nome": "Milano",
        "cap": "20100",
        "regione": "Lombardia",
        "latitudine": 45.4612,
        "longitudine": 9.1878
    }
    ```
    """
    service = ComuniUpdaterService(db)
    result = service.lookup_cap_from_api(cap)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"CAP {cap} not found"
        )

    return result
