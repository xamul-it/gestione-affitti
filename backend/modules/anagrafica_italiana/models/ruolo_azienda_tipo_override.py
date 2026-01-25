"""
Ruolo Azienda Tipo Override - Tenant-specific overlay for anag_ruoli_azienda_tipi.

This table lives in TENANT SCHEMA and stores per-tenant changes
to the public.anag_ruoli_azienda_tipi domain data.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class RuoloAziendaTipoOverride(Base):
    """
    Tenant-specific overrides for core anag_ruoli_azienda_tipi.

    Stored in tenant schema; references public.anag_ruoli_azienda_tipi.
    If is_deleted is True, the role type is hidden for that tenant.
    """
    __tablename__ = "anag_ruoli_azienda_tipi_overrides"

    __table_args__ = (
        Index("ix_anag_ruoli_azienda_tipi_overrides_ruolo", "ruolo_tipo_id", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True)
    ruolo_tipo_id = Column(
        Integer,
        ForeignKey("public.anag_ruoli_azienda_tipi.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    nome = Column(String(100), nullable=True)
    descrizione = Column(String(500), nullable=True)
    attivo = Column(Boolean, nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<RuoloAziendaTipoOverride(ruolo_tipo_id={self.ruolo_tipo_id}, deleted={self.is_deleted})>"
