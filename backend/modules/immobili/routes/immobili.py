from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db
from datetime import date

from ..models import UnitaImmobiliare
from ..schemas.immobili import (
    UnitaImmobiliareCreate, UnitaImmobiliareUpdate, UnitaImmobiliareResponse,
)
from ..services.ape import classi_da_ape
from ..services.codici_beni import verifica_codice_libero
from ..services.elimina_bene import elimina_bene
from ..services.variazioni_catastali import registra_variazioni

router = APIRouter(prefix="/unita-immobiliari", tags=["Unità Immobiliari"])


def _risposte(db: Session, unita: List[UnitaImmobiliare]) -> List[UnitaImmobiliareResponse]:
    """Responses with the energy class of the current APE."""
    classi = classi_da_ape(db, [u.id for u in unita])
    return [UnitaImmobiliareResponse.model_validate(u).model_copy(update={"classe_energetica": classi.get(u.id)})
            for u in unita]


@router.get("/", response_model=List[UnitaImmobiliareResponse])
def get_unita_immobiliari(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.view")),
):
    """Ottieni lista di tutte le unità immobiliari"""
    unita_immobiliari = db.query(UnitaImmobiliare)\
        .options(joinedload(UnitaImmobiliare.categoria_catastale))\
        .offset(skip).limit(limit).all()
    return _risposte(db, unita_immobiliari)


@router.get("/{unita_immobiliare_id}", response_model=UnitaImmobiliareResponse)
def get_unita_immobiliare(
    unita_immobiliare_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.view")),
):
    """Ottieni dettagli di un'unità immobiliare specifica"""
    unita_immobiliare = db.query(UnitaImmobiliare)\
        .options(joinedload(UnitaImmobiliare.categoria_catastale))\
        .filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not unita_immobiliare:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {unita_immobiliare_id} non trovato"
        )
    return _risposte(db, [unita_immobiliare])[0]


@router.post("/", response_model=UnitaImmobiliareResponse, status_code=status.HTTP_201_CREATED)
def create_unita_immobiliare(
    unita_immobiliare: UnitaImmobiliareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.create")),
):
    """Crea una nuova unità immobiliare"""
    verifica_codice_libero(db, unita_immobiliare.codice)

    new_unita = UnitaImmobiliare(**unita_immobiliare.model_dump())
    db.add(new_unita)
    db.commit()
    db.refresh(new_unita)
    return _risposte(db, [new_unita])[0]


@router.put("/{unita_immobiliare_id}", response_model=UnitaImmobiliareResponse)
def update_unita_immobiliare(
    unita_immobiliare_id: int,
    unita_immobiliare: UnitaImmobiliareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.edit")),
):
    """Aggiorna un'unità immobiliare esistente"""
    db_unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not db_unita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {unita_immobiliare_id} non trovato"
        )

    update_data = unita_immobiliare.model_dump(exclude_unset=True)
    verifica_codice_libero(db, update_data.get("codice"), escludi_id=unita_immobiliare_id)
    registra_variazioni(
        db, db_unita, update_data,
        origine="MANUALE", documento_id=None, data_riferimento=date.today(), utente_id=current_user.id,
    )
    for field, value in update_data.items():
        setattr(db_unita, field, value)

    db.commit()
    db.refresh(db_unita)
    return _risposte(db, [db_unita])[0]


@router.delete("/{unita_immobiliare_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unita_immobiliare(
    unita_immobiliare_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("immobile.delete")),
):
    """Elimina un'unità immobiliare"""
    db_unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == unita_immobiliare_id).first()
    if not db_unita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {unita_immobiliare_id} non trovato"
        )

    elimina_bene(db, db_unita, getattr(current_user, "id", None))
    db.commit()
    return None
