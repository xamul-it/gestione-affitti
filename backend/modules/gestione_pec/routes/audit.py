"""
Route di sola lettura per l'audit PEC.

Endpoint:
  GET /pec/audit/accessi   — log accessi (pec.audit.view)
  GET /pec/audit/risposte  — log risposte inviate (pec.audit.view)
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import require_permission

from ..models.audit_accesso import PecAuditAccesso
from ..models.audit_risposta import PecAuditRisposta
from ..schemas.audit import AuditAccessoRead, AuditRispostaRead

router = APIRouter(prefix="/pec/audit", tags=["pec-audit"])


@router.get("/accessi", response_model=List[AuditAccessoRead])
def list_audit_accessi(
    casella_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    azione: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(require_permission("pec.audit.view")),
):
    """Restituisce il log degli accessi alle caselle PEC, ordinato dal più recente."""
    q = db.query(PecAuditAccesso)
    if casella_id is not None:
        q = q.filter(PecAuditAccesso.casella_id == casella_id)
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
    _: dict = Depends(require_permission("pec.audit.view")),
):
    """Restituisce il log immutabile delle risposte PEC inviate."""
    q = db.query(PecAuditRisposta)
    if casella_id is not None:
        q = q.filter(PecAuditRisposta.casella_id == casella_id)
    if user_id is not None:
        q = q.filter(PecAuditRisposta.user_id == user_id)
    if smtp_status:
        q = q.filter(PecAuditRisposta.smtp_status == smtp_status.upper())
    q = q.order_by(PecAuditRisposta.created_at.desc())
    return q.offset(offset).limit(limit).all()
