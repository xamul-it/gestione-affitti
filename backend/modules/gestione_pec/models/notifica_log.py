"""
Modello PecNotificaLog — log delle notifiche email inviate agli utenti abilitati.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from app.core.database import Base


class PecNotificaLog(Base):
    __tablename__ = "pec_notifiche_log"

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

    email_destinatario = Column(String(255), nullable=False)

    # Stato notifica: SENT | FAILED
    stato = Column(String(20), nullable=False)
    errore = Column(Text, nullable=True)

    sent_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
