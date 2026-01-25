"""
Comune Italia Override - Tenant-specific overlay for anag_comuni_italia.

This table lives in TENANT SCHEMA and stores per-tenant changes
to the public.anag_comuni_italia domain data.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class ComuneItaliaOverride(Base):
    """
    Tenant-specific overrides for core anag_comuni_italia.

    Stored in tenant schema; references public.anag_comuni_italia.
    If is_deleted is True, the comune is hidden for that tenant.
    """
    __tablename__ = "anag_comuni_italia_overrides"

    __table_args__ = (
        Index("ix_anag_comuni_italia_overrides_comune", "comune_id", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True)
    comune_id = Column(
        Integer,
        ForeignKey("public.anag_comuni_italia.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Optional override fields (only those set will replace core values)
    nome = Column(String(100), nullable=True)
    nome_normalized = Column(String(100), nullable=True)
    codice_istat = Column(String(10), nullable=True)
    codice_catastale = Column(String(10), nullable=True)
    cap = Column(String(10), nullable=True)
    provincia_sigla = Column(String(2), nullable=True)
    provincia_nome = Column(String(100), nullable=True)
    regione = Column(String(100), nullable=True)
    latitudine = Column(Numeric(10, 7), nullable=True)
    longitudine = Column(Numeric(10, 7), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ComuneItaliaOverride(comune_id={self.comune_id}, deleted={self.is_deleted})>"
