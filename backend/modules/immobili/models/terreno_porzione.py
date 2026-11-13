"""
Porzione di un terreno (Catasto Terreni): quality, class, surface in m²,
dominical and agrarian income, deductions. A parcel has at least one.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class TerrenoPorzione(Base):
    __tablename__ = "immo_terreni_porzioni"
    __table_args__ = (
        CheckConstraint("superficie_mq >= 0", name="immo_terreni_porzioni_superficie_mq_check"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True)
    terreno_id = Column(Integer, ForeignKey("immo_terreni.id", ondelete="CASCADE"), nullable=False, index=True)
    porzione = Column(String(5), nullable=True)  # es. AA, AB
    qualita = Column(String(100), nullable=False)
    classe = Column(String(10), nullable=True)
    superficie_mq = Column(Float, nullable=False)
    reddito_dominicale = Column(Numeric(12, 2), nullable=True)
    reddito_agrario = Column(Numeric(12, 2), nullable=True)
    deduzioni = Column(String(100), nullable=True)

    terreno = relationship("Terreno", back_populates="porzioni")
