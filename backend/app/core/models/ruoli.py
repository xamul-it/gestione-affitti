"""
Sistema di registrazione dinamica dei ruoli.

Permette ai moduli di registrare i propri ruoli senza che il core
debba conoscerli in anticipo, mantenendo la modularità del sistema.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RuoloDisponibile(Base):
    """
    Registro dei tipi di ruolo disponibili nella piattaforma.

    Ogni modulo può registrare i propri ruoli durante l'inizializzazione.
    Il core non conosce i ruoli specifici, ma fornisce solo il meccanismo
    di gestione.

    Esempi:
    - Modulo affitti_lungo registra: proprietario, affittuario, tecnico
    - Modulo condominio registra: amministratore, condomino
    - Modulo affitti_brevi registra: host, ospite
    """
    __tablename__ = "core_ruoli_disponibili"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # Identificativo univoco del ruolo (es: 'proprietario', 'affittuario')
    codice = Column(String(50), nullable=False, index=True)

    # Modulo che ha registrato questo ruolo
    modulo_id = Column(String(50), nullable=False, index=True)

    # Nome visualizzabile del ruolo
    nome_display = Column(String(100), nullable=False)

    # Descrizione del ruolo
    descrizione = Column(Text, nullable=True)

    # Nome della tabella che contiene i dati di specializzazione
    # (es: 'proprietari', 'affittuari', 'tecnici')
    tabella_specializzazione = Column(String(100), nullable=True)

    # Metadati aggiuntivi in formato JSON (opzionale)
    # Può contenere configurazioni specifiche del modulo
    metadata_json = Column(Text, nullable=True)

    # Flag attivo/disattivo
    attivo = Column(Boolean, default=True, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Vincolo di unicità: un modulo non può registrare due volte lo stesso codice
    __table_args__ = (
        UniqueConstraint('codice', 'modulo_id', name='uq_ruolo_modulo'),
    )

    # Relationships
    assegnazioni = relationship("SoggettoRuolo", back_populates="ruolo")

    def __repr__(self):
        return f"<RuoloDisponibile {self.codice} (modulo: {self.modulo_id})>"


class SoggettoRuolo(Base):
    """
    Tabella di associazione molti-a-molti tra soggetti e ruoli.

    Un soggetto può avere più ruoli (anche da moduli diversi).
    Un ruolo può essere assegnato a più soggetti.

    Il campo record_specializzazione_id punta al record nella tabella
    di specializzazione del modulo (es: id nella tabella 'proprietari').
    """
    __tablename__ = "core_soggetti_ruoli"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key al soggetto anagrafico
    # Riferimento a anag_soggetti_anagrafici nel modulo anagrafica_italiana
    soggetto_id = Column(Integer, nullable=False, index=True)

    # Foreign key al ruolo disponibile
    ruolo_id = Column(
        Integer,
        ForeignKey("core_ruoli_disponibili.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ID del record nella tabella di specializzazione del modulo
    # Es: se ruolo = 'proprietario', questo è l'ID nella tabella 'proprietari'
    record_specializzazione_id = Column(Integer, nullable=True, index=True)

    # Flag attivo/disattivo (per storicizzare assegnazioni passate)
    attivo = Column(Boolean, default=True, nullable=False)

    # Note sull'assegnazione (opzionale)
    note = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Vincolo di unicità: un soggetto non può avere lo stesso ruolo più volte
    # con lo stesso record di specializzazione
    __table_args__ = (
        UniqueConstraint(
            'soggetto_id',
            'ruolo_id',
            'record_specializzazione_id',
            name='uq_soggetto_ruolo_record'
        ),
    )

    # Relationships
    ruolo = relationship("RuoloDisponibile", back_populates="assegnazioni")

    def __repr__(self):
        return f"<SoggettoRuolo soggetto_id={self.soggetto_id} ruolo_id={self.ruolo_id}>"
