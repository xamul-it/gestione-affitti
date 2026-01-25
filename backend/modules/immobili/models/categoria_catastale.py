"""
Categoria Catastale Model - Italian cadastral property categories.

Stores the official Italian cadastral categories (A/1, A/2, C/6, etc.)
used to classify properties for tax and regulatory purposes.

SCHEMA: PUBLIC (domain data condiviso tra tutti i tenant)
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class CategoriaCatastale(Base):
    """
    Italian cadastral property category.

    Categories are official classifications from the Italian cadastral system:
    - Group A: Residential properties (A/1 to A/11)
    - Group B: Community buildings (schools, hospitals, etc.)
    - Group C: Commercial/Accessory properties (C/1 to C/7)
    - Group D: Industrial properties
    - Group E: Special purpose properties
    - Group F: Special urban areas

    Examples:
    - A/2: Standard residential apartment
    - A/8: Villa
    - C/6: Garage/Box
    - C/1: Commercial shop
    """
    __tablename__ = "immo_categorie_catastali"
    __table_args__ = (
        CheckConstraint("gruppo IN ('A', 'B', 'C', 'D', 'E', 'F')", name="immo_check_gruppo_valid"),
        {"schema": "public", "extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(10), nullable=False, unique=True, index=True)  # 'A/2', 'C/6', etc.
    nome = Column(String(200), nullable=False)  # Full descriptive name
    gruppo = Column(String(1), nullable=False, index=True)  # 'A', 'B', 'C', 'D', 'E', 'F'
    descrizione = Column(Text, nullable=True)  # Additional description
    ordinamento = Column(Integer, default=0)  # For sorting in UI
    attiva = Column(Boolean, default=True, index=True)  # Soft delete flag
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CategoriaCatastale(codice='{self.codice}', nome='{self.nome}')>"
