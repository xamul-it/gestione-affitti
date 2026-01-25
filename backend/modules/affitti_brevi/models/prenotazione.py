"""
Prenotazione Model - Booking from Channel

Represents a booking received from a channel (Airbnb, Booking.com, Direct, etc.).
This is the "raw" booking data as received from the platform.

The operational "Soggiorno" is created from one or more Prenotazioni.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class StatoPrenotazione(str, enum.Enum):
    """Booking status from platform perspective"""
    CONFERMATA = "CONFERMATA"           # Confirmed booking
    IN_ATTESA = "IN_ATTESA"             # Pending confirmation
    CANCELLATA = "CANCELLATA"           # Cancelled
    MODIFICATA = "MODIFICATA"           # Modified (dates/guests changed)
    RIFIUTATA = "RIFIUTATA"             # Rejected by host


class Prenotazione(Base):
    """
    Booking from Channel

    Represents a booking as received from a booking platform.
    Contains the original booking data (dates, code, price).

    One Prenotazione creates one Soggiorno (operational stay).
    In case of conflicts (double booking), only one Soggiorno is marked as valid.
    """
    __tablename__ = "ab_prenotazioni"

    id = Column(Integer, primary_key=True, index=True)

    # Property and channel reference
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    calendario_canale_id = Column(
        Integer,
        ForeignKey("ab_calendari_canali.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Source calendar/channel (null for manual bookings)"
    )

    # Booking identification from platform
    codice_prenotazione = Column(String(100), nullable=False, index=True,
                                comment="Platform booking code or manual reference")
    codice_conferma = Column(String(100), nullable=True,
                            comment="Confirmation code (if different from booking code)")

    # Stay dates
    data_checkin = Column(Date, nullable=False, index=True)
    data_checkout = Column(Date, nullable=False, index=True)

    # Guest info from platform (preliminary, before Soggiorno details)
    numero_ospiti = Column(Integer, nullable=False, default=1)
    nome_ospite_principale = Column(String(200), nullable=True,
                                   comment="Primary guest name from platform")
    email_ospite = Column(String(200), nullable=True)
    telefono_ospite = Column(String(50), nullable=True)

    # Pricing from platform
    prezzo_totale = Column(Numeric(10, 2), nullable=True,
                          comment="Total booking price (may be extracted from iCal)")
    prezzo_notte_medio = Column(Numeric(10, 2), nullable=True,
                               comment="Average nightly rate")
    valuta = Column(String(3), default="EUR", nullable=False)

    # Platform fees
    commissione_canale = Column(Numeric(10, 2), nullable=True,
                               comment="Channel commission/fee")
    incasso_netto = Column(Numeric(10, 2), nullable=True,
                          comment="Net income after commission")

    # Booking status
    stato = Column(String(30), default=StatoPrenotazione.CONFERMATA.value,
                  nullable=False, index=True)

    # Import tracking
    importata_da_ical = Column(Integer, default=0, nullable=False,
                              comment="1 if imported from iCal, 0 if manual")
    uid_ical = Column(String(200), nullable=True,
                     comment="iCal UID for deduplication")
    ultima_modifica_ical = Column(DateTime(timezone=True), nullable=True)

    # Raw data storage
    dati_originali = Column(Text, nullable=True,
                           comment="Original iCal/API data (JSON) for debugging")

    # Notes
    note = Column(Text, nullable=True)
    note_interne = Column(Text, nullable=True,
                         comment="Internal notes (not visible to guest)")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship(
        "UnitaImmobiliare",
        foreign_keys=[unita_immobiliare_id]
    )
    calendario_canale = relationship(
        "CalendarioCanale",
        foreign_keys=[calendario_canale_id],
        backref="prenotazioni"
    )
    soggiorno = relationship(
        "Soggiorno",
        back_populates="prenotazione",
        uselist=False
    )

    # Indexes for common queries
    __table_args__ = (
        Index('ix_ab_prenotazioni_immobile_date',
              'unita_immobiliare_id', 'data_checkin', 'data_checkout'),
        Index('ix_ab_prenotazioni_stato_date',
              'stato', 'data_checkin'),
    )

    def __repr__(self):
        return f"<Prenotazione(id={self.id}, codice={self.codice_prenotazione}, checkin={self.data_checkin})>"

    @property
    def notti(self) -> int:
        """Calculate number of nights"""
        if self.data_checkin and self.data_checkout:
            return (self.data_checkout - self.data_checkin).days
        return 0

    @property
    def is_attiva(self) -> bool:
        """Check if booking is active (not cancelled/rejected)"""
        return self.stato not in [
            StatoPrenotazione.CANCELLATA.value,
            StatoPrenotazione.RIFIUTATA.value
        ]

    @property
    def canale_codice(self) -> str:
        """Get channel code (shortcut)"""
        if self.calendario_canale and self.calendario_canale.canale:
            return self.calendario_canale.canale.codice
        return "SCONOSCIUTO"
