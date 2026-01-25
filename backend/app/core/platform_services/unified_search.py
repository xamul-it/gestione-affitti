"""
Unified Search Service

Platform-level service for cross-module entity search.
Modules register their searchable entities with search configurations.
"""
from typing import List, Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, String, cast
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class SearchableField:
    """Definition of a searchable field in an entity."""
    name: str
    label: str
    weight: int = 1  # Higher weight = more relevant in results


@dataclass
class SearchableEntity:
    """Configuration for a searchable entity."""
    # Identity
    module_name: str
    entity_name: str
    display_name: str
    display_name_plural: str

    # Model
    model_class: Type

    # Search configuration
    search_fields: List[SearchableField]

    # Result formatting
    title_template: str  # e.g., "{nome} {cognome}"
    subtitle_template: Optional[str] = None  # e.g., "{email}"
    url_template: str = "/{entity}/{id}"  # e.g., "/anagrafiche/{id}"

    # Display
    icon: str = "search"
    color: str = "#6c757d"

    # Ordering
    default_order_by: Optional[str] = None

    # Permissions
    required_permission: Optional[str] = None

    # Custom result builder (optional)
    result_builder: Optional[Callable] = None


class UnifiedSearchRegistry:
    """
    Registry for searchable entities across all modules.

    Modules register their entities at startup, and the unified search
    queries all registered entities.
    """

    _instance = None
    _entities: Dict[str, SearchableEntity] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._entities = {}
        return cls._instance

    @classmethod
    def register(cls, entity: SearchableEntity) -> None:
        """Register a searchable entity."""
        key = f"{entity.module_name}.{entity.entity_name}"
        cls._entities[key] = entity
        logger.info(f"[UnifiedSearch] Registered searchable entity: {key}")

    @classmethod
    def unregister(cls, module_name: str, entity_name: str) -> None:
        """Unregister a searchable entity."""
        key = f"{module_name}.{entity_name}"
        if key in cls._entities:
            del cls._entities[key]
            logger.info(f"[UnifiedSearch] Unregistered searchable entity: {key}")

    @classmethod
    def get_all_entities(cls) -> List[SearchableEntity]:
        """Get all registered searchable entities."""
        return list(cls._entities.values())

    @classmethod
    def get_entity(cls, module_name: str, entity_name: str) -> Optional[SearchableEntity]:
        """Get a specific searchable entity."""
        key = f"{module_name}.{entity_name}"
        return cls._entities.get(key)

    @classmethod
    def get_entities_by_module(cls, module_name: str) -> List[SearchableEntity]:
        """Get all searchable entities for a module."""
        return [e for e in cls._entities.values() if e.module_name == module_name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered entities (mainly for testing)."""
        cls._entities = {}


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent SQL injection and normalize input.
    """
    if not query:
        return ""

    # Escape SQL LIKE wildcards
    query = query.replace("\\", "\\\\")
    query = query.replace("%", "\\%")
    query = query.replace("_", "\\_")

    # Remove potentially dangerous characters but keep Italian accents
    # Allow: alphanumeric, spaces, accented chars, common punctuation
    query = re.sub(r"[^\w\s\-.,àèéìòùÀÈÉÌÒÙ@]", "", query, flags=re.UNICODE)

    # Normalize whitespace
    query = " ".join(query.split())

    return query.strip()


def format_result_text(template: str, obj: Any) -> str:
    """
    Format a result text using a template and object attributes.

    Template example: "{nome} {cognome}" with obj.nome="Mario", obj.cognome="Rossi"
    Result: "Mario Rossi"
    """
    if not template:
        return str(obj)

    result = template

    # Find all {field} placeholders
    fields = re.findall(r"\{(\w+(?:\.\w+)*)\}", template)

    for field in fields:
        value = obj
        try:
            # Support nested fields like {immobile.indirizzo}
            for part in field.split("."):
                if value is None:
                    break
                value = getattr(value, part, None)

            if value is None:
                value = ""

            result = result.replace(f"{{{field}}}", str(value))
        except Exception:
            result = result.replace(f"{{{field}}}", "")

    return result.strip()


class UnifiedSearchService:
    """
    Service for executing unified search across all registered entities.
    """

    def __init__(self, db: Session):
        self.db = db
        self.registry = UnifiedSearchRegistry()

    def search(
        self,
        query: str,
        modules: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        limit_per_entity: int = 5,
        total_limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Execute unified search across all registered entities.

        Args:
            query: Search query string
            modules: Optional list of module names to search (None = all)
            entities: Optional list of entity names to search (None = all)
            limit_per_entity: Max results per entity type
            total_limit: Max total results

        Returns:
            Dict with 'results' grouped by entity and 'total' count
        """
        sanitized_query = sanitize_search_query(query)

        if len(sanitized_query) < 2:
            return {"results": {}, "total": 0, "query": query}

        search_pattern = f"%{sanitized_query}%"

        all_entities = self.registry.get_all_entities()
        results_by_entity = {}
        total_count = 0

        for entity in all_entities:
            # Filter by module if specified
            if modules and entity.module_name not in modules:
                continue

            # Filter by entity if specified
            if entities and entity.entity_name not in entities:
                continue

            try:
                entity_results = self._search_entity(
                    entity, search_pattern, limit_per_entity
                )

                if entity_results:
                    key = f"{entity.module_name}.{entity.entity_name}"
                    results_by_entity[key] = {
                        "module_name": entity.module_name,
                        "entity_name": entity.entity_name,
                        "display_name": entity.display_name,
                        "display_name_plural": entity.display_name_plural,
                        "icon": entity.icon,
                        "color": entity.color,
                        "items": entity_results,
                        "count": len(entity_results),
                    }
                    total_count += len(entity_results)

            except Exception as e:
                logger.error(f"[UnifiedSearch] Error searching {entity.entity_name}: {e}")
                continue

        return {
            "results": results_by_entity,
            "total": total_count,
            "query": query,
        }

    def _search_entity(
        self,
        entity: SearchableEntity,
        search_pattern: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search a single entity type.
        """
        model = entity.model_class

        # Build OR conditions for all search fields
        conditions = []
        for field in entity.search_fields:
            column = getattr(model, field.name, None)
            if column is not None:
                # Cast non-string columns to string for ILIKE
                if not isinstance(column.type, String):
                    conditions.append(cast(column, String).ilike(search_pattern))
                else:
                    conditions.append(column.ilike(search_pattern))

        if not conditions:
            return []

        # Build query
        query = self.db.query(model).filter(or_(*conditions))

        # Apply ordering
        if entity.default_order_by:
            order_field = entity.default_order_by
            if order_field.startswith("-"):
                order_col = getattr(model, order_field[1:], None)
                if order_col:
                    query = query.order_by(order_col.desc())
            else:
                order_col = getattr(model, order_field, None)
                if order_col:
                    query = query.order_by(order_col)

        # Execute with limit
        items = query.limit(limit).all()

        # Format results
        results = []
        for item in items:
            if entity.result_builder:
                result = entity.result_builder(item)
            else:
                result = self._build_result(entity, item)
            results.append(result)

        return results

    def _build_result(
        self,
        entity: SearchableEntity,
        item: Any
    ) -> Dict[str, Any]:
        """
        Build a search result dict from an entity item.
        """
        # Format title and subtitle
        title = format_result_text(entity.title_template, item)
        subtitle = format_result_text(entity.subtitle_template, item) if entity.subtitle_template else None

        # Format URL
        url = entity.url_template.replace("{id}", str(item.id))
        url = url.replace("{entity}", entity.entity_name.lower())

        return {
            "id": item.id,
            "title": title,
            "subtitle": subtitle,
            "url": url,
            "type": entity.entity_name,
            "module": entity.module_name,
        }

    def get_searchable_entities(self) -> List[Dict[str, Any]]:
        """
        Get list of all searchable entities for UI display.
        """
        entities = self.registry.get_all_entities()
        return [
            {
                "module_name": e.module_name,
                "entity_name": e.entity_name,
                "display_name": e.display_name,
                "display_name_plural": e.display_name_plural,
                "icon": e.icon,
                "color": e.color,
                "search_fields": [f.label for f in e.search_fields],
            }
            for e in entities
        ]


# Convenience function for registering entities
def register_searchable_entity(
    module_name: str,
    entity_name: str,
    display_name: str,
    display_name_plural: str,
    model_class: Type,
    search_fields: List[Dict[str, Any]],
    title_template: str,
    subtitle_template: Optional[str] = None,
    url_template: str = "/{entity}/{id}",
    icon: str = "search",
    color: str = "#6c757d",
    default_order_by: Optional[str] = None,
    required_permission: Optional[str] = None,
    result_builder: Optional[Callable] = None,
) -> None:
    """
    Convenience function to register a searchable entity.

    Example:
        register_searchable_entity(
            module_name="anagrafica_italiana",
            entity_name="SoggettoAnagrafico",
            display_name="Soggetto",
            display_name_plural="Soggetti Anagrafici",
            model_class=SoggettoAnagrafico,
            search_fields=[
                {"name": "nome", "label": "Nome"},
                {"name": "cognome", "label": "Cognome"},
                {"name": "codice_fiscale", "label": "Codice Fiscale"},
                {"name": "email", "label": "Email"},
            ],
            title_template="{nome} {cognome}",
            subtitle_template="{codice_fiscale} - {email}",
            url_template="/anagrafiche/{id}",
            icon="user",
            color="#3498db",
            default_order_by="cognome",
        )
    """
    fields = [
        SearchableField(
            name=f["name"],
            label=f["label"],
            weight=f.get("weight", 1)
        )
        for f in search_fields
    ]

    entity = SearchableEntity(
        module_name=module_name,
        entity_name=entity_name,
        display_name=display_name,
        display_name_plural=display_name_plural,
        model_class=model_class,
        search_fields=fields,
        title_template=title_template,
        subtitle_template=subtitle_template,
        url_template=url_template,
        icon=icon,
        color=color,
        default_order_by=default_order_by,
        required_permission=required_permission,
        result_builder=result_builder,
    )

    UnifiedSearchRegistry.register(entity)
