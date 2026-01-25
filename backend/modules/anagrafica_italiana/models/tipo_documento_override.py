"""
Tipo Documento Override - Tenant-specific overlay for anag_tipi_documento.

Stores per-tenant overrides for document types seeded in public.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class TipoDocumentoOverride(Base):
    """
    Tenant-specific overrides for core anag_tipi_documento.

    Stored in tenant schema; references public.anag_tipi_documento.
    """
    __tablename__ = "anag_tipi_documento_overrides"

    __table_args__ = (
        Index("ix_anag_tipi_documento_overrides_tipo", "tipo_documento_id", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True)
    tipo_documento_id = Column(
        Integer,
        ForeignKey("public.anag_tipi_documento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    codice = Column(String(50), nullable=True)
    nome = Column(String(100), nullable=True)
    descrizione = Column(String(255), nullable=True)
    categoria = Column(String(50), nullable=True)
    richiede_scadenza = Column(Boolean, nullable=True)
    attivo = Column(Boolean, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
