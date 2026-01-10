"""
Prenotazioni Routes - API endpoints for booking management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from ..models import Prenotazione
from ..schemas.prenotazione import PrenotazioneCreate, PrenotazioneUpdate, PrenotazioneResponse

router = APIRouter(prefix="/prenotazioni", tags=["Prenotazioni"])


@router.get("/", response_model=List[PrenotazioneResponse])
def get_prenotazioni(
    skip: int = 0,
    limit: int = 100,
    immobile_id: Optional[int] = None,
    data_da: Optional[date] = None,
    data_a: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni lista di tutte le prenotazioni con filtri opzionali

    - **immobile_id**: Filtra per immobile specifico
    - **data_da**: Filtra prenotazioni con check-in >= data_da
    - **data_a**: Filtra prenotazioni con check-out <= data_a
    """
    query = db.query(Prenotazione)

    if immobile_id:
        query = query.filter(Prenotazione.unita_immobiliare_id == immobile_id)
    if data_da:
        query = query.filter(Prenotazione.data_checkout >= data_da)
    if data_a:
        query = query.filter(Prenotazione.data_checkin <= data_a)

    prenotazioni = query.offset(skip).limit(limit).all()
    return prenotazioni


@router.get("/immobile/{immobile_id}", response_model=List[PrenotazioneResponse])
def get_prenotazioni_by_immobile(immobile_id: int, db: Session = Depends(get_db)):
    """Ottieni tutte le prenotazioni per uno specifico immobile"""
    prenotazioni = db.query(Prenotazione).filter(
        Prenotazione.unita_immobiliare_id == immobile_id
    ).order_by(Prenotazione.data_checkin.desc()).all()
    return prenotazioni


@router.get("/{prenotazione_id}", response_model=PrenotazioneResponse)
def get_prenotazione(prenotazione_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una prenotazione specifica"""
    prenotazione = db.query(Prenotazione).filter(Prenotazione.id == prenotazione_id).first()
    if not prenotazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenotazione con ID {prenotazione_id} non trovata"
        )
    return prenotazione


@router.post("/", response_model=PrenotazioneResponse, status_code=status.HTTP_201_CREATED)
def create_prenotazione(prenotazione: PrenotazioneCreate, db: Session = Depends(get_db)):
    """Crea una nuova prenotazione"""
    # Check if booking code already exists for this platform
    existing = db.query(Prenotazione).filter(
        Prenotazione.codice_prenotazione == prenotazione.codice_prenotazione,
        Prenotazione.portale_origine == prenotazione.portale_origine
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prenotazione {prenotazione.codice_prenotazione} già esistente per {prenotazione.portale_origine.value}"
        )

    # Validate date range
    if prenotazione.data_checkout <= prenotazione.data_checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La data di checkout deve essere successiva alla data di checkin"
        )

    new_prenotazione = Prenotazione(**prenotazione.model_dump())
    db.add(new_prenotazione)
    db.commit()
    db.refresh(new_prenotazione)
    return new_prenotazione


@router.put("/{prenotazione_id}", response_model=PrenotazioneResponse)
def update_prenotazione(prenotazione_id: int, prenotazione: PrenotazioneUpdate, db: Session = Depends(get_db)):
    """Aggiorna una prenotazione esistente"""
    db_prenotazione = db.query(Prenotazione).filter(Prenotazione.id == prenotazione_id).first()
    if not db_prenotazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenotazione con ID {prenotazione_id} non trovata"
        )

    update_data = prenotazione.model_dump(exclude_unset=True)

    # Validate date range if dates are being updated
    data_checkin = update_data.get('data_checkin', db_prenotazione.data_checkin)
    data_checkout = update_data.get('data_checkout', db_prenotazione.data_checkout)

    if data_checkout <= data_checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La data di checkout deve essere successiva alla data di checkin"
        )

    for field, value in update_data.items():
        setattr(db_prenotazione, field, value)

    db.commit()
    db.refresh(db_prenotazione)
    return db_prenotazione


@router.delete("/{prenotazione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prenotazione(prenotazione_id: int, db: Session = Depends(get_db)):
    """Elimina una prenotazione"""
    db_prenotazione = db.query(Prenotazione).filter(Prenotazione.id == prenotazione_id).first()
    if not db_prenotazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenotazione con ID {prenotazione_id} non trovata"
        )

    db.delete(db_prenotazione)
    db.commit()
    return None
