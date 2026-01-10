from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class StatoContratto(str, enum.Enum):
    ATTIVO = "ATTIVO"
    SCADUTO = "SCADUTO"
    DISDETTO = "DISDETTO"
    TERMINATO = "TERMINATO"


class UsoImmobile(str, enum.Enum):
    ABITATIVO = "ABITATIVO"
    COMMERCIALE = "COMMERCIALE"
    UFFICIO = "UFFICIO"
    MAGAZZINO = "MAGAZZINO"
    ALTRO = "ALTRO"


class TipologiaContratto(str, enum.Enum):
    LIBERO_MERCATO = "LIBERO_MERCATO"  # 4+4 abitativo o durata variabile commerciale
    CANONE_CONCORDATO = "CANONE_CONCORDATO"  # 3+2 con accordi territoriali
    TRANSITORIO = "TRANSITORIO"  # Durata limitata per esigenze temporanee
    STUDENTI = "STUDENTI"  # Contratti per studenti universitari
    FORESTERIA = "FORESTERIA"  # Uso foresteria aziendale
    COMMERCIALE_LIBERO = "COMMERCIALE_LIBERO"  # 6+6 o altra durata
    ALTRO = "ALTRO"


class RegimeFiscale(str, enum.Enum):
    ORDINARIO_IRPEF = "ORDINARIO_IRPEF"  # Tassazione ordinaria IRPEF
    CEDOLARE_SECCA_21 = "CEDOLARE_SECCA_21"  # Cedolare secca 21% (libero mercato)
    CEDOLARE_SECCA_10 = "CEDOLARE_SECCA_10"  # Cedolare secca 10% (canone concordato)


class Contratto(Base):
    __tablename__ = "contratti"

    id = Column(Integer, primary_key=True, index=True)
    numero_contratto = Column(String(50), unique=True, index=True, nullable=False)

    # Riferimenti
    unita_immobiliare_id = Column(Integer, ForeignKey("unita_immobiliari.id"), nullable=False, index=True)
    affittuario_id = Column(Integer, ForeignKey("affittuari.id"), nullable=False, index=True)

    # Tipologia e uso
    uso_immobile = Column(SQLEnum(UsoImmobile), nullable=False, default=UsoImmobile.ABITATIVO)
    tipologia_contratto = Column(SQLEnum(TipologiaContratto), nullable=False)

    # Durata (separata dalla tipologia)
    durata_anni_iniziale = Column(Integer, nullable=False)  # es. 4 per il 4+4
    durata_anni_rinnovo = Column(Integer, nullable=True)  # es. 4 per il 4+4, null se non rinnovabile
    data_inizio = Column(Date, nullable=False)
    data_fine = Column(Date, nullable=False)

    # Aspetti economici
    canone_mensile = Column(Numeric(10, 2), nullable=False)
    giorno_pagamento = Column(Integer, default=1)
    deposito_cauzionale = Column(Numeric(10, 2), nullable=True)

    # Regime fiscale
    regime_fiscale = Column(SQLEnum(RegimeFiscale), nullable=False, default=RegimeFiscale.ORDINARIO_IRPEF)

    # Adeguamento ISTAT
    adeguamento_istat = Column(Boolean, default=False)
    percentuale_istat = Column(Numeric(5, 2), nullable=True)  # es. 75.00 per 75%
    data_ultimo_adeguamento = Column(Date, nullable=True)

    # Registrazione
    registrazione_numero = Column(String(100), nullable=True)
    registrazione_data = Column(Date, nullable=True)
    registrazione_agenzia = Column(String(200), nullable=True)

    # Stato e note
    stato = Column(SQLEnum(StatoContratto), default=StatoContratto.ATTIVO, index=True)
    note = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship("UnitaImmobiliare", back_populates="contratti")
    affittuario = relationship("Affittuario", back_populates="contratti")
    incassi = relationship("Incasso", back_populates="contratto")
