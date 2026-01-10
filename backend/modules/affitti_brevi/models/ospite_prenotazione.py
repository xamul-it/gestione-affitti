"""
OspitePrenotazione Model - Guest linked to Booking

Links a guest (SoggettoAnagrafico) to a booking (Prenotazione).
A booking can have multiple guests (family, group).
Tracks whether the guest is the primary contact and document upload status.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


class OspitePrenotazione(Base):
    """
    Guest linked to Booking

    Associates a guest (from anagrafica_italiana) with a booking.
    Multiple guests can be linked to a single booking.
    Tracks document status for police communication requirements.
    """
    __tablename__ = "ospiti_prenotazioni"

    id = Column(Integer, primary_key=True, index=True)

    # References
    prenotazione_id = Column(Integer, ForeignKey("prenotazioni.id"), nullable=False, index=True)
    soggetto_anagrafico_id = Column(Integer, ForeignKey("soggetti_anagrafici.id"), nullable=False, index=True)

    # Guest role
    ospite_principale = Column(Boolean, default=False, nullable=False,
                              comment="True if this is the primary contact for the booking")

    # Document tracking for police communication
    documento_identita_caricato = Column(Boolean, default=False, nullable=False)
    tipo_documento = Column(String(50), nullable=True,
                          comment="CARTA_IDENTITA, PASSAPORTO, PATENTE, etc.")
    numero_documento = Column(String(50), nullable=True)
    data_scadenza_documento = Column(Date, nullable=True)

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    prenotazione = relationship("Prenotazione", back_populates="ospiti")
    soggetto_anagrafico = relationship("SoggettoAnagrafico",
                                      foreign_keys=[soggetto_anagrafico_id])

    def __repr__(self):
        return f"<OspitePrenotazione(id={self.id}, prenotazione_id={self.prenotazione_id}, soggetto_id={self.soggetto_anagrafico_id})>"
