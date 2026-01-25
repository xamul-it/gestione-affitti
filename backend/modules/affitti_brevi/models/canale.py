"""
Canale Model - Booking Platform Channel Configuration

Defines supported booking platforms (Airbnb, Booking.com, VRBO, Direct, etc.)
with their visual representation for the unified calendar.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Canale(Base):
    """
    Booking Platform Channel

    Configures supported booking platforms with their visual identifiers
    for the unified calendar view.

    Default channels (seeded):
    - AIRBNB: Red (A)
    - BOOKING_COM: Blue (B)
    - VRBO: Orange (V)
    - DIRETTO: Green (D)
    """
    __tablename__ = "ab_canali"

    id = Column(Integer, primary_key=True, index=True)

    # Channel identification
    codice = Column(String(50), unique=True, nullable=False, index=True,
                   comment="Unique channel code (e.g., AIRBNB, BOOKING_COM)")
    nome = Column(String(100), nullable=False,
                 comment="Display name (e.g., 'Airbnb', 'Booking.com')")

    # Visual representation for calendar
    colore = Column(String(7), nullable=False, default="#808080",
                   comment="Hex color for calendar display (e.g., #FF5A5F for Airbnb)")
    simbolo = Column(String(5), nullable=False, default="?",
                    comment="Short symbol for calendar cell (e.g., A, B, V, D)")
    icona = Column(String(50), nullable=True,
                  comment="Icon name for UI (e.g., 'airbnb', 'hotel')")

    # iCal configuration
    supporta_ical = Column(Boolean, default=True, nullable=False,
                          comment="Whether this channel supports iCal import")
    url_pattern_ical = Column(String(500), nullable=True,
                             comment="URL pattern for iCal feeds (platform-specific)")

    # Status
    attivo = Column(Boolean, default=True, nullable=False,
                   comment="Whether channel is available for use")

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Canale(id={self.id}, codice={self.codice}, nome={self.nome})>"


# Default channels to seed
DEFAULT_CANALI = [
    {
        "codice": "AIRBNB",
        "nome": "Airbnb",
        "colore": "#FF5A5F",  # Airbnb red
        "simbolo": "A",
        "icona": "airbnb",
        "supporta_ical": True,
    },
    {
        "codice": "BOOKING_COM",
        "nome": "Booking.com",
        "colore": "#003580",  # Booking blue
        "simbolo": "B",
        "icona": "hotel",
        "supporta_ical": True,
    },
    {
        "codice": "VRBO",
        "nome": "VRBO / HomeAway",
        "colore": "#FF8C00",  # Orange
        "simbolo": "V",
        "icona": "home",
        "supporta_ical": True,
    },
    {
        "codice": "DIRETTO",
        "nome": "Prenotazione Diretta",
        "colore": "#28A745",  # Green
        "simbolo": "D",
        "icona": "phone",
        "supporta_ical": False,
    },
    {
        "codice": "ALTRO",
        "nome": "Altro Canale",
        "colore": "#6C757D",  # Gray
        "simbolo": "X",
        "icona": "globe",
        "supporta_ical": True,
    },
]
