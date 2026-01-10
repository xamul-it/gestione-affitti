"""
API routes for CategoriaCatastale (Italian cadastral categories).

Provides CRUD operations for managing cadastral categories.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..models import CategoriaCatastale
from ..schemas.categoria_catastale import (
    CategoriaCatastale as CategoriaCatastaleSchema,
    CategoriaCatastaleCreate,
    CategoriaCatastaleUpdate,
)

router = APIRouter(prefix="/categorie-catastali", tags=["Categorie Catastali"])


@router.get("/", response_model=List[CategoriaCatastaleSchema])
def get_categorie_catastali(
    skip: int = 0,
    limit: int = 100,
    attive_solo: bool = Query(False, description="Filter only active categories"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all categorie catastali.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        attive_solo: If True, return only active categories
        db: Database session

    Returns:
        List of categorie catastali
    """
    query = db.query(CategoriaCatastale)

    if attive_solo:
        query = query.filter(CategoriaCatastale.attiva == True)

    categorie = query.order_by(CategoriaCatastale.ordinamento).offset(skip).limit(limit).all()
    return categorie


@router.get("/{categoria_id}", response_model=CategoriaCatastaleSchema)
def get_categoria_catastale(categoria_id: int, db: Session = Depends(get_db)):
    """
    Get a specific categoria catastale by ID.

    Args:
        categoria_id: ID of the categoria
        db: Database session

    Returns:
        Categoria catastale details

    Raises:
        HTTPException: 404 if categoria not found
    """
    categoria = db.query(CategoriaCatastale).filter(CategoriaCatastale.id == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria catastale non trovata")
    return categoria


@router.post("/", response_model=CategoriaCatastaleSchema, status_code=201)
def create_categoria_catastale(
    categoria: CategoriaCatastaleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new categoria catastale.

    Args:
        categoria: Categoria data to create
        db: Database session

    Returns:
        Created categoria catastale

    Raises:
        HTTPException: 400 if codice already exists
    """
    # Check if codice already exists
    existing = db.query(CategoriaCatastale).filter(
        CategoriaCatastale.codice == categoria.codice.upper()
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Categoria con codice '{categoria.codice}' già esistente"
        )

    db_categoria = CategoriaCatastale(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.put("/{categoria_id}", response_model=CategoriaCatastaleSchema)
def update_categoria_catastale(
    categoria_id: int,
    categoria: CategoriaCatastaleUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing categoria catastale.

    Args:
        categoria_id: ID of the categoria to update
        categoria: Updated categoria data
        db: Database session

    Returns:
        Updated categoria catastale

    Raises:
        HTTPException: 404 if categoria not found, 400 if codice conflicts
    """
    db_categoria = db.query(CategoriaCatastale).filter(CategoriaCatastale.id == categoria_id).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoria catastale non trovata")

    # Check if new codice conflicts with existing
    if categoria.codice:
        existing = db.query(CategoriaCatastale).filter(
            CategoriaCatastale.codice == categoria.codice.upper(),
            CategoriaCatastale.id != categoria_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Categoria con codice '{categoria.codice}' già esistente"
            )

    # Update fields
    update_data = categoria.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_categoria, field, value)

    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.delete("/{categoria_id}", status_code=204)
def delete_categoria_catastale(categoria_id: int, db: Session = Depends(get_db)):
    """
    Delete (soft delete) a categoria catastale.

    Args:
        categoria_id: ID of the categoria to delete
        db: Database session

    Raises:
        HTTPException: 404 if categoria not found
    """
    db_categoria = db.query(CategoriaCatastale).filter(CategoriaCatastale.id == categoria_id).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoria catastale non trovata")

    # Soft delete
    db_categoria.attiva = False
    db.commit()
    return None
