"""
Human-readable labels for polymorphic entities (entity_type/entity_id), used
by core lists that span entities (e.g. all the documents of a module).

Modules register a resolver for their entity types:

    entity_label_registry.register("IMMOBILE", resolve)  # resolve(db, ids) -> {id: label}
"""
from typing import Callable, Dict, Iterable

from sqlalchemy.orm import Session

Resolver = Callable[[Session, list], Dict[int, str]]


class EntityLabelRegistry:
    def __init__(self):
        self._resolvers: Dict[str, Resolver] = {}

    def register(self, entity_type: str, resolver: Resolver) -> None:
        self._resolvers[entity_type] = resolver

    def labels(self, db: Session, entity_type: str, ids: Iterable[int]) -> Dict[int, str]:
        ids = sorted(set(ids))
        found: Dict[int, str] = {}
        resolver = self._resolvers.get(entity_type)
        if resolver and ids:
            try:
                found = resolver(db, ids) or {}
            except Exception:
                found = {}
        return {i: found.get(i) or f"{entity_type} #{i}" for i in ids}


entity_label_registry = EntityLabelRegistry()
