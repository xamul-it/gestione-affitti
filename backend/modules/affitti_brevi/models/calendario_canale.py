"""
CalendarioCanale Model - Property-Channel Link with iCal Configuration

Links a property (UnitaImmobiliare) to a booking channel with optional iCal sync.
Each property can have multiple channel configurations.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class StatoSincronizzazione(str, enum.Enum):
    """iCal synchronization status"""
    MAI_SINCRONIZZATO = "MAI_SINCRONIZZATO"
    IN_CORSO = "IN_CORSO"
    SUCCESSO = "SUCCESSO"
    ERRORE = "ERRORE"


class CalendarioCanale(Base):
    """
    Property-Channel Configuration

    Links a property to a booking channel with iCal synchronization settings.
    Tracks sync status and stores external dashboard links.

    One property can have multiple channels (Airbnb + Booking.com + Direct).
    Each channel configuration is unique per property.
    """
    __tablename__ = "ab_calendari_canali"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to property
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Reference to channel
    canale_id = Column(
        Integer,
        ForeignKey("ab_canali.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # External identifiers
    codice_esterno = Column(String(100), nullable=True,
                           comment="Property ID on the external platform")
    url_annuncio = Column(String(500), nullable=True,
                         comment="Direct link to property listing on platform")

    # iCal configuration
    url_ical = Column(String(500), nullable=True,
                     comment="iCal feed URL for import")
    url_ical_export = Column(String(500), nullable=True,
                            comment="iCal export URL for channel managers")

    # Sync status tracking
    stato_sincronizzazione = Column(
        String(30),
        default=StatoSincronizzazione.MAI_SINCRONIZZATO.value,
        nullable=False
    )
    ultima_sincronizzazione = Column(DateTime(timezone=True), nullable=True)
    errore_sincronizzazione = Column(Text, nullable=True)
    prenotazioni_importate = Column(Integer, default=0,
                                   comment="Total bookings imported from this channel")

    # Sync settings
    sync_attiva = Column(Boolean, default=True, nullable=False,
                        comment="Enable/disable automatic sync")
    intervallo_sync_ore = Column(Integer, default=6, nullable=False,
                                comment="Hours between automatic syncs")

    # Enable/disable channel
    attivo = Column(Boolean, default=True, nullable=False,
                   comment="Whether this channel is active for this property")

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship(
        "UnitaImmobiliare",
        foreign_keys=[unita_immobiliare_id],
        backref="calendari_canali"
    )
    canale = relationship(
        "Canale",
        foreign_keys=[canale_id],
        backref="calendari"
    )

    # Unique constraint: one channel per property
    __table_args__ = (
        UniqueConstraint('unita_immobiliare_id', 'canale_id',
                        name='uq_calendario_canale_immobile_canale'),
    )

    def __repr__(self):
        return f"<CalendarioCanale(id={self.id}, immobile={self.unita_immobiliare_id}, canale={self.canale_id})>"

    @property
    def is_sync_pending(self):
        """Check if sync should be performed"""
        if not self.sync_attiva or not self.url_ical:
            return False

        if self.stato_sincronizzazione == StatoSincronizzazione.MAI_SINCRONIZZATO.value:
            return True

        if not self.ultima_sincronizzazione:
            return True

        from datetime import datetime, timezone, timedelta
        next_sync = self.ultima_sincronizzazione + timedelta(hours=self.intervallo_sync_ore)
        return datetime.now(timezone.utc) >= next_sync

    def mark_sync_started(self):
        """Mark synchronization as started"""
        self.stato_sincronizzazione = StatoSincronizzazione.IN_CORSO.value

    def mark_sync_success(self, prenotazioni_count: int = 0):
        """Mark synchronization as successful"""
        from datetime import datetime, timezone
        self.stato_sincronizzazione = StatoSincronizzazione.SUCCESSO.value
        self.ultima_sincronizzazione = datetime.now(timezone.utc)
        self.errore_sincronizzazione = None
        self.prenotazioni_importate += prenotazioni_count

    def mark_sync_error(self, error_message: str):
        """Mark synchronization as failed"""
        self.stato_sincronizzazione = StatoSincronizzazione.ERRORE.value
        self.errore_sincronizzazione = error_message[:500] if error_message else None
