"""
Catastal changes log of a unit: one row per changed field, written by the
visura import (origine VISURA, linked to the visura document) and by manual
edits (origine MANUALE). Spec 2026-11-09 tipologie documentali, section 4.
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class VariazioneCatastale(Base):
    __tablename__ = "immo_variazioni_catastali"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    bene_id = Column(
        Integer, ForeignKey("immo_beni.id", ondelete="CASCADE"), nullable=False, index=True
    )
    documento_id = Column(Integer, nullable=True)  # core_documenti.id (core chain: no FK)
    origine = Column(String(20), nullable=False)  # VISURA | MANUALE
    campo = Column(String(50), nullable=False)
    valore_precedente = Column(Text, nullable=True)
    valore_nuovo = Column(Text, nullable=True)
    data_riferimento = Column(Date, nullable=False)
    utente_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    bene = relationship("Bene", back_populates="variazioni_catastali")
