"""
Document Service - Business service for file and document management.

Wraps the existing FileStorage class and provides:
- Database integration with Documento model
- File validation (type, size limits)
- Metadata management
- Secure file access control
- Batch operations

Note: This was moved from platform_services to affitti_lungo module
as it is business-specific (uses Documento model from affitti_lungo).

Usage:
    from affitti_lungo.services.document_service import DocumentService

    doc_service = DocumentService(db)

    # Upload document
    documento = doc_service.upload(
        file=uploaded_file,
        entity_type="IMMOBILE",
        entity_id=123,
        filename="planimetria.pdf",
        tipo="PLANIMETRIA",
        descrizione="Planimetria appartamento"
    )

    # Get document metadata
    documento = doc_service.get(documento_id)

    # Download file
    file_path = doc_service.get_file_path(documento_id)

    # Delete document (file + metadata)
    doc_service.delete(documento_id)
"""
from typing import BinaryIO, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi import HTTPException, status, UploadFile
import mimetypes

from app.core.file_storage import file_storage
from ..models.documenti import Documento


class DocumentService:
    """
    Platform service for document management.

    Provides abstraction over file storage with database integration.
    Modules should use this service instead of accessing FileStorage directly.
    """

    # Allowed file types and their MIME types
    ALLOWED_EXTENSIONS = {
        # Documents
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.txt': 'text/plain',
        '.odt': 'application/vnd.oasis.opendocument.text',
        '.ods': 'application/vnd.oasis.opendocument.spreadsheet',

        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',

        # Archives
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
    }

    # Max file size: 50MB default
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self, db: Session):
        """
        Initialize document service.

        Args:
            db: Database session
        """
        self.db = db
        self.storage = file_storage

    def validate_file(
        self,
        filename: str,
        file_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> None:
        """
        Validate file before upload.

        Args:
            filename: Original filename
            file_size: File size in bytes
            max_size: Maximum allowed size (overrides default)

        Raises:
            HTTPException: If validation fails
        """
        # Check extension
        file_extension = Path(filename).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS.keys())}"
            )

        # Check file size
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
        """
        Upload a file and create documento record.

        Args:
            file: File object (BinaryIO or FastAPI UploadFile)
            entity_type: Entity type (e.g., "IMMOBILE", "CONTRATTO")
            entity_id: Entity ID
            filename: Original filename
            tipo: Document type (e.g., "PLANIMETRIA", "CONTRATTO")
            descrizione: Optional description
            validate: Whether to validate file before upload

        Returns:
            Dict with documento metadata and file info

        Raises:
            HTTPException: If validation fails or upload error
        """
        # Handle UploadFile
        if hasattr(file, 'file'):
            actual_file = file.file
            if not filename and hasattr(file, 'filename'):
                filename = file.filename
            file_size = getattr(file, 'size', None)
        else:
            actual_file = file
            file_size = None

        # Validate if requested
        if validate:
            self.validate_file(filename, file_size)

        try:
            # Save file to storage
            relative_path = self.storage.save_file(
                file=actual_file,
                entity_type=entity_type,
                entity_id=entity_id,
                filename=filename
            )

            # Get actual file size
            if not file_size:
                file_size = self.storage.get_file_size(relative_path)

            # Create documento record
            documento = Documento(
                entity_type=entity_type,
                entity_id=entity_id,
                tipo=tipo,
                nome_file=filename,
                file_path=relative_path,
                file_size=file_size,
                descrizione=descrizione
            )

            self.db.add(documento)
            self.db.commit()
            self.db.refresh(documento)

            return {
                "id": documento.id,
                "nome_file": documento.nome_file,
                "tipo": documento.tipo,
                "file_size": documento.file_size,
                "file_path": documento.file_path,
                "entity_type": documento.entity_type,
                "entity_id": documento.entity_id,
                "descrizione": documento.descrizione,
                "data_caricamento": documento.data_caricamento
            }

        except Exception as e:
            self.db.rollback()
            # Try to cleanup file if database insert failed
            try:
                self.storage.delete_file(relative_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}"
            )

    def get(self, documento_id: int) -> Optional[Any]:
        """
        Get documento record by ID.

        Args:
            documento_id: Documento ID

        Returns:
            Documento instance or None
        """
        return self.db.query(Documento).filter(Documento.id == documento_id).first()

    def get_or_404(self, documento_id: int) -> Any:
        """
        Get documento or raise 404.

        Args:
            documento_id: Documento ID

        Returns:
            Documento instance

        Raises:
            HTTPException: 404 if not found
        """
        documento = self.get(documento_id)
        if not documento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento with id {documento_id} not found"
            )
        return documento

    def get_file_path(self, documento_id: int) -> Path:
        """
        Get absolute file path for download.

        Args:
            documento_id: Documento ID

        Returns:
            Absolute Path to file

        Raises:
            HTTPException: If documento not found or file doesn't exist
        """
        documento = self.get_or_404(documento_id)
        file_path = self.storage.get_file_path(documento.file_path)

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )

        return file_path

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        tipo: Optional[str] = None
    ) -> List[Any]:
        """
        Get all documents for an entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID
            tipo: Optional document type filter

        Returns:
            List of Documento instances
        """
        query = self.db.query(Documento).filter(
            Documento.entity_type == entity_type,
            Documento.entity_id == entity_id
        )

        if tipo:
            query = query.filter(Documento.tipo == tipo)

        return query.all()

    def delete(self, documento_id: int) -> bool:
        """
        Delete document (file + database record).

        Args:
            documento_id: Documento ID

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If documento not found
        """
        documento = self.get_or_404(documento_id)

        try:
            # Delete file from storage
            self.storage.delete_file(documento.file_path)

            # Delete database record
            self.db.delete(documento)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}"
            )

    def delete_by_entity(self, entity_type: str, entity_id: int) -> int:
        """
        Delete all documents for an entity.

        Useful when deleting parent entity (cascade delete).

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            Number of documents deleted
        """
        documenti = self.get_by_entity(entity_type, entity_id)
        count = 0

        for documento in documenti:
            try:
                self.delete(documento.id)
                count += 1
            except:
                pass  # Continue deleting others

        return count

    def update_metadata(
        self,
        documento_id: int,
        tipo: Optional[str] = None,
        descrizione: Optional[str] = None
    ) -> Any:
        """
        Update document metadata (not the file itself).

        Args:
            documento_id: Documento ID
            tipo: New document type
            descrizione: New description

        Returns:
            Updated Documento instance

        Raises:
            HTTPException: If documento not found
        """
        documento = self.get_or_404(documento_id)

        if tipo is not None:
            documento.tipo = tipo
        if descrizione is not None:
            documento.descrizione = descrizione

        self.db.commit()
        self.db.refresh(documento)

        return documento

    def get_storage_stats(self, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get storage statistics.

        Args:
            entity_type: Optional filter by entity type

        Returns:
            Dict with total_files, total_size, size_by_type
        """
        from sqlalchemy import func

        query = self.db.query(
            func.count(Documento.id).label('total_files'),
            func.sum(Documento.file_size).label('total_size')
        )

        if entity_type:
            query = query.filter(Documento.entity_type == entity_type)

        result = query.first()

        # Get breakdown by type
        type_query = self.db.query(
            Documento.tipo,
            func.count(Documento.id).label('count'),
            func.sum(Documento.file_size).label('size')
        )

        if entity_type:
            type_query = type_query.filter(Documento.entity_type == entity_type)

        type_stats = type_query.group_by(Documento.tipo).all()

        return {
            'total_files': result.total_files or 0,
            'total_size': result.total_size or 0,
            'size_by_type': [
                {
                    'tipo': stat.tipo,
                    'count': stat.count,
                    'size': stat.size
                }
                for stat in type_stats
            ]
        }
