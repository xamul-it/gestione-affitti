"""
TassaPrenotazione Model - Calculated Tourist Tax for Booking

Stores the calculated tourist tax for a specific booking.
Includes breakdown of calculation for transparency and reporting.
"""
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


class TassaPrenotazione(Base):
    """
    Calculated Tourist Tax for Booking

    Stores the tourist tax calculation result for a specific booking.
    Created automatically when booking is saved or can be recalculated manually.
    """
    __tablename__ = "tasse_prenotazioni"

    id = Column(Integer, primary_key=True, index=True)

    # References
    prenotazione_id = Column(Integer, ForeignKey("prenotazioni.id"),
                            nullable=False, index=True, unique=True)
    config_id = Column(Integer, ForeignKey("tasse_soggiorno_config.id"),
                      nullable=False, index=True)

    # Calculated amounts
    importo_totale = Column(Numeric(10, 2), nullable=False,
                          comment="Importo totale tassa di soggiorno")
    numero_ospiti_tassabili = Column(Integer, nullable=False,
                                    comment="Numero ospiti soggetti a tassa (dopo esenzioni)")
    numero_notti_tassabili = Column(Integer, nullable=False,
                                   comment="Numero notti soggette a tassa (dopo limite max)")

    # Calculation breakdown (JSON for flexibility)
    dettaglio_calcolo = Column(JSON, nullable=True,
                              comment="Breakdown del calcolo per trasparenza")

    # Example dettaglio_calcolo structure:
    # {
    #   "tipo_calcolo": "SCAGLIONI",
    #   "ospiti_totali": 3,
    #   "ospiti_esenti": 1,  # 1 bambino sotto età minima
    #   "ospiti_tassabili": 2,
    #   "notti_totali": 10,
    #   "notti_tassabili": 7,  # limite max 7 notti
    #   "scaglioni": [
    #     {"notti": "1-5", "importo_notte": 2.50, "subtotale": 25.00},
    #     {"notti": "6-7", "importo_notte": 1.50, "subtotale": 6.00}
    #   ],
    #   "importo_totale": 31.00
    # }

    # Override capability (manual adjustment)
    importo_manuale = Column(Numeric(10, 2), nullable=True,
                           comment="Override manuale dell'importo calcolato")
    note_manuale = Column(Text, nullable=True,
                         comment="Motivo dell'override manuale")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    data_ultimo_calcolo = Column(DateTime(timezone=True), server_default=func.now(),
                                 comment="Timestamp ultimo calcolo automatico")

    # Relationships
    prenotazione = relationship("Prenotazione",
                               foreign_keys=[prenotazione_id])
    config = relationship("TassaSoggiornoConfig", back_populates="tasse_prenotazioni")

    def __repr__(self):
        return f"<TassaPrenotazione(id={self.id}, prenotazione_id={self.prenotazione_id}, importo={self.importo_totale})>"

    @property
    def importo_finale(self):
        """Final tax amount (manual override or calculated)"""
        return self.importo_manuale if self.importo_manuale is not None else self.importo_totale

    @property
    def is_overridden(self):
        """Check if tax was manually overridden"""
        return self.importo_manuale is not None
