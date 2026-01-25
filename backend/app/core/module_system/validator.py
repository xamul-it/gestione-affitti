"""
Module validation helpers.
"""
from typing import Dict, List, Tuple
from sqlalchemy import inspect

from app.core.module_system.models import Module


def check_public_tables(module: Module, db) -> Tuple[bool, List[str]]:
    """
    Validate that required public tables exist for a module.
    """
    manifest = module.manifest or {}
    schema_target = manifest.get("schema_target")
    if schema_target not in {"public", "public + tenant"}:
        return True, []

    public_tables = manifest.get("public_tables") or []
    if not public_tables:
        return True, []

    inspector = inspect(db.get_bind())
    missing = [table for table in public_tables if not inspector.has_table(table, schema="public")]
    return len(missing) == 0, missing


def ensure_module_health(module: Module, db) -> Dict[str, object]:
    """
    Update module state based on public schema validation.
    """
    ok, missing = check_public_tables(module, db)
    if not ok:
        if module.state != "broken":
            module.state = "broken"
            db.commit()
    else:
        if module.state == "broken" and module.registered:
            module.state = "installed"
            db.commit()

    return {"ok": ok, "missing": missing}
