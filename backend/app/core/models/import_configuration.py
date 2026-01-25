"""
Import Configuration Model
Stores saved field mappings for CSV imports
"""
from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class ImportConfiguration(Base):
    """
    Model for storing import configurations.
    Allows users to save field mappings for reuse.
    """
    __tablename__ = "core_import_configurations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    module_name = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(100), nullable=False, index=True)
    field_mapping = Column(JSON, nullable=False)  # {"CSV_Column": "model_field"}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))  # For future user management

    def __repr__(self):
        return f"<ImportConfiguration(id={self.id}, name='{self.name}', entity='{self.entity_name}')>"
