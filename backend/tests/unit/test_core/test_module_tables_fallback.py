"""
TenantModuleService.MODULE_TABLES is the list install_module_for_tenant
checks after installing a module: any table listed there must exist, or
the install is declared failed.

It still listed ab_attivita_schedulate(_log), dropped together with the
old AttivitaSchedulata engine, so installing affitti_brevi on any new
tenant failed - on 2026-11-09 it stopped a production promote halfway.
Every listed table must belong to a model the module still defines.
"""
import importlib

import pytest

from app.core.database import Base
from app.core.services.tenant_module_service import TenantModuleService


@pytest.mark.parametrize("module_id", sorted(TenantModuleService.MODULE_TABLES))
def test_fallback_tables_are_defined_by_the_module_models(module_id):
    importlib.import_module(f"{module_id}.models")
    defined = set(Base.metadata.tables)
    stale = [t for t in TenantModuleService.MODULE_TABLES[module_id] if t not in defined]
    assert stale == [], f"{module_id}: tabelle elencate ma senza modello: {stale}"
