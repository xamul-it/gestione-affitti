"""
Modello PecCasella — configurazione di una casella PEC.

Le credenziali (username, password) sono SEMPRE cifrate con Fernet prima del salvataggio.
Il modello non gestisce mai credenziali in chiaro: la cifratura avviene nel route layer.
"""
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.sql import func
from app.core.database import Base


class PecCasella(Base):
    __tablename__ = "pec_caselle"

    id = Column(Integer, primary_key=True, index=True)
    nome_display = Column(String(200), nullable=False)
    indirizzo_pec = Column(String(255), nullable=False)

    # Protocollo di connessione
    protocollo = Column(String(10), nullable=False, default="IMAP")

    # Configurazione IMAP
    imap_host = Column(String(255), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)
    imap_ssl = Column(Boolean, nullable=False, default=True)
    imap_folder = Column(String(100), nullable=False, default="INBOX")

    # Comportamento flag \Seen sul server.
    # False → usa BODY.PEEK[], il flag \Seen NON viene impostato sul server.
    # True  → usa BODY[] normale, il server marca il messaggio come letto.
    segna_letto_su_server = Column(Boolean, nullable=False, default=False)

    # Configurazione SMTP (opzionale, per invio risposte)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True, default=465)
    smtp_tls = Column(String(20), nullable=True)  # "SSL" | "STARTTLS" | "none"

    # Credenziali sempre cifrate con Fernet — mai in chiaro
    username_enc = Column(Text, nullable=False)
    password_enc = Column(Text, nullable=False)

    # Configurazione polling
    polling_intervallo_minuti = Column(Integer, nullable=False, default=15)
    is_attiva = Column(Boolean, nullable=False, default=True)
    ultimo_polling_at = Column(DateTime(timezone=True), nullable=True)
    ultimo_uid_visto = Column(String(100), nullable=True)  # per polling incrementale
    errori_consecutivi = Column(Integer, nullable=False, default=0)
    ultimo_errore = Column(Text, nullable=True)

    note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("indirizzo_pec", name="uq_pec_caselle_indirizzo_pec"),
    )
