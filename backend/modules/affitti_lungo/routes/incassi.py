from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import Incasso
from ..schemas.incassi import IncassoCreate, IncassoUpdate, IncassoResponse

router = APIRouter(prefix="/incassi", tags=["Incassi"])


@router.get("/", response_model=List[IncassoResponse])
def get_incassi(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutti gli incassi"""
    incassi = db.query(Incasso).offset(skip).limit(limit).all()
    return incassi


@router.get("/{incasso_id}", response_model=IncassoResponse)
def get_incasso(incasso_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un incasso specifico"""
    incasso = db.query(Incasso).filter(Incasso.id == incasso_id).first()
    if not incasso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incasso con ID {incasso_id} non trovato"
        )
    return incasso


@router.get("/contratto/{contratto_id}", response_model=List[IncassoResponse])
def get_incassi_by_contratto(contratto_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti gli incassi di un contratto"""
    incassi = db.query(Incasso).filter(Incasso.contratto_id == contratto_id).all()
    return incassi


@router.post("/", response_model=IncassoResponse, status_code=status.HTTP_201_CREATED)
def create_incasso(incasso: IncassoCreate, db: Session = Depends(get_db)):
    """Crea un nuovo incasso"""
    new_incasso = Incasso(**incasso.model_dump())
    db.add(new_incasso)
    db.commit()
    db.refresh(new_incasso)
    return new_incasso


@router.put("/{incasso_id}", response_model=IncassoResponse)
def update_incasso(incasso_id: int, incasso: IncassoUpdate, db: Session = Depends(get_db)):
    """Aggiorna un incasso esistente"""
    db_incasso = db.query(Incasso).filter(Incasso.id == incasso_id).first()
    if not db_incasso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incasso con ID {incasso_id} non trovato"
        )

    update_data = incasso.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_incasso, field, value)

    db.commit()
    db.refresh(db_incasso)
    return db_incasso


@router.delete("/{incasso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incasso(incasso_id: int, db: Session = Depends(get_db)):
    """Elimina un incasso"""
    db_incasso = db.query(Incasso).filter(Incasso.id == incasso_id).first()
    if not db_incasso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incasso con ID {incasso_id} non trovato"
        )

    db.delete(db_incasso)
    db.commit()
    return None
