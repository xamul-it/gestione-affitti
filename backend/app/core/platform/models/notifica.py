"""
Notifica Model - Generic Core Notification Service

Platform-level notification (email and/or in-app) for a single recipient.
Any module or core service creates these via
app.core.platform_services.NotificationService — never by instantiating
this class directly outside that service.

Tenant-scoped table (like Scadenza): created only inside each tenant
schema by backend/alembic/versions/2026091802_create_core_notifiche_tenant_table.py,
never by create_core_tables() (see app/main.py TENANT_ONLY_CORE_TABLES).
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from datetime import datetime
import enum

from app.core.database import Base


class CanaleNotifica(str, enum.Enum):
    """Which channel(s) a notification should be delivered through."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    ENTRAMBI = "ENTRAMBI"


class StatoEmailNotifica(str, enum.Enum):
    """Delivery status of the email leg of a notification (in-app is always created)."""
    NON_RICHIESTA = "NON_RICHIESTA"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notifica(Base):
    """
    A single notification for a single user.

    entity_type/entity_id/link_url are an optional, free-form pointer back
    to whatever triggered the notification (same polymorphic pattern as
    Scadenza) — used only to build a frontend deep-link, never joined on.
    """
    __tablename__ = "core_notifiche"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("core_users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Recipient user",
    )

    tipo = Column(String(100), nullable=False, comment="Free namespace, e.g. 'scadenza.reminder'")
    titolo = Column(String(255), nullable=False)
    corpo = Column(Text, nullable=False)

    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    link_url = Column(String(500), nullable=True)

    canali = Column(String(20), nullable=False, default=CanaleNotifica.ENTRAMBI.value)
    stato_email = Column(String(20), nullable=False, default=StatoEmailNotifica.NON_RICHIESTA.value)
    errore_email = Column(Text, nullable=True)

    letta = Column(Boolean, nullable=False, default=False)
    letta_il = Column(DateTime, nullable=True)

    creata_il = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_core_notifiche_user_letta", "user_id", "letta"),
        Index("idx_core_notifiche_tipo", "tipo"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<Notifica(id={self.id}, user_id={self.user_id}, tipo='{self.tipo}', letta={self.letta})>"
