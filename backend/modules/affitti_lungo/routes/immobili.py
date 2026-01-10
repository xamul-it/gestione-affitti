from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from ..models import UnitaImmobiliare
from ..schemas.immobili import UnitaImmobiliareCreate, UnitaImmobiliareUpdate, UnitaImmobiliareResponse

router = APIRouter(prefix="/unita-immobiliari", tags=["Unità Immobiliari"])


@router.get("/", response_model=List[UnitaImmobiliareResponse])
def get_unita_immobiliari(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutte le unità immobiliari"""
    unita_immobiliari = db.query(UnitaImmobiliare)\
        .options(joinedload(UnitaImmobiliare.categoria_catastale))\
        .offset(skip).limit(limit).all()
    return unita_immobiliari


@router.get("/{unita_immobiliare_id}", response_model=UnitaImmobiliareResponse)
def get_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un'unità immobiliare specifica"""
    unita_immobiliare = db.query(UnitaImmobiliare)\
        .options(joinedload(UnitaImmobiliare.categoria_catastale))\
        .filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not unita_immobiliare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {unita_immobiliare_id} non trovato"
        )
    return unita_immobiliare


@router.post("/", response_model=UnitaImmobiliareResponse, status_code=status.HTTP_201_CREATED)
def create_unita_immobiliare(unita_immobiliare: UnitaImmobiliareCreate, db: Session = Depends(get_db)):
    """Crea una nuova unità immobiliare"""
    db_unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.codice == unita_immobiliare.codice).first()
    if db_unita:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unità immobiliare con codice {unita_immobiliare.codice} già esistente"
        )

    new_unita = UnitaImmobiliare(**unita_immobiliare.model_dump())
    db.add(new_unita)
    db.commit()
    db.refresh(new_unita)
    return new_unita


@router.put("/{unita_immobiliare_id}", response_model=UnitaImmobiliareResponse)
def update_unita_immobiliare(unita_immobiliare_id: int, unita_immobiliare: UnitaImmobiliareUpdate, db: Session = Depends(get_db)):
    """Aggiorna un'unità immobiliare esistente"""
    db_unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not db_unita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {unita_immobiliare_id} non trovato"
        )

    update_data = unita_immobiliare.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_unita, field, value)

    db.commit()
    db.refresh(db_unita)
    return db_unita


@router.delete("/{unita_immobiliare_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Elimina un'unità immobiliare"""
    db_unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not db_unita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {unita_immobiliare_id} non trovato"
        )

    db.delete(db_unita)
    db.commit()
    return None
