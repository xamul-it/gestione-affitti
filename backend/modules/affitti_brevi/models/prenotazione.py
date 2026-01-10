"""
Prenotazione Model - Booking/Reservation

Central model for short-term rental bookings.
Links to CalendarioIcal (platform source) and UnitaImmobiliare (property).
Tracks check-in/out dates, pricing, guest count, and status.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum, Text, Numeric
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


class StatoPrenotazione(str, enum.Enum):
    """Booking status"""
    CONFERMATA = "CONFERMATA"
    IN_ATTESA = "IN_ATTESA"
    CANCELLATA = "CANCELLATA"
    CHECK_IN_EFFETTUATO = "CHECK_IN_EFFETTUATO"
    CHECK_OUT_EFFETTUATO = "CHECK_OUT_EFFETTUATO"
    NO_SHOW = "NO_SHOW"


class OriginePrenotazione(str, enum.Enum):
    """Booking source"""
    BOOKING_COM = "BOOKING_COM"
    AIRBNB = "AIRBNB"
    VRBO = "VRBO"
    DIRETTA = "DIRETTA"  # Direct booking (not through platform)
    ALTRO = "ALTRO"


class Prenotazione(Base):
    """
    Short-Term Rental Booking

    Represents a booking for a short-term rental property.
    Can be created manually or automatically imported via iCal sync.
    """
    __tablename__ = "prenotazioni"

    id = Column(Integer, primary_key=True, index=True)

    # Property reference
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False, index=True)

    # Calendar source (null for manual bookings)
    calendario_ical_id = Column(Integer, ForeignKey("calendari_ical.id"), nullable=True, index=True)

    # Booking identification
    codice_prenotazione = Column(String(100), nullable=False, index=True,
                                 comment="Platform booking code or manual code")
    portale_origine = Column(SQLEnum(OriginePrenotazione), nullable=False)

    # Stay dates
    data_checkin = Column(Date, nullable=False, index=True)
    data_checkout = Column(Date, nullable=False, index=True)

    # Guest information
    numero_ospiti = Column(Integer, nullable=False, default=1)

    # Pricing
    prezzo_totale = Column(Numeric(10, 2), nullable=True,
                          comment="Total booking price (may be extracted from iCal or entered manually)")
    valuta = Column(String(3), default="EUR", nullable=False)

    # Price override (manual correction)
    prezzo_manuale = Column(Numeric(10, 2), nullable=True,
                           comment="Manual price override if iCal extraction fails")

    # Status
    stato = Column(SQLEnum(StatoPrenotazione), default=StatoPrenotazione.CONFERMATA, nullable=False, index=True)

    # Notes
    note = Column(Text, nullable=True)

    # Import tracking
    importata_da_ical = Column(Integer, default=0, nullable=False,
                              comment="1 if imported from iCal, 0 if manual")
    ultima_modifica_ical = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare",
                                    foreign_keys=[unita_immobiliare_id])
    calendario_ical = relationship("CalendarioIcal", back_populates="prenotazioni")
    ospiti = relationship("OspitePrenotazione", back_populates="prenotazione", cascade="all, delete-orphan")
    comunicazioni_polizia = relationship("ComunicazionePolizia", back_populates="prenotazione", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Prenotazione(id={self.id}, codice={self.codice_prenotazione}, checkin={self.data_checkin})>"

    @property
    def notti(self):
        """Calculate number of nights"""
        if self.data_checkin and self.data_checkout:
            return (self.data_checkout - self.data_checkin).days
        return 0

    @property
    def prezzo_notte(self):
        """Calculate price per night"""
        prezzo = self.prezzo_manuale if self.prezzo_manuale else self.prezzo_totale
        if prezzo and self.notti > 0:
            return float(prezzo) / self.notti
        return None
