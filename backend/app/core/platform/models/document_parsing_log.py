"""
DocumentParsingLog Model - Debug logs for external parsing calls.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class DocumentParsingLog(Base):
    """
    Stores request/response/callback logs for document parsing services.
    """
    __tablename__ = "core_document_parsing_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    job_uuid = Column(String(36), nullable=True, index=True)
    tenant_schema = Column(String(100), nullable=True, index=True)
    parsing_service = Column(String(50), nullable=True, index=True)
    direction = Column(String(20), nullable=False)  # REQUEST | RESPONSE | CALLBACK | ERROR
    url = Column(String(500), nullable=True)
    status_code = Column(Integer, nullable=True)
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    error_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "job_uuid": self.job_uuid,
            "tenant_schema": self.tenant_schema,
            "parsing_service": self.parsing_service,
            "direction": self.direction,
            "url": self.url,
            "status_code": self.status_code,
            "request_payload": self.request_payload,
            "response_payload": self.response_payload,
            "error_text": self.error_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
