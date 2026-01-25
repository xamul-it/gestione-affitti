"""
TabellaMillesimale Model - Millesimal table for condominium expense distribution.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TipoRipartizione(str, enum.Enum):
    """Tipologie di ripartizione secondo codice civile italiano"""
    MILLESIMI = "millesimi"  # Ripartizione pura a millesimi (art. 1123 c.c.)
    MILLESIMI_CONSUMO = "millesimi_consumo"  # Millesimi + consumo (es. riscaldamento 30%+70%)
    OCCUPANTI = "occupanti"  # Per numero occupanti (es. acqua)
    MILLESIMI_PIANO = "millesimi_piano"  # Millesimi con coefficiente piano (ascensore art. 1124)
    PERSONALIZZATA = "personalizzata"  # Quote personalizzate/fisse


class TabellaMillesimale(Base):
    """
    Millesimal table for condominium expense distribution.

    Each condominium can have multiple tables for different expense types
    (general expenses, elevator, heating, etc.)
    """
    __tablename__ = "immo_tabelle_millesimali"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("immo_condomini.id"), nullable=False)
    nome = Column(String(255), nullable=False)  # es. "Spese Generali", "Ascensore", "Riscaldamento"
    codice = Column(String(50), nullable=False, index=True)  # codice identificativo
    tipo_ripartizione = Column(Enum(TipoRipartizione), nullable=False, default=TipoRipartizione.MILLESIMI)

    # Parametri per ripartizione mista (es. riscaldamento)
    percentuale_millesimi = Column(Float, default=100.0)  # % ripartita a millesimi
    percentuale_consumo = Column(Float, default=0.0)  # % ripartita a consumo
    percentuale_occupanti = Column(Float, default=0.0)  # % ripartita per occupanti

    descrizione = Column(Text)
    note = Column(Text)
    attiva = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    condominio = relationship("Condominio", back_populates="tabelle_millesimali")
    millesimi_unita = relationship("MillesimiUnita", back_populates="tabella_millesimale", cascade="all, delete-orphan")
    spese = relationship("Spesa", back_populates="tabella_millesimale")
