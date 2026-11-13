"""
Common API of the beni (units and land parcels): listing with type filter
and search, detail, cadastral changes. Creating and editing the specific
data stays on /unita-immobiliari and /terreni.
"""
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_active_user
from app.core.auth.models import User
from app.core.database import get_db

from ..models import Bene, VariazioneCatastale
from ..schemas.bene import BeneResponse
from ..schemas.immobili import VariazioneCatastaleResponse

router = APIRouter(prefix="/beni", tags=["Beni"])

_FOGLIO_PARTICELLA = re.compile(r"^\s*0*(\w+)\s*/\s*0*(\w+)\s*$")

# Units are seen with immobile.view, land parcels with terreno.view.
_PERMESSO_PER_TIPO = {"UNITA": "immobile.view", "TERRENO": "terreno.view"}


def _tipi_visibili(utente) -> set:
    if getattr(utente, "is_superuser", False):
        return set(_PERMESSO_PER_TIPO)
    permessi = utente.get_permissions()
    return {tipo for tipo, permesso in _PERMESSO_PER_TIPO.items() if permesso in permessi}


def _tipi_o_403(utente) -> set:
    tipi = _tipi_visibili(utente)
    if not tipi:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    return tipi


def _bene_visibile(db: Session, bene_id: int, utente) -> Bene:
    tipi = _tipi_o_403(utente)
    bene = db.get(Bene, bene_id)
    if not bene or bene.tipo_bene not in tipi:
        raise HTTPException(status_code=404, detail="Bene non trovato")
    return bene


@router.get("/", response_model=List[BeneResponse])
def get_beni(
    tipo_bene: Optional[str] = Query(None, pattern="^(UNITA|TERRENO)$"),
    q: Optional[str] = Query(None, description="Codice, indirizzo, comune o foglio/particella (es. 40/154)"),
    attivo: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tipi = _tipi_o_403(current_user)
    if tipo_bene:
        tipi = tipi & {tipo_bene}
    if not tipi:
        return []
    query = db.query(Bene).filter(Bene.tipo_bene.in_(tipi))
    if attivo is not None:
        query = query.filter(Bene.attivo.is_(attivo))
    if q and q.strip():
        testo = q.strip()
        fp = _FOGLIO_PARTICELLA.match(testo)
        if fp:
            # Leading zeros are ignored, as in the visure matching.
            query = query.filter(
                Bene.foglio.op("~")(f"^0*{re.escape(fp.group(1))}$"),
                Bene.particella.op("~")(f"^0*{re.escape(fp.group(2))}$"),
            )
        else:
            like = f"%{testo}%"
            query = query.filter(or_(
                Bene.codice.ilike(like), Bene.indirizzo.ilike(like), Bene.comune.ilike(like),
            ))
    return query.order_by(Bene.codice).limit(500).all()


@router.get("/{bene_id}", response_model=BeneResponse)
def get_bene(
    bene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _bene_visibile(db, bene_id, current_user)


@router.get("/{bene_id}/variazioni-catastali", response_model=List[VariazioneCatastaleResponse])
def get_variazioni_catastali(
    bene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Storico delle variazioni dei dati catastali del bene, dalla più recente."""
    _bene_visibile(db, bene_id, current_user)
    return (
        db.query(VariazioneCatastale)
        .filter(VariazioneCatastale.bene_id == bene_id)
        .order_by(VariazioneCatastale.created_at.desc(), VariazioneCatastale.id.desc())
        .all()
    )
