"""
TassaSoggiornoScaglione Model - Tourist Tax Tier

Tiered rates for municipalities using SCAGLIONI calculation type.
Allows different rates for different night ranges (e.g., first 5 nights €2, next 5 nights €1).
"""
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)


class TassaSoggiornoScaglione(Base):
    """
    Tourist Tax Tier

    Defines a tax rate tier for a range of nights.
    Used when config.tipo_calcolo = SCAGLIONI.

    Example:
        - Tier 1: Nights 1-5  @ €2.50 per night
        - Tier 2: Nights 6-10 @ €1.50 per night
        - Tier 3: Nights 11+  @ €1.00 per night
    """
    __tablename__ = "tasse_soggiorno_scaglioni"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to config
    config_id = Column(Integer, ForeignKey("tasse_soggiorno_config.id"),
                      nullable=False, index=True)

    # Night range for this tier
    notte_da = Column(Integer, nullable=False,
                     comment="Prima notte di questo scaglione (1-based)")
    notte_a = Column(Integer, nullable=True,
                    comment="Ultima notte di questo scaglione (NULL = infinito)")

    # Rate for this tier
    importo = Column(Numeric(10, 2), nullable=False,
                    comment="Importo per notte per persona in questo scaglione")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    config = relationship("TassaSoggiornoConfig", back_populates="scaglioni")

    def __repr__(self):
        notte_a_str = str(self.notte_a) if self.notte_a else '∞'
        return f"<TassaSoggiornoScaglione(id={self.id}, notti={self.notte_da}-{notte_a_str}, importo={self.importo})>"

    def contains_night(self, night_number: int) -> bool:
        """Check if a night number falls within this tier"""
        if night_number < self.notte_da:
            return False
        if self.notte_a is None:
            return True
        return night_number <= self.notte_a

    @property
    def nights_in_tier(self) -> int:
        """Calculate number of nights in this tier"""
        if self.notte_a is None:
            return float('inf')  # Infinite nights
        return self.notte_a - self.notte_da + 1
