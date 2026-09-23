"""
Routes for recurring property expenses/deadlines (IMU, TARI, utility bills).

Each spesa ricorrente optionally creates a linked core Scadenza for
reminders/notifications (via ScadenzaService), so a user_id is required —
these routes require authentication (unlike most of this module's CRUD,
which predates any auth wiring), since they touch financial data and
create audit-logged reminder rows on the user's behalf.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db
from app.core.platform.models import PrioritaScadenza
from app.core.platform_services import ScadenzaService
from app.core.schemas import ScadenzaCreate

from ..models import Condominio, SpesaRicorrenteImmobile, UnitaImmobiliare
from ..schemas import (
    DuplicaSpesaRequest,
    SegnaPagatoRequest,
    SpesaRicorrenteCreate,
    SpesaRicorrenteResponse,
    SpesaRicorrenteUpdate,
)

router = APIRouter(prefix="/spese-ricorrenti", tags=["spese-ricorrenti"])


def _titolo(spesa: SpesaRicorrenteImmobile, target_label: str) -> str:
    rata = f" ({spesa.rata})" if spesa.rata else ""
    return f"{spesa.tipo_spesa} {spesa.periodo}{rata} - {target_label}"


@router.get("/", response_model=List[SpesaRicorrenteResponse])
def get_spese_ricorrenti(
    unita_immobiliare_id: Optional[int] = Query(None),
    condominio_id: Optional[int] = Query(None),
    pagato: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.read")),
):
    """Recupera le spese ricorrenti con filtri opzionali"""
    query = db.query(SpesaRicorrenteImmobile)
    if unita_immobiliare_id:
        query = query.filter(SpesaRicorrenteImmobile.unita_immobiliare_id == unita_immobiliare_id)
    if condominio_id:
        query = query.filter(SpesaRicorrenteImmobile.condominio_id == condominio_id)
    if pagato is not None:
        query = query.filter(SpesaRicorrenteImmobile.pagato == pagato)
    return query.order_by(SpesaRicorrenteImmobile.data_scadenza.desc()).all()


@router.get("/{spesa_id}", response_model=SpesaRicorrenteResponse)
def get_spesa_ricorrente(
    spesa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.read")),
):
    """Recupera una spesa ricorrente specifica"""
    spesa = db.query(SpesaRicorrenteImmobile).filter(SpesaRicorrenteImmobile.id == spesa_id).first()
    if not spesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spesa ricorrente non trovata")
    return spesa


@router.post("/", response_model=SpesaRicorrenteResponse, status_code=status.HTTP_201_CREATED)
def create_spesa_ricorrente(
    spesa: SpesaRicorrenteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.write")),
):
    """
    Crea una nuova spesa/scadenza ricorrente per un'unità immobiliare o un
    condominio, e un promemoria collegato nello scadenzario di piattaforma.
    """
    target_label: str
    if spesa.unita_immobiliare_id:
        unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == spesa.unita_immobiliare_id).first()
        if not unita:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unità immobiliare non trovata")
        target_label = unita.codice
    else:
        condominio = db.query(Condominio).filter(Condominio.id == spesa.condominio_id).first()
        if not condominio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condominio non trovato")
        target_label = condominio.nome

    data = spesa.model_dump(exclude={"destinatari_ids"})
    db_spesa = SpesaRicorrenteImmobile(**data)
    db.add(db_spesa)
    db.flush()  # get db_spesa.id

    scadenza_service = ScadenzaService(db)
    scadenza = scadenza_service.create_scadenza(
        ScadenzaCreate(
            modulo="immobili",
            entity_type="SPESA_RICORRENTE",
            entity_id=db_spesa.id,
            titolo=_titolo(db_spesa, target_label),
            descrizione=spesa.note,
            data_scadenza=spesa.data_scadenza,
            priorita=PrioritaScadenza.ALTA,
            destinatari_ids=spesa.destinatari_ids or [],
        ),
        user_id=current_user.id,
    )
    db_spesa.scadenza_id = scadenza.id

    db.commit()
    db.refresh(db_spesa)
    return db_spesa


@router.put("/{spesa_id}", response_model=SpesaRicorrenteResponse)
def update_spesa_ricorrente(
    spesa_id: int,
    spesa: SpesaRicorrenteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.write")),
):
    """Aggiorna una spesa ricorrente (es. correggere importo prima del pagamento)"""
    db_spesa = db.query(SpesaRicorrenteImmobile).filter(SpesaRicorrenteImmobile.id == spesa_id).first()
    if not db_spesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spesa ricorrente non trovata")

    for key, value in spesa.model_dump(exclude_unset=True).items():
        setattr(db_spesa, key, value)

    db.commit()
    db.refresh(db_spesa)
    return db_spesa


@router.post("/{spesa_id}/segna-pagato", response_model=SpesaRicorrenteResponse)
def segna_pagato(
    spesa_id: int,
    payload: SegnaPagatoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.write")),
):
    """Segna una spesa ricorrente come pagata e completa il promemoria collegato"""
    db_spesa = db.query(SpesaRicorrenteImmobile).filter(SpesaRicorrenteImmobile.id == spesa_id).first()
    if not db_spesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spesa ricorrente non trovata")

    db_spesa.pagato = True
    db_spesa.data_pagamento = payload.data_pagamento or date.today()
    if payload.note:
        db_spesa.note = payload.note

    if db_spesa.scadenza_id:
        ScadenzaService(db).completa_scadenza(
            db_spesa.scadenza_id,
            user_id=current_user.id,
            note=f"Pagato il {db_spesa.data_pagamento.isoformat()}",
        )

    db.commit()
    db.refresh(db_spesa)
    return db_spesa


@router.post("/{spesa_id}/duplica", response_model=SpesaRicorrenteResponse, status_code=status.HTTP_201_CREATED)
def duplica_spesa_ricorrente(
    spesa_id: int,
    payload: DuplicaSpesaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.write")),
):
    """
    Duplica una spesa ricorrente per un nuovo periodo (es. l'anno
    successivo), pre-compilando tipo/responsabile/target e — salvo
    diversa indicazione — importo e rata dell'originale. Non c'è
    generazione automatica ricorrente: aliquote e importi di IMU/TARI e
    utenze sono decisi esternamente (comune, stato, fornitore) e cambiano
    ogni periodo, quindi ogni nuova occorrenza va creata (e confermata)
    esplicitamente.
    """
    originale = db.query(SpesaRicorrenteImmobile).filter(SpesaRicorrenteImmobile.id == spesa_id).first()
    if not originale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spesa ricorrente non trovata")

    if originale.unita_immobiliare_id:
        target_label = originale.unita_immobiliare.codice
    else:
        target_label = originale.condominio.nome

    nuova = SpesaRicorrenteImmobile(
        unita_immobiliare_id=originale.unita_immobiliare_id,
        condominio_id=originale.condominio_id,
        tipo_spesa=originale.tipo_spesa,
        responsabile=originale.responsabile,
        periodo=payload.periodo,
        rata=payload.rata if payload.rata is not None else originale.rata,
        importo=payload.importo if payload.importo is not None else originale.importo,
        data_scadenza=payload.data_scadenza,
        pagato=False,
    )
    db.add(nuova)
    db.flush()

    scadenza_service = ScadenzaService(db)
    scadenza = scadenza_service.create_scadenza(
        ScadenzaCreate(
            modulo="immobili",
            entity_type="SPESA_RICORRENTE",
            entity_id=nuova.id,
            titolo=_titolo(nuova, target_label),
            data_scadenza=nuova.data_scadenza,
            priorita=PrioritaScadenza.ALTA,
        ),
        user_id=current_user.id,
    )
    nuova.scadenza_id = scadenza.id

    db.commit()
    db.refresh(nuova)
    return nuova


@router.delete("/{spesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spesa_ricorrente(
    spesa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("spese_ricorrenti_immobile.delete")),
):
    """Elimina una spesa ricorrente (il promemoria collegato resta, orfano di riferimento)"""
    db_spesa = db.query(SpesaRicorrenteImmobile).filter(SpesaRicorrenteImmobile.id == spesa_id).first()
    if not db_spesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spesa ricorrente non trovata")

    db.delete(db_spesa)
    db.commit()
    return None
