"""
Bene catastale - common asset of the Catasto Fabbricati (unit) and the
Catasto Terreni (land). Specialisations share the bene's id (joined-table
inheritance): see docs/superpowers/specs/2026-11-10-beni-catastali-design.md.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Bene(Base):
    """Identification and children common to every cadastral asset."""
    __tablename__ = "immo_beni"
    __table_args__ = (
        CheckConstraint("tipo_bene IN ('UNITA', 'TERRENO')", name="immo_beni_tipo_bene_check"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True)
    tipo_bene = Column(String(10), nullable=False, index=True)
    codice = Column(String(50), unique=True, index=True, nullable=False)
    comune_codice = Column(String(4), index=True)
    comune = Column(String(100))
    provincia = Column(String(2))
    indirizzo = Column(String(255))
    cap = Column(String(10))
    sezione = Column(String(20))
    foglio = Column(String(20))
    particella = Column(String(20))
    denominatore = Column(String(20))
    subalterno = Column(String(20))
    partita = Column(String(20))
    descrizione = Column(Text)
    note = Column(Text)
    attivo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __mapper_args__ = {"polymorphic_on": tipo_bene}

    # immo_diritti_immobile has no real FK constraint in some older tenant
    # schemas before 2026111201: keep the ORM cascade for rights. The others
    # have ON DELETE CASCADE in the DB, so trust it (passive_deletes).
    diritti = relationship("DirittoImmobile", back_populates="bene", cascade="all, delete-orphan")
    assegnazioni_conduttore = relationship("AssegnazioneConduttore", back_populates="bene", passive_deletes=True)
    variazioni_catastali = relationship("VariazioneCatastale", back_populates="bene", passive_deletes=True)
    spese_ricorrenti = relationship(
        "SpesaRicorrenteImmobile",
        back_populates="bene",
        foreign_keys="SpesaRicorrenteImmobile.bene_id",
        passive_deletes=True,
    )
