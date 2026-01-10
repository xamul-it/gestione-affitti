"""
Scadenze API Routes - Universal Deadline/Reminder System

RESTful API endpoints for managing scadenze (deadlines and reminders).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform_services import ScadenzaService
from app.core.schemas import (
    ScadenzaCreate,
    ScadenzaTODOCreate,
    ScadenzaUpdate,
    ScadenzaResponse,
    ScadenzaListFilters,
    ScadenzaBadgeResponse,
    ScadenzaCompletaRequest,
    ScadenzaPosticipaRequest,
    ScadenzaLogResponse,
    PrioritaScadenza,
    StatoScadenza
)


router = APIRouter(prefix="/scadenze", tags=["Scadenze"])


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================

@router.post("/", response_model=ScadenzaResponse, status_code=201)
def create_scadenza(
    data: ScadenzaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new scadenza (deadline/reminder).

    Can be attached to an entity (modulo, entity_type, entity_id) or standalone (TODO).
    """
    service = ScadenzaService(db)
    scadenza = service.create_scadenza(data, current_user.id)
    return scadenza


@router.post("/todo", response_model=ScadenzaResponse, status_code=201)
def create_todo(
    data: ScadenzaTODOCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a standalone TODO (entity-less reminder).

    Simplified endpoint for creating quick reminders not attached to any entity.
    """
    service = ScadenzaService(db)
    scadenza = service.create_todo(data, current_user.id)
    return scadenza


@router.get("/{scadenza_id}", response_model=ScadenzaResponse)
def get_scadenza(
    scadenza_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific scadenza by ID.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check visibility (creator or recipient)
    is_visible = (
        scadenza.creato_da == current_user.id or
        any(dest.user_id == current_user.id for dest in scadenza.destinatari)
    )

    if not is_visible and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    return scadenza


@router.get("/", response_model=List[ScadenzaResponse])
def list_scadenze(
    modulo: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    stato: Optional[StatoScadenza] = Query(None),
    priorita: Optional[PrioritaScadenza] = Query(None),
    solo_todo: Optional[bool] = Query(None),
    solo_scadute: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List scadenze with filters.

    Returns scadenze visible to current user (created by or recipient).
    """
    filters = ScadenzaListFilters(
        modulo=modulo,
        entity_type=entity_type,
        entity_id=entity_id,
        stato=stato,
        priorita=priorita,
        solo_todo=solo_todo,
        solo_scadute=solo_scadute
    )

    service = ScadenzaService(db)

    # Filter by user visibility
    scadenze = service.list_scadenze(
        filters=filters,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    return scadenze


@router.put("/{scadenza_id}", response_model=ScadenzaResponse)
def update_scadenza(
    scadenza_id: int,
    data: ScadenzaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a scadenza.

    Only creator or superuser can update.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check permissions
    if scadenza.creato_da != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo il creatore può modificare")

    updated = service.update_scadenza(scadenza_id, data, current_user.id)
    return updated


@router.delete("/{scadenza_id}", status_code=204)
def delete_scadenza(
    scadenza_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete (soft delete) a scadenza.

    Only creator or superuser can delete.
    Sets stato to CANCELLATA.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check permissions
    if scadenza.creato_da != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo il creatore può cancellare")

    service.delete_scadenza(scadenza_id, current_user.id)
    return None


# =============================================================================
# STATE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/{scadenza_id}/completa", response_model=ScadenzaResponse)
def completa_scadenza(
    scadenza_id: int,
    request: ScadenzaCompletaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark scadenza as completed.

    Any user with visibility can complete a scadenza.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check visibility
    is_visible = (
        scadenza.creato_da == current_user.id or
        any(dest.user_id == current_user.id for dest in scadenza.destinatari)
    )

    if not is_visible and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    completed = service.completa_scadenza(
        scadenza_id,
        current_user.id,
        request.note
    )

    return completed


@router.post("/{scadenza_id}/posticipa", response_model=ScadenzaResponse)
def posticipa_scadenza(
    scadenza_id: int,
    request: ScadenzaPosticipaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Postpone scadenza to a new date.

    Only creator or superuser can postpone.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check permissions
    if scadenza.creato_da != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo il creatore può posticipare")

    postponed = service.posticipa_scadenza(
        scadenza_id,
        request.nuova_data,
        current_user.id,
        request.note
    )

    return postponed


@router.post("/{scadenza_id}/riattiva", response_model=ScadenzaResponse)
def riattiva_scadenza(
    scadenza_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reactivate a completed or cancelled scadenza.

    Only creator or superuser can reactivate.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check permissions
    if scadenza.creato_da != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Solo il creatore può riattivare")

    reactivated = service.riattiva_scadenza(scadenza_id, current_user.id)
    return reactivated


# =============================================================================
# QUERY ENDPOINTS
# =============================================================================

@router.get("/entity/{modulo}/{entity_type}/{entity_id}", response_model=List[ScadenzaResponse])
def get_scadenze_by_entity(
    modulo: str,
    entity_type: str,
    entity_id: int,
    include_completed: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all scadenze for a specific entity.

    Useful for displaying scadenze in entity detail pages.
    """
    service = ScadenzaService(db)
    scadenze = service.get_scadenze_by_entity(
        modulo=modulo,
        entity_type=entity_type,
        entity_id=entity_id,
        include_completed=include_completed
    )

    return scadenze


@router.get("/my/scadenze", response_model=List[ScadenzaResponse])
def get_my_scadenze(
    include_completed: bool = Query(False),
    only_overdue: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all scadenze visible to current user.

    Includes scadenze created by user or where user is recipient.
    """
    service = ScadenzaService(db)
    scadenze = service.get_my_scadenze(
        user_id=current_user.id,
        include_completed=include_completed,
        only_overdue=only_overdue
    )

    return scadenze


# =============================================================================
# STATISTICS & BADGE ENDPOINTS
# =============================================================================

@router.get("/badge/info", response_model=ScadenzaBadgeResponse)
def get_badge_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get badge info for UI display (counts and color).

    Used by frontend to show badge indicator with counts.
    """
    service = ScadenzaService(db)
    badge = service.get_badge_info(user_id=current_user.id)
    return badge


@router.get("/statistics/summary")
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed statistics for current user.

    Returns counts broken down by stato, priorita, etc.
    """
    service = ScadenzaService(db)
    stats = service.get_statistics(user_id=current_user.id)
    return stats


# =============================================================================
# AUDIT LOG ENDPOINTS
# =============================================================================

@router.get("/{scadenza_id}/logs", response_model=List[ScadenzaLogResponse])
def get_scadenza_logs(
    scadenza_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit log for a scadenza.

    Shows all changes and actions performed on the scadenza.
    """
    service = ScadenzaService(db)
    scadenza = service.get_scadenza(scadenza_id)

    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    # Check visibility
    is_visible = (
        scadenza.creato_da == current_user.id or
        any(dest.user_id == current_user.id for dest in scadenza.destinatari)
    )

    if not is_visible and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    logs = service.get_logs(scadenza_id)
    return logs
