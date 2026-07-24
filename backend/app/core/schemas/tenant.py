"""
Pydantic schemas for Tenant operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""
    schema_name: str = Field(..., min_length=3, max_length=63, description="PostgreSQL schema name")
    nome_display: str = Field(..., min_length=1, max_length=100, description="Display name")
    descrizione: Optional[str] = Field(None, max_length=255, description="Description")

    @validator('schema_name')
    def validate_schema_name(cls, v):
        """Validate schema name follows PostgreSQL naming rules."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Schema name must be alphanumeric with underscores/hyphens")
        if v.lower() in ['public', 'pg_catalog', 'information_schema']:
            raise ValueError(f"Cannot use system schema name: {v}")
        return v.lower()  # Normalize to lowercase


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    nome_display: Optional[str] = Field(None, min_length=1, max_length=100)
    descrizione: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    id: int
    schema_name: str
    nome_display: str
    descrizione: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserTenantResponse(BaseModel):
    """Schema for user-tenant relationship response."""
    id: int
    user_id: int
    tenant_id: int
    is_default: bool
    access_granted_at: datetime
    access_revoked_at: Optional[datetime]

    class Config:
        orm_mode = True


class TenantWithAccessResponse(BaseModel):
    """Schema for tenant with user access info."""
    id: int
    schema_name: str
    nome_display: str
    descrizione: Optional[str]
    active: bool
    is_default: bool
    access_granted_at: Optional[str]  # ISO format string


class GrantTenantAccessRequest(BaseModel):
    """Schema for granting user access to tenant."""
    user_id: int = Field(..., gt=0)
    is_default: bool = Field(default=False)


class SwitchTenantRequest(BaseModel):
    """Schema for switching to a different tenant."""
    tenant_id: int = Field(..., gt=0)


class TenantModuleResponse(BaseModel):
    """Schema for tenant module status."""
    module_id: str
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    enabled: bool
    needs_install: bool = False
    installed_at: Optional[str]  # ISO format string
    tenant_tables: List[str] = Field(default_factory=list)
    table_count: int
    config: Optional[Dict[str, Any]] = None


class InstallModuleRequest(BaseModel):
    """Schema for installing a module."""
    module_id: str = Field(..., min_length=1)
    seed_test_data: bool = Field(default=False)


class UninstallModuleRequest(BaseModel):
    """Schema for uninstalling a module."""
    module_id: str = Field(..., min_length=1)
    drop_tables: bool = Field(default=False, description="Whether to drop tables (irreversible)")


class TenantModuleConfigUpdate(BaseModel):
    """Schema for updating tenant module configuration."""
    config: Dict[str, Any] = Field(default_factory=dict)
