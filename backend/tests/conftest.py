"""
Global pytest configuration and fixtures.

This file is automatically discovered by pytest and makes all fixtures
available to all test modules.

For new fixture implementations, see tests/fixtures/ directory.
"""

import pytest
from app.core.database import get_db

# Import all enhanced fixtures from fixtures/ directory
from tests.fixtures.database import (
    db_engine,
    db_session,
    tenant_db_session,
    db_session_with_rollback,
    clear_db,
    db_query_counter,
)

from tests.fixtures.auth import (
    test_password,
    test_user,
    admin_user,
    inactive_user,
    user_token,
    admin_token,
    user_token_with_tenant,
    expired_token,
    create_access_token,
)

from tests.fixtures.tenant import (
    test_tenant,
    another_tenant,
)

from tests.fixtures.api_client import (
    client,
    auth_client,
    admin_client,
    another_tenant_client,
    AuthenticatedClient,
)


# Backward compatibility fixture
@pytest.fixture
def auth_headers(client, user_token_with_tenant):
    """
    Get authentication headers for test user (backward compatibility).

    Note: Prefer using auth_client fixture for new tests.
    """
    return {"Authorization": f"Bearer {user_token_with_tenant}"}


# Database dependency override for integration tests
@pytest.fixture(autouse=True, scope="function")
def override_get_db(db_session):
    """
    Automatically override database dependency for all tests.

    This ensures all tests use the test database session.
    """
    from app.main import app

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db

    yield

    app.dependency_overrides.clear()
