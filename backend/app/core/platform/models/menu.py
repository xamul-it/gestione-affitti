"""
Menu System Models

Modelli per il sistema di menu dinamico della piattaforma.
Permette ai moduli di registrare voci di menu che vengono
composte dinamicamente nel frontend.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from app.core.database import Base
from datetime import datetime


class MenuItem(Base):
    """Voce di menu registrata da un modulo"""
    __tablename__ = "core_platform_menu_items"
    __table_args__ = {"extend_existing": True}

    id = Column(String(100), primary_key=True)  # es: "affitti.immobili"
    module_id = Column(String(100), nullable=False, index=True)  # es: "affitti_lungo"

    # Menu item properties
    label = Column(String(200), nullable=False)  # es: "Immobili"
    path = Column(String(500), nullable=False)  # es: "/immobili"
    icon = Column(String(50), nullable=True)  # es: "building"

    # Hierarchy support
    parent_id = Column(String(100), nullable=True, index=True)  # Per submenu
    order_index = Column(Integer, default=0, index=True)  # Ordinamento

    # Permission
    required_permission = Column(String(100), nullable=True)  # es: "affitti.view_immobile"

    # Domain data flag
    is_domain_data = Column(Boolean, default=False, nullable=False)  # True per dati di riferimento/configurazione

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MenuItem {self.id}: {self.label}>"

    def to_dict(self):
        """Converte in dizionario per JSON response"""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'label': self.label,
            'path': self.path,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'order_index': self.order_index,
            'required_permission': self.required_permission,
            'is_domain_data': self.is_domain_data,
            'is_active': self.is_active
        }
