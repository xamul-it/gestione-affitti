from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import Contratto
from ..schemas.contratti import ContrattoCreate, ContrattoUpdate, ContrattoResponse

router = APIRouter(prefix="/contratti", tags=["Contratti"])


@router.get("/", response_model=List[ContrattoResponse])
def get_contratti(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni lista di tutti i contratti"""
    contratti = db.query(Contratto).offset(skip).limit(limit).all()
    return contratti


@router.get("/{contratto_id}", response_model=ContrattoResponse)
def get_contratto(contratto_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un contratto specifico"""
    contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
    if not contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contratto con ID {contratto_id} non trovato"
        )
    return contratto


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[ContrattoResponse])
def get_contratti_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti i contratti di un'unità immobiliare"""
    contratti = db.query(Contratto).filter(Contratto.unita_immobiliare_id == unita_immobiliare_id).all()
    return contratti


@router.get("/affittuario/{affittuario_id}", response_model=List[ContrattoResponse])
def get_contratti_by_affittuario(affittuario_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti i contratti di un affittuario"""
    contratti = db.query(Contratto).filter(Contratto.affittuario_id == affittuario_id).all()
    return contratti


@router.post("/", response_model=ContrattoResponse, status_code=status.HTTP_201_CREATED)
def create_contratto(contratto: ContrattoCreate, db: Session = Depends(get_db)):
    """Crea un nuovo contratto"""
    db_contratto = db.query(Contratto).filter(
        Contratto.numero_contratto == contratto.numero_contratto
    ).first()
    if db_contratto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contratto con numero {contratto.numero_contratto} già esistente"
        )

    new_contratto = Contratto(**contratto.model_dump())
    db.add(new_contratto)
    db.commit()
    db.refresh(new_contratto)
    return new_contratto


@router.put("/{contratto_id}", response_model=ContrattoResponse)
def update_contratto(contratto_id: int, contratto: ContrattoUpdate, db: Session = Depends(get_db)):
    """Aggiorna un contratto esistente"""
    db_contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
    if not db_contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contratto con ID {contratto_id} non trovato"
        )

    update_data = contratto.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contratto, field, value)

    db.commit()
    db.refresh(db_contratto)
    return db_contratto


@router.delete("/{contratto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contratto(contratto_id: int, db: Session = Depends(get_db)):
    """Elimina un contratto"""
    db_contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
    if not db_contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contratto con ID {contratto_id} non trovato"
        )

    db.delete(db_contratto)
    db.commit()
    return None
