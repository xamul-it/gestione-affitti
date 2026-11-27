"""
Raggruppamento (ramo) of beni: complex, building, farm... A pure tree: a ramo
has at most one parent, a bene is in at most one ramo (immo_beni.raggruppamento_id).
Types, cycle check, archive and delete rules: services/raggruppamenti.py.
See docs/superpowers/specs/2026-11-10-beni-catastali-design.md ("Raggruppamenti").

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Raggruppamento(Base):
    __tablename__ = "immo_raggruppamenti"
    __table_args__ = (
        CheckConstraint("padre_id IS NULL OR padre_id <> id", name="immo_raggruppamenti_non_se_stesso"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    tipo = Column(String(30), nullable=False)
    nome = Column(String(200), nullable=False)
    padre_id = Column(Integer, ForeignKey("immo_raggruppamenti.id", ondelete="RESTRICT"), nullable=True, index=True)
    descrizione = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    attivo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    padre = relationship("Raggruppamento", remote_side=[id], back_populates="figli")
    figli = relationship("Raggruppamento", back_populates="padre")
    beni = relationship("Bene", back_populates="raggruppamento")
