from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import Tecnico
from ..schemas.tecnici import TecnicoCreate, TecnicoUpdate, TecnicoResponse

router = APIRouter(prefix="/tecnici", tags=["Tecnici"])


@router.get("/", response_model=List[TecnicoResponse])
def get_tecnici(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = False,
    db: Session = Depends(get_db)
):
    """Ottieni lista di tutti i tecnici"""
    query = db.query(Tecnico)
    if attivi_solo:
        query = query.filter(Tecnico.attivo == True)
    tecnici = query.offset(skip).limit(limit).all()
    return tecnici


@router.get("/{tecnico_id}", response_model=TecnicoResponse)
def get_tecnico(tecnico_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un tecnico specifico"""
    tecnico = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    if not tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {tecnico_id} non trovato"
        )
    return tecnico


@router.post("/", response_model=TecnicoResponse, status_code=status.HTTP_201_CREATED)
def create_tecnico(tecnico: TecnicoCreate, db: Session = Depends(get_db)):
    """Crea un nuovo tecnico"""
    new_tecnico = Tecnico(**tecnico.model_dump())
    db.add(new_tecnico)
    db.commit()
    db.refresh(new_tecnico)
    return new_tecnico


@router.put("/{tecnico_id}", response_model=TecnicoResponse)
def update_tecnico(
    tecnico_id: int,
    tecnico: TecnicoUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna un tecnico esistente"""
    db_tecnico = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    if not db_tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {tecnico_id} non trovato"
        )

    # Aggiorna solo i campi forniti
    for field, value in tecnico.model_dump(exclude_unset=True).items():
        setattr(db_tecnico, field, value)

    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico


@router.delete("/{tecnico_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tecnico(tecnico_id: int, db: Session = Depends(get_db)):
    """Elimina un tecnico (soft delete - imposta attivo=False)"""
    db_tecnico = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    if not db_tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {tecnico_id} non trovato"
        )

    # Soft delete
    db_tecnico.attivo = False
    db.commit()
    return None
