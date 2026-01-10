"""
Comune Italia Override - Tenant-specific overlay for comuni_italia.

Stores per-tenant changes and soft deletions without touching core data.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class ComuneItaliaOverride(Base):
    """
    Tenant-specific overrides for core comuni_italia.

    If is_deleted is True, the comune is hidden for that tenant.
    """
    __tablename__ = "comuni_italia_overrides"
    __table_args__ = (
        Index("ix_comuni_italia_overrides_tenant_comune", "tenant_id", "comune_id", unique=True),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    comune_id = Column(Integer, ForeignKey("public.comuni_italia.id", ondelete="CASCADE"), nullable=False, index=True)

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

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ComuneItaliaOverride(tenant_id={self.tenant_id}, comune_id={self.comune_id}, deleted={self.is_deleted})>"
