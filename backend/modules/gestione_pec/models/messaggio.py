"""
Modello PecMessaggio — un singolo messaggio PEC ricevuto.

Il flag is_letto è gestito internamente dall'applicazione e NON viene mai
propagato al server IMAP (per quello esiste segna_letto_su_server su PecCasella).
"""
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PecMessaggio(Base):
    __tablename__ = "pec_messaggi"

    id = Column(Integer, primary_key=True, index=True)
    casella_id = Column(
        Integer,
        ForeignKey("pec_caselle.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identificatori IMAP/RFC 2822
    uid_imap = Column(String(100), nullable=False)
    message_id = Column(String(500), nullable=True)
    in_reply_to = Column(String(500), nullable=True)
    thread_id = Column(String(500), nullable=True, index=True)

    # Intestazioni
    da = Column(String(500), nullable=False)
    a = Column(Text, nullable=True)
    cc = Column(Text, nullable=True)
    oggetto = Column(String(1000), nullable=True)
    data_invio = Column(DateTime(timezone=True), nullable=True)
    data_ricezione = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Corpo
    corpo_testo = Column(Text, nullable=True)
    corpo_html = Column(Text, nullable=True)

    # Allegati: lista di dict [{nome, content_type, dimensione_bytes, part_id}]
    allegati_meta = Column(JSON, nullable=True)

    # Stato applicativo (MAI propagato al server)
    is_letto = Column(Boolean, nullable=False, default=False)
    is_risposto = Column(Boolean, nullable=False, default=False)

    # SHA-256 del contenuto per deduplicazione
    hash_contenuto = Column(String(64), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    casella = relationship("PecCasella", backref="messaggi")

    __table_args__ = (
        UniqueConstraint(
            "casella_id", "uid_imap", name="uq_pec_messaggi_casella_uid"
        ),
    )
