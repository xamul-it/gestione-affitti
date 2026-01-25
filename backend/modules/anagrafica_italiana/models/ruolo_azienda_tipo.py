"""
RuoloAziendaTipo - Tipologia di ruolo aziendale (dato di dominio)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime

from app.core.database import Base


class RuoloAziendaTipo(Base):
    """
    Tipologia di ruolo aziendale normalizzata.

    Questo modello serve per:
    - Evitare duplicati (es: "segretaria" vs "Segretaria")
    - Fornire auto-complete durante l'inserimento
    - Permettere normalizzazione/fusione di ruoli simili
    """
    __tablename__ = "anag_ruoli_azienda_tipi"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True, index=True)
    descrizione = Column(String(500), nullable=True)
    attivo = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RuoloAziendaTipo(id={self.id}, nome='{self.nome}')>"
