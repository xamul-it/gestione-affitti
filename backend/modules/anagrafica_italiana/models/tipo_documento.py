"""
Tipo Documento Model - Tipologie di documenti per l'anagrafica.

Gestisce i tipi di documenti che possono essere associati ai soggetti anagrafici:
- Documenti di identità (CI, Passaporto)
- Documenti fiscali (Codice Fiscale, Partita IVA)
- Documenti professionali (Patente, Certificazioni)
- Altri documenti
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TipoDocumento(Base):
    """
    Tipologie di documenti per soggetti anagrafici.

    Definisce le categorie standard di documenti che possono essere
    allegati alle anagrafiche (carta identità, codice fiscale, etc.).

    Esempi:
    - CARTA_IDENTITA: Carta d'Identità
    - CODICE_FISCALE: Codice Fiscale
    - PARTITA_IVA: Partita IVA
    - PATENTE: Patente di Guida
    - PASSAPORTO: Passaporto
    """
    __tablename__ = "anag_tipi_documento"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(50), nullable=False, unique=True, index=True)  # CARTA_IDENTITA, CODICE_FISCALE, etc.
    nome = Column(String(100), nullable=False)  # Nome leggibile
    descrizione = Column(String(255), nullable=True)
    categoria = Column(String(50), nullable=True, index=True)  # identita, fiscale, professionale, altro
    richiede_scadenza = Column(Boolean, default=False)  # Se il documento ha una data di scadenza
    attivo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TipoDocumento(codice='{self.codice}', nome='{self.nome}')>"
