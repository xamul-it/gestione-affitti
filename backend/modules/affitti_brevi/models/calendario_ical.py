"""
CalendarioIcal Model - iCal Calendar Configuration

Links a property (UnitaImmobiliare) to a booking platform's iCal feed URL.
Each property can have multiple calendar configurations (one per platform).
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


class PortaleBooking(str, enum.Enum):
    """Supported booking platforms"""
    BOOKING_COM = "BOOKING_COM"
    AIRBNB = "AIRBNB"
    VRBO = "VRBO"
    ALTRO = "ALTRO"


class StatoSincronizzazione(str, enum.Enum):
    """Synchronization status"""
    MAI_SINCRONIZZATO = "MAI_SINCRONIZZATO"
    IN_CORSO = "IN_CORSO"
    SUCCESSO = "SUCCESSO"
    ERRORE = "ERRORE"


class CalendarioIcal(Base):
    """
    iCal Calendar Configuration

    Links a property to a booking platform's iCal feed URL for automatic synchronization.
    Tracks sync status and stores external dashboard link.
    """
    __tablename__ = "calendari_ical"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to property
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False, index=True)

    # Platform configuration
    portale = Column(SQLEnum(PortaleBooking), nullable=False)
    url_ical = Column(String(500), nullable=False)
    url_dashboard_portale = Column(String(500), nullable=True, comment="External link to platform dashboard")

    # Sync status tracking
    stato_sincronizzazione = Column(SQLEnum(StatoSincronizzazione),
                                   default=StatoSincronizzazione.MAI_SINCRONIZZATO,
                                   nullable=False)
    ultima_sincronizzazione = Column(DateTime(timezone=True), nullable=True)
    errore_sincronizzazione = Column(Text, nullable=True)

    # Enable/disable sync
    attivo = Column(Boolean, default=True, nullable=False)

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare",
                                    foreign_keys=[unita_immobiliare_id])
    prenotazioni = relationship("Prenotazione", back_populates="calendario_ical")

    def __repr__(self):
        return f"<CalendarioIcal(id={self.id}, portale={self.portale.value}, immobile_id={self.unita_immobiliare_id})>"
