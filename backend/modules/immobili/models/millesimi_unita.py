from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MillesimiUnita(Base):
    """
    Associazione tra un'unità immobiliare e una tabella millesimale con i relativi valori.
    Un'unità immobiliare può avere diversi valori millesimali per diverse tabelle
    (es. 45/1000 per spese generali, 60/1000 per ascensore, ecc.)
    """
    __tablename__ = "millesimi_unita"

    id = Column(Integer, primary_key=True, index=True)
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False)
    tabella_millesimale_id = Column(Integer, ForeignKey("tabelle_millesimali.id"), nullable=False)

    # Valori per il calcolo
    millesimi = Column(Float, nullable=False)  # Valore millesimale (es. 45.5 su 1000)

    # Per ripartizioni speciali
    piano = Column(Integer)  # Numero piano (per ascensore con art. 1124)
    numero_occupanti = Column(Integer, default=0)  # Numero occupanti (per acqua, ecc.)

    # Per consumi (riscaldamento, acqua a consumo)
    consumo = Column(Float, default=0.0)  # Consumo rilevato (kWh, mc, ecc.)
    unita_misura_consumo = Column(String(20))  # es. "kWh", "mc", "litri"

    # Quota personalizzata (per ripartizioni PERSONALIZZATA)
    quota_fissa = Column(Float)  # Importo o percentuale fissa

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constraints: un'unità immobiliare può avere un solo valore per ogni tabella millesimale
    __table_args__ = (
        UniqueConstraint('unita_immobiliare_id', 'tabella_millesimale_id', name='_unita_tabella_uc'),
    )

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="millesimi")
    tabella_millesimale = relationship("TabellaMillesimale", back_populates="millesimi_unita")
