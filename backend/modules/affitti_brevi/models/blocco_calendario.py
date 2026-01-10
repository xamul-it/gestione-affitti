"""
BloccoCalendario Model - Manual Calendar Block

Allows manual blocking of dates for a property on a specific platform.
Used for maintenance periods, personal use, or temporary closure.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
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


class TipoBlocco(str, enum.Enum):
    """Type of calendar block"""
    MANUTENZIONE = "MANUTENZIONE"  # Maintenance
    USO_PERSONALE = "USO_PERSONALE"  # Personal use
    CHIUSURA_TEMPORANEA = "CHIUSURA_TEMPORANEA"  # Temporary closure
    ALTRO = "ALTRO"  # Other


class PortaleBlocco(str, enum.Enum):
    """Platform to block (matches PortaleBooking from calendario_ical.py)"""
    BOOKING_COM = "BOOKING_COM"
    AIRBNB = "AIRBNB"
    VRBO = "VRBO"
    TUTTI = "TUTTI"  # Block on all platforms
    ALTRO = "ALTRO"


class BloccoCalendario(Base):
    """
    Manual Calendar Block

    Blocks dates for a property on a specific platform.
    Prevents bookings during maintenance, personal use, or closure periods.
    Visible in the multi-platform calendar view with strikethrough symbol.
    """
    __tablename__ = "blocchi_calendario"

    id = Column(Integer, primary_key=True, index=True)

    # Property reference
    immobile_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False, index=True)

    # Platform scope
    portale = Column(SQLEnum(PortaleBlocco), nullable=False,
                    comment="Which platform to block (or TUTTI for all platforms)")

    # Date range
    data_inizio = Column(Date, nullable=False, index=True)
    data_fine = Column(Date, nullable=False, index=True)

    # Block type and reason
    tipo_blocco = Column(SQLEnum(TipoBlocco), nullable=False)
    motivo = Column(Text, nullable=True, comment="Reason for blocking")

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare",
                                    foreign_keys=[immobile_id])

    def __repr__(self):
        return f"<BloccoCalendario(id={self.id}, immobile_id={self.immobile_id}, tipo={self.tipo_blocco.value}, {self.data_inizio} - {self.data_fine})>"

    @property
    def giorni_bloccati(self):
        """Calculate number of days blocked"""
        if self.data_inizio and self.data_fine:
            return (self.data_fine - self.data_inizio).days + 1
        return 0
