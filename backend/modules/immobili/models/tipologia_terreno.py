"""
TipologiaTerreno Model - Land type domain data.

Stores land type classifications (Agricolo, Edificabile, etc.)
in the public schema as shared domain data.
Tenant admins can customize via override tables in tenant schema.

SCHEMA: PUBLIC (domain data condiviso tra tutti i tenant)
PREFIX: immo_ (modulo immobili)
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
    Tenant-specific overrides are stored in tenant_schema.immo_tipologie_terreno_overrides.
    """
    __tablename__ = "immo_tipologie_terreno"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(10), nullable=False, unique=True, index=True)
    nome = Column(String(100), nullable=False)
    descrizione = Column(Text, nullable=True)
    ordinamento = Column(Integer, default=0)
    attiva = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TipologiaTerreno(codice='{self.codice}', nome='{self.nome}')>"
