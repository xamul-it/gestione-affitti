"""
TassaSoggiornoConfig Model - Tourist Tax Configuration

Per-municipality configuration for tourist tax calculation.
Supports three calculation types:
- FISSO: Fixed amount per night per person
- PERCENTUALE: Percentage of nightly rate
- SCAGLIONI: Tiered rates based on number of nights
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Enum as SQLEnum, Text
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


class TipoCalcoloTassa(str, enum.Enum):
    """Tourist tax calculation type"""
    FISSO = "FISSO"                    # Fixed amount per night per person
    PERCENTUALE = "PERCENTUALE"        # Percentage of nightly rate
    SCAGLIONI = "SCAGLIONI"           # Tiered rates by night count


class TassaSoggiornoConfig(Base):
    """
    Tourist Tax Configuration by Municipality

    Stores tax calculation rules per municipality.
    Each municipality can have different rates and exemptions.
    Supports historical configurations with date ranges.
    """
    __tablename__ = "tasse_soggiorno_config"

    id = Column(Integer, primary_key=True, index=True)

    # Municipality reference (future: FK to comuni table)
    comune_id = Column(Integer, nullable=False, index=True, comment="ID del comune (ref to immobili.comuni)")
    comune_nome = Column(String(200), nullable=False, comment="Nome comune per visualizzazione")

    # Calculation type
    tipo_calcolo = Column(SQLEnum(TipoCalcoloTassa), nullable=False)

    # Fixed amount calculation (tipo_calcolo = FISSO)
    importo_fisso = Column(Numeric(10, 2), nullable=True,
                          comment="Importo fisso per notte per persona (es. €2.50)")

    # Percentage calculation (tipo_calcolo = PERCENTUALE)
    percentuale = Column(Numeric(5, 2), nullable=True,
                        comment="Percentuale del prezzo notte (es. 5.00 per 5%)")

    # Note: Tiered rates are in separate TassaSoggiornoScaglione table

    # Exemptions
    eta_minima = Column(Integer, nullable=True, default=0,
                       comment="Età minima soggetta a tassa (bambini sotto esenti)")
    eta_massima = Column(Integer, nullable=True,
                         comment="Età massima soggetta a tassa (over esenti)")
    notti_max = Column(Integer, nullable=True,
                      comment="Numero max notti tassabili (es. solo prime 7 notti)")

    # Configuration validity period
    data_inizio_validita = Column(Date, nullable=False,
                                  comment="Data inizio validità configurazione")
    data_fine_validita = Column(Date, nullable=True,
                               comment="Data fine validità (NULL = attiva)")

    # Active flag
    attiva = Column(Boolean, default=True, nullable=False)

    # Notes
    note = Column(Text, nullable=True,
                 comment="Note su regolamento comunale, esenzioni speciali, etc.")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scaglioni = relationship("TassaSoggiornoScaglione",
                            back_populates="config",
                            cascade="all, delete-orphan",
                            order_by="TassaSoggiornoScaglione.notte_da")
    tasse_prenotazioni = relationship("TassaPrenotazione",
                                     back_populates="config")

    def __repr__(self):
        return f"<TassaSoggiornoConfig(id={self.id}, comune={self.comune_nome}, tipo={self.tipo_calcolo.value})>"

    @property
    def is_active_for_date(self, date):
        """Check if config is active for a given date"""
        if not self.attiva:
            return False
        if date < self.data_inizio_validita:
            return False
        if self.data_fine_validita and date > self.data_fine_validita:
            return False
        return True
