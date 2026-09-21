from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import Condominio
from ..schemas.condomini import CondominioCreate, CondominioUpdate, CondominioResponse

router = APIRouter(prefix="/condomini", tags=["Condomini"])


@router.get("/", response_model=List[CondominioResponse])
def get_condomini(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = False,
    db: Session = Depends(get_db)
):
    """Ottieni lista di tutti i condomini"""
    query = db.query(Condominio)
    if attivi_solo:
        query = query.filter(Condominio.attivo == True)
    condomini = query.offset(skip).limit(limit).all()
    return condomini


@router.get("/{condominio_id}", response_model=CondominioResponse)
def get_condominio(condominio_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un condominio specifico"""
    condominio = db.query(Condominio).filter(Condominio.id == condominio_id).first()
    if not condominio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condominio con ID {condominio_id} non trovato"
        )
    return condominio


@router.post("/", response_model=CondominioResponse, status_code=status.HTTP_201_CREATED)
def create_condominio(condominio: CondominioCreate, db: Session = Depends(get_db)):
    """Crea un nuovo condominio"""
    # Verifica unicità codice
    db_condominio = db.query(Condominio).filter(Condominio.codice == condominio.codice).first()
    if db_condominio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Condominio con codice {condominio.codice} già esistente"
        )

    new_condominio = Condominio(**condominio.model_dump())
    db.add(new_condominio)
    db.commit()
    db.refresh(new_condominio)
    return new_condominio


@router.put("/{condominio_id}", response_model=CondominioResponse)
def update_condominio(condominio_id: int, condominio: CondominioUpdate, db: Session = Depends(get_db)):
    """Aggiorna un condominio esistente"""
    db_condominio = db.query(Condominio).filter(Condominio.id == condominio_id).first()
    if not db_condominio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condominio con ID {condominio_id} non trovato"
        )

    # Aggiorna solo i campi forniti
    update_data = condominio.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_condominio, field, value)

    db.commit()
    db.refresh(db_condominio)
    return db_condominio


@router.delete("/{condominio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condominio(condominio_id: int, db: Session = Depends(get_db)):
    """Elimina un condominio"""
    db_condominio = db.query(Condominio).filter(Condominio.id == condominio_id).first()
    if not db_condominio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Condominio con ID {condominio_id} non trovato"
        )

    db.delete(db_condominio)
    db.commit()
    return None
