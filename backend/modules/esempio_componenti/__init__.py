"""
Esempio Componenti Module - Cross-Cutting Components Demo

Modulo dimostrativo per esemplificare l'uso dei componenti trasversali
della piattaforma: DataTable configurabile, Import/Export, Domini.

Module Standard Compliance:
- module_short_code: ESEMPIO
- schema_target: public + tenant

Tables:
PUBLIC SCHEMA (domain data):
- categorie_esempio: Example categories
- priorita_esempio: Example priorities

TENANT SCHEMA (business data):
- elementi_esempio: Example elements with various field types
"""
from typing import Optional
from sqlalchemy.orm import Session
import logging

# Import models to ensure they're available early (before routes are loaded)
from . import models
from .__manifest__ import manifest
from .seeds import seed_all_public

logger = logging.getLogger(__name__)


def get_routers():
    """
    Lazily import routers to avoid circular imports at module import time.
    """
    from .routes import categorie_router, priorita_router, elementi_router
    return [categorie_router, priorita_router, elementi_router]


# Routers provided by this module (lazy)
ROUTERS = []

# Menu items da registrare con la platform
MENU_ITEMS = [
    {
        "id": "esempio.elementi",
        "label": "Elementi",
        "path": "/esempio/elementi",
        "icon": "list",
        "order_index": 10,
        "required_permission": "esempio.view"
    },
    {
        "id": "esempio.categorie",
        "label": "Categorie",
        "path": "/esempio/categorie",
        "icon": "tag",
        "order_index": 20,
        "required_permission": "esempio.view",
        "is_domain_data": True,
    },
    {
        "id": "esempio.priorita",
        "label": "Priorità",
        "path": "/esempio/priorita",
        "icon": "alert-triangle",
        "order_index": 30,
        "required_permission": "esempio.view",
        "is_domain_data": True,
    },
]

# Widget da registrare con la platform
WIDGETS = [
    {
        "id": "esempio.stats",
        "title": "Statistiche Elementi",
        "component": "EsempioStatsWidget",
        "description": "Panoramica degli elementi di esempio",
        "default_width": 4,
        "default_height": 3,
        "category": "stats",
        "module_id": "esempio_componenti",
        "required_permission": "esempio.view"
    },
]

__all__ = [
    "manifest",
    "models",
    "ROUTERS",
    "get_routers",
    "MENU_ITEMS",
    "WIDGETS",
    "register",
    "install",
]


# ============================================================================
# MODULE LIFECYCLE ENDPOINTS
# ============================================================================

def register(db: Session) -> dict:
    """
    Register module: create PUBLIC schema tables and seed domain data.

    This endpoint is called by the core during module registration.
    It should:
    1. Create tables in PUBLIC schema (handled by core via migrations)
    2. Seed domain data in PUBLIC schema

    Args:
        db: Database session (search_path = public)

    Returns:
        Dictionary with registration results
    """
    logger.info("[ESEMPIO] Executing register endpoint...")

    result = {
        "status": "success",
        "module": "esempio_componenti",
        "phase": "register",
        "seeds": {}
    }

    try:
        # Seed public domain data
        result["seeds"] = seed_all_public(db)
        logger.info(f"[ESEMPIO] Register completed successfully: {result}")

    except Exception as e:
        logger.error(f"[ESEMPIO] Register failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        raise

    return result


def install(
    db: Session,
    tenant_id: Optional[int] = None,
    tenant_schema: Optional[str] = None
) -> dict:
    """
    Install module for tenant: create TENANT schema tables and seed initial data.

    This endpoint is called by the core during module installation for a tenant.
    It should:
    1. Create tables in TENANT schema (handled by core via migrations)
    2. Seed tenant-specific initial data

    Signature supports multiple calling conventions:
    - install(db)
    - install(db, tenant_id)
    - install(db, tenant_id, tenant_schema)

    Args:
        db: Database session (search_path = tenant_schema, public)
        tenant_id: Optional tenant ID
        tenant_schema: Optional tenant schema name

    Returns:
        Dictionary with installation results
    """
    logger.info(f"[ESEMPIO] Executing install endpoint for tenant_id={tenant_id}, schema={tenant_schema}...")

    result = {
        "status": "success",
        "module": "esempio_componenti",
        "phase": "install",
        "tenant_id": tenant_id,
        "tenant_schema": tenant_schema,
        "seeds": {}
    }

    try:
        # No tenant-specific seed data for this example module
        # Tenant tables are created by Alembic migrations
        logger.info(f"[ESEMPIO] Install completed successfully: {result}")

    except Exception as e:
        logger.error(f"[ESEMPIO] Install failed for tenant {tenant_id}: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        raise

    return result


def register_module(app):
    """
    Legacy callback: Called by the module loader to register this module.

    This function is kept for backward compatibility.
    New code should use the register() and install() endpoints.
    """
    logger.info("[ESEMPIO] Module registered via legacy register_module()")
    print("[Esempio Componenti] Registering module...")
    print("[Esempio Componenti] Demonstrating cross-cutting platform components")
    print("[Esempio Componenti] Registration complete!")
