"""
Ospiti Routes - API endpoints for guest management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import OspitePrenotazione
from ..schemas.ospite_prenotazione import OspitePrenotazioneCreate, OspitePrenotazioneUpdate, OspitePrenotazioneResponse

router = APIRouter(prefix="/ospiti", tags=["Ospiti"])


@router.get("/", response_model=List[OspitePrenotazioneResponse])
def get_ospiti(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutti gli ospiti"""
    ospiti = db.query(OspitePrenotazione).offset(skip).limit(limit).all()
    return ospiti


@router.get("/prenotazione/{prenotazione_id}", response_model=List[OspitePrenotazioneResponse])
def get_ospiti_by_prenotazione(prenotazione_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti gli ospiti di una specifica prenotazione"""
    ospiti = db.query(OspitePrenotazione).filter(
        OspitePrenotazione.prenotazione_id == prenotazione_id
    ).all()
    return ospiti


@router.get("/{ospite_id}", response_model=OspitePrenotazioneResponse)
def get_ospite(ospite_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un ospite specifico"""
    ospite = db.query(OspitePrenotazione).filter(OspitePrenotazione.id == ospite_id).first()
    if not ospite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ospite con ID {ospite_id} non trovato"
        )
    return ospite


@router.post("/", response_model=OspitePrenotazioneResponse, status_code=status.HTTP_201_CREATED)
def create_ospite(ospite: OspitePrenotazioneCreate, db: Session = Depends(get_db)):
    """Collega un ospite ad una prenotazione"""
    # Check if guest is already linked to this booking
    existing = db.query(OspitePrenotazione).filter(
        OspitePrenotazione.prenotazione_id == ospite.prenotazione_id,
        OspitePrenotazione.soggetto_anagrafico_id == ospite.soggetto_anagrafico_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questo ospite è già collegato a questa prenotazione"
        )

    new_ospite = OspitePrenotazione(**ospite.model_dump())
    db.add(new_ospite)
    db.commit()
    db.refresh(new_ospite)
    return new_ospite


@router.put("/{ospite_id}", response_model=OspitePrenotazioneResponse)
def update_ospite(ospite_id: int, ospite: OspitePrenotazioneUpdate, db: Session = Depends(get_db)):
    """Aggiorna i dati di un ospite"""
    db_ospite = db.query(OspitePrenotazione).filter(OspitePrenotazione.id == ospite_id).first()
    if not db_ospite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ospite con ID {ospite_id} non trovato"
        )

    update_data = ospite.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ospite, field, value)

    db.commit()
    db.refresh(db_ospite)
    return db_ospite


@router.delete("/{ospite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ospite(ospite_id: int, db: Session = Depends(get_db)):
    """Rimuovi un ospite da una prenotazione"""
    db_ospite = db.query(OspitePrenotazione).filter(OspitePrenotazione.id == ospite_id).first()
    if not db_ospite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ospite con ID {ospite_id} non trovato"
        )

    db.delete(db_ospite)
    db.commit()
    return None
