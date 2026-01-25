"""
Canali Routes - API endpoints for booking channel management

Manages:
- Booking platforms (Airbnb, Booking.com, etc.)
- Visual representation in calendar (colors, symbols)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from ..models import Canale
from ..schemas.canale import (
    CanaleCreate,
    CanaleUpdate,
    CanaleResponse,
    CanaleListResponse,
)

router = APIRouter(prefix="/canali", tags=["Canali"])


@router.get("/", response_model=CanaleListResponse)
def get_canali(
    skip: int = 0,
    limit: int = 100,
    attivo: bool = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all booking channels.

    Returns channels with their visual properties for calendar display.
    """
    query = db.query(Canale)

    if attivo is not None:
        query = query.filter(Canale.attivo == attivo)

    totale = query.count()
    canali = query.order_by(Canale.ordine, Canale.nome).offset(skip).limit(limit).all()

    return CanaleListResponse(
        canali=canali,
        totale=totale,
        skip=skip,
        limit=limit
    )


@router.get("/attivi", response_model=List[CanaleResponse])
def get_canali_attivi(db: Session = Depends(get_db)):
    """
    Get only active channels.

    Shortcut for filtering active channels in UI dropdowns.
    """
    canali = db.query(Canale).filter(
        Canale.attivo == True
    ).order_by(Canale.ordine, Canale.nome).all()

    return canali


@router.get("/legenda")
def get_canali_legenda(db: Session = Depends(get_db)):
    """
    Get channel legend for calendar display.

    Returns simplified list with visual properties only.
    Used by frontend to build calendar legend.
    """
    canali = db.query(Canale).filter(
        Canale.attivo == True
    ).order_by(Canale.ordine).all()

    return {
        "canali": [
            {
                "codice": c.codice,
                "nome": c.nome,
                "colore": c.colore,
                "simbolo": c.simbolo
            }
            for c in canali
        ]
    }


@router.get("/{canale_id}", response_model=CanaleResponse)
def get_canale(canale_id: int, db: Session = Depends(get_db)):
    """Get channel details by ID."""
    canale = db.query(Canale).filter(Canale.id == canale_id).first()
    if not canale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canale con ID {canale_id} non trovato"
        )
    return canale


@router.get("/codice/{codice}", response_model=CanaleResponse)
def get_canale_by_codice(codice: str, db: Session = Depends(get_db)):
    """Get channel details by code."""
    canale = db.query(Canale).filter(Canale.codice == codice.upper()).first()
    if not canale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canale con codice '{codice}' non trovato"
        )
    return canale


@router.post("/", response_model=CanaleResponse, status_code=status.HTTP_201_CREATED)
def create_canale(canale: CanaleCreate, db: Session = Depends(get_db)):
    """
    Create a new booking channel.

    Required fields:
    - codice: Unique identifier (uppercase, e.g., AIRBNB, BOOKING_COM)
    - nome: Display name

    Optional visual properties:
    - colore: Hex color code (e.g., #FF5A5F for Airbnb red)
    - simbolo: Single character symbol for calendar (e.g., A, B)
    """
    # Check for duplicate codice
    existing = db.query(Canale).filter(Canale.codice == canale.codice.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Canale con codice '{canale.codice}' già esistente"
        )

    # Convert codice to uppercase
    canale_dict = canale.model_dump()
    canale_dict['codice'] = canale_dict['codice'].upper()

    new_canale = Canale(**canale_dict)
    db.add(new_canale)
    db.commit()
    db.refresh(new_canale)
    return new_canale


@router.put("/{canale_id}", response_model=CanaleResponse)
def update_canale(
    canale_id: int,
    canale: CanaleUpdate,
    db: Session = Depends(get_db)
):
    """Update channel properties."""
    db_canale = db.query(Canale).filter(Canale.id == canale_id).first()
    if not db_canale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canale con ID {canale_id} non trovato"
        )

    update_data = canale.model_dump(exclude_unset=True)

    # Convert codice to uppercase if provided
    if 'codice' in update_data:
        update_data['codice'] = update_data['codice'].upper()
        # Check for duplicate
        existing = db.query(Canale).filter(
            Canale.codice == update_data['codice'],
            Canale.id != canale_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Canale con codice '{update_data['codice']}' già esistente"
            )

    for field, value in update_data.items():
        setattr(db_canale, field, value)

    db.commit()
    db.refresh(db_canale)
    return db_canale


@router.delete("/{canale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_canale(canale_id: int, db: Session = Depends(get_db)):
    """
    Delete a channel.

    Note: Cannot delete channels that have associated calendars or bookings.
    """
    db_canale = db.query(Canale).filter(Canale.id == canale_id).first()
    if not db_canale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canale con ID {canale_id} non trovato"
        )

    # Check for associated data
    if db_canale.calendari and len(db_canale.calendari) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare: il canale ha calendari associati"
        )

    db.delete(db_canale)
    db.commit()
    return None


@router.post("/{canale_id}/attiva", response_model=CanaleResponse)
def attiva_canale(canale_id: int, db: Session = Depends(get_db)):
    """Activate a channel."""
    db_canale = db.query(Canale).filter(Canale.id == canale_id).first()
    if not db_canale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canale con ID {canale_id} non trovato"
        )

    db_canale.attivo = True
    db.commit()
    db.refresh(db_canale)
    return db_canale


@router.post("/{canale_id}/disattiva", response_model=CanaleResponse)
def disattiva_canale(canale_id: int, db: Session = Depends(get_db)):
    """Deactivate a channel."""
    db_canale = db.query(Canale).filter(Canale.id == canale_id).first()
    if not db_canale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canale con ID {canale_id} non trovato"
        )

    db_canale.attivo = False
    db.commit()
    db.refresh(db_canale)
    return db_canale
