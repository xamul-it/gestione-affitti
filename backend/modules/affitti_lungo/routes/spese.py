from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import Spesa
from ..schemas.spese import SpesaCreate, SpesaUpdate, SpesaResponse

router = APIRouter(prefix="/spese", tags=["Spese"])


@router.get("/", response_model=List[SpesaResponse])
def get_spese(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutte le spese"""
    spese = db.query(Spesa).offset(skip).limit(limit).all()
    return spese


@router.get("/{spesa_id}", response_model=SpesaResponse)
def get_spesa(spesa_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una spesa specifica"""
    spesa = db.query(Spesa).filter(Spesa.id == spesa_id).first()
    if not spesa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spesa con ID {spesa_id} non trovata"
        )
    return spesa


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[SpesaResponse])
def get_spese_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni tutte le spese di un'unità immobiliare"""
    spese = db.query(Spesa).filter(Spesa.unita_immobiliare_id == unita_immobiliare_id).all()
    return spese


@router.post("/", response_model=SpesaResponse, status_code=status.HTTP_201_CREATED)
def create_spesa(spesa: SpesaCreate, db: Session = Depends(get_db)):
    """Crea una nuova spesa"""
    new_spesa = Spesa(**spesa.model_dump())
    db.add(new_spesa)
    db.commit()
    db.refresh(new_spesa)
    return new_spesa


@router.put("/{spesa_id}", response_model=SpesaResponse)
def update_spesa(spesa_id: int, spesa: SpesaUpdate, db: Session = Depends(get_db)):
    """Aggiorna una spesa esistente"""
    db_spesa = db.query(Spesa).filter(Spesa.id == spesa_id).first()
    if not db_spesa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spesa con ID {spesa_id} non trovata"
        )

    update_data = spesa.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_spesa, field, value)

    db.commit()
    db.refresh(db_spesa)
    return db_spesa


@router.delete("/{spesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spesa(spesa_id: int, db: Session = Depends(get_db)):
    """Elimina una spesa"""
    db_spesa = db.query(Spesa).filter(Spesa.id == spesa_id).first()
    if not db_spesa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spesa con ID {spesa_id} non trovata"
        )

    db.delete(db_spesa)
    db.commit()
    return None
