"""
TassaSoggiornoScaglione Model - Tourist Tax Tiered Rates

Defines tiered rates for tourist tax calculation.
Each tier specifies a rate for a range of nights.

Example:
    Night 1-3:  €3.00 per person per night
    Night 4-7:  €2.00 per person per night
    Night 8+:   €1.00 per person per night
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TassaSoggiornoScaglione(Base):
    """
    Tourist Tax Tiered Rate

    Defines a rate tier for tourist tax calculation.
    Used when TassaSoggiornoConfig.tipo_calcolo = SCAGLIONI.
    """
    __tablename__ = "ab_tasse_soggiorno_scaglioni"

    id = Column(Integer, primary_key=True, index=True)

    # Link to configuration
    config_id = Column(
        Integer,
        ForeignKey("ab_tasse_soggiorno_config.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Night range (1-indexed)
    notte_da = Column(Integer, nullable=False,
                     comment="Starting night number (1 = first night)")
    notte_a = Column(Integer, nullable=True,
                    comment="Ending night number (NULL = unlimited)")

    # Rate for this tier
    importo = Column(Numeric(10, 2), nullable=False,
                    comment="Amount per person per night for this tier")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    config = relationship(
        "TassaSoggiornoConfig",
        back_populates="scaglioni"
    )

    def __repr__(self):
        notte_a_str = str(self.notte_a) if self.notte_a else "∞"
        return f"<TassaSoggiornoScaglione(config={self.config_id}, notti={self.notte_da}-{notte_a_str}, importo={self.importo})>"

    @property
    def descrizione(self) -> str:
        """Human readable description"""
        if self.notte_a:
            return f"Notti {self.notte_da}-{self.notte_a}: €{self.importo}/persona/notte"
        else:
            return f"Notti {self.notte_da}+: €{self.importo}/persona/notte"

    def contains_night(self, night_number: int) -> bool:
        """Check if a night number falls within this tier"""
        if night_number < self.notte_da:
            return False
        if self.notte_a is None:
            return True
        return night_number <= self.notte_a

    @property
    def nights_in_tier(self) -> int:
        """Calculate number of nights in this tier (inf if unbounded)"""
        if self.notte_a is None:
            return 999999  # Use large number instead of float('inf') for compatibility
        return self.notte_a - self.notte_da + 1
