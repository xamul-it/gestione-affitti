"""
Debug routes for roles and permissions (Admin only).
"""
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_role
from app.core.auth.models import Role, Permission
from app.core.database import get_public_db

router = APIRouter(prefix="/roles-debug", tags=["roles-debug"])


class PermissionSummary(BaseModel):
    id: int
    name: str
    description: str | None
    resource: str
    action: str

    class Config:
        from_attributes = True


class RoleWithPermissions(BaseModel):
    id: int
    name: str
    description: str | None
    is_system: bool
    permissions: List[PermissionSummary]

    class Config:
        from_attributes = True


@router.get("/with-permissions", response_model=List[RoleWithPermissions], dependencies=[Depends(require_role(["Admin"]))])
def list_roles_with_permissions(
    db: Session = Depends(get_public_db)
):
    """
    Return roles with their assigned permissions (Admin only).
    """
    roles = db.query(Role).all()
    results = []
    for role in roles:
        perms = sorted(
            role.permissions,
            key=lambda p: (p.resource, p.action, p.name),
        )
        results.append(
            RoleWithPermissions(
                id=role.id,
                name=role.name,
                description=role.description,
                is_system=role.is_system,
                permissions=[PermissionSummary.from_orm(p) for p in perms],
            )
        )
    return results
