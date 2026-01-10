"""
Dashboard Models

Modelli per il sistema di dashboard e widget della piattaforma.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class Widget(Base):
    """Widget disponibile per dashboard"""
    __tablename__ = "platform_widgets"

    id = Column(String(100), primary_key=True)
    module_id = Column(String(100), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    component = Column(String(200), nullable=False)  # Nome componente React
    description = Column(String(500))

    default_width = Column(Integer, default=6)  # Grid 12 colonne
    default_height = Column(Integer, default=4)
    category = Column(String(50))  # 'stats', 'alerts', 'charts'

    required_permission = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserDashboard(Base):
    """Layout dashboard personalizzato per utente"""
    __tablename__ = "platform_user_dashboards"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    layout = Column(JSON, nullable=False)  # [{i: 'widget_id', x, y, w, h}]
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
