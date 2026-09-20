"""
DocumentJob Model - Async Document Parsing Job Tracker

Platform-level model for tracking asynchronous document parsing jobs.
Supports integration with external parsing services (MRZ, OCR, etc.).
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean,
    Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid
from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Document parsing job status"""
    PENDING = "PENDING"          # Created, waiting to be sent to service
    QUEUED = "QUEUED"            # Sent to parsing service, waiting for processing
    PROCESSING = "PROCESSING"    # Service is currently processing
    COMPLETED = "COMPLETED"      # Parsing completed successfully
    FAILED = "FAILED"            # Parsing failed
    TIMEOUT = "TIMEOUT"          # Service timeout
    CANCELLED = "CANCELLED"      # Cancelled by user


class DocumentJob(Base):
    """
    Tracks asynchronous document parsing jobs.

    Workflow:
        1. Upload document → save to temp storage
        2. Create DocumentJob (status=PENDING)
        3. Submit to parsing service (status=QUEUED)
        4. Service processes and calls callback
        5. Update status=COMPLETED/FAILED, save result
        6. Create Scadenza notification for user action

    Multi-tenancy:
        - tenant_schema ensures data isolation
        - file_path is relative and includes tenant prefix

    Entity Attachment (optional):
        - entity_type/entity_id: Link to target entity (e.g., "soggetto_anagrafico", 123)
        - NULL for "create from document" workflow

    Parsing Service Integration:
        - parsing_service: Service identifier (e.g., "mrz", "contract_parser")
        - parsing_config: JSON config passed to service
        - parsing_result: JSON result from service
        - confidence_score: 0-100 quality score
        - needs_review: Flag for manual review
    """
    __tablename__ = "core_document_jobs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Unique job identifier (used in callbacks)
    job_uuid = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        comment="Unique job identifier for callbacks"
    )

    # Multi-tenancy
    tenant_schema = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Tenant schema for data isolation"
    )

    # File information
    file_path = Column(
        String(500),
        nullable=False,
        comment="Relative file path with tenant prefix"
    )
    original_filename = Column(
        String(255),
        nullable=False,
        comment="Original uploaded filename"
    )
    mime_type = Column(
        String(100),
        nullable=True,
        comment="MIME type (image/jpeg, application/pdf, etc.)"
    )

    # Document type and parsing config
    document_type_key = Column(
        String(100),
        nullable=False,
        comment="Full document type key (module.CODE)"
    )
    parsing_service = Column(
        String(50),
        nullable=False,
        comment="Parsing service identifier (mrz, contract_parser, etc.)"
    )
    parsing_config = Column(
        JSON,
        nullable=True,
        comment="Service-specific configuration"
    )

    # Entity target (optional for 'create from document' workflow)
    entity_type = Column(
        String(100),
        nullable=True,
        comment="Target entity type (null for create workflow)"
    )
    entity_id = Column(
        Integer,
        nullable=True,
        comment="Target entity ID (null for create workflow)"
    )

    # Job status and result
    status = Column(
        SQLEnum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING,
        index=True,
        comment="Current job status"
    )
    parsing_result = Column(
        JSON,
        nullable=True,
        comment="Parsed data from service"
    )
    parsing_error = Column(
        Text,
        nullable=True,
        comment="Error message if failed"
    )
    confidence_score = Column(
        Integer,
        nullable=True,
        comment="Parsing confidence 0-100"
    )
    needs_review = Column(
        Boolean,
        default=False,
        comment="Flag for manual review requirement"
    )

    # Timing
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Job creation timestamp"
    )
    queued_at = Column(
        DateTime,
        nullable=True,
        comment="When sent to parsing service"
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="When processing completed/failed"
    )

    # Retry logic
    retry_count = Column(
        Integer,
        default=0,
        comment="Number of retry attempts"
    )
    max_retries = Column(
        Integer,
        default=3,
        comment="Maximum retry attempts"
    )

    # User tracking
    created_by = Column(
        Integer,
        ForeignKey('core_users.id', ondelete='CASCADE'),
        nullable=False,
        comment="User who created this job"
    )

    # Notification integration
    scadenza_id = Column(
        Integer,
        nullable=True,
        comment="Linked notification/reminder. No FK constraint: Scadenza is "
                "tenant-scoped (see 2026091801/2026092001 migrations), a "
                "cross-schema FK from public.core_document_jobs isn't "
                "possible in Postgres, and the one code path that joins "
                "them (document_parsing_service.py) already filters by "
                "tenant_schema explicitly.",
    )

    # Relationships
    creator = relationship(
        "User",
        back_populates="document_jobs"
    )
    # No `notification` relationship to Scadenza: it was only ever backed
    # by the now-removed cross-schema FK (see scadenza_id above), had no
    # real join condition SQLAlchemy could infer without one, and had no
    # callers — document_parsing_service.py only ever does a plain
    # `job.scadenza_id = scadenza.id` assignment, never an ORM traversal.

    # Indexes for performance
    __table_args__ = (
        Index('idx_document_jobs_tenant', 'tenant_schema'),
        Index('idx_document_jobs_status', 'status'),
        Index('idx_document_jobs_entity', 'entity_type', 'entity_id'),
        Index('idx_document_jobs_created', 'created_at'),
        Index('idx_document_jobs_creator', 'created_by'),
        {"extend_existing": True}
    )

    def __repr__(self):
        return (
            f"<DocumentJob(id={self.id}, uuid={self.job_uuid}, "
            f"status={self.status}, service={self.parsing_service})>"
        )

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return (
            self.status in (JobStatus.FAILED, JobStatus.TIMEOUT) and
            self.retry_count < self.max_retries
        )

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (no more processing)"""
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.TIMEOUT,
            JobStatus.CANCELLED
        )

    @property
    def is_pending_action(self) -> bool:
        """Check if job needs user action (completed and not linked to entity)"""
        return (
            self.status == JobStatus.COMPLETED and
            self.entity_id is None
        )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "job_uuid": self.job_uuid,
            "tenant_schema": self.tenant_schema,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "document_type_key": self.document_type_key,
            "parsing_service": self.parsing_service,
            "parsing_config": self.parsing_config,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status.value if self.status else None,
            "parsing_result": self.parsing_result,
            "parsing_error": self.parsing_error,
            "confidence_score": self.confidence_score,
            "needs_review": self.needs_review,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_by": self.created_by,
            "scadenza_id": self.scadenza_id,
            "can_retry": self.can_retry,
            "is_terminal": self.is_terminal,
            "is_pending_action": self.is_pending_action,
        }
