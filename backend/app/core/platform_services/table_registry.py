"""
Table Registry Service

Central registry for table definitions.
Modules register their table configurations at startup.
"""
from typing import Dict, Optional, List
from app.core.schemas.table_configuration import TableDefinition, ColumnDefinition


class TableRegistry:
    """
    Singleton registry for table definitions.

    Modules register their table definitions at startup.
    Frontend can query available tables and their column definitions.
    """
    _instance = None
    _tables: Dict[str, TableDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tables = {}
        return cls._instance

    @classmethod
    def register(cls, definition: TableDefinition) -> None:
        """
        Register a table definition.

        Args:
            definition: TableDefinition object with columns and configuration
        """
        key = f"{definition.module_name}.{definition.entity_name}"
        cls._tables[key] = definition
        print(f"[TableRegistry] Registered table: {key}")

    @classmethod
    def register_dict(cls, config: dict) -> None:
        """
        Register a table from dictionary config.

        Convenience method for modules to register without importing schemas.
        """
        columns = [ColumnDefinition(**col) for col in config.get("columns", [])]
        definition = TableDefinition(
            module_name=config["module_name"],
            entity_name=config["entity_name"],
            title=config.get("title", config["entity_name"]),
            columns=columns,
            default_visible=config.get("default_visible", [c.field for c in columns if c.visible]),
            default_sort_field=config.get("default_sort_field"),
            default_sort_order=config.get("default_sort_order", "asc"),
            default_page_size=config.get("default_page_size", 20),
            selectable=config.get("selectable", True),
            searchable=config.get("searchable", True),
            exportable=config.get("exportable", True),
            row_actions=config.get("row_actions", ["view", "edit", "delete"]),
            bulk_actions=config.get("bulk_actions", ["bulkDelete"]),
        )
        cls.register(definition)

    @classmethod
    def get(cls, module_name: str, entity_name: str) -> Optional[TableDefinition]:
        """
        Get a table definition.

        Args:
            module_name: Module technical name
            entity_name: Entity name

        Returns:
            TableDefinition or None if not found
        """
        key = f"{module_name}.{entity_name}"
        return cls._tables.get(key)

    @classmethod
    def get_all(cls) -> List[TableDefinition]:
        """Get all registered table definitions."""
        return list(cls._tables.values())

    @classmethod
    def get_by_module(cls, module_name: str) -> List[TableDefinition]:
        """Get all table definitions for a module."""
        return [t for t in cls._tables.values() if t.module_name == module_name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        cls._tables = {}


# Singleton instance
table_registry = TableRegistry()


def register_table(config: dict) -> None:
    """
    Convenience function for registering tables.

    Usage in module __init__.py:
        from app.core.platform_services.table_registry import register_table

        register_table({
            "module_name": "anagrafica_italiana",
            "entity_name": "SoggettoAnagrafico",
            "title": "Soggetti Anagrafici",
            "columns": [
                {"field": "nome", "label": "Nome", "type": "text", "required": True},
                {"field": "cognome", "label": "Cognome", "type": "text", "required": True},
                ...
            ],
            "default_visible": ["nome", "cognome", "codice_fiscale", "email"],
            "default_sort_field": "cognome",
        })
    """
    table_registry.register_dict(config)
