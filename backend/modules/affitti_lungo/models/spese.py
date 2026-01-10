from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class CategoriaSpesa(str, enum.Enum):
    MANUTENZIONE = "manutenzione"
    UTENZE = "utenze"
    TASSE = "tasse"
    ASSICURAZIONE = "assicurazione"
    AMMINISTRAZIONE = "amministrazione"
    RISTRUTTURAZIONE = "ristrutturazione"
    ALTRO = "altro"


class Spesa(Base):
    __tablename__ = "spese"

    id = Column(Integer, primary_key=True, index=True)
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False)
    tabella_millesimale_id = Column(Integer, ForeignKey("tabelle_millesimali.id"), nullable=True)  # Se NULL, spesa diretta
    data = Column(Date, nullable=False)
    importo = Column(Float, nullable=False)
    categoria = Column(Enum(CategoriaSpesa), nullable=False)
    descrizione = Column(String(255), nullable=False)
    fornitore = Column(String(255))
    numero_fattura = Column(String(100))
    pagata = Column(Integer, default=0)  # 0 = no, 1 = si
    data_pagamento = Column(Date)
    metodo_pagamento = Column(String(50))  # Bonifico, Contanti, Carta, etc.

    # Per spese condominiali
    spesa_condominiale = Column(Integer, default=0)  # 0 = spesa diretta, 1 = spesa condominiale da ripartire
    ripartita = Column(Integer, default=0)  # 0 = non ripartita, 1 = ripartita

    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="spese")
    tabella_millesimale = relationship("TabellaMillesimale", back_populates="spese")
    ripartizioni = relationship("RipartizioneSpesa", back_populates="spesa", cascade="all, delete-orphan")
