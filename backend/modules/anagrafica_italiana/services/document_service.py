"""
Document Service - Business service for file and document management.

Owned by anagrafica_italiana to avoid cyclic dependencies.
"""
from typing import BinaryIO, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
from fastapi import HTTPException, status, UploadFile
import mimetypes

from app.core.file_storage import file_storage
from ..models.documento import Documento


class DocumentService:
    """
    Service for document management.
    """

    ALLOWED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.txt': 'text/plain',
        '.odt': 'application/vnd.oasis.opendocument.text',
        '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self, db: Session, tenant_schema: Optional[str] = None):
        self.db = db
        self.storage = file_storage
        self.tenant_schema = tenant_schema

    def _ensure_tenant_context(self) -> None:
        if self.tenant_schema:
            if self.tenant_schema.replace('_', '').replace('-', '').isalnum():
                self.db.execute(text(f"SET search_path TO {self.tenant_schema}, public"))

    def validate_file(
        self,
        filename: str,
        file_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> None:
        file_extension = Path(filename).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS.keys())}"
            )

        if file_size:
            max_allowed = max_size or self.MAX_FILE_SIZE
            if file_size > max_allowed:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max size: {max_allowed / (1024 * 1024):.1f}MB"
                )

    def upload(
        self,
        file: BinaryIO | UploadFile,
        entity_type: str,
        entity_id: int,
        filename: str,
        tipo: str,
        descrizione: Optional[str] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        self._ensure_tenant_context()
        if hasattr(file, 'file'):
            actual_file = file.file
            if not filename and hasattr(file, 'filename'):
                filename = file.filename
            file_size = getattr(file, 'size', None)
        else:
            actual_file = file
            file_size = None

        if validate:
            self.validate_file(filename, file_size)

        try:
            relative_path = self.storage.save_file(
                file=actual_file,
                entity_type=entity_type,
                entity_id=entity_id,
                filename=filename
            )

            if not file_size:
                file_size = self.storage.get_file_size(relative_path)

            mime_type, _ = mimetypes.guess_type(filename)
            documento = Documento(
                entity_type=entity_type,
                entity_id=entity_id,
                tipo_documento=tipo,
                nome_file=filename,
                file_path=relative_path,
                mime_type=mime_type,
                dimensione=file_size,
                descrizione=descrizione
            )

            self.db.add(documento)
            self.db.commit()
            # Ensure tenant search_path before ORM refresh (refresh issues a SELECT).
            self._ensure_tenant_context()
            self.db.refresh(documento)

            return {
                "id": documento.id,
                "nome_file": documento.nome_file,
                "tipo_documento": documento.tipo_documento,
                "dimensione": documento.dimensione,
                "file_path": documento.file_path,
                "entity_type": documento.entity_type,
                "entity_id": documento.entity_id,
                "descrizione": documento.descrizione,
                "created_at": documento.created_at
            }

        except Exception as e:
            self.db.rollback()
            try:
                self.storage.delete_file(relative_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}"
            )

    def get(self, documento_id: int) -> Optional[Any]:
        self._ensure_tenant_context()
        return self.db.query(Documento).filter(Documento.id == documento_id).first()

    def get_or_404(self, documento_id: int) -> Any:
        self._ensure_tenant_context()
        documento = self.get(documento_id)
        if not documento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento non trovato")
        return documento

    def get_file_path(self, documento_id: int) -> str:
        self._ensure_tenant_context()
        documento = self.get_or_404(documento_id)
        return self.storage.get_file_path(documento.file_path)

    def delete(self, documento_id: int) -> bool:
        self._ensure_tenant_context()
        documento = self.get_or_404(documento_id)
        try:
            self.storage.delete_file(documento.file_path)
        except Exception:
            pass
        self.db.delete(documento)
        self.db.commit()
        return True

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        tipo_documento: Optional[str] = None
    ) -> List[Any]:
        self._ensure_tenant_context()
        query = self.db.query(Documento).filter(
            Documento.entity_type == entity_type,
            Documento.entity_id == entity_id
        )
        if tipo_documento:
            query = query.filter(Documento.tipo_documento == tipo_documento)
        return query.all()
