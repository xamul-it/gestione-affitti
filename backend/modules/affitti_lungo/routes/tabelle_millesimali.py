from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from ..models import TabellaMillesimale
from ..schemas.tabelle_millesimali import TabellaMillesimaleCreate, TabellaMillesimaleUpdate, TabellaMillesimaleResponse

router = APIRouter(prefix="/tabelle-millesimali", tags=["Tabelle Millesimali"])


@router.get("/", response_model=List[TabellaMillesimaleResponse])
def get_tabelle(
    skip: int = 0,
    limit: int = 100,
    condominio_id: int = None,
    attive_solo: bool = False,
    db: Session = Depends(get_db)
):
    """Ottieni lista delle tabelle millesimali"""
    query = db.query(TabellaMillesimale)
    if condominio_id:
        query = query.filter(TabellaMillesimale.condominio_id == condominio_id)
    if attive_solo:
        query = query.filter(TabellaMillesimale.attiva == True)
    tabelle = query.offset(skip).limit(limit).all()
    return tabelle


@router.get("/condominio/{condominio_id}", response_model=List[TabellaMillesimaleResponse])
def get_tabelle_by_condominio(condominio_id: int, db: Session = Depends(get_db)):
    """Ottieni tutte le tabelle millesimali di un condominio"""
    tabelle = db.query(TabellaMillesimale).filter(
        TabellaMillesimale.condominio_id == condominio_id
    ).all()
    return tabelle


@router.get("/{tabella_id}", response_model=TabellaMillesimaleResponse)
def get_tabella(tabella_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una tabella millesimale specifica"""
    tabella = db.query(TabellaMillesimale).filter(TabellaMillesimale.id == tabella_id).first()
    if not tabella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tabella millesimale con ID {tabella_id} non trovata"
        )
    return tabella


@router.post("/", response_model=TabellaMillesimaleResponse, status_code=status.HTTP_201_CREATED)
def create_tabella(tabella: TabellaMillesimaleCreate, db: Session = Depends(get_db)):
    """Crea una nuova tabella millesimale"""
    # Verifica unicità codice per il condominio
    db_tabella = db.query(TabellaMillesimale).filter(
        TabellaMillesimale.condominio_id == tabella.condominio_id,
        TabellaMillesimale.codice == tabella.codice
    ).first()
    if db_tabella:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tabella con codice {tabella.codice} già esistente per questo condominio"
        )

    new_tabella = TabellaMillesimale(**tabella.model_dump())
    db.add(new_tabella)
    db.commit()
    db.refresh(new_tabella)
    return new_tabella


@router.put("/{tabella_id}", response_model=TabellaMillesimaleResponse)
def update_tabella(tabella_id: int, tabella: TabellaMillesimaleUpdate, db: Session = Depends(get_db)):
    """Aggiorna una tabella millesimale esistente"""
    db_tabella = db.query(TabellaMillesimale).filter(TabellaMillesimale.id == tabella_id).first()
    if not db_tabella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tabella millesimale con ID {tabella_id} non trovata"
        )

    update_data = tabella.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tabella, field, value)

    db.commit()
    db.refresh(db_tabella)
    return db_tabella


@router.delete("/{tabella_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tabella(tabella_id: int, db: Session = Depends(get_db)):
    """Elimina una tabella millesimale"""
    db_tabella = db.query(TabellaMillesimale).filter(TabellaMillesimale.id == tabella_id).first()
    if not db_tabella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tabella millesimale con ID {tabella_id} non trovata"
        )

    db.delete(db_tabella)
    db.commit()
    return None
