"""
Affitti Brevi Module - Short-Term Rental Management

This module provides comprehensive management for short-term rentals including:
- Unified calendar per property aggregating all channels
- iCal synchronization from Booking.com, Airbnb, Vrbo, and more
- Conflict detection and resolution
- Check-in/check-out management with guest data collection
- Tourist tax calculation with exemptions
- Police communications (Alloggiati Web) with 24h deadline
- ISTAT statistics and tax declarations

Architecture:
- Canale: Booking platform configuration (visual properties)
- CalendarioCanale: Property-channel link with iCal sync
- Prenotazione: Booking from any channel
- Soggiorno: Operational stay (check-in/out, guests, compliance)
- OspiteSoggiorno: Guest data for police communications
- TassaSoggiorno: Calculated tourist tax per stay
- Comunicazione: Mandatory communications (Police, ISTAT, Tax)
"""
from typing import Optional
import logging

from sqlalchemy.orm import Session

from .__manifest__ import manifest
from .seeds import seed_canali

logger = logging.getLogger(__name__)

# Menu items da registrare con la platform
MENU_ITEMS = manifest.get("menu_items", [])

# Widget da registrare con la platform
WIDGETS = manifest.get("widgets", [])

__all__ = ["manifest", "register", "install", "MENU_ITEMS", "WIDGETS"]


def register(db: Session) -> dict:
    """
    Register module in public schema (no-op for tenant-only module).
    """
    logger.info("[AFFITTI_BREVI] register called (tenant-only module)")
    return {
        "status": "success",
        "module": "affitti_brevi",
        "phase": "register",
        "seeds": {},
    }


def install(
    db: Session,
    tenant_id: Optional[int] = None,
    tenant_schema: Optional[str] = None,
    seed_test_data: bool = False,
) -> dict:
    """
    Install module for tenant: seed default booking channels.
    """
    logger.info(
        "[AFFITTI_BREVI] install called tenant_id=%s schema=%s",
        tenant_id,
        tenant_schema,
    )

    result = {
        "status": "success",
        "module": "affitti_brevi",
        "phase": "install",
        "tenant_id": tenant_id,
        "tenant_schema": tenant_schema,
        "seeds": {},
    }

    try:
        result["seeds"]["canali"] = seed_canali(db)
    except Exception as exc:
        logger.error("[AFFITTI_BREVI] install failed: %s", exc)
        result["status"] = "error"
        result["error"] = str(exc)
        raise

    return result


def register_module(app):
    """Called by module loader to register routes and services"""
    from .routes import (
        canali,
        calendari,
        calendario_unificato,
        prenotazioni,
        soggiorni,
        sync,
    )

    # Register routes
    prefix = "/api/v1/affitti-brevi"
    tags = ["affitti_brevi"]

    app.include_router(canali.router, prefix=prefix, tags=tags)
    app.include_router(calendari.router, prefix=prefix, tags=tags)
    app.include_router(calendario_unificato.router, prefix=prefix, tags=tags)
    app.include_router(calendario_unificato.legacy_router, prefix=prefix, tags=tags)
    app.include_router(prenotazioni.router, prefix=prefix, tags=tags)
    app.include_router(soggiorni.router, prefix=prefix, tags=tags)
    app.include_router(sync.router, prefix=prefix, tags=tags)
    # "tasse" disabilitato — vedi nota in routes/__init__.py

    print("[Affitti Brevi] Module registered successfully!")
    print("[Affitti Brevi] Routes: canali, calendari, calendario-unificato, prenotazioni, soggiorni, sync")

    # Avvia lo scheduler di sincronizzazione iCal automatica.
    # start() è no-op (con un warning) se già in esecuzione — protegge da
    # doppie attivazioni causate da hot-reload di uvicorn.
    try:
        from .services.sync_scheduler import get_scheduler
        scheduler = get_scheduler()
        if not scheduler.is_running:
            scheduler.start()
            print("[Affitti Brevi] Sync scheduler iCal avviato")
    except Exception as exc:
        logger.error("[Affitti Brevi] Impossibile avviare lo scheduler di sync iCal: %s", exc, exc_info=True)

    # Avvia lo scheduler di generazione scadenze compliance (Polizia, tassa
    # di soggiorno). Stesso motivo/pattern del blocco sopra.
    try:
        from .services.compliance_scheduler import get_compliance_scheduler
        compliance_scheduler = get_compliance_scheduler()
        if not compliance_scheduler.is_running:
            compliance_scheduler.start()
            print("[Affitti Brevi] Scheduler scadenze compliance avviato")
    except Exception as exc:
        logger.error("[Affitti Brevi] Impossibile avviare lo scheduler scadenze compliance: %s", exc, exc_info=True)
