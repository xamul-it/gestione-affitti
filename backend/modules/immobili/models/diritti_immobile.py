"""
DirittoImmobile Model - Property rights management.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from enum import Enum


class TipoDiritto(str, Enum):
    PROPRIETARIO = "PROPRIETARIO"
    COMPROPRIETARIO = "COMPROPRIETARIO"
    USUFRUTTUARIO = "USUFRUTTUARIO"
    NUDA_PROPRIETA = "NUDA_PROPRIETA"
    ALTRO = "ALTRO"


class DirittoImmobile(Base):
    """
    Property right association.

    Links a proprietario to a property unit with a specific right type
    (ownership, co-ownership, usufruct, bare ownership, etc.)
    """
    __tablename__ = "immo_diritti_immobile"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    unita_immobiliare_id = Column(Integer, ForeignKey("immo_unita_immobiliari.id", ondelete="CASCADE"), nullable=False, index=True)
    proprietario_id = Column(Integer, ForeignKey("immo_proprietari.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_diritto = Column(SQLEnum(TipoDiritto), nullable=False)
    quota_percentuale = Column(Numeric(5, 2), nullable=True)  # es. 50.00 per 50%
    data_inizio = Column(String(10), nullable=True)  # formato YYYY-MM-DD
    data_fine = Column(String(10), nullable=True)  # formato YYYY-MM-DD
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="diritti")
    proprietario = relationship("Proprietario")
