"""
Modello PecAuditRisposta — log append-only delle risposte inviate via PEC.

Questo modello è append-only e garantisce la non-ripudiabilità: include uno
snapshot immutabile del messaggio originale al momento della risposta e un
hash di integrità.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from app.core.database import Base


class PecAuditRisposta(Base):
    __tablename__ = "pec_audit_risposte"

    id = Column(Integer, primary_key=True, index=True)
    casella_id = Column(
        Integer,
        ForeignKey("pec_caselle.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    messaggio_originale_id = Column(
        Integer,
        ForeignKey("pec_messaggi.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Intenzionalmente senza FK reale: cross-schema (public.core_users)
    user_id = Column(Integer, nullable=False, index=True)

    # Dati della risposta inviata
    destinatari = Column(Text, nullable=True)
    oggetto_risposta = Column(String(1000), nullable=True)
    corpo_risposta_testo = Column(Text, nullable=True)
    corpo_risposta_html = Column(Text, nullable=True)
    message_id_risposta = Column(String(500), nullable=True)

    # Snapshot immutabile del messaggio originale al momento della risposta
    snapshot_da = Column(String(500), nullable=True)
    snapshot_oggetto = Column(String(1000), nullable=True)
    snapshot_corpo_testo = Column(Text, nullable=True)
    snapshot_data_invio = Column(DateTime(timezone=True), nullable=True)

    # Stato invio SMTP: SENT | FAILED | QUEUED
    smtp_status = Column(String(20), nullable=True)
    smtp_error = Column(Text, nullable=True)

    # Hash per non-ripudio (SHA-256 dei campi chiave della risposta)
    hash_integrita = Column(String(64), nullable=True)

    inviato_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
