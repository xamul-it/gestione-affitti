"""
Routes for module-provided roles (ruoli disponibili).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_role
from app.core.database import get_public_db
from app.core.models import RuoloDisponibile
from app.core.module_system.models import Module

router = APIRouter(prefix="/ruoli-disponibili", tags=["ruoli-disponibili"])


class RuoloDisponibileResponse(BaseModel):
    id: int
    codice: str
    nome_display: str
    descrizione: Optional[str]
    modulo_id: str
    tabella_specializzazione: Optional[str]
    attivo: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[RuoloDisponibileResponse], dependencies=[Depends(require_role(["Admin"]))])
def list_ruoli_disponibili(
    db: Session = Depends(get_public_db),
    attivo_only: bool = True,
):
    """
    List all module-provided roles (Admin only).
    """
    query = db.query(RuoloDisponibile).join(
        Module, Module.technical_name == RuoloDisponibile.modulo_id
    ).filter(
        Module.registered == True
    )
    if attivo_only:
        query = query.filter(RuoloDisponibile.attivo == True)
    return query.order_by(RuoloDisponibile.modulo_id, RuoloDisponibile.nome_display).all()
