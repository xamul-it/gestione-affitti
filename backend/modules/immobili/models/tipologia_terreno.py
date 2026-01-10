"""
TipologiaTerreno Model - Land type domain data.

Stores land type classifications (Agricolo, Edificabile, etc.)
in the public schema as shared domain data.
Tenant admins can extend with tenant-specific types.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TipologiaTerreno(Base):
    """
    Land type classification (domain data in public schema).

    Standard types from functional analysis:
    - AGR: Agricolo (agricultural, cultivable land)
    - EDI: Edificabile (buildable land)
    - BOS: Bosco/Forestale (forest, woodland)
    - IND: Industriale (industrial/artisanal use)
    - ALT: Altro (other types)

    This table is in the public schema and shared across all tenants.
    Platform admin manages the base types.
    Tenant-specific types can be added via override mechanism.
    """
    __tablename__ = "tipologie_terreno"
    __table_args__ = {"schema": "public"}  # Explicit public schema for domain data

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(10), nullable=False, unique=True, index=True)  # 'AGR', 'EDI', etc.
    nome = Column(String(100), nullable=False)  # Full name
    descrizione = Column(Text, nullable=True)  # Detailed description
    ordinamento = Column(Integer, default=0)  # For sorting in UI
    attiva = Column(Boolean, default=True, index=True)  # Soft delete flag

    # Tenant customization (null = platform default, value = tenant-specific)
    tenant_id = Column(Integer, nullable=True, index=True)  # null = shared, value = tenant-specific

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        tenant_info = f", tenant={self.tenant_id}" if self.tenant_id else ""
        return f"<TipologiaTerreno(codice='{self.codice}', nome='{self.nome}'{tenant_info})>"
