"""
Anagrafica Italiana Module

This module provides Italian-specific registry functionality for managing
persons and companies according to Italian regulations.

Module Standard Compliance:
- module_short_code: anag
- schema_target: public + tenant
- Prefix: anag_ (su tutte le tabelle)

Tables:
PUBLIC SCHEMA (domain data):
- anag_comuni_italia: Italian municipalities
- anag_ruoli_azienda_tipi: Business role types

TENANT SCHEMA (business data):
- anag_soggetti_anagrafici: Registry subjects (persons and companies)
- anag_ruoli_azienda: Business roles (person-company associations)
- anag_comuni_italia_overrides: Tenant customizations for municipalities
- anag_ruoli_azienda_tipi_overrides: Tenant customizations for role types

The document registry (core_tipi_documento, core_stati_documento,
core_documenti, core_documenti_files + their tenant overrides) is a core
platform service (app/core/platform/models), not owned by this module —
see docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md.
"""
from typing import Optional
from sqlalchemy.orm import Session
import logging

# Import models to ensure they're available early (before routes are loaded)
from . import models
from .__manifest__ import manifest
from .seeds import seed_public, seed_tenant

logger = logging.getLogger(__name__)


def _register_table_definitions() -> None:
    try:
        from app.core.platform_services.table_registry import register_table

        register_table({
            "module_name": "anagrafica_italiana",
            "entity_name": "TipoDocumento",
            "title": "Tipi Documento",
            "columns": [
                {"field": "codice", "label": "Codice", "type": "text", "sortable": True, "filterable": True},
                {"field": "nome", "label": "Nome", "type": "text", "sortable": True, "filterable": True},
                {"field": "categoria", "label": "Categoria", "type": "text", "sortable": True, "filterable": True},
                {"field": "richiede_scadenza", "label": "Scadenza", "type": "boolean", "sortable": True},
                {"field": "attivo", "label": "Attivo", "type": "boolean", "sortable": True},
                {"field": "parsing_service", "label": "Parsing Service", "type": "text", "sortable": False, "visible": False},
                {"field": "parsing_callback_url", "label": "Callback URL", "type": "text", "sortable": False, "visible": False},
                {"field": "parsing_config", "label": "Parsing Config", "type": "text", "sortable": False, "visible": False},
            ],
            "default_visible": [
                "codice",
                "nome",
                "categoria",
                "richiede_scadenza",
                "attivo",
            ],
            "default_sort_field": "nome",
            "default_sort_order": "asc",
            "default_page_size": 50,
            "selectable": False,
            "searchable": True,
            "exportable": False,
            "row_actions": [],
            "bulk_actions": [],
        })
    except Exception as exc:
        logger.warning("Table definitions registration failed: %s", exc)

def get_routers():
    """
    Lazily import routers to avoid circular imports at module import time.
    """
    routers = []
    from .routes import soggetti_v2, domini, ruoli_azienda, ruoli_azienda_tipi

    routers.extend([
        soggetti_v2.router,
        domini.router,
        ruoli_azienda.router,
        ruoli_azienda_tipi.router,
    ])

    try:
        from .routes import documenti
        routers.append(documenti.router)
    except Exception as exc:
        logger.warning("Skipping documenti router: %s", exc)

    try:
        from .routes import anagrafica_from_document
        routers.append(anagrafica_from_document.router)
    except Exception as exc:
        logger.warning("Skipping anagrafica_from_document router: %s", exc)

    return routers


# Routers provided by this module (lazy)
ROUTERS = []

# Menu items da registrare con la platform (dalla manifest)
MENU_ITEMS = manifest.get("menu_items", [])

# Widget da registrare con la platform (dalla manifest)
WIDGETS = manifest.get("widgets", [])

# Legacy export for backward compatibility
router = None

__all__ = [
    "router",
    "ROUTERS",
    "get_routers",
    "manifest",
    "models",
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
    logger.info("[ANAG] Executing register endpoint...")

    result = {
        "status": "success",
        "module": "anagrafica_italiana",
        "phase": "register",
        "seeds": {}
    }

    try:
        # Seed public domain data
        result["seeds"] = seed_public(db)
        logger.info(f"[ANAG] Register completed successfully: {result}")

    except Exception as e:
        logger.error(f"[ANAG] Register failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        raise

    return result


def install(
    db: Session,
    tenant_id: Optional[int] = None,
    tenant_schema: Optional[str] = None,
    seed_test_data: bool = False
) -> dict:
    """
    Install module for tenant: create TENANT schema tables and seed initial data.

    This endpoint is called by the core during module installation for a tenant.
    It should:
    1. Create tables in TENANT schema (handled by core via migrations)
    2. Seed tenant-specific initial data

    Args:
        db: Database session (search_path = tenant_schema, public)
        tenant_id: Optional tenant ID
        tenant_schema: Optional tenant schema name
        seed_test_data: If True, generate sample test data

    Returns:
        Dictionary with installation results
    """
    logger.info(f"[ANAG] Executing install endpoint for tenant_id={tenant_id}, schema={tenant_schema}...")

    result = {
        "status": "success",
        "module": "anagrafica_italiana",
        "phase": "install",
        "tenant_id": tenant_id,
        "tenant_schema": tenant_schema,
        "seeds": {}
    }

    try:
        # Seed tenant-specific data
        result["seeds"] = seed_tenant(
            db,
            seed_test_data=seed_test_data,
            tenant_id=tenant_id,
            tenant_schema=tenant_schema
        )
        logger.info(f"[ANAG] Install completed successfully: {result}")

    except Exception as e:
        logger.error(f"[ANAG] Install failed for tenant {tenant_id}: {e}")
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
    if getattr(app.state, "anagrafica_registered", False):
        return

    from app.core.config import settings

    logger.info("[ANAG] Module registered via legacy register_module()")
    _register_table_definitions()
    routers = get_routers()
    for router in routers:
        app.include_router(router, prefix=settings.API_V1_STR)
    app.state.anagrafica_registered = True
    print("[Anagrafica Italiana Module] Registering module...")
    print("[Anagrafica Italiana Module] Providing Italian registry functionality")
    print("[Anagrafica Italiana Module] Registration complete!")
