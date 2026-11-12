from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from ..models import AssegnazioneConduttore, Bene, Conduttore
from ..schemas import (
    AssegnazioneConduttoreCreate,
    AssegnazioneConduttoreUpdate,
    AssegnazioneConduttoreResponse,
)

router = APIRouter(prefix="/assegnazioni-conduttore", tags=["assegnazioni-conduttore"])


def _vede_soggetti(user) -> bool:
    """Names of anagrafiche need soggetto.view, as in the relazioni API."""
    permessi = user.get_permissions() if hasattr(user, "get_permissions") else set()
    return "*" in permessi or "soggetto.view" in permessi


def _con_nome(db: Session, assegnazioni, user):
    """Attach soggetto_id and conduttore_nome to each assignment (one query),
    only for users allowed to see anagrafiche."""
    from anagrafica_italiana.models import SoggettoAnagrafico

    if not _vede_soggetti(user):
        for a in assegnazioni:
            a.soggetto_id = None
            a.conduttore_nome = None
        return assegnazioni
    ids = {a.conduttore_id for a in assegnazioni}
    righe = (
        db.query(Conduttore.id, SoggettoAnagrafico)
        .join(SoggettoAnagrafico, SoggettoAnagrafico.id == Conduttore.soggetto_id)
        .filter(Conduttore.id.in_(ids))
        .all()
        if ids else []
    )
    per_conduttore = {cid: s for cid, s in righe}
    for a in assegnazioni:
        s = per_conduttore.get(a.conduttore_id)
        a.soggetto_id = s.id if s else None
        a.conduttore_nome = (
            (s.ragione_sociale or " ".join(p for p in (s.nome, s.cognome) if p)) or None
        ) if s else None
    return assegnazioni


@router.get("/", response_model=List[AssegnazioneConduttoreResponse])
def get_assegnazioni(
    bene_id: Optional[int] = Query(None),
    conduttore_id: Optional[int] = Query(None),
    solo_correnti: bool = Query(False, description="Solo assegnazioni senza data_fine (in corso)"),
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("conduttore.view")),
):
    """Recupera tutte le assegnazioni con filtri opzionali"""
    query = db.query(AssegnazioneConduttore)

    if bene_id:
        query = query.filter(AssegnazioneConduttore.bene_id == bene_id)
    if conduttore_id:
        query = query.filter(AssegnazioneConduttore.conduttore_id == conduttore_id)
    if solo_correnti:
        query = query.filter(AssegnazioneConduttore.data_fine.is_(None))

    return _con_nome(db, query.order_by(AssegnazioneConduttore.bene_id, AssegnazioneConduttore.data_inizio).all(), current_user)


@router.get("/bene/{bene_id}", response_model=List[AssegnazioneConduttoreResponse])
def get_assegnazioni_by_bene(bene_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("conduttore.view"))):
    """Recupera tutte le assegnazioni (storiche e correnti) di un bene"""
    bene = db.query(Bene).filter(Bene.id == bene_id).first()
    if not bene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bene non trovato")

    return _con_nome(db, db.query(AssegnazioneConduttore).filter(
        AssegnazioneConduttore.bene_id == bene_id
    ).order_by(AssegnazioneConduttore.data_inizio.desc()).all(), current_user)


@router.get("/{assegnazione_id}", response_model=AssegnazioneConduttoreResponse)
def get_assegnazione(assegnazione_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("conduttore.view"))):
    """Recupera una assegnazione specifica"""
    assegnazione = db.query(AssegnazioneConduttore).filter(AssegnazioneConduttore.id == assegnazione_id).first()
    if not assegnazione:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assegnazione non trovata")
    return _con_nome(db, [assegnazione], current_user)[0]


@router.post("/", response_model=AssegnazioneConduttoreResponse, status_code=status.HTTP_201_CREATED)
def create_assegnazione(assegnazione: AssegnazioneConduttoreCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("conduttore.create"))):
    """Assegna un conduttore a un bene per un periodo"""
    bene = db.query(Bene).filter(Bene.id == assegnazione.bene_id).first()
    if not bene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bene non trovato")

    conduttore = db.query(Conduttore).filter(Conduttore.id == assegnazione.conduttore_id).first()
    if not conduttore:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conduttore non trovato")

    db_assegnazione = AssegnazioneConduttore(**assegnazione.model_dump())
    db.add(db_assegnazione)
    db.commit()
    db.refresh(db_assegnazione)
    return _con_nome(db, [db_assegnazione], current_user)[0]


@router.put("/{assegnazione_id}", response_model=AssegnazioneConduttoreResponse)
def update_assegnazione(
    assegnazione_id: int,
    assegnazione: AssegnazioneConduttoreUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("conduttore.edit")),
):
    """Aggiorna una assegnazione (es. valorizzare data_fine per chiuderla)"""
    db_assegnazione = db.query(AssegnazioneConduttore).filter(AssegnazioneConduttore.id == assegnazione_id).first()
    if not db_assegnazione:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assegnazione non trovata")

    for key, value in assegnazione.model_dump(exclude_unset=True).items():
        setattr(db_assegnazione, key, value)

    db.commit()
    db.refresh(db_assegnazione)
    return _con_nome(db, [db_assegnazione], current_user)[0]


@router.delete("/{assegnazione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assegnazione(assegnazione_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("conduttore.delete"))):
    """Elimina una assegnazione"""
    db_assegnazione = db.query(AssegnazioneConduttore).filter(AssegnazioneConduttore.id == assegnazione_id).first()
    if not db_assegnazione:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assegnazione non trovata")

    db.delete(db_assegnazione)
    db.commit()
    return None
