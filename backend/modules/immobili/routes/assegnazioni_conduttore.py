from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from ..models import AssegnazioneConduttore, UnitaImmobiliare, Conduttore
from ..schemas import (
    AssegnazioneConduttoreCreate,
    AssegnazioneConduttoreUpdate,
    AssegnazioneConduttoreResponse,
)

router = APIRouter(prefix="/assegnazioni-conduttore", tags=["assegnazioni-conduttore"])


@router.get("/", response_model=List[AssegnazioneConduttoreResponse])
def get_assegnazioni(
    unita_immobiliare_id: Optional[int] = Query(None),
    conduttore_id: Optional[int] = Query(None),
    solo_correnti: bool = Query(False, description="Solo assegnazioni senza data_fine (in corso)"),
    db: Session = Depends(get_db),
):
    """Recupera tutte le assegnazioni con filtri opzionali"""
    query = db.query(AssegnazioneConduttore)

    if unita_immobiliare_id:
        query = query.filter(AssegnazioneConduttore.unita_immobiliare_id == unita_immobiliare_id)
    if conduttore_id:
        query = query.filter(AssegnazioneConduttore.conduttore_id == conduttore_id)
    if solo_correnti:
        query = query.filter(AssegnazioneConduttore.data_fine.is_(None))

    return query.order_by(AssegnazioneConduttore.unita_immobiliare_id, AssegnazioneConduttore.data_inizio).all()


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[AssegnazioneConduttoreResponse])
def get_assegnazioni_by_unita(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Recupera tutte le assegnazioni (storiche e correnti) di un'unità immobiliare"""
    unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not unita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unità immobiliare non trovata")

    return db.query(AssegnazioneConduttore).filter(
        AssegnazioneConduttore.unita_immobiliare_id == unita_immobiliare_id
    ).order_by(AssegnazioneConduttore.data_inizio.desc()).all()


@router.get("/{assegnazione_id}", response_model=AssegnazioneConduttoreResponse)
def get_assegnazione(assegnazione_id: int, db: Session = Depends(get_db)):
    """Recupera una assegnazione specifica"""
    assegnazione = db.query(AssegnazioneConduttore).filter(AssegnazioneConduttore.id == assegnazione_id).first()
    if not assegnazione:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assegnazione non trovata")
    return assegnazione


@router.post("/", response_model=AssegnazioneConduttoreResponse, status_code=status.HTTP_201_CREATED)
def create_assegnazione(assegnazione: AssegnazioneConduttoreCreate, db: Session = Depends(get_db)):
    """Assegna un conduttore a un'unità immobiliare per un periodo"""
    unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == assegnazione.unita_immobiliare_id).first()
    if not unita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unità immobiliare non trovata")

    conduttore = db.query(Conduttore).filter(Conduttore.id == assegnazione.conduttore_id).first()
    if not conduttore:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conduttore non trovato")

    db_assegnazione = AssegnazioneConduttore(**assegnazione.model_dump())
    db.add(db_assegnazione)
    db.commit()
    db.refresh(db_assegnazione)
    return db_assegnazione


@router.put("/{assegnazione_id}", response_model=AssegnazioneConduttoreResponse)
def update_assegnazione(
    assegnazione_id: int,
    assegnazione: AssegnazioneConduttoreUpdate,
    db: Session = Depends(get_db),
):
    """Aggiorna una assegnazione (es. valorizzare data_fine per chiuderla)"""
    db_assegnazione = db.query(AssegnazioneConduttore).filter(AssegnazioneConduttore.id == assegnazione_id).first()
    if not db_assegnazione:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assegnazione non trovata")

    for key, value in assegnazione.model_dump(exclude_unset=True).items():
        setattr(db_assegnazione, key, value)

    db.commit()
    db.refresh(db_assegnazione)
    return db_assegnazione


@router.delete("/{assegnazione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assegnazione(assegnazione_id: int, db: Session = Depends(get_db)):
    """Elimina una assegnazione"""
    db_assegnazione = db.query(AssegnazioneConduttore).filter(AssegnazioneConduttore.id == assegnazione_id).first()
    if not db_assegnazione:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assegnazione non trovata")

    db.delete(db_assegnazione)
    db.commit()
    return None
