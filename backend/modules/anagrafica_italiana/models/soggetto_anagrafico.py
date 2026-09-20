"""
Modello anagrafico centralizzato per soggetti italiani.
Un soggetto può avere più ruoli contemporaneamente (proprietario, affittuario, tecnico, etc.).

Questo modulo gestisce l'anagrafica di persone fisiche e giuridiche secondo
le normative italiane (codice fiscale, partita IVA, etc.).
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TipoSoggetto(str, enum.Enum):
    """Tipologia di soggetto anagrafico"""
    PERSONA_FISICA = "PERSONA_FISICA"
    PERSONA_GIURIDICA = "PERSONA_GIURIDICA"


class SoggettoAnagrafico(Base):
    """
    Tabella anagrafica centralizzata per tutti i soggetti della piattaforma.

    Gestisce i dati anagrafici di base per persone fisiche e giuridiche italiane.
    Le specializzazioni (proprietario, affittuario, tecnico, etc.) sono gestite
    tramite il sistema dinamico di ruoli (SoggettoRuolo).

    Vantaggi:
    - Nessuna duplicazione di dati anagrafici
    - Un soggetto può avere più ruoli simultaneamente
    - Aggiornamenti centralizzati (es. cambio telefono in un solo punto)
    - Facile estensione per nuovi ruoli da parte di moduli
    """
    __tablename__ = "anag_soggetti_anagrafici"
    __table_args__ = {'extend_existing': True}

    # Identificativi
    id = Column(Integer, primary_key=True, index=True)
    tipo_soggetto = Column(SQLEnum(TipoSoggetto), nullable=False, index=True)

    # Link to platform User (nullable - not all soggetti have system access)
    # Se valorizzato, l'anagrafica può accedere al sistema come utente
    # L'email dell'anagrafica sarà usata come username
    # FK is enforced in tenant migration to public.core_users; keep model loose to avoid
    # cross-module metadata resolution during module migrations.
    user_id = Column(Integer, nullable=True, unique=True, index=True)
    user = relationship(
        "User",
        primaryjoin="SoggettoAnagrafico.user_id==User.id",
        foreign_keys=[user_id],
        backref="soggetto_anagrafico",
    )

    # Dati fiscali italiani (almeno uno deve essere valorizzato)
    codice_fiscale = Column(String(16), unique=True, index=True, nullable=True)
    partita_iva = Column(String(11), unique=True, index=True, nullable=True)

    # Documento identità (per soggetti stranieri senza codice fiscale italiano,
    # es. turisti stranieri in affitti brevi). Nessun vincolo di unicità DB
    # deliberato: il match è a livello applicativo (SimilarityMatchingService),
    # non a livello di constraint — un numero documento sporco/duplicato non
    # deve mai bloccare una scrittura.
    tipo_documento_identita = Column(String(50), nullable=True, index=True)
    numero_documento_identita = Column(String(50), nullable=True, index=True)
    stato_rilascio_documento = Column(String(100), nullable=True)

    # Persona fisica
    nome = Column(String(100), nullable=True)
    cognome = Column(String(100), nullable=True)
    data_nascita = Column(Date, nullable=True)
    luogo_nascita = Column(String(100), nullable=True)

    # Persona giuridica
    ragione_sociale = Column(String(200), nullable=True)

    # Contatti
    email = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    cellulare = Column(String(20), nullable=True)
    pec = Column(String(255), nullable=True)

    # Indirizzo
    indirizzo = Column(String(255), nullable=True)
    citta = Column(String(100), nullable=True)
    cap = Column(String(10), nullable=True)
    provincia = Column(String(2), nullable=True)

    # Meta
    note = Column(String(1000), nullable=True)
    attivo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Sistema di ruoli dinamici
    ruoli_assegnati = relationship(
        "SoggettoRuolo",
        primaryjoin="SoggettoRuolo.soggetto_id==SoggettoAnagrafico.id",
        foreign_keys="[SoggettoRuolo.soggetto_id]",
    )

    # Ruoli azienda (associazioni persona-azienda)
    ruoli_in_aziende = relationship(
        "RuoloAzienda",
        foreign_keys="[RuoloAzienda.persona_fisica_id]",
        back_populates="persona_fisica",
        cascade="all, delete-orphan"
    )
    persone_associate = relationship(
        "RuoloAzienda",
        foreign_keys="[RuoloAzienda.persona_giuridica_id]",
        back_populates="persona_giuridica",
        cascade="all, delete-orphan"
    )

    # Relationships con moduli esterni (cross-module)
    # Questi sono dichiarati come stringhe per lazy loading e evitare import circolari
    proprietari = relationship("Proprietario", back_populates="soggetto", foreign_keys="[Proprietario.soggetto_id]")
    affittuari = relationship("Affittuario", back_populates="soggetto", foreign_keys="[Affittuario.soggetto_id]")
    tecnici = relationship("Tecnico", back_populates="soggetto", foreign_keys="[Tecnico.soggetto_id]")

    def __repr__(self):
        if self.tipo_soggetto == TipoSoggetto.PERSONA_FISICA:
            nome_completo = f"{self.nome} {self.cognome}"
        else:
            nome_completo = self.ragione_sociale
        return f"<SoggettoAnagrafico {self.id}: {nome_completo}>"

    @property
    def nome_completo(self):
        """Restituisce il nome completo del soggetto"""
        if self.tipo_soggetto == TipoSoggetto.PERSONA_FISICA:
            return f"{self.nome} {self.cognome}".strip()
        else:
            return self.ragione_sociale or ""

    @property
    def identificativo_fiscale(self):
        """Restituisce il primo identificativo fiscale disponibile"""
        return self.codice_fiscale or self.partita_iva or ""
