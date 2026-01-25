from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RipartizioneSpesa(Base):
    """
    Ripartizione di una spesa condominiale tra i vari immobili.
    Ogni record rappresenta la quota di spesa attribuita a un singolo immobile.
    """
    __tablename__ = "ripartizioni_spese"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    spesa_id = Column(Integer, ForeignKey("spese.id"), nullable=False)
    unita_immobiliare_id = Column(Integer, ForeignKey("immo_unita_immobiliari.id"), nullable=False)

    # Importi calcolati
    importo_ripartito = Column(Float, nullable=False)  # Quota di spesa attribuita a questo immobile

    # Dettagli del calcolo (per trasparenza)
    millesimi_applicati = Column(Float)  # Millesimi usati nel calcolo
    consumo_applicato = Column(Float)  # Consumo usato nel calcolo
    occupanti_applicati = Column(Integer)  # Numero occupanti usato nel calcolo
    coefficiente_piano = Column(Float)  # Coefficiente piano se applicato

    # Importi parziali per ripartizioni miste
    importo_da_millesimi = Column(Float)  # Quota calcolata a millesimi
    importo_da_consumo = Column(Float)  # Quota calcolata a consumo
    importo_da_occupanti = Column(Float)  # Quota calcolata per occupanti

    # Stato pagamento
    pagata = Column(Integer, default=0)  # 0 = non pagata, 1 = pagata
    data_pagamento = Column(DateTime(timezone=True))

    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    spesa = relationship("Spesa", back_populates="ripartizioni")
    unita_immobiliare = relationship("UnitaImmobiliare")
