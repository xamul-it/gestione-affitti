from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Incasso(Base):
    __tablename__ = "incassi"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    contratto_id = Column(Integer, ForeignKey("contratti.id"), nullable=False)
    data_incasso = Column(Date, nullable=False)
    importo = Column(Float, nullable=False)
    mese_riferimento = Column(String(7), nullable=False)  # Formato: YYYY-MM
    metodo_pagamento = Column(String(50))  # Bonifico, Contanti, Assegno, etc.
    numero_ricevuta = Column(String(100))
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contratto = relationship("Contratto", back_populates="incassi")
