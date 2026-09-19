"""
Notifiche API Routes - Generic Core Notification Service

Every endpoint operates only on the authenticated user's own notifications
— user_id always comes from the token, never from a query/path parameter.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.auth.models import User
from app.core.platform_services import NotificationService
from app.core.schemas import NotificaResponse, NotificaBadgeResponse, SegnaTutteLetteResponse


router = APIRouter(prefix="/notifiche", tags=["Notifiche"])


@router.get("/", response_model=List[NotificaResponse])
def list_notifiche(
    solo_non_lette: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's notifications, most recent first."""
    service = NotificationService(db)
    return service.list_for_user(current_user.id, solo_non_lette=solo_non_lette, skip=skip, limit=limit)


@router.post("/{notifica_id}/segna-letta", response_model=NotificaResponse)
def segna_letta(
    notifica_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notifica = service.segna_letta(notifica_id, current_user.id)
    if not notifica:
        raise HTTPException(status_code=404, detail="Notifica non trovata")
    return notifica


@router.post("/segna-tutte-lette", response_model=SegnaTutteLetteResponse)
def segna_tutte_lette(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    count = service.segna_tutte_lette(current_user.id)
    return SegnaTutteLetteResponse(count=count)


@router.get("/badge", response_model=NotificaBadgeResponse)
def badge(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    return NotificaBadgeResponse(count_non_lette=service.badge_count(current_user.id))
