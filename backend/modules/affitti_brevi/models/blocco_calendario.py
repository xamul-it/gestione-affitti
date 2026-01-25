"""
BloccoCalendario Model - Manual Calendar Block

Allows manual blocking of dates for a property on specific channels.
Used for maintenance periods, personal use, or temporary closure.
NOTE: According to analysis, internal technical closures are NOT in scope.
This model is for visibility purposes only (shows as "X" in calendar).
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TipoBlocco(str, enum.Enum):
    """Type of calendar block"""
    USO_PERSONALE = "USO_PERSONALE"              # Personal use by owner
    CHIUSURA_CANALE = "CHIUSURA_CANALE"          # Channel reported closure
    ALTRO = "ALTRO"                              # Other


class BloccoCalendario(Base):
    """
    Manual Calendar Block

    Blocks dates for a property, visible in the unified calendar view.
    Represented as "X" in the calendar (Chiuso/Non disponibile).

    Can apply to:
    - All channels (canale_id = null)
    - A specific channel (canale_id set)
    """
    __tablename__ = "ab_blocchi_calendario"

    id = Column(Integer, primary_key=True, index=True)

    # Property reference
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Channel scope (null = all channels)
    canale_id = Column(
        Integer,
        ForeignKey("ab_canali.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Specific channel (null = all channels)"
    )

    # Date range
    data_inizio = Column(Date, nullable=False, index=True)
    data_fine = Column(Date, nullable=False, index=True)

    # Block type and reason
    tipo = Column(String(30), default=TipoBlocco.ALTRO.value, nullable=False)
    motivo = Column(Text, nullable=True, comment="Reason for blocking")

    # Source tracking
    da_canale = Column(Boolean, default=False, nullable=False,
                      comment="True if imported from channel, False if manual")
    codice_blocco_esterno = Column(String(100), nullable=True,
                                  comment="External block ID from channel")

    # Status
    attivo = Column(Boolean, default=True, nullable=False)

    # Notes
    note = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship(
        "UnitaImmobiliare",
        foreign_keys=[unita_immobiliare_id]
    )
    canale = relationship(
        "Canale",
        foreign_keys=[canale_id]
    )

    # Indexes
    __table_args__ = (
        Index('ix_ab_blocchi_immobile_date',
              'unita_immobiliare_id', 'data_inizio', 'data_fine'),
    )

    def __repr__(self):
        canale_str = f"canale={self.canale_id}" if self.canale_id else "tutti"
        return f"<BloccoCalendario(id={self.id}, immobile={self.unita_immobiliare_id}, {canale_str}, {self.data_inizio}-{self.data_fine})>"

    @property
    def giorni_bloccati(self) -> int:
        """Calculate number of days blocked"""
        if self.data_inizio and self.data_fine:
            return (self.data_fine - self.data_inizio).days + 1
        return 0

    def copre_data(self, data: 'Date') -> bool:
        """Check if block covers a specific date"""
        return self.data_inizio <= data <= self.data_fine

    def copre_canale(self, canale_id: int) -> bool:
        """Check if block applies to a specific channel"""
        if self.canale_id is None:
            return True  # Applies to all channels
        return self.canale_id == canale_id
