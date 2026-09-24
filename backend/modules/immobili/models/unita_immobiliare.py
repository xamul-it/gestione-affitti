"""
Unità Immobiliare Model - Real estate property unit.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UnitaImmobiliare(Base):
    """
    Real estate property unit.

    Represents a single property unit (apartment, house, office, garage, etc.)
    that can be part of a condominium or stand-alone.
    """
    __tablename__ = "immo_unita_immobiliari"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(50), unique=True, index=True, nullable=False)
    tipo = Column(String(50), nullable=False)  # Appartamento, Casa, Ufficio, Box, Negozio, etc.
    condominio_id = Column(Integer, ForeignKey("immo_condomini.id"), nullable=True)  # Opzionale per unità non condominiali
    indirizzo = Column(String(255), nullable=False)
    citta = Column(String(100), nullable=False)
    cap = Column(String(10))
    provincia = Column(String(2))
    superficie_mq = Column(Float)
    locali = Column(Integer)
    piano = Column(String(20))
    classe_energetica = Column(String(10))
    rendita_catastale = Column(Float)
    foglio = Column(String(20))
    particella = Column(String(20))
    subalterno = Column(String(20))
    descrizione = Column(Text)
    note = Column(Text)

    # FK to public.immo_categorie_catastali (domain data)
    categoria_catastale_id = Column(
        Integer,
        ForeignKey("public.immo_categorie_catastali.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    codice_auto_generated = Column(Boolean, default=False)  # Track if codice was auto-generated
    indirizzo_parsed_warnings = Column(ARRAY(Text), nullable=True)  # Address parsing warnings

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    condominio = relationship("Condominio", back_populates="unita")
    contratti = relationship("Contratto", back_populates="unita_immobiliare")
    spese = relationship("Spesa", back_populates="unita_immobiliare")
    # immo_certificati_energetici and immo_diritti_immobile have no real FK
    # constraint in the DB (their ondelete="CASCADE" above is decorative),
    # so cascade must be ORM-managed here rather than relying on passive_deletes.
    certificati_energetici = relationship("CertificatoEnergetico", back_populates="unita_immobiliare", cascade="all, delete-orphan")
    diritti = relationship("DirittoImmobile", back_populates="unita_immobiliare", cascade="all, delete-orphan")
    # immo_assegnazioni_conduttore and immo_spese_ricorrenti DO have a real
    # ON DELETE CASCADE constraint, so trust the DB instead of doing N extra
    # DELETEs — without passive_deletes, SQLAlchemy still tries to null out
    # these non-nullable child FKs in Python and crashes.
    assegnazioni_conduttore = relationship("AssegnazioneConduttore", back_populates="unita_immobiliare", passive_deletes=True)
    spese_ricorrenti = relationship(
        "SpesaRicorrenteImmobile",
        back_populates="unita_immobiliare",
        foreign_keys="SpesaRicorrenteImmobile.unita_immobiliare_id",
        passive_deletes=True,
    )
    millesimi = relationship("MillesimiUnita", back_populates="unita_immobiliare", cascade="all, delete-orphan")
    categoria_catastale = relationship("CategoriaCatastale", foreign_keys=[categoria_catastale_id])
