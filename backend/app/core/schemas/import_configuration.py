"""
Import Configuration Schemas
Pydantic models for validation
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class ImportConfigurationBase(BaseModel):
    """Base schema for import configuration"""
    name: str = Field(..., min_length=1, max_length=200, description="Configuration name")
    module_name: str = Field(..., description="Module name (e.g., 'affitti_lungo')")
    entity_name: str = Field(..., description="Entity name (e.g., 'UnitaImmobiliare')")
    field_mapping: Dict[str, str] = Field(..., description="CSV column to model field mapping")


class ImportConfigurationCreate(ImportConfigurationBase):
    """Schema for creating import configuration"""
    created_by: Optional[str] = None


class ImportConfigurationUpdate(BaseModel):
    """Schema for updating import configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    field_mapping: Optional[Dict[str, str]] = None


class ImportConfigurationResponse(ImportConfigurationBase):
    """Schema for import configuration response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
