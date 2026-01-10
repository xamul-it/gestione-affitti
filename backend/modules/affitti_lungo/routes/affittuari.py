from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import Affittuario
from ..schemas.affittuari import AffittuarioCreate, AffittuarioUpdate, AffittuarioResponse

router = APIRouter(prefix="/affittuari", tags=["Affittuari"])


@router.get("/", response_model=List[AffittuarioResponse])
def get_affittuari(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutti gli affittuari"""
    affittuari = db.query(Affittuario).offset(skip).limit(limit).all()
    return affittuari


@router.get("/{affittuario_id}", response_model=AffittuarioResponse)
def get_affittuario(affittuario_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un affittuario specifico"""
    affittuario = db.query(Affittuario).filter(Affittuario.id == affittuario_id).first()
    if not affittuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Affittuario con ID {affittuario_id} non trovato"
        )
    return affittuario


@router.post("/", response_model=AffittuarioResponse, status_code=status.HTTP_201_CREATED)
def create_affittuario(affittuario: AffittuarioCreate, db: Session = Depends(get_db)):
    """Crea un nuovo affittuario"""
    db_affittuario = db.query(Affittuario).filter(
        Affittuario.codice_fiscale == affittuario.codice_fiscale
    ).first()
    if db_affittuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Affittuario con codice fiscale {affittuario.codice_fiscale} già esistente"
        )

    new_affittuario = Affittuario(**affittuario.model_dump())
    db.add(new_affittuario)
    db.commit()
    db.refresh(new_affittuario)
    return new_affittuario


@router.put("/{affittuario_id}", response_model=AffittuarioResponse)
def update_affittuario(affittuario_id: int, affittuario: AffittuarioUpdate, db: Session = Depends(get_db)):
    """Aggiorna un affittuario esistente"""
    db_affittuario = db.query(Affittuario).filter(Affittuario.id == affittuario_id).first()
    if not db_affittuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Affittuario con ID {affittuario_id} non trovato"
        )

    update_data = affittuario.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_affittuario, field, value)

    db.commit()
    db.refresh(db_affittuario)
    return db_affittuario


@router.delete("/{affittuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_affittuario(affittuario_id: int, db: Session = Depends(get_db)):
    """Elimina un affittuario"""
    db_affittuario = db.query(Affittuario).filter(Affittuario.id == affittuario_id).first()
    if not db_affittuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Affittuario con ID {affittuario_id} non trovato"
        )

    db.delete(db_affittuario)
    db.commit()
    return None
