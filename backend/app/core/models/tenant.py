"""
Tenant models for multi-tenant architecture
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import deferred
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Tenant(Base):
    """
    Tenant (logical database) in the platform.
    Each tenant has its own PostgreSQL schema for data isolation.
    """
    __tablename__ = "core_tenants"
    __table_args__ = {'schema': 'public', 'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    schema_name = Column(String(63), unique=True, nullable=False, index=True)
    nome_display = Column(String(100), nullable=False)
    descrizione = Column(String(255))
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user_tenants = relationship("UserTenant", back_populates="tenant", cascade="all, delete-orphan")
    tenant_modules = relationship("TenantModule", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, schema_name='{self.schema_name}', nome_display='{self.nome_display}')>"


class UserTenant(Base):
    """
    Association User ↔ Tenant (many-to-many with metadata).
    Tracks which users have access to which tenants and their default tenant.
    """
    __tablename__ = "core_user_tenants"
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),
        {'schema': 'public', 'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core_users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("public.core_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    access_granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_tenants")
    tenant = relationship("Tenant", back_populates="user_tenants")

    def __repr__(self):
        return f"<UserTenant(user_id={self.user_id}, tenant_id={self.tenant_id}, is_default={self.is_default})>"


class TenantModule(Base):
    """
    Association Tenant ↔ Module.
    Tracks which modules are enabled for each tenant.
    """
    __tablename__ = "core_tenant_modules"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'module_id', name='uq_tenant_module'),
        {'schema': 'public', 'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("public.core_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(50), nullable=False, index=True)  # e.g., "immobili", "affitti_lungo"
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disabled_at = Column(DateTime, nullable=True)
    installed_version = Column(String(20), nullable=True)
    config = deferred(Column(JSONB, nullable=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="tenant_modules")

    def __repr__(self):
        return f"<TenantModule(tenant_id={self.tenant_id}, module_id='{self.module_id}', enabled={self.enabled})>"
