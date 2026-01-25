"""
Table Configuration Schemas

Pydantic schemas for table configuration API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ColumnDefinition(BaseModel):
    """Definition of a table column for frontend rendering."""
    field: str = Field(..., description="Field name (can be nested: 'user.name')")
    label: str = Field(..., description="Display label")
    type: str = Field(default="text", description="Column type: text, number, date, datetime, boolean, currency, badge, link")
    sortable: bool = Field(default=True, description="Can be sorted")
    filterable: bool = Field(default=True, description="Can be filtered")
    visible: bool = Field(default=True, description="Visible by default")
    required: bool = Field(default=False, description="Required column (cannot be hidden)")
    width: Optional[str] = Field(default=None, description="Column width (e.g., '150px', '20%')")
    align: Optional[str] = Field(default="left", description="Text alignment: left, center, right")

    # Type-specific options
    format: Optional[str] = Field(default=None, description="Format string for dates/numbers")
    linkTo: Optional[str] = Field(default=None, description="Link template for 'link' type: '/entity/:id'")
    badgeMap: Optional[Dict[str, Dict[str, str]]] = Field(default=None, description="Status to badge config map")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "nome",
                "label": "Nome",
                "type": "text",
                "sortable": True,
                "filterable": True,
                "visible": True,
                "required": True
            }
        }


class TableDefinition(BaseModel):
    """
    Complete table definition from backend.

    Defines all available columns, their types, and default configuration.
    Modules register their table definitions at startup.
    """
    module_name: str = Field(..., description="Module technical name")
    entity_name: str = Field(..., description="Entity/model name")
    title: str = Field(..., description="Table title")
    columns: List[ColumnDefinition] = Field(..., description="Column definitions")

    # Default configuration
    default_visible: List[str] = Field(default=[], description="Default visible column fields")
    default_sort_field: Optional[str] = Field(default=None, description="Default sort field")
    default_sort_order: str = Field(default="asc", description="Default sort order")
    default_page_size: int = Field(default=20, description="Default page size")

    # Features
    selectable: bool = Field(default=True, description="Enable row selection")
    searchable: bool = Field(default=True, description="Enable search")
    exportable: bool = Field(default=True, description="Enable export")

    # Row actions
    row_actions: List[str] = Field(default=["view", "edit", "delete"], description="Available row actions")
    bulk_actions: List[str] = Field(default=["bulkDelete"], description="Available bulk actions")

    class Config:
        json_schema_extra = {
            "example": {
                "module_name": "anagrafica_italiana",
                "entity_name": "SoggettoAnagrafico",
                "title": "Soggetti Anagrafici",
                "columns": [],
                "default_visible": ["nome", "cognome", "codice_fiscale"],
                "default_sort_field": "cognome",
                "default_sort_order": "asc"
            }
        }


class TableConfigurationBase(BaseModel):
    """Base schema for table configuration."""
    visible_columns: List[str] = Field(..., description="Ordered list of visible column fields")
    column_widths: Optional[Dict[str, str]] = Field(default=None, description="Column width overrides")
    sort_field: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default="asc", description="Sort order: asc or desc")
    page_size: Optional[int] = Field(default=20, ge=5, le=100, description="Rows per page")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Saved filter values")


class TableConfigurationCreate(TableConfigurationBase):
    """Schema for creating a table configuration."""
    module_name: str
    entity_name: str


class TableConfigurationUpdate(BaseModel):
    """Schema for updating a table configuration."""
    visible_columns: Optional[List[str]] = None
    column_widths: Optional[Dict[str, str]] = None
    sort_field: Optional[str] = None
    sort_order: Optional[str] = None
    page_size: Optional[int] = Field(default=None, ge=5, le=100)
    filters: Optional[Dict[str, Any]] = None


class TableConfigurationResponse(TableConfigurationBase):
    """Schema for table configuration response."""
    id: int
    user_id: int
    module_name: str
    entity_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TableConfigWithDefinition(BaseModel):
    """
    Combined response with table definition and user configuration.

    Frontend receives both the table structure and user preferences.
    """
    definition: TableDefinition
    user_config: Optional[TableConfigurationResponse] = None

    class Config:
        json_schema_extra = {
            "example": {
                "definition": {
                    "module_name": "anagrafica_italiana",
                    "entity_name": "SoggettoAnagrafico",
                    "title": "Soggetti Anagrafici",
                    "columns": []
                },
                "user_config": None
            }
        }
