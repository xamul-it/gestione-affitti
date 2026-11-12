"""
Unità Immobiliare Model - Real estate property unit.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, ARRAY
from sqlalchemy.orm import relationship, synonym
from sqlalchemy.sql import func
from .bene import Bene


class UnitaImmobiliare(Bene):
    """
    Real estate property unit.

    Represents a single property unit (apartment, house, office, garage, etc.)
    that can be part of a condominium or stand-alone. Its id is the id of
    its Bene (immo_beni), which holds code, address and cadastral
    identification; `citta` is the bene's `comune`.
    """
    __tablename__ = "immo_unita_immobiliari"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, ForeignKey("immo_beni.id", ondelete="CASCADE"), primary_key=True)
    tipo = Column(String(50), nullable=False)  # Appartamento, Casa, Ufficio, Box, Negozio, etc.
    condominio_id = Column(Integer, ForeignKey("immo_condomini.id"), nullable=True)  # Opzionale per unità non condominiali
    superficie_mq = Column(Float)
    locali = Column(Integer)
    piano = Column(String(20))
    classe_energetica = Column(String(10))
    rendita_catastale = Column(Float)

    # FK to public.immo_categorie_catastali (domain data)
    categoria_catastale_id = Column(
        Integer,
        ForeignKey("public.immo_categorie_catastali.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    codice_auto_generated = Column(Boolean, default=False)  # Track if codice was auto-generated
    indirizzo_parsed_warnings = Column(ARRAY(Text), nullable=True)  # Address parsing warnings

    # created_at / updated_at live on the Bene.
    __mapper_args__ = {"polymorphic_identity": "UNITA"}

    citta = synonym("comune")

    # Relationships
    condominio = relationship("Condominio", back_populates="unita")
    contratti = relationship("Contratto", back_populates="unita_immobiliare")
    spese = relationship("Spesa", back_populates="unita_immobiliare")
    # immo_certificati_energetici has no real FK constraint in the DB, so
    # cascade must be ORM-managed here. Rights, tenant assignments, cadastral
    # changes and recurring costs belong to the Bene (see bene.py).
    certificati_energetici = relationship("CertificatoEnergetico", back_populates="unita_immobiliare", cascade="all, delete-orphan")
    millesimi = relationship("MillesimiUnita", back_populates="unita_immobiliare", cascade="all, delete-orphan")
    categoria_catastale = relationship("CategoriaCatastale", foreign_keys=[categoria_catastale_id])
