"""
Ruolo Azienda Tipo Override - Tenant-specific overlay for ruoli_azienda_tipi.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base


class RuoloAziendaTipoOverride(Base):
    """
    Tenant-specific overrides for core ruoli_azienda_tipi.

    If is_deleted is True, the role type is hidden for that tenant.
    """
    __tablename__ = "ruoli_azienda_tipi_overrides"
    __table_args__ = (
        Index("ix_ruoli_azienda_tipi_overrides_tenant_ruolo", "tenant_id", "ruolo_tipo_id", unique=True),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ruolo_tipo_id = Column(Integer, ForeignKey("public.ruoli_azienda_tipi.id", ondelete="CASCADE"), nullable=False, index=True)

    nome = Column(String(100), nullable=True)
    descrizione = Column(String(500), nullable=True)
    attivo = Column(Boolean, nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return (
            f"<RuoloAziendaTipoOverride(tenant_id={self.tenant_id}, "
            f"ruolo_tipo_id={self.ruolo_tipo_id}, deleted={self.is_deleted})>"
        )
