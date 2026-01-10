"""
Roles management routes (Admin only).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_public_db
from app.core.auth.models import Role, Permission
from app.core.auth.dependencies import require_role
from pydantic import BaseModel

router = APIRouter(prefix="/roles", tags=["roles"])


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_system: bool

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    resource: str
    action: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[RoleResponse], dependencies=[Depends(require_role(["Admin"]))])
def list_roles(
    db: Session = Depends(get_public_db)
):
    """
    List all roles (Admin only).
    """
    roles = db.query(Role).all()
    return roles


@router.get("/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_role(["Admin"]))])
def get_role(
    role_id: int,
    db: Session = Depends(get_public_db)
):
    """
    Get role by ID (Admin only).
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.get("/permissions/all", response_model=List[PermissionResponse], dependencies=[Depends(require_role(["Admin"]))])
def list_permissions(
    db: Session = Depends(get_public_db)
):
    """
    List all permissions (Admin only).
    """
    permissions = db.query(Permission).all()
    return permissions
