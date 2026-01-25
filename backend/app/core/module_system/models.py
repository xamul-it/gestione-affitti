"""
SQLAlchemy models for the module system.

These models track installed modules, their dependencies, permissions,
hooks, and extension points.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Module(Base):
    """
    Main registry of installed modules.
    Tracks module metadata, installation status, and configuration.
    """
    __tablename__ = "core_modules"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # Identification
    technical_name = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False)

    # Author and category
    author = Column(String(200))
    category = Column(String(50))

    # State management
    state = Column(String(20), default='installed')  # installed, enabled, disabled, broken
    enabled = Column(Boolean, default=False)
    registered = Column(Boolean, default=False)
    registered_at = Column(DateTime(timezone=True), nullable=True)

    # Licensing
    license = Column(String(50))
    price = Column(DECIMAL(10, 2), default=0)

    # Installation
    install_path = Column(String(500), nullable=False)
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    installed_by = Column(Integer, nullable=True)  # Future: FK to users table

    # Compatibility
    core_version_min = Column(String(20))
    core_version_max = Column(String(20))

    # License validation (for commercial modules)
    license_key = Column(String(200))
    license_valid_until = Column(DateTime(timezone=True))

    # Metadata and configuration
    manifest = Column(JSON, nullable=False)  # Full manifest as JSON
    config = Column(JSON)  # Module-specific runtime configuration

    # Additional info
    summary = Column(Text)
    description = Column(Text)
    website = Column(String(500))
    icon = Column(String(500))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    dependencies = relationship("ModuleDependency", back_populates="module", cascade="all, delete-orphan")
    permissions = relationship("ModulePermission", back_populates="module", cascade="all, delete-orphan")
    hooks = relationship("ModuleHook", back_populates="module", cascade="all, delete-orphan")
    extensions = relationship("ModuleExtension", back_populates="module", cascade="all, delete-orphan")
    endpoints = relationship("ModuleEndpoint", back_populates="module", cascade="all, delete-orphan")


class ModuleDependency(Base):
    """
    Tracks dependencies between modules.
    A module can depend on other modules with version constraints.
    """
    __tablename__ = "core_module_dependencies"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("core_modules.id", ondelete="CASCADE"), nullable=False)

    # Dependency info
    depends_on = Column(String(100), nullable=False)  # technical_name of dependency
    version_constraint = Column(String(50))  # e.g., ">=1.0.0,<2.0.0"
    optional = Column(Boolean, default=False)

    # Relationship
    module = relationship("Module", back_populates="dependencies")


class ModulePermission(Base):
    """
    Tracks permissions declared by modules and their grant status.
    Admin can grant or revoke permissions without uninstalling the module.
    """
    __tablename__ = "core_module_permissions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("core_modules.id", ondelete="CASCADE"), nullable=False)

    # Permission details
    permission = Column(String(100), nullable=False)  # e.g., "database.read", "api.external"
    granted = Column(Boolean, default=True)

    # Audit
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(Integer, nullable=True)  # Future: FK to users table

    # Relationship
    module = relationship("Module", back_populates="permissions")


class ModuleHook(Base):
    """
    Tracks backend hooks registered by modules.
    Hooks allow modules to react to lifecycle events.
    """
    __tablename__ = "core_module_hooks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("core_modules.id", ondelete="CASCADE"), nullable=False)

    # Hook details
    hook_name = Column(String(200), nullable=False)  # e.g., "contratto.before_create"
    handler = Column(String(500), nullable=False)  # e.g., "backend.hooks:validate_contratto"
    order = Column(Integer, default=0)  # Execution order (lower runs first)
    enabled = Column(Boolean, default=True)

    # Relationship
    module = relationship("Module", back_populates="hooks")


class ModuleExtension(Base):
    """
    Tracks frontend extension points registered by modules.
    Extension points allow modules to inject UI components.
    """
    __tablename__ = "core_module_extensions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("core_modules.id", ondelete="CASCADE"), nullable=False)

    # Extension point details
    extension_point = Column(String(200), nullable=False)  # e.g., "immobile.detail.tabs"
    config = Column(JSON, nullable=False)  # Extension configuration (label, component, etc.)
    order = Column(Integer, default=0)  # Rendering order
    enabled = Column(Boolean, default=True)

    # Relationship
    module = relationship("Module", back_populates="extensions")


class ModuleEndpoint(Base):
    """
    Tracks API endpoints registered by modules.
    Used for documentation and conflict detection.
    """
    __tablename__ = "core_module_endpoints"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("core_modules.id", ondelete="CASCADE"), nullable=False)

    # Endpoint details
    path = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, PATCH
    handler = Column(String(500), nullable=False)  # Python path to handler function
    tags = Column(JSON)  # OpenAPI tags

    # Relationship
    module = relationship("Module", back_populates="endpoints")
