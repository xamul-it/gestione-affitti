"""
Route di sola lettura per l'audit PEC.

Endpoint:
  GET /pec/audit/accessi   — log accessi (pec.audit.view)
  GET /pec/audit/risposte  — log risposte inviate (pec.audit.view)

Come per /pec/messaggi, pec.audit.view da solo non basta a vedere
l'audit di qualsiasi casella: chi non ha pec.admin (e non è superuser)
vede solo le caselle per cui è abilitato in pec_utenti_abilitati.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import get_current_active_user, require_permission
from app.core.auth.models import User

from ..models.audit_accesso import PecAuditAccesso
from ..models.audit_risposta import PecAuditRisposta
from ..models.utente_abilitato import PecUtenteAbilitato
from ..schemas.audit import AuditAccessoRead, AuditRispostaRead

router = APIRouter(prefix="/pec/audit", tags=["pec-audit"])


def _ha_permesso_admin(user: User) -> bool:
    """Ritorna True se l'utente è superuser o ha il permesso pec.admin."""
    if user.is_superuser:
        return True
    perms = user.get_permissions()
    return "pec.admin" in perms or "*" in perms


def _caselle_abilitate_ids(db: Session, user: User) -> List[int]:
    """ID delle caselle per cui l'utente è esplicitamente abilitato."""
    rows = (
        db.query(PecUtenteAbilitato.casella_id)
        .filter(PecUtenteAbilitato.user_id == user.id)
        .all()
    )
    return [row[0] for row in rows]


def _applica_scoping_casella(query, model, casella_id: Optional[int], db: Session, user: User):
    """
    Applica il filtro per-casella alla query di audit:
    - admin/superuser: nessuna restrizione oltre a un eventuale casella_id richiesto.
    - altri: se casella_id è specificato deve essere tra le caselle abilitate
      (403 altrimenti); se non specificato, la query è limitata alle sole
      caselle abilitate.
    """
    if _ha_permesso_admin(user):
        if casella_id is not None:
            query = query.filter(model.casella_id == casella_id)
        return query

    abilitate = _caselle_abilitate_ids(db, user)
    if casella_id is not None:
        if casella_id not in abilitate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accesso non autorizzato alla casella",
            )
        return query.filter(model.casella_id == casella_id)

    return query.filter(model.casella_id.in_(abilitate)) if abilitate else query.filter(False)


@router.get("/accessi", response_model=List[AuditAccessoRead])
def list_audit_accessi(
    casella_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    azione: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: dict = Depends(require_permission("pec.audit.view")),
):
    """Restituisce il log degli accessi alle caselle PEC, ordinato dal più recente."""
    q = db.query(PecAuditAccesso)
    q = _applica_scoping_casella(q, PecAuditAccesso, casella_id, db, current_user)
    if user_id is not None:
        q = q.filter(PecAuditAccesso.user_id == user_id)
    if azione:
        q = q.filter(PecAuditAccesso.azione == azione.upper())
    q = q.order_by(PecAuditAccesso.timestamp.desc())
    return q.offset(offset).limit(limit).all()


@router.get("/risposte", response_model=List[AuditRispostaRead])
def list_audit_risposte(
    casella_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    smtp_status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: dict = Depends(require_permission("pec.audit.view")),
):
    """Restituisce il log immutabile delle risposte PEC inviate."""
    q = db.query(PecAuditRisposta)
    q = _applica_scoping_casella(q, PecAuditRisposta, casella_id, db, current_user)
    if user_id is not None:
        q = q.filter(PecAuditRisposta.user_id == user_id)
    if smtp_status:
        q = q.filter(PecAuditRisposta.smtp_status == smtp_status.upper())
    q = q.order_by(PecAuditRisposta.created_at.desc())
    return q.offset(offset).limit(limit).all()
