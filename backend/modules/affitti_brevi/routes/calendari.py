"""
Calendari iCal Routes - API endpoints for calendar configuration management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import CalendarioIcal
from ..schemas.calendario_ical import CalendarioIcalCreate, CalendarioIcalUpdate, CalendarioIcalResponse

router = APIRouter(prefix="/calendari", tags=["Calendari iCal"])


@router.get("/", response_model=List[CalendarioIcalResponse])
def get_calendari(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutti i calendari iCal configurati"""
    calendari = db.query(CalendarioIcal).offset(skip).limit(limit).all()
    return calendari


@router.get("/immobile/{immobile_id}", response_model=List[CalendarioIcalResponse])
def get_calendari_by_immobile(immobile_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti i calendari configurati per uno specifico immobile"""
    calendari = db.query(CalendarioIcal).filter(
        CalendarioIcal.unita_immobiliare_id == immobile_id
    ).all()
    return calendari


@router.get("/{calendario_id}", response_model=CalendarioIcalResponse)
def get_calendario(calendario_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un calendario iCal specifico"""
    calendario = db.query(CalendarioIcal).filter(CalendarioIcal.id == calendario_id).first()
    if not calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )
    return calendario


@router.post("/", response_model=CalendarioIcalResponse, status_code=status.HTTP_201_CREATED)
def create_calendario(calendario: CalendarioIcalCreate, db: Session = Depends(get_db)):
    """Crea una nuova configurazione calendario iCal"""
    # Check if calendar already exists for this property/channel combination
    existing = db.query(CalendarioIcal).filter(
        CalendarioIcal.unita_immobiliare_id == calendario.unita_immobiliare_id,
        CalendarioIcal.canale_id == calendario.canale_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calendario già configurato per questo immobile e questo canale"
        )

    new_calendario = CalendarioIcal(**calendario.model_dump())
    db.add(new_calendario)
    db.commit()
    db.refresh(new_calendario)
    return new_calendario


@router.put("/{calendario_id}", response_model=CalendarioIcalResponse)
def update_calendario(calendario_id: int, calendario: CalendarioIcalUpdate, db: Session = Depends(get_db)):
    """Aggiorna una configurazione calendario iCal esistente"""
    db_calendario = db.query(CalendarioIcal).filter(CalendarioIcal.id == calendario_id).first()
    if not db_calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    update_data = calendario.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_calendario, field, value)

    db.commit()
    db.refresh(db_calendario)
    return db_calendario


@router.delete("/{calendario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendario(calendario_id: int, db: Session = Depends(get_db)):
    """Elimina una configurazione calendario iCal"""
    db_calendario = db.query(CalendarioIcal).filter(CalendarioIcal.id == calendario_id).first()
    if not db_calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    db.delete(db_calendario)
    db.commit()
    return None
