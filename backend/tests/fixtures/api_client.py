"""
Enhanced API test client with authentication and tenant context.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Optional, Dict, Any

from app.main import app


class AuthenticatedClient:
    """
    Wrapper around FastAPI TestClient with authentication support.

    This client automatically includes authentication headers in all requests.
    """

    def __init__(self, client: TestClient, token: Optional[str] = None):
        """
        Initialize authenticated client.

        Args:
            client: FastAPI TestClient instance
            token: JWT token for authentication
        """
        self.client = client
        self.token = token

    @property
    def headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def get(self, url: str, **kwargs) -> Any:
        """GET request with authentication."""
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> Any:
        """POST request with authentication."""
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.post(url, **kwargs)

    def put(self, url: str, **kwargs) -> Any:
        """PUT request with authentication."""
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.put(url, **kwargs)

    def patch(self, url: str, **kwargs) -> Any:
        """PATCH request with authentication."""
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.patch(url, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        """DELETE request with authentication."""
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.delete(url, **kwargs)


@pytest.fixture
def client():
    """
    Create FastAPI test client.

    Returns:
        TestClient: FastAPI test client instance
    """
    return TestClient(app)


@pytest.fixture
def auth_client(client, user_token_with_tenant):
    """
    Create authenticated API client.

    Args:
        client: Base test client
        user_token_with_tenant: JWT token with tenant context

    Returns:
        AuthenticatedClient: Client with authentication
    """
    return AuthenticatedClient(client, user_token_with_tenant)


@pytest.fixture
def admin_client(client, admin_token):
    """
    Create authenticated API client for admin user.

    Args:
        client: Base test client
        admin_token: Admin JWT token

    Returns:
        AuthenticatedClient: Client with admin authentication
    """
    return AuthenticatedClient(client, admin_token)


@pytest.fixture
def another_tenant_client(client, test_user, another_tenant):
    """
    Create client authenticated as different tenant.

    Useful for testing tenant isolation.

    Args:
        client: Base test client
        test_user: Test user
        another_tenant: Another tenant fixture

    Returns:
        AuthenticatedClient: Client for different tenant
    """
    from tests.fixtures.auth import create_access_token

    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_schema": another_tenant.schema_name
        }
    )

    return AuthenticatedClient(client, token)
