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

A module can also declare, with the same signature,

    "object_edit_permissions": {"RAGGRUPPAMENTO": "immobili.services.relazioni_bene:..."}

whose rows are permissions ALL required (on top of the rule above) to write
the relations of an object: e.g. a group of beni whose relations are inherited
by units and land parcels needs both immobile.edit and terreno.edit. A hook
that cannot be loaded blocks the writes (fail closed).
"""
import importlib
import logging
from typing import Dict, Optional, Set

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.platform_services.relazioni_moduli import moduli_attivi

logger = logging.getLogger(__name__)


_BLOCCA_SCRITTURA = "__nessuno__"  # a permission nobody has: a broken edit hook blocks writes


def _manifest_hooks(db: Session, tenant_schema: Optional[str], chiave: str = "object_permissions") -> Dict[str, str]:
    """{entity_type: "module.path:function"} of the modules enabled in the tenant."""
    from app.core.module_system.models import Module

    attivi = moduli_attivi(db, tenant_schema)
    hooks: Dict[str, str] = {}
    for module in db.query(Module).all():
        if attivi is not None and module.technical_name not in attivi:
            continue
        hooks.update((module.manifest or {}).get(chiave) or {})
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


def permessi_modifica(db: Session, tenant_schema: Optional[str], *, entity_type: Optional[str],
                      entity_id: Optional[int]) -> Optional[Set[str]]:
    """Permissions that allow writing the relations of one object: the hook's view permission with
    ".view" replaced by ".edit". None when the entity type has no hook (the type's own
    permesso_oggetto rule applies); an empty set when the hook does not list the object."""
    hook = hook_selects(db, tenant_schema).get(entity_type) if entity_type else None
    if hook is None:
        return None
    sub = hook.subquery()
    rows = db.execute(sa.select(sub.c.permesso).where(sub.c.entity_id == entity_id)).all()
    return {r[0].rsplit(".", 1)[0] + ".edit" for r in rows if r[0]}


def permessi_modifica_richiesti(db: Session, tenant_schema: Optional[str], *, entity_type: Optional[str],
                                entity_id: Optional[int]) -> Optional[Set[str]]:
    """Permissions ALL required to write the relations of one object (object_edit_permissions hook).
    None when the entity type has no such hook; an empty set when nothing extra is required."""
    path = _manifest_hooks(db, tenant_schema, "object_edit_permissions").get(entity_type) if entity_type else None
    if path is None:
        return None
    try:
        module_name, func_name = path.split(":")
        sub = getattr(importlib.import_module(module_name), func_name)(db, tenant_schema).subquery()
        rows = db.execute(sa.select(sub.c.permesso).where(sub.c.entity_id == entity_id)).all()
    except Exception:
        logger.exception("Hook object_edit_permissions non valido per %s: %s", entity_type, path)
        return {_BLOCCA_SCRITTURA}
    return {r[0] for r in rows if r[0]}
