from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import MillesimiUnita
from ..schemas.millesimi_unita import MillesimiUnitaCreate, MillesimiUnitaUpdate, MillesimiUnitaResponse

router = APIRouter(prefix="/millesimi-immobile", tags=["Millesimi Immobile"])


@router.get("/", response_model=List[MillesimiUnitaResponse])
def get_millesimi(
    skip: int = 0,
    limit: int = 100,
    unita_immobiliare_id: int = None,
    tabella_id: int = None,
    db: Session = Depends(get_db)
):
    """Ottieni lista dei millesimi immobile"""
    query = db.query(MillesimiUnita)
    if unita_immobiliare_id:
        query = query.filter(MillesimiUnita.unita_immobiliare_id == unita_immobiliare_id)
    if tabella_id:
        query = query.filter(MillesimiUnita.tabella_millesimale_id == tabella_id)
    millesimi = query.offset(skip).limit(limit).all()
    return millesimi


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[MillesimiUnitaResponse])
def get_millesimi_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti i millesimi di un'unità immobiliare (tutte le tabelle)"""
    millesimi = db.query(MillesimiUnita).filter(
        MillesimiUnita.unita_immobiliare_id == unita_immobiliare_id
    ).all()
    return millesimi


@router.get("/tabella/{tabella_id}", response_model=List[MillesimiUnitaResponse])
def get_millesimi_by_tabella(tabella_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti gli immobili associati a una tabella millesimale"""
    millesimi = db.query(MillesimiUnita).filter(
        MillesimiUnita.tabella_millesimale_id == tabella_id
    ).all()
    return millesimi


@router.get("/{millesimi_id}", response_model=MillesimiUnitaResponse)
def get_millesimo(millesimi_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un record millesimi specifico"""
    millesimo = db.query(MillesimiUnita).filter(MillesimiUnita.id == millesimi_id).first()
    if not millesimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record millesimi con ID {millesimi_id} non trovato"
        )
    return millesimo


@router.post("/", response_model=MillesimiUnitaResponse, status_code=status.HTTP_201_CREATED)
def create_millesimo(millesimo: MillesimiUnitaCreate, db: Session = Depends(get_db)):
    """Crea un nuovo record millesimi per un'unità immobiliare"""
    # Verifica che non esista già per questa combinazione
    db_millesimo = db.query(MillesimiUnita).filter(
        MillesimiUnita.unita_immobiliare_id == millesimo.unita_immobiliare_id,
        MillesimiUnita.tabella_millesimale_id == millesimo.tabella_millesimale_id
    ).first()
    if db_millesimo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questa unità immobiliare ha già millesimi per questa tabella"
        )

    new_millesimo = MillesimiUnita(**millesimo.model_dump())
    db.add(new_millesimo)
    db.commit()
    db.refresh(new_millesimo)
    return new_millesimo


@router.put("/{millesimi_id}", response_model=MillesimiUnitaResponse)
def update_millesimo(millesimi_id: int, millesimo: MillesimiUnitaUpdate, db: Session = Depends(get_db)):
    """Aggiorna un record millesimi esistente"""
    db_millesimo = db.query(MillesimiUnita).filter(MillesimiUnita.id == millesimi_id).first()
    if not db_millesimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record millesimi con ID {millesimi_id} non trovato"
        )

    update_data = millesimo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_millesimo, field, value)

    db.commit()
    db.refresh(db_millesimo)
    return db_millesimo


@router.delete("/{millesimi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_millesimo(millesimi_id: int, db: Session = Depends(get_db)):
    """Elimina un record millesimi"""
    db_millesimo = db.query(MillesimiUnita).filter(MillesimiUnita.id == millesimi_id).first()
    if not db_millesimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record millesimi con ID {millesimi_id} non trovato"
        )

    db.delete(db_millesimo)
    db.commit()
    return None
