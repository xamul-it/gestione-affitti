"""
ParsingServiceConfig Model - Endpoint/config for external parsing services.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class ParsingServiceConfig(Base):
    __tablename__ = "core_parsing_services"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    service_key = Column(String(50), nullable=False, unique=True, index=True)
    transport_type = Column(String(20), nullable=False, default="HTTP")  # HTTP | REDIS | WS
    endpoint_url = Column(String(500), nullable=True)
    redis_queue = Column(String(200), nullable=True)
    timeout_seconds = Column(Integer, nullable=True, default=300)
    enabled = Column(String(5), nullable=False, default="true")  # store as string for simplicity
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "service_key": self.service_key,
            "transport_type": self.transport_type,
            "endpoint_url": self.endpoint_url,
            "redis_queue": self.redis_queue,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled == "true",
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
