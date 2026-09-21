"""
Immobili Module - Real Estate Property Management

Manages properties, condominiums, owners, and cadastral data.

Module Standard Compliance:
- module_short_code: IMMO
- schema_target: public + tenant
- Prefix: immo_ (su tutte le tabelle)

Tables:
PUBLIC SCHEMA (domain data):
- immo_categorie_catastali: Italian cadastral categories
- immo_tipologie_terreno: Land type classifications

TENANT SCHEMA (business data):
- immo_tipologie_terreno_overrides: Tenant customizations
- immo_terreni: Land parcels
- immo_unita_immobiliari: Property units
- immo_condomini: Condominium buildings
- immo_proprietari: Property owners (role)
- immo_diritti_immobile: Property rights
- immo_certificati_energetici: Energy certificates
- immo_tabelle_millesimali: Millesimal tables
- immo_millesimi_unita: Unit millesimal values
- immo_tipo_immobile_categoria_map: Type to category mapping
"""
from typing import Optional
from sqlalchemy.orm import Session
import logging

# Import models to ensure they're available early (before routes are loaded)
from . import models
from .__manifest__ import manifest
from .seeds import seed_all_public, seed_tenant_data

logger = logging.getLogger(__name__)

def get_routers():
    """
    Lazily import routers to avoid circular imports at module import time.
    """
    from .routes import (
        categorie_catastali_router,
        terreni_router,
        tipologie_terreno_router,
        immobili_router,
        condomini_router,
        proprietari_router,
        diritti_immobile_router,
        certificati_energetici_router,
        tabelle_millesimali_router,
        millesimi_immobile_router,
    )
    return [
        categorie_catastali_router,
        terreni_router,
        tipologie_terreno_router,
        immobili_router,
        condomini_router,
        proprietari_router,
        diritti_immobile_router,
        certificati_energetici_router,
        tabelle_millesimali_router,
        millesimi_immobile_router,
    ]


# Routers provided by this module (lazy)
ROUTERS = []

# Menu items da registrare con la platform
MENU_ITEMS = [
    {
        "id": "immobili.unita",
        "label": "Unità Immobiliari",
        "path": "/unita-immobiliari",
        "icon": "building",
        "order_index": 10,
        "required_permission": "immobile.view"
    },
    {
        "id": "immobili.terreni",
        "label": "Terreni",
        "path": "/terreni",
        "icon": "leaf",
        "order_index": 15,
        "required_permission": "terreno.view"
    },
    {
        "id": "immobili.proprietari",
        "label": "Proprietari",
        "path": "/proprietari",
        "icon": "user",
        "order_index": 20,
        "required_permission": "proprietario.view"
    },
    {
        "id": "immobili.condomini",
        "label": "Condomini",
        "path": "/condomini",
        "icon": "building-2",
        "order_index": 30,
        "required_permission": "condominio.view"
    },
    {
        "id": "immobili.certificati",
        "label": "Certificati Energetici",
        "path": "/certificati-energetici",
        "icon": "zap",
        "order_index": 40,
        "required_permission": "certificato_energetico.view"
    },
    {
        "id": "immobili.categorie_catastali",
        "label": "Categorie Catastali",
        "path": "/categorie-catastali",
        "icon": "list",
        "order_index": 90,
        "required_permission": "platform.admin",
        "is_domain_data": True,
    },
    {
        "id": "immobili.tipologie_terreno",
        "label": "Tipologie Terreno",
        "path": "/tipologie-terreno",
        "icon": "leaf",
        "order_index": 95,
        "required_permission": "platform.admin",
        "is_domain_data": True,
    },
]

# Widget da registrare con la platform
WIDGETS = [
    {
        "id": "immobili.stats",
        "title": "Statistiche Immobili",
        "component": "ImmobiliStatsWidget",
        "description": "Panoramica generale delle unità immobiliari, proprietari e condomini",
        "default_width": 6,
        "default_height": 4,
        "category": "stats",
        "module_id": "immobili",
        "required_permission": "immobile.view"
    },
    {
        "id": "immobili.certificati_scadenza",
        "title": "Certificati in Scadenza",
        "component": "CertificatiScadenzaWidget",
        "description": "Monitoraggio certificati energetici in scadenza o scaduti",
        "default_width": 6,
        "default_height": 4,
        "category": "alerts",
        "module_id": "immobili",
        "required_permission": "certificato_energetico.view"
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
    logger.info("[IMMO] Executing register endpoint...")

    result = {
        "status": "success",
        "module": "immobili",
        "phase": "register",
        "seeds": {}
    }

    try:
        # Seed public domain data
        result["seeds"] = seed_all_public(db)
        logger.info(f"[IMMO] Register completed successfully: {result}")

    except Exception as e:
        logger.error(f"[IMMO] Register failed: {e}")
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

    Signature supports multiple calling conventions:
    - install(db)
    - install(db, tenant_id)
    - install(db, tenant_id, tenant_schema)

    Args:
        db: Database session (search_path = tenant_schema, public)
        tenant_id: Optional tenant ID
        tenant_schema: Optional tenant schema name
        seed_test_data: If True, generate sample test data

    Returns:
        Dictionary with installation results
    """
    logger.info(f"[IMMO] Executing install endpoint for tenant_id={tenant_id}, schema={tenant_schema}...")

    result = {
        "status": "success",
        "module": "immobili",
        "phase": "install",
        "tenant_id": tenant_id,
        "tenant_schema": tenant_schema,
        "seeds": {}
    }

    try:
        # Seed tenant-specific data
        result["seeds"] = seed_tenant_data(
            db,
            tenant_id,
            tenant_schema,
            seed_test_data=seed_test_data,
        )
        logger.info(f"[IMMO] Install completed successfully: {result}")

    except Exception as e:
        logger.error(f"[IMMO] Install failed for tenant {tenant_id}: {e}")
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
    logger.info("[IMMO] Module registered via legacy register_module()")
    print("[Immobili Module] Registering module...")
    print("[Immobili Module] Providing property management functionality")
    print("[Immobili Module] Registration complete!")
