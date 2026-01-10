"""
Seed platform-level permissions for multi-tenant system.
"""
from sqlalchemy.orm import Session
from app.core.auth.models import Permission, Role, role_permissions


def seed_platform_permissions(db: Session):
    """Seed platform-level permissions."""

    platform_perms = [
        # Platform admin permissions
        {
            "name": "platform.admin",
            "description": "Full platform administration access",
            "resource": "platform",
            "action": "admin"
        },
        {
            "name": "platform.tenants.create",
            "description": "Create new tenants",
            "resource": "tenants",
            "action": "create"
        },
        {
            "name": "platform.tenants.delete",
            "description": "Delete tenants",
            "resource": "tenants",
            "action": "delete"
        },
        {
            "name": "platform.tenants.manage",
            "description": "Manage tenant settings",
            "resource": "tenants",
            "action": "manage"
        },
        {
            "name": "platform.domains.write",
            "description": "Modify shared domain data",
            "resource": "domains",
            "action": "write"
        },
        {
            "name": "platform.modules.manage",
            "description": "Install/uninstall modules for tenants",
            "resource": "modules",
            "action": "manage"
        },

        # Tenant admin permissions
        {
            "name": "tenant.admin",
            "description": "Full tenant administration access",
            "resource": "tenant",
            "action": "admin"
        },
        {
            "name": "tenant.users.manage",
            "description": "Manage users within tenant",
            "resource": "users",
            "action": "manage"
        },
        {
            "name": "tenant.modules.request",
            "description": "Request module installation",
            "resource": "modules",
            "action": "request"
        },

        # Regular tenant permissions
        {
            "name": "tenant.data.read",
            "description": "Read access to tenant data",
            "resource": "tenant_data",
            "action": "read"
        },
        {
            "name": "tenant.data.write",
            "description": "Write access to tenant data",
            "resource": "tenant_data",
            "action": "write"
        },
    ]

    for perm_data in platform_perms:
        existing = db.query(Permission).filter_by(name=perm_data["name"]).first()
        if not existing:
            db.add(Permission(**perm_data))

    db.commit()


def create_platform_admin_role(db: Session) -> Role:
    """
    Create Platform Administrator role with full permissions.

    Returns:
        Platform Admin role
    """
    # Check if role already exists
    existing_role = db.query(Role).filter_by(name="Platform Administrator").first()
    if existing_role:
        return existing_role

    role = Role(
        name="Platform Administrator",
        description="Full platform administration access",
        is_system=True
    )
    db.add(role)
    db.flush()

    # Assign all platform.* permissions
    platform_perms = db.query(Permission).filter(
        Permission.name.like("platform.%")
    ).all()

    for perm in platform_perms:
        db.execute(role_permissions.insert().values(
            role_id=role.id,
            permission_id=perm.id
        ))

    db.commit()
    db.refresh(role)
    return role


def create_tenant_admin_role(db: Session) -> Role:
    """
    Create Tenant Administrator role with tenant-level permissions.

    Returns:
        Tenant Admin role
    """
    # Check if role already exists
    existing_role = db.query(Role).filter_by(name="Tenant Administrator").first()
    if existing_role:
        return existing_role

    role = Role(
        name="Tenant Administrator",
        description="Full tenant administration access",
        is_system=True
    )
    db.add(role)
    db.flush()

    # Assign all tenant.* permissions
    tenant_perms = db.query(Permission).filter(
        Permission.name.like("tenant.%")
    ).all()

    for perm in tenant_perms:
        db.execute(role_permissions.insert().values(
            role_id=role.id,
            permission_id=perm.id
        ))

    db.commit()
    db.refresh(role)
    return role


def seed_all_platform_permissions(db: Session):
    """
    Seed all platform permissions and roles.
    Call this during application startup or migration.
    """
    print("Seeding platform permissions...")
    seed_platform_permissions(db)

    print("Creating Platform Administrator role...")
    create_platform_admin_role(db)

    print("Creating Tenant Administrator role...")
    create_tenant_admin_role(db)

    print("Platform permissions seeded successfully!")
