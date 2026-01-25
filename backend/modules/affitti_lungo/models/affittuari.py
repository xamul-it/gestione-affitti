from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Affittuario(Base):
    """
    Tabella specializzazione per il ruolo di Affittuario.

    Contiene SOLO i dati specifici del ruolo di affittuario.
    I dati anagrafici sono centralizzati in soggetti_anagrafici.

    Un soggetto può essere contemporaneamente proprietario, affittuario, tecnico, etc.
    """
    __tablename__ = "affittuari"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key al soggetto anagrafico (OBBLIGATORIO)
    # Riferimento a anag_soggetti_anagrafici nel modulo anagrafica_italiana
    soggetto_id = Column(
        Integer,
        ForeignKey("anag_soggetti_anagrafici.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # SOLO campi specifici per il ruolo di affittuario
    note_affittuario = Column(String(500), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # DEPRECATED FIELDS - manteniamo per compatibilità durante la transizione
    # Questi campi saranno rimossi nella prossima versione
    # Usare soggetto.* per accedere ai dati anagrafici
    nome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.nome
    cognome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.cognome
    codice_fiscale = Column(String(16), nullable=True)  # DEPRECATED: use soggetto.codice_fiscale
    data_nascita = Column(Date, nullable=True)  # DEPRECATED: use soggetto.data_nascita
    luogo_nascita = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.luogo_nascita
    email = Column(String(255), nullable=True)  # DEPRECATED: use soggetto.email
    telefono = Column(String(50), nullable=True)  # DEPRECATED: use soggetto.telefono
    cellulare = Column(String(50), nullable=True)  # DEPRECATED: use soggetto.cellulare
    indirizzo_residenza = Column(String(255), nullable=True)  # DEPRECATED: use soggetto.indirizzo
    citta_residenza = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.citta
    cap_residenza = Column(String(10), nullable=True)  # DEPRECATED: use soggetto.cap
    provincia_residenza = Column(String(2), nullable=True)  # DEPRECATED: use soggetto.provincia
    note = Column(Text, nullable=True)  # DEPRECATED: use note_affittuario

    # Relationships
    soggetto = relationship("SoggettoAnagrafico", foreign_keys=[soggetto_id], back_populates="affittuari")
    contratti = relationship("Contratto", back_populates="affittuario")

    def __repr__(self):
        return f"<Affittuario {self.id}: Soggetto {self.soggetto_id}>"
