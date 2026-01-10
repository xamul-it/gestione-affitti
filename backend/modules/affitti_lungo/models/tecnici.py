from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class SpecializzazioneTecnico(str, enum.Enum):
    ELETTRICISTA = "ELETTRICISTA"
    IDRAULICO = "IDRAULICO"
    TERMOTECNICO = "TERMOTECNICO"
    GEOMETRA = "GEOMETRA"
    ARCHITETTO = "ARCHITETTO"
    INGEGNERE = "INGEGNERE"
    CERTIFICATORE_ENERGETICO = "CERTIFICATORE_ENERGETICO"
    MANUTENTORE_CALDAIE = "MANUTENTORE_CALDAIE"
    ALTRO = "ALTRO"


class Tecnico(Base):
    """
    Tabella specializzazione per il ruolo di Tecnico.

    Contiene SOLO i dati specifici del ruolo di tecnico (specializzazione, albo, etc.).
    I dati anagrafici sono centralizzati in soggetti_anagrafici.

    Un soggetto può essere contemporaneamente proprietario, affittuario, tecnico, etc.
    """
    __tablename__ = "tecnici"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key al soggetto anagrafico (OBBLIGATORIO)
    soggetto_id = Column(
        Integer,
        ForeignKey("soggetti_anagrafici.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # SOLO campi specifici per il ruolo di tecnico
    specializzazione = Column(SQLEnum(SpecializzazioneTecnico), nullable=False)
    numero_iscrizione_albo = Column(String(50), nullable=True)
    note_tecnico = Column(String(500), nullable=True)
    attivo = Column(Boolean, default=True, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # DEPRECATED FIELDS - manteniamo per compatibilità durante la transizione
    # Questi campi saranno rimossi nella prossima versione
    # Usare soggetto.* per accedere ai dati anagrafici
    nome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.nome
    cognome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.cognome
    ragione_sociale = Column(String(200), nullable=True)  # DEPRECATED: use soggetto.ragione_sociale
    partita_iva = Column(String(20), nullable=True)  # DEPRECATED: use soggetto.partita_iva
    codice_fiscale = Column(String(16), nullable=True)  # DEPRECATED: use soggetto.codice_fiscale
    telefono = Column(String(20), nullable=True)  # DEPRECATED: use soggetto.telefono
    email = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.email
    indirizzo = Column(String(250), nullable=True)  # DEPRECATED: use soggetto.indirizzo
    note = Column(String(500), nullable=True)  # DEPRECATED: use note_tecnico

    # Relationships
    soggetto = relationship("SoggettoAnagrafico", foreign_keys=[soggetto_id], back_populates="tecnici")

    def __repr__(self):
        return f"<Tecnico {self.id}: Soggetto {self.soggetto_id} - {self.specializzazione.value}>"
