"""
CategoriaEsempio Model - Domain Data

Categoria di esempio per classificare gli elementi.
Questa tabella è nel PUBLIC schema (dati condivisi tra tutti i tenant).
Viene creata alla registrazione del modulo e popolata con seed data.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text
from app.core.database import Base


class CategoriaEsempio(Base):
    """
    Categoria di esempio - DOMAIN DATA (public schema).

    Le categorie sono condivise tra tutti i tenant.
    I tenant possono usarle ma non modificarle.
    """
    __tablename__ = "categorie_esempio"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)

    codice = Column(String(20), unique=True, nullable=False, index=True)
    """Codice univoco della categoria (es: 'CAT001')"""

    nome = Column(String(100), nullable=False)
    """Nome della categoria"""

    descrizione = Column(Text, nullable=True)
    """Descrizione opzionale"""

    colore = Column(String(7), nullable=True, default="#3498db")
    """Colore esadecimale per UI (es: '#3498db')"""

    icona = Column(String(50), nullable=True)
    """Nome icona per UI (es: 'folder', 'star')"""

    ordine = Column(Integer, nullable=False, default=0)
    """Ordine di visualizzazione"""

    attivo = Column(Boolean, nullable=False, default=True)
    """Se la categoria è attiva e selezionabile"""

    def __repr__(self):
        return f"<CategoriaEsempio(codice='{self.codice}', nome='{self.nome}')>"
