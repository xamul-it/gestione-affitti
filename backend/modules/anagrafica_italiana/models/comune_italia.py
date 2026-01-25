"""
Comune Italia Model - Italian municipalities reference data.

Provides comprehensive data for Italian municipalities (comuni) including:
- Official ISTAT codes
- Postal codes (CAP)
- Province and region information
- Geographic coordinates (for future GIS features)

Used for address normalization and CAP lookup during import.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class ComuneItalia(Base):
    """
    Italian municipality reference data.

    Contains ~8,000 Italian municipalities with official codes and postal data.
    Primary use case: CAP (postal code) lookup during address normalization.

    Data source: ISTAT (Istituto Nazionale di Statistica)
    Update frequency: Annually (municipality boundaries can change)

    Example records:
    - Milano: ISTAT='015146', CAP='20100', Provincia='MI'
    - Bologna: ISTAT='037006', CAP='40100', Provincia='BO'
    - Forlì: ISTAT='040012', CAP='47121', Provincia='FO'
    """
    __tablename__ = "anag_comuni_italia"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)  # Official name with accents
    nome_normalized = Column(String(100), nullable=False, index=True)  # Lowercase, no accents
    codice_istat = Column(String(10), nullable=False, unique=True)  # Official ISTAT code
    codice_catastale = Column(String(10), nullable=True)  # Cadastral code (4 chars)
    cap = Column(String(10), nullable=True, index=True)  # Postal code (can be multiple)
    provincia_sigla = Column(String(2), nullable=False, index=True)  # Province abbreviation
    provincia_nome = Column(String(100), nullable=True)  # Province full name
    regione = Column(String(100), nullable=True)  # Region name
    latitudine = Column(Numeric(10, 7), nullable=True)  # Geographic latitude
    longitudine = Column(Numeric(10, 7), nullable=True)  # Geographic longitude
    attivo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_anag_comuni_nome_provincia", "nome_normalized", "provincia_sigla"),
        {"schema": "public", "extend_existing": True}
    )

    def __repr__(self):
        return f"<ComuneItalia(nome='{self.nome}', provincia='{self.provincia_sigla}', cap='{self.cap}')>"
