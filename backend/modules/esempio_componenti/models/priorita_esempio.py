"""
PrioritaEsempio Model - Domain Data

Priorità di esempio per classificare l'urgenza degli elementi.
Questa tabella è nel PUBLIC schema (dati condivisi tra tutti i tenant).
Viene creata alla registrazione del modulo e popolata con seed data.
"""
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class PrioritaEsempio(Base):
    """
    Priorità di esempio - DOMAIN DATA (public schema).

    Le priorità sono condivise tra tutti i tenant.
    I tenant possono usarle ma non modificarle.
    """
    __tablename__ = "esem_priorita_esempio"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)

    codice = Column(String(10), unique=True, nullable=False, index=True)
    """Codice univoco della priorità (es: 'P1', 'P2')"""

    nome = Column(String(50), nullable=False)
    """Nome della priorità"""

    livello = Column(Integer, nullable=False, default=0)
    """Livello numerico (più alto = più urgente)"""

    colore = Column(String(7), nullable=True, default="#95a5a6")
    """Colore esadecimale per UI"""

    attivo = Column(Boolean, nullable=False, default=True)
    """Se la priorità è attiva e selezionabile"""

    def __repr__(self):
        return f"<PrioritaEsempio(codice='{self.codice}', nome='{self.nome}', livello={self.livello})>"
