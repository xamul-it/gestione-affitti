"""
ScadenzaDestinatario Model - Multi-recipient support for Scadenze

Junction table that links Scadenze to multiple User recipients.
Tracks notification status per recipient.
"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ScadenzaDestinatario(Base):
    """
    Links a Scadenza to a User recipient and tracks notification status.

    Usage:
        - If scadenza has no destinatari records, only creator is notified
        - If scadenza has destinatari records, all listed users are notified
        - notificato flag tracks if user has been notified
        - notificato_il tracks when notification was sent

    Examples:
        # Notify 3 specific users about a contract deadline
        ScadenzaDestinatario(scadenza_id=1, user_id=5)
        ScadenzaDestinatario(scadenza_id=1, user_id=8)
        ScadenzaDestinatario(scadenza_id=1, user_id=12)

        # TODO with no recipients = only creator notified
        # (no ScadenzaDestinatario records created)
    """
    __tablename__ = "scadenza_destinatari"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    scadenza_id = Column(
        Integer,
        ForeignKey('scadenze.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to parent scadenza"
    )
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="Recipient user"
    )

    # Notification tracking
    notificato = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Has user been notified?"
    )
    notificato_il = Column(
        DateTime,
        nullable=True,
        comment="When was notification sent?"
    )

    # Relationships
    scadenza = relationship(
        "Scadenza",
        back_populates="destinatari"
    )
    user = relationship(
        "User",
        back_populates="scadenze_destinate"
    )

    # Indexes and constraints
    __table_args__ = (
        # Prevent duplicate recipient entries
        UniqueConstraint('scadenza_id', 'user_id', name='uq_scadenza_user'),
        # Fast lookups
        Index('idx_destinatari_scadenza', 'scadenza_id'),
        Index('idx_destinatari_user', 'user_id'),
        Index('idx_destinatari_notificato', 'notificato'),
    )

    def __repr__(self):
        notif_status = "✓" if self.notificato else "✗"
        return f"<ScadenzaDestinatario(scadenza_id={self.scadenza_id}, user_id={self.user_id}, notificato={notif_status})>"

    def mark_notified(self):
        """Mark this recipient as notified"""
        self.notificato = True
        self.notificato_il = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "scadenza_id": self.scadenza_id,
            "user_id": self.user_id,
            "notificato": self.notificato,
            "notificato_il": self.notificato_il.isoformat() if self.notificato_il else None,
        }
