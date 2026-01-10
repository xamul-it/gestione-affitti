"""
API routes for Terreni (Land parcels).

Provides CRUD operations for managing land parcels.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from ..models import Terreno, TipologiaTerreno
from ..schemas.terreno import (
    TerrenoResponse,
    TerrenoCreate,
    TerrenoUpdate,
)

router = APIRouter(prefix="/terreni", tags=["Terreni"])


@router.get("/", response_model=List[TerrenoResponse])
def get_terreni(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = Query(False, description="Filter only active terreni"),
    tipologia_id: Optional[int] = Query(None, description="Filter by tipologia ID"),
    tipologia_codice: Optional[str] = Query(None, description="Filter by tipologia codice (AGR, EDI, etc.)"),
    comune: Optional[str] = Query(None, description="Filter by comune"),
    provincia: Optional[str] = Query(None, description="Filter by provincia"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all terreni with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        attivi_solo: If True, return only active terreni
        tipologia_id: Filter by tipologia ID (FK)
        tipologia_codice: Filter by tipologia codice (AGR, EDI, BOS, IND, ALT)
        comune: Filter by municipality name
        provincia: Filter by province code
        db: Database session

    Returns:
        List of terreni with tipologia relationship loaded
    """
    query = db.query(Terreno).options(joinedload(Terreno.tipologia))

    if attivi_solo:
        query = query.filter(Terreno.attivo == True)

    if tipologia_id:
        query = query.filter(Terreno.tipologia_id == tipologia_id)

    if tipologia_codice:
        # Join with tipologie_terreno to filter by codice
        query = query.join(TipologiaTerreno).filter(
            TipologiaTerreno.codice == tipologia_codice.upper()
        )

    if comune:
        query = query.filter(Terreno.comune.ilike(f"%{comune}%"))

    if provincia:
        query = query.filter(Terreno.provincia == provincia.upper())

    terreni = query.order_by(Terreno.codice).offset(skip).limit(limit).all()
    return terreni


@router.get("/{terreno_id}", response_model=TerrenoResponse)
def get_terreno(terreno_id: int, db: Session = Depends(get_db)):
    """
    Get a specific terreno by ID.

    Args:
        terreno_id: ID of the terreno
        db: Database session

    Returns:
        Terreno details with tipologia

    Raises:
        HTTPException: 404 if terreno not found
    """
    terreno = db.query(Terreno).options(
        joinedload(Terreno.tipologia)
    ).filter(Terreno.id == terreno_id).first()
    if not terreno:
        raise HTTPException(status_code=404, detail="Terreno non trovato")
    return terreno


@router.get("/codice/{codice}", response_model=TerrenoResponse)
def get_terreno_by_codice(codice: str, db: Session = Depends(get_db)):
    """
    Get a specific terreno by codice.

    Args:
        codice: Unique code of the terreno
        db: Database session

    Returns:
        Terreno details

    Raises:
        HTTPException: 404 if terreno not found
    """
    terreno = db.query(Terreno).options(
        joinedload(Terreno.tipologia)
    ).filter(Terreno.codice == codice.upper()).first()
    if not terreno:
        raise HTTPException(status_code=404, detail=f"Terreno con codice '{codice}' non trovato")
    return terreno


@router.post("/", response_model=TerrenoResponse, status_code=201)
def create_terreno(
    terreno: TerrenoCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new terreno.

    Args:
        terreno: Terreno data to create
        db: Database session

    Returns:
        Created terreno

    Raises:
        HTTPException: 400 if codice already exists or tipologia not found
    """
    # Check if codice already exists
    existing = db.query(Terreno).filter(
        Terreno.codice == terreno.codice.upper()
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Terreno con codice '{terreno.codice}' già esistente"
        )

    # Validate tipologia_id if provided
    if terreno.tipologia_id:
        tipologia = db.query(TipologiaTerreno).filter(
            TipologiaTerreno.id == terreno.tipologia_id,
            TipologiaTerreno.attiva == True
        ).first()
        if not tipologia:
            raise HTTPException(
                status_code=400,
                detail=f"Tipologia terreno con ID {terreno.tipologia_id} non trovata o non attiva"
            )

    db_terreno = Terreno(**terreno.model_dump())
    db.add(db_terreno)
    db.commit()
    db.refresh(db_terreno)

    # Reload with relationship
    db_terreno = db.query(Terreno).options(
        joinedload(Terreno.tipologia)
    ).filter(Terreno.id == db_terreno.id).first()

    return db_terreno


@router.put("/{terreno_id}", response_model=TerrenoResponse)
def update_terreno(
    terreno_id: int,
    terreno: TerrenoUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing terreno.

    Args:
        terreno_id: ID of the terreno to update
        terreno: Updated terreno data
        db: Database session

    Returns:
        Updated terreno

    Raises:
        HTTPException: 404 if terreno not found, 400 if codice conflicts or tipologia not found
    """
    db_terreno = db.query(Terreno).filter(Terreno.id == terreno_id).first()
    if not db_terreno:
        raise HTTPException(status_code=404, detail="Terreno non trovato")

    # Check if new codice conflicts with existing
    if terreno.codice:
        existing = db.query(Terreno).filter(
            Terreno.codice == terreno.codice.upper(),
            Terreno.id != terreno_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Terreno con codice '{terreno.codice}' già esistente"
            )

    # Validate tipologia_id if provided
    update_data = terreno.model_dump(exclude_unset=True)
    if "tipologia_id" in update_data and update_data["tipologia_id"] is not None:
        tipologia = db.query(TipologiaTerreno).filter(
            TipologiaTerreno.id == update_data["tipologia_id"],
            TipologiaTerreno.attiva == True
        ).first()
        if not tipologia:
            raise HTTPException(
                status_code=400,
                detail=f"Tipologia terreno con ID {update_data['tipologia_id']} non trovata o non attiva"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(db_terreno, field, value)

    db.commit()

    # Reload with relationship
    db_terreno = db.query(Terreno).options(
        joinedload(Terreno.tipologia)
    ).filter(Terreno.id == terreno_id).first()

    return db_terreno


@router.delete("/{terreno_id}", status_code=204)
def delete_terreno(terreno_id: int, db: Session = Depends(get_db)):
    """
    Delete (soft delete) a terreno.

    Args:
        terreno_id: ID of the terreno to delete
        db: Database session

    Raises:
        HTTPException: 404 if terreno not found
    """
    db_terreno = db.query(Terreno).filter(Terreno.id == terreno_id).first()
    if not db_terreno:
        raise HTTPException(status_code=404, detail="Terreno non trovato")

    # Soft delete
    db_terreno.attivo = False
    db.commit()
    return None


@router.post("/{terreno_id}/restore", response_model=TerrenoResponse)
def restore_terreno(terreno_id: int, db: Session = Depends(get_db)):
    """
    Restore a soft-deleted terreno.

    Args:
        terreno_id: ID of the terreno to restore
        db: Database session

    Returns:
        Restored terreno

    Raises:
        HTTPException: 404 if terreno not found
    """
    db_terreno = db.query(Terreno).filter(Terreno.id == terreno_id).first()
    if not db_terreno:
        raise HTTPException(status_code=404, detail="Terreno non trovato")

    db_terreno.attivo = True
    db.commit()

    # Reload with relationship
    db_terreno = db.query(Terreno).options(
        joinedload(Terreno.tipologia)
    ).filter(Terreno.id == terreno_id).first()

    return db_terreno
