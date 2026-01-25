"""
Table Configuration Model

Stores user preferences for table configurations:
- Visible columns and their order
- Default sorting
- Page size preferences

Each configuration is scoped to:
- User (user_id)
- Table identifier (module_name + entity_name)
- Tenant (via schema isolation)
"""
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TableConfiguration(Base):
    """
    User-specific table configuration preferences.

    Stores column visibility, order, sorting, and other display preferences
    for each table in the application.
    """
    __tablename__ = "core_table_configurations"

    id = Column(Integer, primary_key=True, index=True)

    # Scope
    user_id = Column(Integer, ForeignKey("core_users.id", ondelete="CASCADE"), nullable=False)
    module_name = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(100), nullable=False, index=True)

    # Configuration data
    visible_columns = Column(JSON, nullable=False, default=list)
    """List of visible column field names in display order"""

    column_widths = Column(JSON, nullable=True, default=dict)
    """Optional column width overrides: {"field": "150px"}"""

    sort_field = Column(String(100), nullable=True)
    """Default sort field"""

    sort_order = Column(String(4), nullable=True, default="asc")
    """Sort order: 'asc' or 'desc'"""

    page_size = Column(Integer, nullable=True, default=20)
    """Number of rows per page"""

    filters = Column(JSON, nullable=True, default=dict)
    """Saved filter presets"""

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'module_name', 'entity_name', name='uq_user_table_config'),
        {"schema": "public", "extend_existing": True},
    )

    def __repr__(self):
        return f"<TableConfiguration(user_id={self.user_id}, module={self.module_name}, entity={self.entity_name})>"
