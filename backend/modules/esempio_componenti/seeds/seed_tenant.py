"""
Seed Tenant - Tenant-specific data for esempio_componenti module.

This file contains tenant-specific initial data that is populated
in the TENANT schema during module installation (endpoints.install).

Each tenant gets their own isolated copy of this data.

Tables populated:
- (none for this example module - tenant tables are empty by default)
"""
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def seed_tenant(db: Session) -> dict:
    """
    Seed tenant-specific data for the esempio_componenti module.

    This function is called by the core during module installation for a tenant
    (endpoints.install). It populates initial data in the TENANT schema.

    For this example module, we don't seed any initial tenant data.
    The tenant's elementi_esempio table starts empty.

    Args:
        db: Database session (search_path = tenant_schema, public)

    Returns:
        Dictionary with counts of seeded records per table
    """
    logger.info("[ESEMPIO] Starting tenant seed...")

    results = {
        "elementi_esempio": 0,  # No initial data for tenant
    }

    logger.info(f"[ESEMPIO] Tenant seed completed: {results}")
    return results
