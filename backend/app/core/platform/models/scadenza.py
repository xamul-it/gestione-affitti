"""
Scadenza Model - Universal Deadline/Reminder System

Platform-level model that works with any module and entity type.
Supports TODO mode (entity-less reminders) and multi-recipient notifications.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class PrioritaScadenza(str, enum.Enum):
    """Scadenza priority levels"""
    BASSA = "BASSA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class StatoScadenza(str, enum.Enum):
    """Scadenza lifecycle states"""
    ATTIVA = "ATTIVA"              # Active, not yet due
    SCADUTA = "SCADUTA"            # Past due date, not completed
    COMPLETATA = "COMPLETATA"      # Marked as complete
    POSTICIPATA = "POSTICIPATA"    # Postponed to new date
    CANCELLATA = "CANCELLATA"      # Soft deleted


class Scadenza(Base):
    """
    Universal deadline/reminder that can be attached to any entity or used as standalone TODO.

    Entity Attachment (optional):
        - modulo: Module name (e.g., 'affitti_lungo', 'immobili')
        - entity_type: Entity type (e.g., 'contratto', 'immobile')
        - entity_id: ID of the specific entity

    TODO Mode:
        - When modulo/entity_type/entity_id are NULL, it's a standalone TODO

    Multi-Recipient:
        - destinatari relationship links to multiple users
        - If no destinatari, only creator is notified

    Audit Trail:
        - All changes tracked in scadenza_log via relationship
    """
    __tablename__ = "scadenze"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Entity polymorphic association (optional - NULL for TODOs)
    modulo = Column(String(100), nullable=True, comment="Module name (null for TODO)")
    entity_type = Column(String(100), nullable=True, comment="Entity type (null for TODO)")
    entity_id = Column(Integer, nullable=True, comment="Entity ID (null for TODO)")

    # Scadenza details
    titolo = Column(String(200), nullable=False, comment="Short title/summary")
    descrizione = Column(Text, nullable=True, comment="Detailed description/notes")
    data_scadenza = Column(Date, nullable=False, index=True, comment="Due date")

    # Classification
    priorita = Column(
        SQLEnum(PrioritaScadenza),
        nullable=False,
        default=PrioritaScadenza.MEDIA,
        comment="Priority level"
    )
    stato = Column(
        SQLEnum(StatoScadenza),
        nullable=False,
        default=StatoScadenza.ATTIVA,
        index=True,
        comment="Current state"
    )

    # Creator tracking
    creato_da = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="User who created this scadenza"
    )
    creato_il = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp"
    )

    # Modification tracking
    modificato_il = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment="Last modification timestamp"
    )

    # Completion tracking
    completato_da = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who completed this scadenza"
    )
    completato_il = Column(
        DateTime,
        nullable=True,
        comment="Completion timestamp"
    )

    # Relationships
    creator = relationship(
        "User",
        foreign_keys=[creato_da],
        back_populates="scadenze_create"
    )
    completer = relationship(
        "User",
        foreign_keys=[completato_da],
        back_populates="scadenze_completate"
    )

    destinatari = relationship(
        "ScadenzaDestinatario",
        back_populates="scadenza",
        cascade="all, delete-orphan"
    )

    logs = relationship(
        "ScadenzaLog",
        back_populates="scadenza",
        cascade="all, delete-orphan",
        order_by="ScadenzaLog.timestamp.desc()"
    )

    # Indexes for performance
    __table_args__ = (
        Index('idx_scadenze_entity', 'modulo', 'entity_type', 'entity_id'),
        Index('idx_scadenze_stato_data', 'stato', 'data_scadenza'),
        Index('idx_scadenze_creator', 'creato_da'),
    )

    def __repr__(self):
        entity_str = f"{self.modulo}/{self.entity_type}#{self.entity_id}" if self.modulo else "TODO"
        return f"<Scadenza(id={self.id}, {entity_str}, titolo='{self.titolo}', stato={self.stato})>"

    @property
    def is_todo(self) -> bool:
        """Check if this is a standalone TODO (no entity attachment)"""
        return self.modulo is None and self.entity_type is None and self.entity_id is None

    @property
    def is_scaduta(self) -> bool:
        """Check if deadline has passed and not completed"""
        from datetime import date
        return (
            self.stato == StatoScadenza.ATTIVA and
            self.data_scadenza < date.today()
        )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "modulo": self.modulo,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "titolo": self.titolo,
            "descrizione": self.descrizione,
            "data_scadenza": self.data_scadenza.isoformat() if self.data_scadenza else None,
            "priorita": self.priorita.value if self.priorita else None,
            "stato": self.stato.value if self.stato else None,
            "creato_da": self.creato_da,
            "creato_il": self.creato_il.isoformat() if self.creato_il else None,
            "modificato_il": self.modificato_il.isoformat() if self.modificato_il else None,
            "completato_da": self.completato_da,
            "completato_il": self.completato_il.isoformat() if self.completato_il else None,
            "is_todo": self.is_todo,
            "is_scaduta": self.is_scaduta,
        }
