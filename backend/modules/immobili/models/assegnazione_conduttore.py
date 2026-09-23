"""
AssegnazioneConduttore Model - links a Conduttore to a specific property
unit for a period of time.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)

Mirrors DirittoImmobile (the proprietario-side per-unit link) but for the
conduttore side. data_fine is nullable: NULL means "currently occupying".
A unit can accumulate a history of past and current occupants over time
(previous tenants, a self-occupying owner before/after a lease, etc.) by
keeping old rows with data_fine set rather than deleting them.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AssegnazioneConduttore(Base):
    """Per-unit occupancy assignment for a Conduttore."""
    __tablename__ = "immo_assegnazioni_conduttore"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conduttore_id = Column(
        Integer,
        ForeignKey("immo_conduttori.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_inizio = Column(Date, nullable=True)
    data_fine = Column(Date, nullable=True, comment="NULL = tuttora in corso")
    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="assegnazioni_conduttore")
    conduttore = relationship("Conduttore", back_populates="assegnazioni")

    def __repr__(self):
        return (
            f"<AssegnazioneConduttore unita={self.unita_immobiliare_id} "
            f"conduttore={self.conduttore_id} dal={self.data_inizio} al={self.data_fine}>"
        )
