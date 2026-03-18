"""
Tenant fixtures for multi-tenancy testing.
"""

import pytest
from app.core.auth.models import Tenant


@pytest.fixture
def test_tenant(db_session):
    """
    Create a test tenant.

    Returns:
        Tenant: Test tenant instance
    """
    tenant = Tenant(
        name="Test Tenant",
        schema_name="tenant_test",
        is_active=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def another_tenant(db_session):
    """
    Create another tenant for isolation tests.

    Returns:
        Tenant: Second tenant instance
    """
    tenant = Tenant(
        name="Another Tenant",
        schema_name="tenant_other",
        is_active=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant
