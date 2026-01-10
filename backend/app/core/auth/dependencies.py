"""
FastAPI dependencies for authentication and authorization.
"""
import logging
from typing import Optional, List, Sequence, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_public_db
from app.core.auth.models import User
from app.core.auth.security import decode_token

# HTTP Bearer token scheme
security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_public_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    logger.debug("Auth: received credentials scheme=%s", credentials.scheme)
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)
    if payload is None:
        logger.debug("Auth failed: token decode returned None")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(
        "Auth token payload keys: sub=%s username=%s type=%s tenant_schema=%s exp=%s",
        payload.get("sub"),
        payload.get("username"),
        payload.get("type"),
        payload.get("tenant_schema"),
        payload.get("exp"),
    )

    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        logger.debug("Auth failed: invalid token type=%s", token_type)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token (sub is stored as string)
    user_id_str: Optional[str] = payload.get("sub")
    token_username: Optional[str] = payload.get("username")
    if user_id_str is None:
        logger.debug("Auth failed: token sub missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = None
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.debug("Auth: token sub not an int value: sub=%s", user_id_str)
        user_id = None

    # Fetch user from database
    user = None
    if user_id is not None:
        logger.debug("Auth: lookup user by id=%s (public db)", user_id)
        user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        fallback_username = token_username or (user_id_str if user_id is None else None)
        if fallback_username:
            logger.debug(
                "Auth: fallback lookup user by username/email=%s (public db)",
                fallback_username,
            )
            user = db.query(User).filter(
                or_(
                    User.username.ilike(fallback_username),
                    User.email.ilike(fallback_username),
                )
            ).first()
    if user is None:
        logger.debug(
            "Auth failed: user not found in public db (sub=%s username=%s)",
            user_id_str,
            token_username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current active user.

    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_roles: List[str]):
    """
    Dependency factory to require specific roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(["Admin"]))])

    Args:
        required_roles: List of role names that are allowed

    Returns:
        Dependency function that checks user roles
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Superusers bypass all role checks
        if current_user.is_superuser:
            return current_user

        # Check if user has any of the required roles
        user_roles = {role.name for role in current_user.roles}
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )

        return current_user

    return role_checker


def require_permission(required_permissions: Union[str, Sequence[str]]):
    """
    Dependency factory to require specific permissions.

    Usage:
        @router.delete("/immobili/{id}", dependencies=[Depends(require_permission(["immobili.delete"]))])

    Args:
        required_permissions: Permission name or list of permission names that are required

    Returns:
        Dependency function that checks user permissions
    """
    if isinstance(required_permissions, str):
        normalized_permissions = [required_permissions]
    else:
        normalized_permissions = list(required_permissions)

    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        # Check if user has all required permissions
        user_permissions = current_user.get_permissions()
        if not all(perm in user_permissions for perm in normalized_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(normalized_permissions)}"
            )

        return current_user

    return permission_checker
