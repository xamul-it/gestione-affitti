"""
Route per la lettura dei messaggi PEC.

Tutti gli endpoint richiedono il permesso `pec.read`.
L'accesso a ciascuna casella è ulteriormente vincolato all'abilitazione
esplicita dell'utente in pec_utenti_abilitati, con bypass per pec.admin.
"""
import logging
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import get_current_active_user, require_permission
from app.core.auth.models import User

from ..models.casella import PecCasella
from ..models.messaggio import PecMessaggio
from ..models.utente_abilitato import PecUtenteAbilitato
from ..schemas.messaggio import MessaggioList, MessaggioRead
from ..services.audit_service import AzioneAudit, log_accesso

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pec/messaggi",
    tags=["PEC - Messaggi"],
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _ha_permesso_admin(user: User) -> bool:
    """Ritorna True se l'utente è superuser o ha il permesso pec.admin."""
    if user.is_superuser:
        return True
    perms = user.get_permissions()
    return "pec.admin" in perms or "*" in perms


def _verifica_accesso_casella(db: Session, casella_id: int, user: User) -> PecCasella:
    """
    Verifica che l'utente abbia accesso alla casella.
    - Superuser o utenti con pec.admin hanno accesso a tutte le caselle.
    - Gli altri devono essere presenti in pec_utenti_abilitati.
    Ritorna la casella, o alza 403/404.
    """
    casella = db.query(PecCasella).filter(PecCasella.id == casella_id).first()
    if not casella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Casella PEC con ID {casella_id} non trovata",
        )

    if _ha_permesso_admin(user):
        return casella

    abilitato = (
        db.query(PecUtenteAbilitato)
        .filter(
            PecUtenteAbilitato.casella_id == casella_id,
            PecUtenteAbilitato.user_id == user.id,
        )
        .first()
    )
    if not abilitato:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso non autorizzato alla casella",
        )
    return casella


def _get_messaggio_or_404(messaggio_id: int, db: Session) -> PecMessaggio:
    msg = db.query(PecMessaggio).filter(PecMessaggio.id == messaggio_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Messaggio con ID {messaggio_id} non trovato",
        )
    return msg


# ---------------------------------------------------------------------------
# Schema inline per la richiesta segna-letto
# ---------------------------------------------------------------------------


class SegnaLettoPayload(BaseModel):
    letto: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=dict,
    dependencies=[Depends(require_permission("pec.read"))],
)
def list_messaggi(
    request: Request,
    casella_id: int,
    page: int = 1,
    page_size: int = 50,
    solo_non_letti: bool = False,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Restituisce i messaggi di una casella PEC con paginazione e filtri.

    Verifica che l'utente sia abilitato alla casella (o abbia pec.admin).
    Registra l'audit OPEN_CASELLA per la prima pagina.
    """
    # Limita page_size massimo
    page_size = min(page_size, 200)
    if page < 1:
        page = 1

    _verifica_accesso_casella(db, casella_id, current_user)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    # Audit: registra apertura casella con il numero di pagina nei dettagli
    log_accesso(
        db=db,
        casella_id=casella_id,
        user_id=current_user.id,
        azione=AzioneAudit.OPEN_CASELLA,
        ip_address=ip,
        user_agent=ua,
        dettagli={"page": page},
    )

    query = db.query(PecMessaggio).filter(PecMessaggio.casella_id == casella_id)

    if solo_non_letti:
        query = query.filter(PecMessaggio.is_letto == False)  # noqa: E712

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            (PecMessaggio.oggetto.ilike(like_q)) | (PecMessaggio.da.ilike(like_q))
        )

    total = query.count()
    pages = max(1, math.ceil(total / page_size))

    items = (
        query.order_by(PecMessaggio.data_ricezione.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [MessaggioList.model_validate(m) for m in items],
        "total": total,
        "page": page,
        "pages": pages,
    }


@router.get(
    "/{messaggio_id}",
    response_model=MessaggioRead,
    dependencies=[Depends(require_permission("pec.read"))],
)
def get_messaggio(
    messaggio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PecMessaggio:
    """
    Restituisce il dettaglio completo di un messaggio PEC.

    Marca automaticamente il messaggio come letto e registra l'audit READ_MESSAGE.
    """
    msg = _get_messaggio_or_404(messaggio_id, db)
    _verifica_accesso_casella(db, msg.casella_id, current_user)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    log_accesso(
        db=db,
        casella_id=msg.casella_id,
        user_id=current_user.id,
        azione=AzioneAudit.READ_MESSAGE,
        messaggio_id=msg.id,
        ip_address=ip,
        user_agent=ua,
    )

    # Marca come letto indipendentemente da segna_letto_su_server (lato IMAP)
    if not msg.is_letto:
        msg.is_letto = True
        db.commit()
        db.refresh(msg)

    return msg


@router.post(
    "/{messaggio_id}/segna-letto",
    dependencies=[Depends(require_permission("pec.read"))],
)
def segna_letto(
    messaggio_id: int,
    payload: SegnaLettoPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, bool]:
    """
    Segna manualmente un messaggio come letto o non letto.
    """
    msg = _get_messaggio_or_404(messaggio_id, db)
    _verifica_accesso_casella(db, msg.casella_id, current_user)

    msg.is_letto = payload.letto
    db.commit()

    return {"ok": True}


@router.get(
    "/{messaggio_id}/thread",
    response_model=list[MessaggioList],
    dependencies=[Depends(require_permission("pec.read"))],
)
def get_thread(
    messaggio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PecMessaggio]:
    """
    Restituisce tutti i messaggi dello stesso thread, ordinati per data_invio ASC.
    """
    msg = _get_messaggio_or_404(messaggio_id, db)
    _verifica_accesso_casella(db, msg.casella_id, current_user)

    if not msg.thread_id:
        # Nessun thread: restituisce solo il messaggio corrente
        return [msg]

    thread = (
        db.query(PecMessaggio)
        .filter(
            PecMessaggio.casella_id == msg.casella_id,
            PecMessaggio.thread_id == msg.thread_id,
        )
        .order_by(PecMessaggio.data_invio.asc())
        .all()
    )
    return thread
