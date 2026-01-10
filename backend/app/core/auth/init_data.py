"""
Initialize default data for authentication system:
- Default roles (Admin, Manager, Viewer)
- Default permissions
- First admin user
"""
from sqlalchemy.orm import Session
from app.core.auth.models import User, Role, Permission
from app.core.auth.security import get_password_hash
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_default_permissions(db: Session) -> dict:
    """
    Create default permissions for the system.
    Returns a dict mapping permission names to Permission objects.
    """
    permissions_data = [
        # Anagrafiche (Soggetti Anagrafici)
        ("soggetto.view", "View registry subjects", "soggetto", "view"),
        ("soggetto.create", "Create registry subjects", "soggetto", "create"),
        ("soggetto.edit", "Edit registry subjects", "soggetto", "edit"),
        ("soggetto.delete", "Delete registry subjects", "soggetto", "delete"),
        ("soggetto.create_user", "Create user account from soggetto", "soggetto", "create_user"),
        ("soggetto.view_user", "View user account details", "soggetto", "view_user"),
        ("soggetto.disable_user", "Disable user account", "soggetto", "disable_user"),

        # Immobili
        ("immobili.read", "View properties", "immobili", "read"),
        ("immobili.write", "Create/edit properties", "immobili", "write"),
        ("immobili.delete", "Delete properties", "immobili", "delete"),

        # Contratti
        ("contratti.read", "View contracts", "contratti", "read"),
        ("contratti.write", "Create/edit contracts", "contratti", "write"),
        ("contratti.delete", "Delete contracts", "contratti", "delete"),

        # Affittuari
        ("affittuari.read", "View tenants", "affittuari", "read"),
        ("affittuari.write", "Create/edit tenants", "affittuari", "write"),
        ("affittuari.delete", "Delete tenants", "affittuari", "delete"),

        # Proprietari
        ("proprietari.read", "View owners", "proprietari", "read"),
        ("proprietari.write", "Create/edit owners", "proprietari", "write"),
        ("proprietari.delete", "Delete owners", "proprietari", "delete"),

        # Spese
        ("spese.read", "View expenses", "spese", "read"),
        ("spese.write", "Create/edit expenses", "spese", "write"),
        ("spese.delete", "Delete expenses", "spese", "delete"),

        # Incassi
        ("incassi.read", "View income", "incassi", "read"),
        ("incassi.write", "Create/edit income", "incassi", "write"),
        ("incassi.delete", "Delete income", "incassi", "delete"),

        # Documenti
        ("documenti.read", "View documents", "documenti", "read"),
        ("documenti.write", "Upload/edit documents", "documenti", "write"),
        ("documenti.delete", "Delete documents", "documenti", "delete"),

        # Users management
        ("users.read", "View users", "users", "read"),
        ("users.write", "Create/edit users", "users", "write"),
        ("users.delete", "Delete users", "users", "delete"),

        # Roles management
        ("roles.read", "View roles", "roles", "read"),
        ("roles.write", "Create/edit roles", "roles", "write"),
        ("roles.delete", "Delete roles", "roles", "delete"),
    ]

    permissions = {}
    for name, description, resource, action in permissions_data:
        # Check if permission already exists
        perm = db.query(Permission).filter(Permission.name == name).first()
        if not perm:
            perm = Permission(
                name=name,
                description=description,
                resource=resource,
                action=action
            )
            db.add(perm)
            logger.info(f"Created permission: {name}")
        permissions[name] = perm

    db.commit()
    return permissions


def create_default_roles(db: Session, permissions: dict) -> dict:
    """
    Create default roles with their permissions.
    Returns a dict mapping role names to Role objects.
    """
    roles_config = {
        "Admin": {
            "description": "Full system access - can manage everything",
            "is_system": True,
            "permissions": list(permissions.keys())  # All permissions
        },
        "Manager": {
            "description": "Can manage properties, contracts, and view reports",
            "is_system": True,
            "permissions": [
                "soggetto.view", "soggetto.create", "soggetto.edit",
                "immobili.read", "immobili.write",
                "contratti.read", "contratti.write",
                "affittuari.read", "affittuari.write",
                "proprietari.read", "proprietari.write",
                "spese.read", "spese.write",
                "incassi.read", "incassi.write",
                "documenti.read", "documenti.write",
            ]
        },
        "Viewer": {
            "description": "Read-only access to properties and contracts",
            "is_system": True,
            "permissions": [
                "soggetto.view",
                "immobili.read",
                "contratti.read",
                "affittuari.read",
                "proprietari.read",
                "spese.read",
                "incassi.read",
                "documenti.read",
            ]
        }
    }

    roles = {}
    for role_name, config in roles_config.items():
        # Check if role already exists
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=config["description"],
                is_system=config["is_system"]
            )
            db.add(role)
            logger.info(f"Created role: {role_name}")

        # Assign permissions to role
        role.permissions.clear()
        for perm_name in config["permissions"]:
            if perm_name in permissions:
                role.permissions.append(permissions[perm_name])

        roles[role_name] = role

    db.commit()
    return roles


def create_first_admin(db: Session, roles: dict) -> None:
    """
    Create the first admin user if no users exist.
    """
    # Check if any users exist
    user_count = db.query(User).count()
    if user_count > 0:
        logger.info("Users already exist, skipping first admin creation")
        return

    # Create first admin user
    admin_user = User(
        email=settings.FIRST_ADMIN_EMAIL,
        username=settings.FIRST_ADMIN_USERNAME,
        full_name=settings.FIRST_ADMIN_FULL_NAME,
        hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
        is_active=True,
        is_superuser=True,  # First user is always superuser
    )

    # Assign Admin role
    if "Admin" in roles:
        admin_user.roles.append(roles["Admin"])

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    logger.info(f"Created first admin user: {admin_user.username} ({admin_user.email})")
    logger.warning(f"⚠️  IMPORTANT: Change the default admin password immediately!")


def init_auth_data(db: Session) -> None:
    """
    Initialize all auth data (permissions, roles, first admin).
    This should be called on application startup.
    """
    logger.info("Initializing authentication data...")

    try:
        # Create permissions
        permissions = create_default_permissions(db)
        logger.info(f"Initialized {len(permissions)} permissions")

        # Create roles
        roles = create_default_roles(db, permissions)
        logger.info(f"Initialized {len(roles)} roles")

        # Create first admin
        create_first_admin(db, roles)

        logger.info("Authentication data initialization complete")

    except Exception as e:
        logger.error(f"Error initializing auth data: {e}")
        db.rollback()
        raise
