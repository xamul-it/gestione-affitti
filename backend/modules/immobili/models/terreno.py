"""
Terreno (Land) model for managing undeveloped land parcels.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Terreno(Base):
    """
    Model for land parcels (non-built real estate).

    Manages undeveloped land with cadastral data, ownership associations,
    and classification according to Italian cadastral system.

    This table is created in tenant schemas (tenant-specific data).
    The tipologia references public.tipologie_terreno (shared domain data).
    """
    __tablename__ = "terreni"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Identification
    codice = Column(String(50), unique=True, index=True, nullable=False)  # es. TER-001
    nome = Column(String(255), nullable=False)  # Nome descrittivo
    descrizione = Column(Text, nullable=True)  # Descrizione estesa

    # Classification - FK to public.tipologie_terreno
    tipologia_id = Column(
        Integer,
        ForeignKey("public.tipologie_terreno.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Location
    indirizzo = Column(String(255), nullable=True)  # Località/indirizzo (può essere generico)
    comune = Column(String(100), nullable=False)
    cap = Column(String(10), nullable=True)
    provincia = Column(String(2), nullable=False)
    nazione = Column(String(100), nullable=True, default="Italia")

    # Physical characteristics
    superficie = Column(Float, nullable=False)  # Superficie in mq o ettari
    unita_misura_superficie = Column(String(10), nullable=True, default="mq")  # "mq" o "ha"

    # Cadastral data (Dati Catastali)
    sezione_catastale = Column(String(20), nullable=True)  # Sezione amministrativa catastale
    foglio = Column(String(20), nullable=True)  # Numero di foglio catastale
    particella = Column(String(20), nullable=True)  # Numero di particella/mappale
    subalterno = Column(String(20), nullable=True)  # Subalterno (raro per terreni)
    qualita_coltura = Column(String(100), nullable=True)  # Qualità colturale per terreni agricoli
    classe_catastale = Column(String(10), nullable=True)  # Classe catastale

    # Fiscal values (Valori fiscali)
    reddito_dominicale = Column(Numeric(12, 2), nullable=True)  # Reddito dominicale
    reddito_agrario = Column(Numeric(12, 2), nullable=True)  # Reddito agrario

    # Notes
    note = Column(Text, nullable=True)

    # Status
    attivo = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tipologia = relationship("TipologiaTerreno", foreign_keys=[tipologia_id])

    def __repr__(self):
        tipologia_info = self.tipologia.codice if self.tipologia else "N/A"
        return f"<Terreno(codice='{self.codice}', nome='{self.nome}', tipologia={tipologia_info})>"
