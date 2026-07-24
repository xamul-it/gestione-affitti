"""
Authentication fixtures for testing.

Provides fixtures for:
- Test users with different roles
- JWT tokens
- Authenticated API clients
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.config import settings
from app.core.auth.models import User
from app.core.auth.security import get_password_hash


@pytest.fixture
def test_password():
    """Standard test password for all test users."""
    return "testpass123"


@pytest.fixture
def test_user(db_session, test_password):
    """
    Create a standard test user.

    Returns:
        User: Test user instance
    """
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash(test_password),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session, test_password):
    """
    Create a superuser for admin tests.

    Returns:
        User: Admin user instance
    """
    user = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash(test_password),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session, test_password):
    """
    Create an inactive user for testing access control.

    Returns:
        User: Inactive user instance
    """
    user = User(
        email="inactive@example.com",
        username="inactiveuser",
        full_name="Inactive User",
        hashed_password=get_password_hash(test_password),
        is_active=False,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create JWT access token for testing.

    Args:
        data: Token payload data
        expires_delta: Token expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


@pytest.fixture
def user_token(test_user):
    """
    Create JWT token for test user.

    Args:
        test_user: Test user fixture

    Returns:
        str: JWT token string
    """
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def admin_token(admin_user):
    """
    Create JWT token for admin user.

    Args:
        admin_user: Admin user fixture

    Returns:
        str: JWT token string
    """
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def user_token_with_tenant(test_user, test_tenant):
    """
    Create JWT token with tenant context.

    Args:
        test_user: Test user fixture
        test_tenant: Test tenant fixture

    Returns:
        str: JWT token with tenant_schema claim
    """
    return create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_schema": test_tenant.schema_name
        }
    )


@pytest.fixture
def expired_token(test_user):
    """
    Create an expired JWT token for testing expiration.

    Args:
        test_user: Test user fixture

    Returns:
        str: Expired JWT token
    """
    return create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
