# Specifiche Tecniche di Implementazione
**Sistema Gestione Documenti Multi-File**

## Indice
1. [Backend Implementation](#backend-implementation)
2. [Frontend Implementation](#frontend-implementation)
3. [File Normalization Service](#file-normalization-service)
4. [Similarity Matching Service](#similarity-matching-service)
5. [Testing Strategy](#testing-strategy)
6. [Performance Considerations](#performance-considerations)

---

## Backend Implementation

### 1. Modelli SQLAlchemy

#### Documento (Modificato)
**File**: `backend/modules/anagrafica_italiana/models/documento.py`

```python
"""
Documento model - Multi-file document support.
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, BigInteger, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EntityType(str, enum.Enum):
    IMMOBILE = "IMMOBILE"
    AFFITTUARIO = "AFFITTUARIO"
    CONTRATTO = "CONTRATTO"
    SPESA = "SPESA"
    INCASSO = "INCASSO"
    TECNICO = "TECNICO"
    CERTIFICATO_ENERGETICO = "CERTIFICATO_ENERGETICO"
    PROPRIETARIO = "PROPRIETARIO"
    SOGGETTO_ANAGRAFICO = "SOGGETTO_ANAGRAFICO"


class Documento(Base):
    """
    Multi-file document entity.

    Represents a logical document (e.g., ID card) which may consist of
    multiple physical files (e.g., front and back images).

    Changes from v1:
        - metadata_parsato: NEW - Aggregated parsed data from all files
        - confidence_score: NEW - Average confidence across all files
        - files: NEW - Relationship to DocumentoFile (1:N)
        - Legacy fields (nome_file, file_path, etc.) kept for backward compatibility
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

    # NEW: Parsed data storage
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
        order_by="DocumentoFile.ordine"
    )
    tipo = relationship("TipoDocumento", foreign_keys=[tipo_documento_id])

    def __repr__(self):
        file_count = len(self.files) if self.files else 0
        return f"<Documento {self.id} - {self.entity_type}:{self.entity_id} ({file_count} files)>"

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
```

#### DocumentoFile (Nuovo)
**File**: `backend/modules/anagrafica_italiana/models/documento_file.py`

```python
"""
DocumentoFile model - Individual files within a document.
"""
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DocumentoFile(Base):
    """
    Individual file belonging to a multi-file document.

    Examples:
        - Front of ID card
        - Back of ID card
        - Page 1 of multi-page contract
        - Page 2 of multi-page contract

    Each file can optionally have parsing results if the file type
    supports automated data extraction.
    """
    __tablename__ = "anag_documenti_files"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    documento_id = Column(
        Integer,
        ForeignKey("anag_documenti.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # File information
    file_path = Column(
        String(500),
        nullable=False,
        comment="Relative path to original file (includes tenant prefix)"
    )
    nome_file = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    dimensione = Column(BigInteger, nullable=True, comment="File size in bytes")

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
        comment="Page type: fronte, retro, pagina_1, etc."
    )

    # Normalized file (cache)
    file_normalizzato_path = Column(
        String(500),
        nullable=True,
        comment="Path to normalized JPEG file"
    )
    normalizzato_width = Column(Integer, nullable=True)
    normalizzato_height = Column(Integer, nullable=True)

    # Parsing information (optional per file)
    parsing_job_id = Column(
        Integer,
        ForeignKey("public.core_document_jobs.id", ondelete="SET NULL"),
        nullable=True,
        comment="DocumentJob if parsing was performed"
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    documento = relationship("Documento", back_populates="files")
    parsing_job = relationship(
        "DocumentJob",
        foreign_keys=[parsing_job_id]
    )

    def __repr__(self):
        return f"<DocumentoFile {self.id} - {self.tipo_pagina} ({self.nome_file})>"

    @property
    def is_parsed(self) -> bool:
        """Check if file has parsing results"""
        return self.parsing_result is not None

    @property
    def is_normalized(self) -> bool:
        """Check if file has been normalized"""
        return self.file_normalizzato_path is not None

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
```

### 2. API Endpoints

#### Upload Multi-File
**File**: `backend/modules/anagrafica_italiana/routes/documenti.py`

```python
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.file_storage import file_storage
from app.core.file_normalization import file_normalization
from app.core.platform_services import DocumentParsingService

from ..models import Documento, DocumentoFile, TipoDocumento
from ..services.document_service import DocumentService

router = APIRouter(prefix="/anagrafica/documenti", tags=["documenti"])
logger = logging.getLogger(__name__)


@router.post("/upload-multi")
async def upload_multi_file_document(
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    tipo_documento_id: int = Form(...),
    descrizione: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    tipo_pagina: Optional[List[str]] = Form(None),  # Optional: specify page type for each file
    db: Session = Depends(get_db),
    tenant_schema: str = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission("documento.create"))
):
    """
    Upload multi-file document (e.g., ID card front + back).

    Args:
        entity_type: Target entity type (SOGGETTO_ANAGRAFICO, IMMOBILE, etc.)
        entity_id: Target entity ID
        tipo_documento_id: Document type ID (reference to TipoDocumento)
        descrizione: Document description
        note: Additional notes
        files: List of files to upload
        tipo_pagina: Optional list of page types (fronte, retro, etc.) matching files order
        db: Database session (injected)
        tenant_schema: Tenant schema (injected)
        current_user: Current user (injected)

    Returns:
        {
            "documento": {...},
            "parsing_jobs": [...]  # If parsing configured
        }

    Raises:
        400: Invalid input
        500: Upload/processing failure
    """
    if not tenant_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant schema mancante"
        )

    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Almeno un file è richiesto"
        )

    logger.info(
        f"[DocumentUploadMulti] User {current_user.id} uploading {len(files)} files "
        f"for {entity_type}:{entity_id}, tipo_documento_id={tipo_documento_id}"
    )

    # Get TipoDocumento
    tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.id == tipo_documento_id).first()
    if not tipo_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TipoDocumento {tipo_documento_id} non trovato"
        )

    # Parse tipo_pagina list
    page_types = tipo_pagina if tipo_pagina else [None] * len(files)
    if len(page_types) != len(files):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tipo_pagina count ({len(page_types)}) must match files count ({len(files)})"
        )

    try:
        # 1. Create Documento parent record
        documento = Documento(
            entity_type=entity_type,
            entity_id=entity_id,
            tipo_documento_id=tipo_documento_id,
            descrizione=descrizione,
            note=note,
            # metadata_parsato will be populated after parsing
        )
        db.add(documento)
        db.flush()  # Get documento.id

        logger.info(f"[DocumentUploadMulti] Created Documento #{documento.id}")

        # 2. Process each file
        documento_files = []
        parsing_jobs = []

        for idx, (file, page_type) in enumerate(zip(files, page_types), start=1):
            # Determine page type
            if page_type is None:
                if len(files) == 1:
                    page_type = "unico"
                elif idx == 1:
                    page_type = "fronte"
                elif idx == 2:
                    page_type = "retro"
                else:
                    page_type = f"pagina_{idx}"

            logger.info(f"[DocumentUploadMulti] Processing file {idx}/{len(files)}: {file.filename} ({page_type})")

            # a. Save original file
            file_content = file.file
            relative_path = file_storage.save_file(
                file=file_content,
                entity_type=entity_type,
                entity_id=entity_id,
                filename=file.filename,
                tenant_schema=tenant_schema
            )

            # b. Normalize file
            normalized_path = None
            normalized_width = None
            normalized_height = None

            try:
                abs_path = file_storage.get_file_path(relative_path, tenant_schema)
                base_name = relative_path.rsplit('.', 1)[0]
                normalized_relative = f"{base_name}_norm.jpg"
                normalized_abs = file_storage.get_file_path(normalized_relative, tenant_schema)

                norm_path, width, height = file_normalization.normalize_file(
                    input_path=abs_path,
                    output_path=normalized_abs
                )
                normalized_path = normalized_relative
                normalized_width = width
                normalized_height = height

                logger.info(f"[DocumentUploadMulti] Normalized to {normalized_path} ({width}x{height})")

            except Exception as e:
                logger.warning(f"[DocumentUploadMulti] Normalization failed: {e}")
                # Continue without normalization

            # c. Create DocumentoFile record
            doc_file = DocumentoFile(
                documento_id=documento.id,
                file_path=relative_path,
                nome_file=file.filename,
                mime_type=file.content_type,
                dimensione=file_storage.get_file_size(relative_path, tenant_schema),
                ordine=idx,
                tipo_pagina=page_type,
                file_normalizzato_path=normalized_path,
                normalizzato_width=normalized_width,
                normalizzato_height=normalized_height
            )
            db.add(doc_file)
            db.flush()  # Get doc_file.id

            documento_files.append(doc_file)

            # d. Check if parsing required for this page type
            if tipo_doc.parsing_multi_file_config:
                page_config = tipo_doc.parsing_multi_file_config.get(page_type, {})
                if page_config.get("parsing_required", False):
                    # Submit to parsing
                    parsing_service = DocumentParsingService(db, tenant_schema)

                    # Use normalized file for parsing if available
                    parsing_file_path = normalized_path if normalized_path else relative_path

                    # Create temporary UploadFile-like object for parsing service
                    from io import BytesIO
                    with open(file_storage.get_file_path(parsing_file_path, tenant_schema), 'rb') as f:
                        file_bytes = f.read()

                    class TempUploadFile:
                        def __init__(self, filename, content, content_type):
                            self.filename = filename
                            self.file = BytesIO(content)
                            self.content_type = content_type

                    temp_file = TempUploadFile(
                        filename=file.filename,
                        content=file_bytes,
                        content_type="image/jpeg" if normalized_path else file.content_type
                    )

                    job = parsing_service.upload_and_parse(
                        file=temp_file,
                        document_type_key=f"anagrafica_italiana.{tipo_doc.codice}",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        user_id=current_user.id,
                        parsing_service_override=page_config.get("service") or tipo_doc.parsing_service,
                        parsing_config_override=page_config.get("config"),
                    )

                    # Link job to DocumentoFile
                    doc_file.parsing_job_id = job.id
                    parsing_jobs.append(job)

                    logger.info(f"[DocumentUploadMulti] Created parsing job {job.job_uuid} for file {doc_file.id}")

        # 3. Commit all changes
        db.commit()
        db.refresh(documento)

        logger.info(
            f"[DocumentUploadMulti] ✓ Completed: documento={documento.id}, "
            f"files={len(documento_files)}, parsing_jobs={len(parsing_jobs)}"
        )

        return {
            "documento": documento.to_dict(),
            "parsing_jobs": [job.to_dict() for job in parsing_jobs]
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"[DocumentUploadMulti] Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'upload: {str(e)}"
        )
```

---

## Frontend Implementation

### 1. DocumentViewer Component

**File**: `frontend/src/components/Platform/Documents/DocumentViewer.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download, RotateCw, Maximize2 } from 'lucide-react';
import './DocumentViewer.css';

const DocumentViewer = ({
  documentoId,
  showMetadata = false,
  onClose = null,
  allowDownload = true
}) => {
  const [documento, setDocumento] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [zoom, setZoom] = useState(1.0);
  const [rotation, setRotation] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    fetchDocumento();
  }, [documentoId]);

  const fetchDocumento = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/anagrafica/documenti/${documentoId}`);
      if (!response.ok) throw new Error('Failed to load document');
      const data = await response.json();
      setDocumento(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadOriginal = async (fileId) => {
    const url = `/api/v1/anagrafica/documenti/file/${fileId}/download-original`;
    window.open(url, '_blank');
  };

  if (loading) return <div className="document-viewer-loading">Caricamento...</div>;
  if (error) return <div className="document-viewer-error">Errore: {error}</div>;
  if (!documento || !documento.files || documento.files.length === 0) {
    return <div className="document-viewer-empty">Nessun file disponibile</div>;
  }

  const currentFile = documento.files[currentPage];
  const imageUrl = currentFile.file_normalizzato_path
    ? `/api/v1/documenti/file/${currentFile.id}/view-normalized`
    : `/api/v1/documenti/file/${currentFile.id}/view-original`;

  return (
    <div className={`document-viewer ${fullscreen ? 'fullscreen' : ''}`}>
      {/* Toolbar */}
      <div className="viewer-toolbar">
        <div className="toolbar-section">
          <button
            onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
            disabled={currentPage === 0}
            title="Pagina precedente"
          >
            <ChevronLeft size={20} />
          </button>
          <span className="page-indicator">
            {currentPage + 1} / {documento.files.length}
            {currentFile.tipo_pagina && ` (${currentFile.tipo_pagina})`}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(documento.files.length - 1, p + 1))}
            disabled={currentPage === documento.files.length - 1}
            title="Pagina successiva"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        <div className="toolbar-section">
          <button onClick={() => setZoom(z => Math.min(3.0, z + 0.25))} title="Zoom in">
            <ZoomIn size={20} />
          </button>
          <span className="zoom-indicator">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom(z => Math.max(0.5, z - 0.25))} title="Zoom out">
            <ZoomOut size={20} />
          </button>
        </div>

        <div className="toolbar-section">
          <button onClick={() => setRotation(r => (r + 90) % 360)} title="Ruota">
            <RotateCw size={20} />
          </button>
          <button onClick={() => setFullscreen(!fullscreen)} title="Schermo intero">
            <Maximize2 size={20} />
          </button>
          {allowDownload && (
            <button onClick={() => downloadOriginal(currentFile.id)} title="Scarica originale">
              <Download size={20} /> Originale
            </button>
          )}
        </div>

        {onClose && (
          <button onClick={onClose} className="close-button">
            ✕
          </button>
        )}
      </div>

      {/* Main viewer */}
      <div className="viewer-content">
        <div className="image-container">
          <img
            src={imageUrl}
            alt={currentFile.nome_file}
            className="document-image"
            style={{
              transform: `scale(${zoom}) rotate(${rotation}deg)`,
              transition: 'transform 0.2s ease'
            }}
          />
        </div>

        {/* Metadata overlay */}
        {showMetadata && documento.metadata_parsato && (
          <div className="metadata-overlay">
            <h4>Dati Estratti</h4>
            {documento.confidence_score !== null && (
              <div className="confidence-badge">
                Affidabilità: {documento.confidence_score}%
              </div>
            )}
            <dl className="metadata-list">
              {Object.entries(documento.metadata_parsato).map(([key, value]) => {
                if (key === 'confidence_scores') return null; // Skip internal field
                return (
                  <div key={key} className="metadata-item">
                    <dt>{formatFieldName(key)}</dt>
                    <dd>{formatFieldValue(value)}</dd>
                  </div>
                );
              })}
            </dl>
          </div>
        )}
      </div>

      {/* Thumbnails */}
      {documento.files.length > 1 && (
        <div className="viewer-thumbnails">
          {documento.files.map((file, idx) => {
            const thumbUrl = file.file_normalizzato_path
              ? `/api/v1/documenti/file/${file.id}/thumbnail`
              : `/api/v1/documenti/file/${file.id}/view-original`;

            return (
              <div
                key={file.id}
                className={`thumbnail ${idx === currentPage ? 'active' : ''}`}
                onClick={() => setCurrentPage(idx)}
              >
                <img src={thumbUrl} alt={file.tipo_pagina} />
                <span className="thumbnail-label">{file.tipo_pagina || `#${idx + 1}`}</span>
                {file.is_parsed && (
                  <span className="parsed-badge" title="Dati estratti">📄</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const formatFieldName = (key) => {
  const labels = {
    codice_fiscale: 'Codice Fiscale',
    nome: 'Nome',
    cognome: 'Cognome',
    data_nascita: 'Data di Nascita',
    luogo_nascita: 'Luogo di Nascita',
    data_emissione: 'Data Emissione',
    data_scadenza: 'Data Scadenza',
    numero_documento: 'Numero Documento',
    autorita_emissione: 'Autorità di Emissione'
  };
  return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const formatFieldValue = (value) => {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

export default DocumentViewer;
```

---

## File Normalization Service

**File**: `backend/app/core/file_normalization.py`

```python
"""
File Normalization Service

Converts various file formats (PDF, PNG, HEIC, etc.) to standardized JPEG
for consistent viewing and parsing.
"""
from PIL import Image
import pdf2image
from pathlib import Path
from typing import List, Tuple, Optional
import logging
import mimetypes

logger = logging.getLogger(__name__)


class FileNormalizationService:
    """
    Service for normalizing document files to JPEG format.

    Features:
        - Convert PDF pages to JPEG
        - Convert images (PNG, HEIC, TIFF, etc.) to JPEG
        - Resize to max dimension while preserving aspect ratio
        - Optimize for web viewing and parsing services
    """

    TARGET_FORMAT = "JPEG"
    MAX_DIMENSION = 2048  # Max width or height in pixels
    JPEG_QUALITY = 85     # Quality 0-100
    DPI = 200             # DPI for PDF conversion

    def __init__(self):
        pass

    def normalize_file(
        self,
        input_path: str,
        output_path: str,
        page_number: int = 1
    ) -> Tuple[str, int, int]:
        """
        Convert file to normalized JPEG.

        Args:
            input_path: Absolute path to original file
            output_path: Absolute path to save normalized file
            page_number: For multi-page PDFs (1-indexed)

        Returns:
            (normalized_path, width, height)

        Raises:
            ValueError: If file type unsupported
            IOError: If file cannot be read/written
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Detect file type
        mime_type = self._detect_mime_type(input_path)
        logger.debug(f"Normalizing {input_path.name} (MIME: {mime_type})")

        # Convert to PIL Image
        if mime_type == "application/pdf":
            image = self._pdf_to_image(input_path, page_number)
        elif mime_type.startswith("image/"):
            image = self._load_image(input_path)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Convert to RGB (JPEG doesn't support transparency)
        image = self._convert_to_rgb(image)

        # Resize if needed
        image = self._resize_if_needed(image)

        # Save as JPEG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(
            output_path,
            "JPEG",
            quality=self.JPEG_QUALITY,
            optimize=True,
            progressive=True  # Progressive loading for web
        )

        logger.info(
            f"Normalized {input_path.name} → {output_path.name} "
            f"({image.width}x{image.height}, {mime_type})"
        )

        return str(output_path), image.width, image.height

    def normalize_pdf_multi_page(
        self,
        input_path: str,
        output_dir: str,
        base_filename: str
    ) -> List[Tuple[str, int, int]]:
        """
        Convert multi-page PDF to multiple JPEGs.

        Args:
            input_path: Absolute path to PDF
            output_dir: Directory to save JPEGs
            base_filename: Base name (will add _p1, _p2, etc.)

        Returns:
            List of (normalized_path, width, height) for each page

        Raises:
            ValueError: If not a PDF
            IOError: If PDF cannot be read
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"PDF not found: {input_path}")

        mime_type = self._detect_mime_type(input_path)
        if mime_type != "application/pdf":
            raise ValueError(f"Not a PDF file: {input_path} (MIME: {mime_type})")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Convert all PDF pages to images
        logger.info(f"Converting PDF {input_path.name} to images...")
        images = pdf2image.convert_from_path(
            input_path,
            dpi=self.DPI,
            fmt='ppm'  # Fast intermediate format
        )

        results = []
        for idx, image in enumerate(images, start=1):
            output_path = output_dir / f"{base_filename}_p{idx}.jpg"

            # Process image
            image = self._convert_to_rgb(image)
            image = self._resize_if_needed(image)

            # Save
            image.save(
                output_path,
                "JPEG",
                quality=self.JPEG_QUALITY,
                optimize=True
            )

            results.append((str(output_path), image.width, image.height))
            logger.info(f"  Page {idx}/{len(images)} → {output_path.name}")

        logger.info(f"PDF conversion complete: {len(images)} pages")
        return results

    def _detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type from file extension"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    def _load_image(self, file_path: Path) -> Image:
        """Load image file using PIL"""
        try:
            return Image.open(file_path)
        except Exception as e:
            raise IOError(f"Failed to load image {file_path.name}: {e}")

    def _pdf_to_image(self, pdf_path: Path, page_number: int) -> Image:
        """Convert single PDF page to PIL Image"""
        try:
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=self.DPI,
                first_page=page_number,
                last_page=page_number
            )
            if not images:
                raise ValueError(f"PDF page {page_number} not found")
            return images[0]
        except Exception as e:
            raise IOError(f"Failed to convert PDF page {page_number}: {e}")

    def _convert_to_rgb(self, image: Image) -> Image:
        """Convert image to RGB color space (required for JPEG)"""
        if image.mode == "RGB":
            return image

        if image.mode in ("RGBA", "LA"):
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            # Paste image using alpha channel as mask
            background.paste(image, mask=image.split()[-1])
            return background

        elif image.mode == "P":
            # Palette mode - convert to RGBA first then to RGB
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background

        else:
            # Other modes (L, CMYK, etc.) - direct conversion
            return image.convert("RGB")

    def _resize_if_needed(self, image: Image) -> Image:
        """Resize image if larger than MAX_DIMENSION"""
        width, height = image.size

        if width <= self.MAX_DIMENSION and height <= self.MAX_DIMENSION:
            return image

        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = self.MAX_DIMENSION
            new_height = int(height * (self.MAX_DIMENSION / width))
        else:
            new_height = self.MAX_DIMENSION
            new_width = int(width * (self.MAX_DIMENSION / height))

        logger.debug(f"Resizing {width}x{height} → {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


# Global instance
file_normalization = FileNormalizationService()
```

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_file_normalization.py

import pytest
from pathlib import Path
from app.core.file_normalization import file_normalization

def test_normalize_jpeg():
    """Test normalizing JPEG image"""
    input_path = "tests/fixtures/sample.jpg"
    output_path = "/tmp/test_normalized.jpg"

    path, width, height = file_normalization.normalize_file(input_path, output_path)

    assert Path(path).exists()
    assert width <= 2048
    assert height <= 2048

def test_normalize_pdf_single_page():
    """Test normalizing single PDF page"""
    input_path = "tests/fixtures/sample.pdf"
    output_path = "/tmp/test_pdf_normalized.jpg"

    path, width, height = file_normalization.normalize_file(input_path, output_path, page_number=1)

    assert Path(path).exists()
    assert Path(path).suffix == ".jpg"

def test_normalize_pdf_multi_page():
    """Test normalizing multi-page PDF"""
    input_path = "tests/fixtures/multi_page.pdf"
    output_dir = "/tmp/test_pdf_multi"
    base_name = "document"

    results = file_normalization.normalize_pdf_multi_page(input_path, output_dir, base_name)

    assert len(results) > 0
    for path, width, height in results:
        assert Path(path).exists()
        assert "_p" in path  # Contains page number
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-31
