"""
Table Configuration API Routes

Endpoints for managing user table preferences and fetching table definitions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user
from app.core.models.table_configuration import TableConfiguration
from app.core.schemas.table_configuration import (
    TableDefinition,
    TableConfigurationCreate,
    TableConfigurationUpdate,
    TableConfigurationResponse,
    TableConfigWithDefinition,
)
from app.core.platform_services.table_registry import table_registry

router = APIRouter(prefix="/tables", tags=["Table Configuration"])


# ==================== Table Definitions ====================

@router.get("/definitions", response_model=List[TableDefinition])
async def list_table_definitions(
    module_name: Optional[str] = Query(None, description="Filter by module")
):
    """
    List all registered table definitions.

    Returns table structure (columns, types, defaults) for all registered tables.
    Optionally filter by module name.
    """
    if module_name:
        return table_registry.get_by_module(module_name)
    return table_registry.get_all()


@router.get("/definitions/{module_name}/{entity_name}", response_model=TableDefinition)
async def get_table_definition(
    module_name: str,
    entity_name: str
):
    """
    Get a specific table definition.

    Returns the complete table structure including columns, types, and defaults.
    """
    definition = table_registry.get(module_name, entity_name)
    if not definition:
        raise HTTPException(
            status_code=404,
            detail=f"Table definition not found: {module_name}.{entity_name}"
        )
    return definition


# ==================== User Configurations ====================

@router.get("/config/{module_name}/{entity_name}", response_model=TableConfigWithDefinition)
async def get_table_config(
    module_name: str,
    entity_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get table configuration for current user.

    Returns both the table definition and user's saved preferences.
    If no user config exists, returns definition with default values.
    """
    # Get table definition
    definition = table_registry.get(module_name, entity_name)
    if not definition:
        raise HTTPException(
            status_code=404,
            detail=f"Table definition not found: {module_name}.{entity_name}"
        )

    # Get user configuration
    user_config = db.query(TableConfiguration).filter(
        TableConfiguration.user_id == current_user.id,
        TableConfiguration.module_name == module_name,
        TableConfiguration.entity_name == entity_name
    ).first()

    return TableConfigWithDefinition(
        definition=definition,
        user_config=user_config
    )


@router.put("/config/{module_name}/{entity_name}", response_model=TableConfigurationResponse)
async def save_table_config(
    module_name: str,
    entity_name: str,
    config: TableConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Save table configuration for current user.

    Creates or updates user's preferences for the specified table.
    """
    # Verify table exists
    definition = table_registry.get(module_name, entity_name)
    if not definition:
        raise HTTPException(
            status_code=404,
            detail=f"Table definition not found: {module_name}.{entity_name}"
        )

    # Find or create configuration
    db_config = db.query(TableConfiguration).filter(
        TableConfiguration.user_id == current_user.id,
        TableConfiguration.module_name == module_name,
        TableConfiguration.entity_name == entity_name
    ).first()

    if db_config:
        # Update existing
        update_data = config.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)
    else:
        # Create new
        db_config = TableConfiguration(
            user_id=current_user.id,
            module_name=module_name,
            entity_name=entity_name,
            visible_columns=config.visible_columns or definition.default_visible,
            column_widths=config.column_widths,
            sort_field=config.sort_field or definition.default_sort_field,
            sort_order=config.sort_order or definition.default_sort_order,
            page_size=config.page_size or definition.default_page_size,
            filters=config.filters,
        )
        db.add(db_config)

    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/config/{module_name}/{entity_name}")
async def reset_table_config(
    module_name: str,
    entity_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Reset table configuration to defaults.

    Deletes user's saved preferences, reverting to default configuration.
    """
    db_config = db.query(TableConfiguration).filter(
        TableConfiguration.user_id == current_user.id,
        TableConfiguration.module_name == module_name,
        TableConfiguration.entity_name == entity_name
    ).first()

    if db_config:
        db.delete(db_config)
        db.commit()

    return {"message": "Configuration reset to defaults"}


# ==================== Batch Operations ====================

@router.get("/my-configs", response_model=List[TableConfigurationResponse])
async def list_my_configs(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all table configurations for current user.

    Returns all saved preferences across all tables.
    """
    configs = db.query(TableConfiguration).filter(
        TableConfiguration.user_id == current_user.id
    ).all()
    return configs


@router.post("/config/{module_name}/{entity_name}/columns")
async def update_visible_columns(
    module_name: str,
    entity_name: str,
    columns: List[str],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Quick endpoint to update only visible columns.

    Convenience method for column selector component.
    """
    # Verify table exists
    definition = table_registry.get(module_name, entity_name)
    if not definition:
        raise HTTPException(
            status_code=404,
            detail=f"Table definition not found: {module_name}.{entity_name}"
        )

    # Validate columns exist in definition
    valid_fields = {col.field for col in definition.columns}
    invalid_columns = set(columns) - valid_fields
    if invalid_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid column fields: {invalid_columns}"
        )

    # Ensure required columns are included
    required_fields = {col.field for col in definition.columns if col.required}
    missing_required = required_fields - set(columns)
    if missing_required:
        # Auto-add required columns
        columns = list(missing_required) + columns

    # Find or create configuration
    db_config = db.query(TableConfiguration).filter(
        TableConfiguration.user_id == current_user.id,
        TableConfiguration.module_name == module_name,
        TableConfiguration.entity_name == entity_name
    ).first()

    if db_config:
        db_config.visible_columns = columns
    else:
        db_config = TableConfiguration(
            user_id=current_user.id,
            module_name=module_name,
            entity_name=entity_name,
            visible_columns=columns,
            sort_field=definition.default_sort_field,
            sort_order=definition.default_sort_order,
            page_size=definition.default_page_size,
        )
        db.add(db_config)

    db.commit()
    db.refresh(db_config)

    return {"visible_columns": db_config.visible_columns}
