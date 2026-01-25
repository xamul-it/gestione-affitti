"""
CategoriaEsempio Routes - Domain Data API

Read-only endpoints for categories (domain data in public schema).
Categories are shared across all tenants.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..models import CategoriaEsempio
from ..schemas import CategoriaEsempioResponse

router = APIRouter(prefix="/categorie", tags=["Esempio - Categorie"])


@router.get("/", response_model=List[CategoriaEsempioResponse])
def list_categorie(
    skip: int = 0,
    limit: int = 100,
    solo_attive: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all categories (domain data).

    Categories are shared across all tenants and are read-only.
    """
    query = db.query(CategoriaEsempio)

    if solo_attive:
        query = query.filter(CategoriaEsempio.attivo == True)

    query = query.order_by(CategoriaEsempio.ordine, CategoriaEsempio.nome)

    return query.offset(skip).limit(limit).all()


@router.get("/{categoria_id}", response_model=CategoriaEsempioResponse)
def get_categoria(
    categoria_id: int,
    db: Session = Depends(get_db)
):
    """Get a single category by ID."""
    categoria = db.query(CategoriaEsempio).filter(
        CategoriaEsempio.id == categoria_id
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria non trovata")

    return categoria
