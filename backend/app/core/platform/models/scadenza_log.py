"""
ScadenzaLog Model - Audit Trail for Scadenze

Tracks all changes and actions performed on Scadenze for full audit history.
Useful for compliance, debugging, and understanding the lifecycle of each deadline.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ScadenzaLog(Base):
    """
    Audit log entry for Scadenza changes.

    Captures:
        - Who made the change (user_id)
        - What action was performed (azione)
        - When it happened (timestamp)
        - What field changed (campo_modificato)
        - Before/after values (valore_precedente, valore_nuovo)
        - Optional notes

    Common Actions:
        - CREATA: Scadenza created
        - MODIFICATA: Field updated
        - STATO_CAMBIATO: State transition (ATTIVA → COMPLETATA, etc.)
        - POSTICIPATA: Due date postponed
        - COMPLETATA: Marked as complete
        - CANCELLATA: Soft deleted
        - DESTINATARIO_AGGIUNTO: Recipient added
        - DESTINATARIO_RIMOSSO: Recipient removed
        - NOTIFICA_INVIATA: Notification sent

    Usage Example:
        # Log state change
        log = ScadenzaLog(
            scadenza_id=1,
            user_id=5,
            azione="STATO_CAMBIATO",
            campo_modificato="stato",
            valore_precedente="ATTIVA",
            valore_nuovo="COMPLETATA",
            note="Contratto firmato, chiudo la scadenza"
        )
    """
    __tablename__ = "scadenza_log"

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
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who performed the action (null for system actions)"
    )

    # Action details
    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When action occurred"
    )
    azione = Column(
        String(50),
        nullable=False,
        comment="Action type (CREATA, MODIFICATA, COMPLETATA, etc.)"
    )

    # Field change details (optional - not all actions modify fields)
    campo_modificato = Column(
        String(100),
        nullable=True,
        comment="Which field was changed (if applicable)"
    )
    valore_precedente = Column(
        Text,
        nullable=True,
        comment="Value before change"
    )
    valore_nuovo = Column(
        Text,
        nullable=True,
        comment="Value after change"
    )

    # Optional notes
    note = Column(
        Text,
        nullable=True,
        comment="Additional context or notes"
    )

    # Relationships
    scadenza = relationship(
        "Scadenza",
        back_populates="logs"
    )
    user = relationship(
        "User",
        back_populates="scadenza_logs"
    )

    # Indexes for performance
    __table_args__ = (
        Index('idx_log_scadenza', 'scadenza_id'),
        Index('idx_log_timestamp', 'timestamp'),
        Index('idx_log_azione', 'azione'),
    )

    def __repr__(self):
        user_str = f"user={self.user_id}" if self.user_id else "system"
        return f"<ScadenzaLog(scadenza_id={self.scadenza_id}, {user_str}, azione={self.azione})>"

    @classmethod
    def log_creation(cls, scadenza_id: int, user_id: int, note: str = None):
        """Helper to log scadenza creation"""
        return cls(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione="CREATA",
            note=note
        )

    @classmethod
    def log_field_change(cls, scadenza_id: int, user_id: int, campo: str,
                        old_value: str, new_value: str, note: str = None):
        """Helper to log field modification"""
        return cls(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione="MODIFICATA",
            campo_modificato=campo,
            valore_precedente=old_value,
            valore_nuovo=new_value,
            note=note
        )

    @classmethod
    def log_state_change(cls, scadenza_id: int, user_id: int,
                        old_state: str, new_state: str, note: str = None):
        """Helper to log state transition"""
        return cls(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione="STATO_CAMBIATO",
            campo_modificato="stato",
            valore_precedente=old_state,
            valore_nuovo=new_state,
            note=note
        )

    @classmethod
    def log_completion(cls, scadenza_id: int, user_id: int, note: str = None):
        """Helper to log completion"""
        return cls(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione="COMPLETATA",
            note=note
        )

    @classmethod
    def log_cancellation(cls, scadenza_id: int, user_id: int, note: str = None):
        """Helper to log cancellation"""
        return cls(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione="CANCELLATA",
            note=note
        )

    @classmethod
    def log_postponement(cls, scadenza_id: int, user_id: int,
                        old_date: str, new_date: str, note: str = None):
        """Helper to log date postponement"""
        return cls(
            scadenza_id=scadenza_id,
            user_id=user_id,
            azione="POSTICIPATA",
            campo_modificato="data_scadenza",
            valore_precedente=old_date,
            valore_nuovo=new_date,
            note=note
        )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "scadenza_id": self.scadenza_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "azione": self.azione,
            "campo_modificato": self.campo_modificato,
            "valore_precedente": self.valore_precedente,
            "valore_nuovo": self.valore_nuovo,
            "note": self.note,
        }
