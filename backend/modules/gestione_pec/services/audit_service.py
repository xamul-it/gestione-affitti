"""
Servizio centralizzato per la scrittura degli audit log PEC.
Tutte le operazioni di audit usano questo servizio.
"""
import logging
from sqlalchemy.orm import Session
from ..models.audit_accesso import PecAuditAccesso

logger = logging.getLogger(__name__)


class AzioneAudit:
    OPEN_CASELLA = "OPEN_CASELLA"
    READ_MESSAGE = "READ_MESSAGE"
    SEARCH = "SEARCH"
    REPLY_SENT = "REPLY_SENT"  # usato in Fase 4


def log_accesso(
    db: Session,
    casella_id: int,
    user_id: int,
    azione: str,
    messaggio_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    dettagli: dict | None = None,
) -> None:
    """
    Registra un accesso. Non rilancia eccezioni — gli errori di audit
    non devono bloccare l'operazione principale.
    """
    try:
        record = PecAuditAccesso(
            casella_id=casella_id,
            messaggio_id=messaggio_id,
            user_id=user_id,
            azione=azione,
            ip_address=ip_address,
            user_agent=user_agent,
            dettagli=dettagli,
        )
        db.add(record)
        db.flush()
    except Exception as e:
        logger.warning(f"[audit] log_accesso failed: {e}")
