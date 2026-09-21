"""
Stato Documento Override - Tenant-specific overlay for core_stati_documento.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class StatoDocumentoOverride(Base):
    """
    Tenant-specific overrides for core_stati_documento.
    """
    __tablename__ = "core_stati_documento_overrides"

    __table_args__ = (
        Index("ix_core_stati_documento_overrides_stato", "stato_documento_id", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True)
    stato_documento_id = Column(
        Integer,
        ForeignKey("public.core_stati_documento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    codice = Column(String(20), nullable=True)
    nome = Column(String(100), nullable=True)
    descrizione = Column(String(255), nullable=True)
    attivo = Column(Boolean, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
