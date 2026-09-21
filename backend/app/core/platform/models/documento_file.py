"""
DocumentoFile Model - Individual files within a multi-file document.

Core platform model (app/core) — see documento.py for why.
"""
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DocumentoFile(Base):
    """
    Individual file belonging to a multi-file document.

    A Documento can have multiple files (e.g., front and back of ID card,
    multiple pages of a contract PDF).

    Each file can optionally have:
    - Normalized version (JPEG for viewing/parsing)
    - Parsing results (if automated data extraction is configured)

    Examples:
        - Front of ID card (tipo_pagina='fronte')
        - Back of ID card (tipo_pagina='retro')
        - Page 1 of multi-page contract (tipo_pagina='pagina_1')
        - Single-page document (tipo_pagina='unico')

    Relationships:
        - documento: Parent Documento (many-to-one)
        - parsing_job: Optional DocumentJob if parsing was performed (many-to-one)
    """
    __tablename__ = "anag_documenti_files"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Parent documento
    documento_id = Column(
        Integer,
        ForeignKey("anag_documenti.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent Documento ID"
    )

    # File information
    file_path = Column(
        String(500),
        nullable=False,
        comment="Relative path to original file (includes tenant prefix)"
    )
    nome_file = Column(
        String(255),
        nullable=False,
        comment="Original filename"
    )
    mime_type = Column(
        String(100),
        nullable=True,
        comment="MIME type (image/jpeg, application/pdf, etc.)"
    )
    dimensione = Column(
        BigInteger,
        nullable=True,
        comment="File size in bytes"
    )

    # Display and organization
    ordine = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Display order (1, 2, 3, ...)"
    )
    tipo_pagina = Column(
        String(50),
        nullable=True,
        comment="Page type: fronte, retro, pagina_1, pagina_2, unico, etc."
    )

    # Normalized file (cache for viewing and parsing)
    file_normalizzato_path = Column(
        String(500),
        nullable=True,
        comment="Path to normalized JPEG file (2048px max, quality 85%)"
    )
    normalizzato_width = Column(
        Integer,
        nullable=True,
        comment="Width of normalized image in pixels"
    )
    normalizzato_height = Column(
        Integer,
        nullable=True,
        comment="Height of normalized image in pixels"
    )

    # Parsing information (optional per file)
    parsing_job_id = Column(
        Integer,
        ForeignKey("core_document_jobs.id", ondelete="SET NULL"),
        nullable=True,
        comment="DocumentJob ID if parsing was performed on this file"
    )
    parsing_result = Column(
        JSON,
        nullable=True,
        comment="Parsed data extracted from this specific file"
    )
    confidence_score = Column(
        Integer,
        nullable=True,
        comment="Parsing confidence for this file (0-100)"
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="File creation timestamp"
    )

    # Relationships
    documento = relationship(
        "Documento",
        back_populates="files"
    )
    parsing_job = relationship(
        "DocumentJob",
        foreign_keys=[parsing_job_id]
    )

    def __repr__(self):
        return (
            f"<DocumentoFile(id={self.id}, documento_id={self.documento_id}, "
            f"tipo_pagina='{self.tipo_pagina}', nome_file='{self.nome_file}')>"
        )

    @property
    def is_parsed(self) -> bool:
        """Check if file has parsing results"""
        return self.parsing_result is not None

    @property
    def is_normalized(self) -> bool:
        """Check if file has been normalized to JPEG"""
        return self.file_normalizzato_path is not None

    @property
    def display_name(self) -> str:
        """Get user-friendly display name"""
        if self.tipo_pagina:
            tipo_map = {
                'fronte': 'Fronte',
                'retro': 'Retro',
                'unico': 'Documento',
            }
            if self.tipo_pagina in tipo_map:
                return tipo_map[self.tipo_pagina]
            elif self.tipo_pagina.startswith('pagina_'):
                page_num = self.tipo_pagina.split('_')[1]
                return f'Pagina {page_num}'
        return self.nome_file

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "documento_id": self.documento_id,
            "file_path": self.file_path,
            "nome_file": self.nome_file,
            "mime_type": self.mime_type,
            "dimensione": self.dimensione,
            "ordine": self.ordine,
            "tipo_pagina": self.tipo_pagina,
            "display_name": self.display_name,
            "file_normalizzato_path": self.file_normalizzato_path,
            "normalizzato_width": self.normalizzato_width,
            "normalizzato_height": self.normalizzato_height,
            "parsing_job_id": self.parsing_job_id,
            "parsing_result": self.parsing_result,
            "confidence_score": self.confidence_score,
            "is_parsed": self.is_parsed,
            "is_normalized": self.is_normalized,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
