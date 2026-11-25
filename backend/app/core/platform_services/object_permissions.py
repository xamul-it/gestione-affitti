"""
Per-object permission hooks declared by the modules in their manifest:

    "object_permissions": {"IMMOBILE": "immobili.services.permessi:permessi_beni"}

A hook is `function(db, tenant_schema) -> sqlalchemy Select` returning the
columns (entity_id, permesso): the permission a user needs to see each object
of that entity type. It is a select, not a dict, so that relazioni_query can
join it in SQL (listings and aggregations stay a single query).

When a hook exists for an entity type, it REPLACES the type's
`permesso_oggetto` for the relations on that entity type: an object absent
from the hook result is not visible. Only hooks of the modules enabled in the
tenant are used. A hook that cannot be loaded hides its objects (fail closed).
"""
import importlib
import logging
from typing import Dict, Optional, Set

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.platform_services.relazioni_moduli import moduli_attivi

logger = logging.getLogger(__name__)


def _manifest_hooks(db: Session, tenant_schema: Optional[str]) -> Dict[str, str]:
    """{entity_type: "module.path:function"} of the modules enabled in the tenant."""
    from app.core.module_system.models import Module

    attivi = moduli_attivi(db, tenant_schema)
    hooks: Dict[str, str] = {}
    for module in db.query(Module).all():
        if attivi is not None and module.technical_name not in attivi:
            continue
        hooks.update((module.manifest or {}).get("object_permissions") or {})
    return hooks


def _nessun_oggetto() -> sa.Select:
    return sa.select(
        sa.cast(sa.null(), sa.Integer).label("entity_id"), sa.cast(sa.null(), sa.String).label("permesso"),
    ).where(sa.false())


def hook_selects(db: Session, tenant_schema: Optional[str]) -> Dict[str, sa.Select]:
    """{entity_type: select(entity_id, permesso)}: each hook is called once."""
    out: Dict[str, sa.Select] = {}
    for entity_type, path in _manifest_hooks(db, tenant_schema).items():
        try:
            module_name, func_name = path.split(":")
            out[entity_type] = getattr(importlib.import_module(module_name), func_name)(db, tenant_schema)
        except Exception:
            logger.exception("Hook object_permissions non valido per %s: %s", entity_type, path)
            out[entity_type] = _nessun_oggetto()
    return out


def oggetto_visibile(db: Session, tenant_schema: Optional[str], permessi: Set[str], *,
                     entity_type: Optional[str], entity_id: Optional[int],
                     permesso_oggetto: Optional[str]) -> bool:
    """Single-object check, same rule as the listings (hook replaces permesso_oggetto)."""
    if "*" in permessi:
        return True
    hook = hook_selects(db, tenant_schema).get(entity_type) if entity_type else None
    if hook is None:
        return permesso_oggetto is None or permesso_oggetto in permessi
    sub = hook.subquery()
    q = sa.select(sa.literal(1)).select_from(sub).where(
        sub.c.entity_id == entity_id, sub.c.permesso.in_(list(permessi)),
    ).limit(1)
    return db.execute(q).first() is not None
