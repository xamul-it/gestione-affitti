"""
Authentication routes (login, logout, user management).
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_public_db
from app.core.auth.models import User, Role
from app.core.auth.schemas import (
    LoginRequest,
    Token,
    RefreshTokenRequest,
    UserResponse,
    UserDetailResponse,
    UserCreate,
    UserUpdate,
    UserChangePassword,
)
from app.core.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.services.tenant_service import TenantService
from app.core.auth.dependencies import (
    get_current_active_user,
    require_role,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_public_db)
):
    """
    Login endpoint - authenticate user and return JWT tokens.
    """
    # Find user by username
    user = db.query(User).filter(User.username == credentials.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Update last login timestamp
    user_id = user.id
    username = user.username
    user.last_login = datetime.utcnow()
    db.commit()

    # Determine default tenant context (if any)
    default_tenant = TenantService.get_default_tenant(user_id, db)
    tenant_schema = default_tenant["schema_name"] if default_tenant else None

    # Create tokens with extended expiration if remember_me is True
    from datetime import timedelta
    if credentials.remember_me:
        # Remember me: 30 days access token, 90 days refresh token
        access_token = create_access_token(
            data={"sub": str(user_id), "username": username},
            expires_delta=timedelta(days=30),
            tenant_schema=tenant_schema
        )
        refresh_token = create_refresh_token(
            data={
                "sub": str(user_id),
                "username": username,
                **({"tenant_schema": tenant_schema} if tenant_schema else {}),
            }
        )  # Already 30 days by default
    else:
        # Standard: short-lived tokens (default: 15 minutes access, 30 days refresh)
        access_token = create_access_token(
            data={"sub": str(user_id), "username": username},
            tenant_schema=tenant_schema
        )
        refresh_token = create_refresh_token(
            data={
                "sub": str(user_id),
                "username": username,
                **({"tenant_schema": tenant_schema} if tenant_schema else {}),
            }
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_public_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID and tenant context (optional)
    user_id_str = payload.get("sub")
    token_username = payload.get("username")
    tenant_schema = payload.get("tenant_schema")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user exists and is active
    user_id = None
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        user_id = None

    user = None
    if user_id is not None:
        user = db.query(User).filter(User.id == user_id).first()
    if not user:
        fallback_username = token_username or (user_id_str if user_id is None else None)
        if fallback_username:
            user = db.query(User).filter(
                or_(
                    User.username.ilike(fallback_username),
                    User.email.ilike(fallback_username),
                )
            ).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user or inactive account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens (preserve tenant context if present)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        tenant_schema=tenant_schema
    )
    refresh_payload = {"sub": str(user.id), "username": user.username}
    if tenant_schema:
        refresh_payload["tenant_schema"] = tenant_schema
    new_refresh_token = create_refresh_token(data=refresh_payload)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserDetailResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    """
    response = UserDetailResponse.model_validate(current_user)
    response.permissions = list(current_user.get_permissions())
    return response


@router.post("/change-password")
def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_public_db)
):
    """
    Change password for current user.
    """
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


# User management endpoints (Admin only)
@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_role(["Admin"]))])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_public_db)
):
    """
    List all users (Admin only).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_role(["Admin"]))])
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_public_db)
):
    """
    Create a new user (Admin only).
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_superuser=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/users/{user_id}", response_model=UserDetailResponse, dependencies=[Depends(require_role(["Admin"]))])
def get_user(
    user_id: int,
    db: Session = Depends(get_public_db)
):
    """
    Get user by ID (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    response = UserDetailResponse.model_validate(user)
    response.permissions = list(user.get_permissions())
    return response


@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_role(["Admin"]))])
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_public_db)
):
    """
    Update user (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_data.email is not None:
        # Check email uniqueness
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email

    if user_data.username is not None:
        # Check username uniqueness
        existing = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already in use"
            )
        user.username = user_data.username

    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}", dependencies=[Depends(require_role(["Admin"]))])
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_public_db)
):
    """
    Delete user (Admin only).
    Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_role(["Admin"]))])
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_public_db)
):
    """
    Assign a role to a user (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if user already has this role
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role"
        )

    user.roles.append(role)
    db.commit()

    return {"message": f"Role '{role.name}' assigned to user '{user.username}'"}


@router.delete("/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_role(["Admin"]))])
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_public_db)
):
    """
    Remove a role from a user (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if user has this role
    if role not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have this role"
        )

    user.roles.remove(role)
    db.commit()

    return {"message": f"Role '{role.name}' removed from user '{user.username}'"}
