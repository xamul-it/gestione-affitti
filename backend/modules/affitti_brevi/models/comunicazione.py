"""
Comunicazione Model - Mandatory Communication Tracking

Tracks mandatory communications for short-term rental compliance:
- Police (Alloggiati Web): Guest data within 24h of check-in
- ISTAT: Statistical reporting (monthly/periodic)
- Municipality: Tourist tax declaration

Each communication has a status, deadline, and audit trail.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TipoComunicazione(str, enum.Enum):
    """Type of mandatory communication"""
    POLIZIA = "POLIZIA"                     # Alloggiati Web (guest data)
    ISTAT = "ISTAT"                         # Statistical reporting
    TASSA_DICHIARAZIONE = "TASSA_DICHIARAZIONE"  # Tourist tax declaration
    ALTRO = "ALTRO"


class StatoComunicazione(str, enum.Enum):
    """Communication status"""
    DA_PREPARARE = "DA_PREPARARE"           # To be prepared (data incomplete)
    PRONTA = "PRONTA"                       # Ready to send (data complete)
    IN_INVIO = "IN_INVIO"                   # Being sent
    INVIATA = "INVIATA"                     # Sent, awaiting confirmation
    CONFERMATA = "CONFERMATA"               # Confirmed by recipient
    ERRORE = "ERRORE"                       # Error during submission
    SCADUTA = "SCADUTA"                     # Deadline passed without sending
    ANNULLATA = "ANNULLATA"                 # Cancelled (e.g., booking cancelled)


class MetodoInvio(str, enum.Enum):
    """Submission method"""
    ALLOGGIATI_WEB = "ALLOGGIATI_WEB"       # Alloggiati Web portal
    SCHEDINE = "SCHEDINE"                   # Paper forms (deprecated)
    API = "API"                             # API integration
    PORTALE = "PORTALE"                     # Generic web portal
    EMAIL = "EMAIL"                         # Email submission
    MANUALE = "MANUALE"                     # Manual entry in external system


class Comunicazione(Base):
    """
    Mandatory Communication Record

    Tracks a single mandatory communication for compliance.
    Linked to a Soggiorno for guest-related communications (Police, ISTAT).
    Can also be standalone for periodic declarations (tax reporting).
    """
    __tablename__ = "ab_comunicazioni"

    id = Column(Integer, primary_key=True, index=True)

    # Link to stay (optional for periodic communications)
    soggiorno_id = Column(
        Integer,
        ForeignKey("ab_soggiorni.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Collegamento alla scadenza core (cross-schema: core_scadenze vive in
    # public, ab_comunicazioni nello schema tenant — nessun vincolo FK
    # reale possibile, stesso motivo per cui Scadenza.entity_id è un
    # intero libero verso le tabelle di modulo).
    scadenza_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="FK logica a core_scadenze.id"
    )

    # Link to property (for property-level communications)
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Communication type and status
    tipo = Column(String(30), nullable=False, index=True)
    stato = Column(String(30), default=StatoComunicazione.DA_PREPARARE.value,
                  nullable=False, index=True)

    # Deadline tracking
    data_scadenza = Column(DateTime(timezone=True), nullable=False, index=True)
    data_scadenza_legale = Column(DateTime(timezone=True), nullable=True,
                                 comment="Legal deadline (if different from operational)")
    urgente = Column(Boolean, default=False, nullable=False,
                    comment="True if deadline is approaching")
    scaduta = Column(Boolean, default=False, nullable=False)

    # Submission details
    metodo_invio = Column(String(30), nullable=True)
    data_invio = Column(DateTime(timezone=True), nullable=True, index=True)
    data_conferma = Column(DateTime(timezone=True), nullable=True)

    # Reference numbers
    numero_protocollo = Column(String(100), nullable=True,
                              comment="Protocol number from recipient")
    numero_ricevuta = Column(String(100), nullable=True)
    codice_struttura = Column(String(50), nullable=True,
                             comment="Property code for communications")

    # Data sent (JSON summary)
    dati_inviati = Column(Text, nullable=True,
                         comment="JSON summary of data sent")

    # Error handling
    errore_messaggio = Column(Text, nullable=True)
    tentativi_invio = Column(Integer, default=0, nullable=False)
    ultimo_tentativo = Column(DateTime(timezone=True), nullable=True)

    # File attachments
    file_ricevuta_path = Column(String(500), nullable=True)
    file_dati_path = Column(String(500), nullable=True,
                           comment="Path to exported data file")

    # Operator tracking
    operatore_preparazione = Column(String(100), nullable=True)
    operatore_invio = Column(String(100), nullable=True)

    # Period (for periodic communications like ISTAT)
    periodo_riferimento = Column(String(20), nullable=True,
                                comment="Reference period (e.g., '2026-01' for monthly)")

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    soggiorno = relationship(
        "Soggiorno",
        back_populates="comunicazioni"
    )
    unita_immobiliare = relationship(
        "UnitaImmobiliare",
        foreign_keys=[unita_immobiliare_id]
    )

    # Indexes
    __table_args__ = (
        Index('ix_ab_comunicazioni_tipo_stato',
              'tipo', 'stato'),
        Index('ix_ab_comunicazioni_scadenza',
              'data_scadenza', 'stato'),
    )

    def __repr__(self):
        return f"<Comunicazione(id={self.id}, tipo={self.tipo}, stato={self.stato})>"

    @property
    def is_in_tempo(self) -> bool:
        """Check if still within deadline"""
        from datetime import datetime, timezone
        if self.scaduta:
            return False
        return datetime.now(timezone.utc) < self.data_scadenza

    @property
    def ore_rimanenti(self) -> float:
        """Hours remaining until deadline"""
        from datetime import datetime, timezone
        if self.scaduta:
            return 0

        now = datetime.now(timezone.utc)
        if now >= self.data_scadenza:
            return 0

        delta = self.data_scadenza - now
        return delta.total_seconds() / 3600

    @property
    def is_pronta_per_invio(self) -> bool:
        """Check if communication is ready to send"""
        return self.stato in [
            StatoComunicazione.PRONTA.value,
            StatoComunicazione.ERRORE.value  # Can retry after error
        ]

    def verifica_scadenza(self):
        """Update scaduta flag based on current time"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if now >= self.data_scadenza:
            self.scaduta = True
            if self.stato in [StatoComunicazione.DA_PREPARARE.value,
                             StatoComunicazione.PRONTA.value]:
                self.stato = StatoComunicazione.SCADUTA.value

        # Mark as urgent if within 6 hours
        if not self.scaduta and self.ore_rimanenti <= 6:
            self.urgente = True

    def mark_inviata(self, metodo: MetodoInvio, protocollo: str = None, ricevuta: str = None):
        """Mark communication as sent"""
        from datetime import datetime, timezone
        self.stato = StatoComunicazione.INVIATA.value
        self.metodo_invio = metodo.value if isinstance(metodo, MetodoInvio) else metodo
        self.data_invio = datetime.now(timezone.utc)
        self.tentativi_invio += 1
        self.ultimo_tentativo = datetime.now(timezone.utc)
        if protocollo:
            self.numero_protocollo = protocollo
        if ricevuta:
            self.numero_ricevuta = ricevuta

    def mark_confermata(self, protocollo: str = None):
        """Mark communication as confirmed"""
        from datetime import datetime, timezone
        self.stato = StatoComunicazione.CONFERMATA.value
        self.data_conferma = datetime.now(timezone.utc)
        if protocollo:
            self.numero_protocollo = protocollo

    def mark_errore(self, messaggio: str):
        """Mark communication as failed"""
        from datetime import datetime, timezone
        self.stato = StatoComunicazione.ERRORE.value
        self.errore_messaggio = messaggio
        self.tentativi_invio += 1
        self.ultimo_tentativo = datetime.now(timezone.utc)

    def set_dati_inviati(self, data: dict):
        """Set sent data from dict"""
        import json
        self.dati_inviati = json.dumps(data, default=str)

    def get_dati_inviati(self) -> dict:
        """Get sent data as dict"""
        if not self.dati_inviati:
            return {}
        import json
        try:
            return json.loads(self.dati_inviati)
        except:
            return {}
