"""
ElementoEsempio Model - Tenant Data

Elemento di esempio che dimostra l'uso di vari tipi di campo.
Questa tabella è nello schema TENANT (dati isolati per tenant).
Viene creata quando il modulo viene abilitato per un tenant.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ElementoEsempio(Base):
    """
    Elemento di esempio - TENANT DATA (tenant schema).

    Ogni tenant ha i propri elementi, isolati dagli altri tenant.
    Dimostra vari tipi di campo per testare DataTable e Import/Export.
    """
    __tablename__ = "elementi_esempio"
    # No schema specified = tenant schema (set via search_path)

    id = Column(Integer, primary_key=True, index=True)

    # === Campi testo ===
    codice = Column(String(20), nullable=False, index=True)
    """Codice identificativo dell'elemento"""

    titolo = Column(String(200), nullable=False)
    """Titolo/nome dell'elemento"""

    descrizione = Column(Text, nullable=True)
    """Descrizione estesa"""

    # === Relazioni con domini (public schema) ===
    categoria_id = Column(Integer, ForeignKey("public.categorie_esempio.id"), nullable=True)
    """FK alla categoria (dominio in public schema)"""

    priorita_id = Column(Integer, ForeignKey("public.priorita_esempio.id"), nullable=True)
    """FK alla priorità (dominio in public schema)"""

    # === Campi numerici ===
    quantita = Column(Integer, nullable=True, default=1)
    """Quantità numerica intera"""

    importo = Column(Numeric(10, 2), nullable=True)
    """Importo monetario con 2 decimali"""

    percentuale = Column(Numeric(5, 2), nullable=True)
    """Percentuale (0.00 - 100.00)"""

    # === Campi data ===
    data_inizio = Column(Date, nullable=True)
    """Data di inizio"""

    data_fine = Column(Date, nullable=True)
    """Data di fine"""

    # === Campi stato ===
    stato = Column(String(20), nullable=False, default="bozza")
    """Stato: 'bozza', 'attivo', 'completato', 'annullato'"""

    attivo = Column(Boolean, nullable=False, default=True)
    """Se l'elemento è attivo"""

    # === Metadati ===
    note = Column(Text, nullable=True)
    """Note aggiuntive"""

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    """Data creazione"""

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    """Data ultimo aggiornamento"""

    # === Relationships (per eager loading) ===
    # Note: These reference public schema tables
    # categoria = relationship("CategoriaEsempio", lazy="joined")
    # priorita = relationship("PrioritaEsempio", lazy="joined")

    def __repr__(self):
        return f"<ElementoEsempio(codice='{self.codice}', titolo='{self.titolo}', stato='{self.stato}')>"
