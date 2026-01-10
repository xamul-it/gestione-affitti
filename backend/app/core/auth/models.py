"""
SQLAlchemy models for authentication and authorization.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
)


class User(Base):
    """
    User model for authentication.
    Supports multiple roles per user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))
    phone = Column(String(50))

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Link to Anagrafica (optional - for business users)
    soggetto_anagrafico_id = Column(Integer, ForeignKey('soggetti_anagrafici.id', ondelete='SET NULL'),
                                     nullable=True, unique=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    user_tenants = relationship("UserTenant", back_populates="user", cascade="all, delete-orphan")

    # Scadenzario relationships
    scadenze_create = relationship("Scadenza", foreign_keys="Scadenza.creato_da", back_populates="creator")
    scadenze_completate = relationship("Scadenza", foreign_keys="Scadenza.completato_da", back_populates="completer")
    scadenze_destinate = relationship("ScadenzaDestinatario", back_populates="user")
    scadenza_logs = relationship("ScadenzaLog", back_populates="user")

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission (through any role)."""
        if self.is_superuser:
            return True
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False

    def get_permissions(self) -> set:
        """Get all permissions from all roles."""
        if self.is_superuser:
            return {"*"}  # Superuser has all permissions
        permissions = set()
        for role in self.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        return permissions


class Role(Base):
    """
    Role model for role-based access control (RBAC).
    Examples: Admin, Manager, Viewer
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)

    # Role info
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

    # System roles cannot be deleted
    is_system = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    """
    Permission model for granular access control.
    Examples: immobili.read, contratti.write, users.manage
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)

    # Permission info
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))

    # Resource and action (for organization)
    resource = Column(String(50), nullable=False)  # e.g., "immobili", "contratti"
    action = Column(String(50), nullable=False)     # e.g., "read", "write", "delete"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# Export the association table for easier access
UserRole = user_roles
