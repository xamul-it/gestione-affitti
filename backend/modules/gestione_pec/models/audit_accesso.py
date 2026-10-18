"""
Modello PecAuditAccesso — log append-only degli accessi alle caselle PEC.

Questo modello è append-only: non supporta UPDATE né DELETE.
Ogni accesso (apertura casella, lettura messaggio, ricerca) viene tracciato.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func
from app.core.database import Base


class PecAuditAccesso(Base):
    __tablename__ = "pec_audit_accessi"

    id = Column(Integer, primary_key=True, index=True)
    casella_id = Column(
        Integer,
        ForeignKey("pec_caselle.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    messaggio_id = Column(
        Integer,
        ForeignKey("pec_messaggi.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Intenzionalmente senza FK reale: cross-schema (public.core_users)
    user_id = Column(Integer, nullable=False, index=True)

    # Azioni tracciate: OPEN_CASELLA | READ_MESSAGE | SEARCH
    azione = Column(String(50), nullable=False)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    dettagli = Column(JSON, nullable=True)

    timestamp = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
