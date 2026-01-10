#!/usr/bin/env python3
"""
Assign platform/tenant roles to a user (default: admin).
"""
import sys

from app.core.database import SessionLocal
from app.core.auth.models import User, Role
from app.core.auth.init_data import create_default_permissions, create_default_roles
from app.core.auth.seed_platform_permissions import (
    seed_platform_permissions,
    create_platform_admin_role,
    create_tenant_admin_role,
)


def get_or_create_role(db, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name, description=f"Auto-created role: {name}", is_system=True)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def main() -> int:
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    db = SessionLocal()
    try:
        # Ensure base permissions/roles exist
        permissions = create_default_permissions(db)
        create_default_roles(db, permissions)
        seed_platform_permissions(db)

        platform_admin_role = create_platform_admin_role(db)
        tenant_admin_role = create_tenant_admin_role(db)
        admin_role = get_or_create_role(db, "Admin")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"User '{username}' not found.")
            return 1

        roles_to_add = {admin_role, platform_admin_role, tenant_admin_role}
        existing = {role.name for role in user.roles}
        for role in roles_to_add:
            if role.name not in existing:
                user.roles.append(role)

        db.commit()
        print(f"Updated roles for user '{username}': {[r.name for r in user.roles]}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
