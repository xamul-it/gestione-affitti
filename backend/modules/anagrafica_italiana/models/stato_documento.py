"""
Stato Documento Model - Stati per documenti anagrafici.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class StatoDocumento(Base):
    """
    Stati documento per documenti anagrafici.

    Esempi:
    - VAL: Valido
    - SCA: In scadenza
    - SCO: Scaduto
    - SOS: Sostituito
    - NAP: Non applicabile
    """
    __tablename__ = "anag_stati_documento"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(20), nullable=False, unique=True, index=True)
    nome = Column(String(100), nullable=False)
    descrizione = Column(String(255), nullable=True)
    attivo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
