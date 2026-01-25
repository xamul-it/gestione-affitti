"""
API routes for TipologiaTerreno (Land Type domain).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..models import TipologiaTerreno
from ..schemas.tipologia_terreno import (
    TipologiaTerrenoResponse,
    TipologiaTerrenoCreate,
    TipologiaTerrenoUpdate,
)

router = APIRouter(prefix="/tipologie-terreno", tags=["Tipologie Terreno"])


@router.get("/", response_model=List[TipologiaTerrenoResponse])
def get_tipologie_terreno(
    skip: int = 0,
    limit: int = 100,
    attive_solo: bool = Query(False, description="Filter only active tipologie"),
    db: Session = Depends(get_db),
):
    query = db.query(TipologiaTerreno)
    if attive_solo:
        query = query.filter(TipologiaTerreno.attiva == True)
    return query.order_by(TipologiaTerreno.ordinamento, TipologiaTerreno.codice).offset(skip).limit(limit).all()


@router.get("/{tipologia_id}", response_model=TipologiaTerrenoResponse)
def get_tipologia_terreno(tipologia_id: int, db: Session = Depends(get_db)):
    tipologia = db.query(TipologiaTerreno).filter(TipologiaTerreno.id == tipologia_id).first()
    if not tipologia:
        raise HTTPException(status_code=404, detail="Tipologia terreno non trovata")
    return tipologia


@router.post("/", response_model=TipologiaTerrenoResponse, status_code=201)
def create_tipologia_terreno(
    tipologia: TipologiaTerrenoCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(TipologiaTerreno).filter(
        TipologiaTerreno.codice == tipologia.codice.upper()
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tipologia terreno con codice '{tipologia.codice}' già esistente"
        )
    db_tipologia = TipologiaTerreno(**tipologia.model_dump())
    db.add(db_tipologia)
    db.commit()
    db.refresh(db_tipologia)
    return db_tipologia


@router.put("/{tipologia_id}", response_model=TipologiaTerrenoResponse)
def update_tipologia_terreno(
    tipologia_id: int,
    tipologia: TipologiaTerrenoUpdate,
    db: Session = Depends(get_db),
):
    db_tipologia = db.query(TipologiaTerreno).filter(TipologiaTerreno.id == tipologia_id).first()
    if not db_tipologia:
        raise HTTPException(status_code=404, detail="Tipologia terreno non trovata")

    if tipologia.codice:
        existing = db.query(TipologiaTerreno).filter(
            TipologiaTerreno.codice == tipologia.codice.upper(),
            TipologiaTerreno.id != tipologia_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Tipologia terreno con codice '{tipologia.codice}' già esistente"
            )

    update_data = tipologia.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tipologia, field, value)
    db.commit()
    db.refresh(db_tipologia)
    return db_tipologia


@router.delete("/{tipologia_id}", status_code=204)
def delete_tipologia_terreno(tipologia_id: int, db: Session = Depends(get_db)):
    db_tipologia = db.query(TipologiaTerreno).filter(TipologiaTerreno.id == tipologia_id).first()
    if not db_tipologia:
        raise HTTPException(status_code=404, detail="Tipologia terreno non trovata")
    db_tipologia.attiva = False
    db.commit()
    return None
