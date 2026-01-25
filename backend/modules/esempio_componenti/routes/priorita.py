"""
PrioritaEsempio Routes - Domain Data API

Read-only endpoints for priorities (domain data in public schema).
Priorities are shared across all tenants.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..models import PrioritaEsempio
from ..schemas import PrioritaEsempioResponse

router = APIRouter(prefix="/priorita", tags=["Esempio - Priorità"])


@router.get("/", response_model=List[PrioritaEsempioResponse])
def list_priorita(
    skip: int = 0,
    limit: int = 100,
    solo_attive: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all priorities (domain data).

    Priorities are shared across all tenants and are read-only.
    Ordered by level (descending) so highest priority comes first.
    """
    query = db.query(PrioritaEsempio)

    if solo_attive:
        query = query.filter(PrioritaEsempio.attivo == True)

    query = query.order_by(PrioritaEsempio.livello.desc(), PrioritaEsempio.nome)

    return query.offset(skip).limit(limit).all()


@router.get("/{priorita_id}", response_model=PrioritaEsempioResponse)
def get_priorita(
    priorita_id: int,
    db: Session = Depends(get_db)
):
    """Get a single priority by ID."""
    priorita = db.query(PrioritaEsempio).filter(
        PrioritaEsempio.id == priorita_id
    ).first()

    if not priorita:
        raise HTTPException(status_code=404, detail="Priorità non trovata")

    return priorita
