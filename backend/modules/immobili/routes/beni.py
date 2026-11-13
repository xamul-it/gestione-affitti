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

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db

from ..models import Bene, VariazioneCatastale
from ..schemas.bene import BeneResponse
from ..schemas.immobili import VariazioneCatastaleResponse

router = APIRouter(prefix="/beni", tags=["Beni"])

_FOGLIO_PARTICELLA = re.compile(r"^\s*0*(\w+)\s*/\s*0*(\w+)\s*$")


@router.get("/", response_model=List[BeneResponse])
def get_beni(
    tipo_bene: Optional[str] = Query(None, pattern="^(UNITA|TERRENO)$"),
    q: Optional[str] = Query(None, description="Codice, indirizzo, comune o foglio/particella (es. 40/154)"),
    attivo: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.view")),
):
    query = db.query(Bene)
    if tipo_bene:
        query = query.filter(Bene.tipo_bene == tipo_bene)
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
    current_user: User = Depends(require_permission("immobile.view")),
):
    bene = db.get(Bene, bene_id)
    if not bene:
        raise HTTPException(status_code=404, detail="Bene non trovato")
    return bene


@router.get("/{bene_id}/variazioni-catastali", response_model=List[VariazioneCatastaleResponse])
def get_variazioni_catastali(
    bene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.view")),
):
    """Storico delle variazioni dei dati catastali del bene, dalla più recente."""
    return (
        db.query(VariazioneCatastale)
        .filter(VariazioneCatastale.bene_id == bene_id)
        .order_by(VariazioneCatastale.created_at.desc(), VariazioneCatastale.id.desc())
        .all()
    )
