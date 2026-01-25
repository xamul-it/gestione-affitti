"""
Tipo Immobile to Categoria Catastale Mapping Model.

Maps free-text property types (e.g., "appartamento", "box") to official
cadastral categories. Supports both system-defined and user-defined mappings.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TipoImmobileCategoriaMap(Base):
    """
    Mapping between property type text and cadastral category.

    This table enables automatic categoria inference during import:
    - System learns from user input over time
    - Supports confidence scoring for ML enhancement
    - Tracks user-defined vs auto-inferred mappings

    Example mappings:
    - "appartamento" → A/2 (confidence: 1.0, user_defined: False)
    - "box" → C/6 (confidence: 1.0, user_defined: False)
    - "casa signorile" → A/1 (confidence: 0.8, user_defined: True)
    """
    __tablename__ = "immo_tipo_immobile_categoria_map"

    id = Column(Integer, primary_key=True, index=True)
    tipo_immobile = Column(String(100), nullable=False, index=True)  # Normalized lowercase
    # FK to public.immo_categorie_catastali
    categoria_catastale_id = Column(
        Integer,
        ForeignKey("public.immo_categorie_catastali.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    confidence_score = Column(Numeric(3, 2), default=1.0)  # 0.0 to 1.0 for future ML
    is_user_defined = Column(Boolean, default=False)  # Manual mapping vs auto-inferred
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)  # Future: user ID tracking

    # Relationship
    categoria_catastale = relationship("CategoriaCatastale")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tipo_immobile", "categoria_catastale_id", name="immo_uq_tipo_categoria"),
        {"extend_existing": True}
    )

    def __repr__(self):
        return f"<TipoImmobileCategoriaMap(tipo='{self.tipo_immobile}', categoria_id={self.categoria_catastale_id})>"
