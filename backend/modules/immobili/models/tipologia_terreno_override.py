"""
Tipologia Terreno Override - Tenant-specific overlay for immo_tipologie_terreno.

This table lives in TENANT SCHEMA and stores per-tenant changes
to the public.immo_tipologie_terreno domain data.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class TipologiaTerrenoOverride(Base):
    """
    Tenant-specific overrides for core tipologie_terreno.

    Stored in tenant schema; references public.immo_tipologie_terreno.
    If is_deleted is True, the tipologia is hidden for that tenant.
    """
    __tablename__ = "immo_tipologie_terreno_overrides"

    __table_args__ = (
        Index("ix_immo_tipologie_terreno_overrides_tipologia", "tipologia_id", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True)
    tipologia_id = Column(
        Integer,
        ForeignKey("public.immo_tipologie_terreno.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    codice = Column(String(20), nullable=True)
    nome = Column(String(100), nullable=True)
    descrizione = Column(Text, nullable=True)
    attivo = Column(Boolean, nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TipologiaTerrenoOverride(tipologia_id={self.tipologia_id}, deleted={self.is_deleted})>"
