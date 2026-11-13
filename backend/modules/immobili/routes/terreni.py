"""
API routes for Terreni (Land parcels).

Provides CRUD operations for managing land parcels.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from ..models import Terreno, TerrenoPorzione, TipologiaTerreno
from ..schemas.terreno import (
    TerrenoResponse,
    TerrenoCreate,
    TerrenoUpdate,
)
from ..services.codici_beni import verifica_codice_libero

router = APIRouter(prefix="/terreni", tags=["Terreni"])


def _query(db: Session):
    return db.query(Terreno).options(joinedload(Terreno.tipologia), selectinload(Terreno.porzioni))


def _carica(db: Session, terreno_id: int) -> Terreno:
    terreno = _query(db).filter(Terreno.id == terreno_id).first()
    if not terreno:
        raise HTTPException(status_code=404, detail="Terreno non trovato")
    return terreno


def _verifica_tipologia(db: Session, tipologia_id: Optional[int]) -> None:
    if tipologia_id is None:
        return
    tipologia = db.query(TipologiaTerreno).filter(
        TipologiaTerreno.id == tipologia_id,
        TipologiaTerreno.attiva == True,  # noqa: E712
    ).first()
    if not tipologia:
        raise HTTPException(
            status_code=400,
            detail=f"Tipologia terreno con ID {tipologia_id} non trovata o non attiva",
        )


_BOOLEANI = ("edificabile", "esente_imu_montano", "attivo")


def _senza_booleani_nulli(dati: dict) -> dict:
    """null on a NOT NULL flag means "leave as it is / default"."""
    return {k: v for k, v in dati.items() if not (k in _BOOLEANI and v is None)}


def _imposta_porzioni(terreno: Terreno, porzioni) -> None:
    terreno.porzioni = [TerrenoPorzione(**p.model_dump()) for p in porzioni]
    terreno.ricalcola_superficie()


@router.get("/", response_model=List[TerrenoResponse])
def get_terreni(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = Query(False, description="Filter only active terreni"),
    tipologia_id: Optional[int] = Query(None, description="Filter by tipologia ID"),
    tipologia_codice: Optional[str] = Query(None, description="Filter by tipologia codice (AGR, EDI, etc.)"),
    comune: Optional[str] = Query(None, description="Filter by comune"),
    provincia: Optional[str] = Query(None, description="Filter by provincia"),
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.view")),
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
    query = db.query(Terreno).options(joinedload(Terreno.tipologia), selectinload(Terreno.porzioni))

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
def get_terreno(terreno_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.view"))):
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
    terreno = _query(db).filter(Terreno.id == terreno_id).first()
    if not terreno:
        raise HTTPException(status_code=404, detail="Terreno non trovato")
    return terreno


@router.get("/codice/{codice}", response_model=TerrenoResponse)
def get_terreno_by_codice(codice: str, db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.view"))):
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
    terreno = _query(db).filter(Terreno.codice == codice.upper()).first()
    if not terreno:
        raise HTTPException(status_code=404, detail=f"Terreno con codice '{codice}' non trovato")
    return terreno


@router.post("/", response_model=TerrenoResponse, status_code=201)
def create_terreno(
    terreno: TerrenoCreate,
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.create")),
):
    """Create a land parcel (a bene of type TERRENO) with its portions."""
    verifica_codice_libero(db, terreno.codice)
    _verifica_tipologia(db, terreno.tipologia_id)

    dati = _senza_booleani_nulli(terreno.model_dump(exclude={"porzioni"}))
    db_terreno = Terreno(**dati)
    _imposta_porzioni(db_terreno, terreno.porzioni)
    db.add(db_terreno)
    db.commit()
    db.expire_all()
    return _carica(db, db_terreno.id)


@router.put("/{terreno_id}", response_model=TerrenoResponse)
def update_terreno(
    terreno_id: int,
    terreno: TerrenoUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.edit")),
):
    """Update a land parcel; `porzioni`, when sent, replaces the existing ones.
    Deactivate / reactivate with `attivo`."""
    db_terreno = _carica(db, terreno_id)
    update_data = _senza_booleani_nulli(terreno.model_dump(exclude_unset=True, exclude={"porzioni"}))
    verifica_codice_libero(db, update_data.get("codice"), escludi_id=terreno_id)
    _verifica_tipologia(db, update_data.get("tipologia_id"))

    for field, value in update_data.items():
        setattr(db_terreno, field, value)
    if terreno.porzioni is not None:
        _imposta_porzioni(db_terreno, terreno.porzioni)

    db.commit()
    db.expire_all()
    return _carica(db, terreno_id)


@router.delete("/{terreno_id}", status_code=204)
def delete_terreno(terreno_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.delete"))):
    """Delete the land parcel for good: bene, portions, rights, tenant
    assignments, recurring costs and cadastral changes (ON DELETE CASCADE).
    To hide it without deleting, set `attivo` to false."""
    db_terreno = _carica(db, terreno_id)
    db.delete(db_terreno)
    db.commit()
    return None


@router.post("/{terreno_id}/restore", response_model=TerrenoResponse)
def restore_terreno(terreno_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("terreno.edit"))):
    """Reactivate a deactivated land parcel."""
    db_terreno = _carica(db, terreno_id)
    db_terreno.attivo = True
    db.commit()
    db.expire_all()
    return _carica(db, terreno_id)
