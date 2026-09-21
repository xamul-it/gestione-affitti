"""
Documento model shared across modules.

Core platform model (app/core), per the module-communication architecture
(docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md)
which lists the document registry as a core service alongside auth,
notifications and the scadenzario — any domain module can attach documents
to its own entities without depending on another domain module for it.

Multi-File Support (v2):
- A Documento can have multiple files (via DocumentoFile relationship)
- Legacy single-file fields (nome_file, file_path) kept for backward compatibility
- Parsed data aggregated in metadata_parsato JSON field
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, BigInteger, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EntityType(str, enum.Enum):
    IMMOBILE = "IMMOBILE"
    CONDOMINIO = "CONDOMINIO"
    AFFITTUARIO = "AFFITTUARIO"
    CONTRATTO = "CONTRATTO"
    SPESA = "SPESA"
    INCASSO = "INCASSO"
    TECNICO = "TECNICO"
    CERTIFICATO_ENERGETICO = "CERTIFICATO_ENERGETICO"
    PROPRIETARIO = "PROPRIETARIO"
    SOGGETTO_ANAGRAFICO = "SOGGETTO_ANAGRAFICO"


class TipoDocumentoEnum(str, enum.Enum):
    CARTA_IDENTITA = "CARTA_IDENTITA"
    PASSAPORTO = "PASSAPORTO"
    PATENTE = "PATENTE"
    PARTITA_IVA = "PARTITA_IVA"
    VISURA_CAMERALE = "VISURA_CAMERALE"
    CERTIFICATO_PROFESSIONALE = "CERTIFICATO_PROFESSIONALE"
    ISCRIZIONE_ALBO = "ISCRIZIONE_ALBO"
    CONTRATTO = "CONTRATTO"
    DOCUMENTO_GENERICO = "DOCUMENTO_GENERICO"
    CERTIFICATO_ENERGETICO = "CERTIFICATO_ENERGETICO"
    VISURA_CATASTALE = "VISURA_CATASTALE"
    PLANIMETRIA = "PLANIMETRIA"
    CONTRATTO_AFFITTO = "CONTRATTO_AFFITTO"
    DOCUMENTO_IDENTITA = "DOCUMENTO_IDENTITA"
    CODICE_FISCALE = "CODICE_FISCALE"
    FATTURA = "FATTURA"
    RICEVUTA_PAGAMENTO = "RICEVUTA_PAGAMENTO"
    PERIZIA = "PERIZIA"
    FOTO = "FOTO"
    ALTRO = "ALTRO"


class Documento(Base):
    """
    Multi-file document entity.

    Represents a logical document (e.g., ID card) which may consist of
    multiple physical files (e.g., front and back images).

    Changes from v1:
        - metadata_parsato: NEW - Aggregated parsed data from all files
        - confidence_score: NEW - Average confidence across all files
        - files: NEW - Relationship to DocumentoFile (1:N)
        - Legacy fields (nome_file, file_path, etc.) are now nullable
    """
    __tablename__ = "anag_documenti"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(SQLEnum(EntityType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)

    tipo_documento_id = Column(
        Integer,
        ForeignKey("public.anag_tipi_documento.id"),
        nullable=True,
        comment="Reference to TipoDocumento in public schema"
    )

    descrizione = Column(String(500), nullable=True)
    note = Column(String(500), nullable=True)
    data_scadenza = Column(Date, nullable=True, index=True)

    # NEW: Parsed data storage (v2)
    metadata_parsato = Column(
        JSON,
        nullable=True,
        comment="Aggregated parsed data from all files"
    )
    confidence_score = Column(
        Integer,
        nullable=True,
        comment="Average confidence score (0-100) from all parsed files"
    )

    # LEGACY: Single-file fields (nullable for backward compatibility)
    tipo_documento = Column(SQLEnum(TipoDocumentoEnum), nullable=True)  # DEPRECATED
    nome_file = Column(String(255), nullable=True, comment="DEPRECATED - Use files relationship")
    file_path = Column(String(500), nullable=True, comment="DEPRECATED - Use files relationship")
    mime_type = Column(String(100), nullable=True, comment="DEPRECATED")
    dimensione = Column(BigInteger, nullable=True, comment="DEPRECATED")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    files = relationship(
        "DocumentoFile",
        back_populates="documento",
        cascade="all, delete-orphan",
        order_by="DocumentoFile.ordine",
        lazy="select"
    )
    tipo = relationship("TipoDocumento", foreign_keys=[tipo_documento_id])

    def __repr__(self):
        file_count = len(self.files) if self.files else 0
        if file_count > 0:
            return f"<Documento {self.id} - {self.entity_type}:{self.entity_id} ({file_count} files)>"
        else:
            # Legacy format
            nome = self.nome_file or "unknown"
            return f"<Documento {nome} - {self.entity_type}:{self.entity_id}>"

    @property
    def is_legacy(self) -> bool:
        """Check if document uses legacy single-file structure"""
        return bool(self.file_path and not self.files)

    def get_files_list(self) -> list:
        """
        Get list of files, supporting both new and legacy structure.

        Returns:
            List of file dictionaries
        """
        if self.files:
            # New multi-file structure
            return [f.to_dict() for f in self.files]
        elif self.file_path:
            # Legacy single-file structure
            return [{
                "id": None,
                "file_path": self.file_path,
                "nome_file": self.nome_file,
                "mime_type": self.mime_type,
                "dimensione": self.dimensione,
                "ordine": 1,
                "tipo_pagina": "unico",
                "_legacy": True
            }]
        else:
            return []

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "entity_type": self.entity_type.value if self.entity_type else None,
            "entity_id": self.entity_id,
            "tipo_documento_id": self.tipo_documento_id,
            "descrizione": self.descrizione,
            "note": self.note,
            "data_scadenza": self.data_scadenza.isoformat() if self.data_scadenza else None,
            "metadata_parsato": self.metadata_parsato,
            "confidence_score": self.confidence_score,
            "files": self.get_files_list(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_legacy": self.is_legacy
        }
