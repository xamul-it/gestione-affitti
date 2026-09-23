"""
Condominio Model - Condominium building management.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Condominio(Base):
    """
    Condominium building entity.

    Represents a multi-unit building with shared ownership areas.
    """
    __tablename__ = "immo_condomini"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=True)  # Optional - codice is the primary identifier
    codice = Column(String(50), unique=True, index=True, nullable=False)
    indirizzo = Column(String(255), nullable=False)
    citta = Column(String(100), nullable=False)
    cap = Column(String(10))
    provincia = Column(String(2))
    codice_fiscale = Column(String(16))
    partita_iva = Column(String(11))

    # Dati amministratore
    amministratore_nome = Column(String(255))
    amministratore_telefono = Column(String(50))
    amministratore_email = Column(String(255))
    amministratore_indirizzo = Column(String(255))

    # Dati bancari per pagamenti
    iban = Column(String(34))

    note = Column(Text)
    attivo = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tabelle_millesimali = relationship("TabellaMillesimale", back_populates="condominio", cascade="all, delete-orphan")
    unita = relationship("UnitaImmobiliare", back_populates="condominio")
    spese_ricorrenti = relationship(
        "SpesaRicorrenteImmobile",
        back_populates="condominio",
        foreign_keys="SpesaRicorrenteImmobile.condominio_id",
    )
