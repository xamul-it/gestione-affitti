"""
Tenant Scan Helper

Elenca gli schema dei tenant attivi con un dato modulo abilitato.
Estratto da sync_scheduler.py: sia lo scheduler di sync iCal sia il
compliance_scheduler (docs/superpowers/specs/2026-09-28-affitti-brevi-motore-
scadenze-compliance-design.md) hanno bisogno della stessa identica
iterazione multi-tenant.
"""
from typing import List
import logging

from sqlalchemy import text

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def get_active_tenant_schemas(modulo: str) -> List[str]:
    """Schemi dei tenant attivi che hanno `modulo` abilitato."""
    from app.core.services.tenant_service import TenantService

    db = SessionLocal()
    try:
        db.connection().execute(text("SET search_path TO public"))
        rows = db.execute(
            text("SELECT id, schema_name FROM public.core_tenants WHERE active = true OR active IS NULL")
        ).fetchall()
        schemas = []
        for tenant_id, schema_name in rows:
            try:
                if modulo in TenantService.get_enabled_modules(tenant_id, db):
                    schemas.append(schema_name)
            except Exception as e:
                logger.warning("Could not check enabled modules for tenant %s: %s", schema_name, e)
        return schemas
    except Exception as e:
        logger.warning("Could not list tenants for '%s' scan: %s", modulo, e)
        return []
    finally:
        db.close()
