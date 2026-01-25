"""
Proprietario Model - Property owner role specialization.

SCHEMA: TENANT
PREFIX: immo_ (modulo immobili)
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Proprietario(Base):
    """
    Tabella specializzazione per il ruolo di Proprietario.

    Contiene SOLO i dati specifici del ruolo di proprietario.
    I dati anagrafici sono centralizzati in anag_soggetti_anagrafici (modulo anagrafica_italiana).

    Un soggetto può essere contemporaneamente proprietario, affittuario, tecnico, etc.
    """
    __tablename__ = "immo_proprietari"
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

    # SOLO campi specifici per il ruolo di proprietario
    note_proprietario = Column(String(500), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # DEPRECATED FIELDS - manteniamo per compatibilità durante la transizione
    # Questi campi saranno rimossi nella prossima versione
    # Usare soggetto.* per accedere ai dati anagrafici
    nome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.nome
    cognome = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.cognome
    codice_fiscale = Column(String(16), nullable=True)  # DEPRECATED: use soggetto.codice_fiscale
    data_nascita = Column(String(10), nullable=True)  # DEPRECATED: use soggetto.data_nascita
    luogo_nascita = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.luogo_nascita
    email = Column(String(255), nullable=True)  # DEPRECATED: use soggetto.email
    telefono = Column(String(20), nullable=True)  # DEPRECATED: use soggetto.telefono
    cellulare = Column(String(20), nullable=True)  # DEPRECATED: use soggetto.cellulare
    indirizzo = Column(String(255), nullable=True)  # DEPRECATED: use soggetto.indirizzo
    citta = Column(String(100), nullable=True)  # DEPRECATED: use soggetto.citta
    cap = Column(String(10), nullable=True)  # DEPRECATED: use soggetto.cap
    provincia = Column(String(2), nullable=True)  # DEPRECATED: use soggetto.provincia
    note = Column(String(500), nullable=True)  # DEPRECATED: use note_proprietario
    attivo = Column(Integer, nullable=True)  # DEPRECATED: use soggetto.attivo

    # Relationships
    soggetto = relationship("SoggettoAnagrafico", foreign_keys=[soggetto_id], back_populates="proprietari")
    diritti_immobile = relationship("DirittoImmobile", back_populates="proprietario")

    def __repr__(self):
        return f"<Proprietario {self.id}: Soggetto {self.soggetto_id}>"
