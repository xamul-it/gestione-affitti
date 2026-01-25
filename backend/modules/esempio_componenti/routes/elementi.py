"""
ElementoEsempio Routes - Tenant Data API

Full CRUD endpoints for elementi (tenant data).
Each tenant has their own isolated elementi.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from ..models import ElementoEsempio, CategoriaEsempio, PrioritaEsempio
from ..schemas import (
    ElementoEsempioCreate,
    ElementoEsempioUpdate,
    ElementoEsempioResponse,
    ElementoEsempioListResponse,
    StatoElemento,
)

router = APIRouter(prefix="/elementi", tags=["Esempio - Elementi"])


def _enrich_elemento(elemento: ElementoEsempio, db: Session) -> dict:
    """Add domain data names/colors to elemento response."""
    data = {
        "id": elemento.id,
        "codice": elemento.codice,
        "titolo": elemento.titolo,
        "descrizione": elemento.descrizione,
        "categoria_id": elemento.categoria_id,
        "priorita_id": elemento.priorita_id,
        "quantita": elemento.quantita,
        "importo": elemento.importo,
        "percentuale": elemento.percentuale,
        "data_inizio": elemento.data_inizio,
        "data_fine": elemento.data_fine,
        "stato": elemento.stato,
        "attivo": elemento.attivo,
        "note": elemento.note,
        "created_at": elemento.created_at,
        "updated_at": elemento.updated_at,
        "categoria_nome": None,
        "categoria_colore": None,
        "priorita_nome": None,
        "priorita_colore": None,
    }

    # Fetch domain data if present
    if elemento.categoria_id:
        categoria = db.query(CategoriaEsempio).filter(
            CategoriaEsempio.id == elemento.categoria_id
        ).first()
        if categoria:
            data["categoria_nome"] = categoria.nome
            data["categoria_colore"] = categoria.colore

    if elemento.priorita_id:
        priorita = db.query(PrioritaEsempio).filter(
            PrioritaEsempio.id == elemento.priorita_id
        ).first()
        if priorita:
            data["priorita_nome"] = priorita.nome
            data["priorita_colore"] = priorita.colore

    return data


@router.get("/", response_model=ElementoEsempioListResponse)
def list_elementi(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in codice, titolo, descrizione"),
    stato: Optional[StatoElemento] = Query(None, description="Filter by stato"),
    categoria_id: Optional[int] = Query(None, description="Filter by categoria"),
    priorita_id: Optional[int] = Query(None, description="Filter by priorità"),
    solo_attivi: bool = Query(True, description="Filter active only"),
    sort_field: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc/desc"),
    db: Session = Depends(get_db)
):
    """
    List elementi with filtering, searching, sorting, and pagination.

    This endpoint is tenant-isolated - each tenant sees only their data.
    """
    query = db.query(ElementoEsempio)

    # Apply filters
    if solo_attivi:
        query = query.filter(ElementoEsempio.attivo == True)

    if stato:
        query = query.filter(ElementoEsempio.stato == stato.value)

    if categoria_id:
        query = query.filter(ElementoEsempio.categoria_id == categoria_id)

    if priorita_id:
        query = query.filter(ElementoEsempio.priorita_id == priorita_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ElementoEsempio.codice.ilike(search_term),
                ElementoEsempio.titolo.ilike(search_term),
                ElementoEsempio.descrizione.ilike(search_term),
            )
        )

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    if sort_field and hasattr(ElementoEsempio, sort_field):
        column = getattr(ElementoEsempio, sort_field)
        if sort_order == "desc":
            column = column.desc()
        query = query.order_by(column)
    else:
        query = query.order_by(ElementoEsempio.created_at.desc())

    # Apply pagination
    items = query.offset(skip).limit(limit).all()

    # Enrich with domain data
    enriched_items = [_enrich_elemento(item, db) for item in items]

    return {
        "items": enriched_items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{elemento_id}", response_model=ElementoEsempioResponse)
def get_elemento(
    elemento_id: int,
    db: Session = Depends(get_db)
):
    """Get a single elemento by ID."""
    elemento = db.query(ElementoEsempio).filter(
        ElementoEsempio.id == elemento_id
    ).first()

    if not elemento:
        raise HTTPException(status_code=404, detail="Elemento non trovato")

    return _enrich_elemento(elemento, db)


@router.post("/", response_model=ElementoEsempioResponse, status_code=201)
def create_elemento(
    data: ElementoEsempioCreate,
    db: Session = Depends(get_db)
):
    """Create a new elemento."""
    # Validate FK references exist
    if data.categoria_id:
        categoria = db.query(CategoriaEsempio).filter(
            CategoriaEsempio.id == data.categoria_id
        ).first()
        if not categoria:
            raise HTTPException(status_code=400, detail="Categoria non trovata")

    if data.priorita_id:
        priorita = db.query(PrioritaEsempio).filter(
            PrioritaEsempio.id == data.priorita_id
        ).first()
        if not priorita:
            raise HTTPException(status_code=400, detail="Priorità non trovata")

    # Create elemento
    elemento = ElementoEsempio(**data.model_dump())
    db.add(elemento)
    db.commit()
    db.refresh(elemento)

    return _enrich_elemento(elemento, db)


@router.put("/{elemento_id}", response_model=ElementoEsempioResponse)
def update_elemento(
    elemento_id: int,
    data: ElementoEsempioUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing elemento."""
    elemento = db.query(ElementoEsempio).filter(
        ElementoEsempio.id == elemento_id
    ).first()

    if not elemento:
        raise HTTPException(status_code=404, detail="Elemento non trovato")

    # Validate FK references if being updated
    update_data = data.model_dump(exclude_unset=True)

    if "categoria_id" in update_data and update_data["categoria_id"]:
        categoria = db.query(CategoriaEsempio).filter(
            CategoriaEsempio.id == update_data["categoria_id"]
        ).first()
        if not categoria:
            raise HTTPException(status_code=400, detail="Categoria non trovata")

    if "priorita_id" in update_data and update_data["priorita_id"]:
        priorita = db.query(PrioritaEsempio).filter(
            PrioritaEsempio.id == update_data["priorita_id"]
        ).first()
        if not priorita:
            raise HTTPException(status_code=400, detail="Priorità non trovata")

    # Update fields
    for field, value in update_data.items():
        setattr(elemento, field, value)

    db.commit()
    db.refresh(elemento)

    return _enrich_elemento(elemento, db)


@router.delete("/{elemento_id}", status_code=204)
def delete_elemento(
    elemento_id: int,
    db: Session = Depends(get_db)
):
    """Delete an elemento."""
    elemento = db.query(ElementoEsempio).filter(
        ElementoEsempio.id == elemento_id
    ).first()

    if not elemento:
        raise HTTPException(status_code=404, detail="Elemento non trovato")

    db.delete(elemento)
    db.commit()

    return None


@router.delete("/", status_code=204)
def bulk_delete_elementi(
    ids: List[int] = Query(..., description="List of IDs to delete"),
    db: Session = Depends(get_db)
):
    """Bulk delete elementi by IDs."""
    deleted = db.query(ElementoEsempio).filter(
        ElementoEsempio.id.in_(ids)
    ).delete(synchronize_session=False)

    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Nessun elemento trovato")

    return None
