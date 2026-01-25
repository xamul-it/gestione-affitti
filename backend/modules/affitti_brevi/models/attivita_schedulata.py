"""
AttivitaSchedulata Model - Scheduled Activity/Task

Represents a scheduled activity for mandatory communications and reporting.
Used for:
- Daily: Police communication deadline check
- Monthly: ISTAT reporting generation
- Periodic: Tourist tax declaration

Each activity can be recurring or one-time.
Tracks execution status and maintains an audit log.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TipoAttivita(str, enum.Enum):
    """Type of scheduled activity"""
    CONTROLLO_SCADENZE_POLIZIA = "CONTROLLO_SCADENZE_POLIZIA"    # Check police deadlines
    GENERAZIONE_REPORT_ISTAT = "GENERAZIONE_REPORT_ISTAT"        # Generate ISTAT report
    DICHIARAZIONE_TASSA = "DICHIARAZIONE_TASSA"                  # Tax declaration
    SYNC_CALENDARI = "SYNC_CALENDARI"                            # iCal sync
    NOTIFICA_CHECKIN = "NOTIFICA_CHECKIN"                        # Check-in notification
    SOLLECITO_DATI = "SOLLECITO_DATI"                           # Data collection reminder
    VERIFICA_CODICI = "VERIFICA_CODICI"                         # CIR/CIN code verification
    REPORT_PERIODICO = "REPORT_PERIODICO"                        # Generic periodic report
    ALTRO = "ALTRO"


class StatoAttivita(str, enum.Enum):
    """Activity execution status"""
    PIANIFICATA = "PIANIFICATA"         # Scheduled, waiting for execution time
    IN_ESECUZIONE = "IN_ESECUZIONE"     # Currently executing
    COMPLETATA = "COMPLETATA"           # Successfully completed
    COMPLETATA_PARZIALE = "COMPLETATA_PARZIALE"  # Partially completed
    FALLITA = "FALLITA"                 # Failed
    BLOCCATA = "BLOCCATA"               # Blocked (requires manual intervention)
    SOSPESA = "SOSPESA"                 # Suspended by user
    ANNULLATA = "ANNULLATA"             # Cancelled


class Periodicita(str, enum.Enum):
    """Recurrence frequency"""
    SINGOLA = "SINGOLA"                 # One-time only
    GIORNALIERA = "GIORNALIERA"         # Daily
    SETTIMANALE = "SETTIMANALE"         # Weekly
    MENSILE = "MENSILE"                 # Monthly
    TRIMESTRALE = "TRIMESTRALE"         # Quarterly


class AttivitaSchedulata(Base):
    """
    Scheduled Activity

    Represents a scheduled task for compliance and operations.
    Can be recurring (daily, weekly, monthly) or one-time.
    Tracks execution history and maintains audit trail.
    """
    __tablename__ = "ab_attivita_schedulate"

    id = Column(Integer, primary_key=True, index=True)

    # Activity identification
    tipo = Column(String(50), nullable=False, index=True)
    nome = Column(String(200), nullable=False,
                 comment="Human-readable activity name")
    descrizione = Column(Text, nullable=True)

    # Scope (optional filters)
    unita_immobiliare_id = Column(
        Integer,
        ForeignKey("immo_unita_immobiliari.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Specific property (null = all properties)"
    )
    canale_id = Column(
        Integer,
        ForeignKey("ab_canali.id", ondelete="SET NULL"),
        nullable=True,
        comment="Specific channel (null = all channels)"
    )

    # Schedule
    periodicita = Column(String(30), default=Periodicita.SINGOLA.value,
                        nullable=False)
    ora_esecuzione = Column(String(5), nullable=True, default="06:00",
                           comment="Execution time (HH:MM) for daily/weekly/monthly")
    giorno_settimana = Column(Integer, nullable=True,
                             comment="Day of week (0=Monday) for weekly tasks")
    giorno_mese = Column(Integer, nullable=True,
                        comment="Day of month for monthly tasks")

    # Next execution
    prossima_esecuzione = Column(DateTime(timezone=True), nullable=True, index=True)
    ultima_esecuzione = Column(DateTime(timezone=True), nullable=True)

    # Status
    stato = Column(String(30), default=StatoAttivita.PIANIFICATA.value,
                  nullable=False, index=True)
    attiva = Column(Boolean, default=True, nullable=False)

    # Execution results
    esito_ultima_esecuzione = Column(Text, nullable=True,
                                    comment="JSON summary of last execution")
    errore_ultima_esecuzione = Column(Text, nullable=True)

    # Statistics
    esecuzioni_totali = Column(Integer, default=0, nullable=False)
    esecuzioni_successo = Column(Integer, default=0, nullable=False)
    esecuzioni_fallite = Column(Integer, default=0, nullable=False)

    # Pre-conditions (JSON array)
    precondizioni = Column(Text, nullable=True,
                          comment="JSON array of required conditions")

    # Output configuration
    output_tipo = Column(String(50), nullable=True,
                        comment="REPORT, INVIO, EXPORT, CHECKLIST, etc.")
    output_destinatari = Column(Text, nullable=True,
                               comment="JSON array of notification recipients")

    # Notification settings
    notifica_completamento = Column(Boolean, default=True, nullable=False)
    notifica_errore = Column(Boolean, default=True, nullable=False)
    notifica_scadenza = Column(Boolean, default=True, nullable=False)

    # Notes
    note = Column(Text, nullable=True)

    # Created by
    creato_da = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    unita_immobiliare = relationship(
        "UnitaImmobiliare",
        foreign_keys=[unita_immobiliare_id]
    )
    canale = relationship(
        "Canale",
        foreign_keys=[canale_id]
    )
    log = relationship(
        "AttivitaSchedulataLog",
        back_populates="attivita",
        cascade="all, delete-orphan",
        order_by="desc(AttivitaSchedulataLog.data_esecuzione)"
    )

    # Indexes
    __table_args__ = (
        Index('ix_ab_attivita_prossima_esec',
              'prossima_esecuzione', 'attiva'),
        Index('ix_ab_attivita_tipo_stato',
              'tipo', 'stato'),
    )

    def __repr__(self):
        return f"<AttivitaSchedulata(id={self.id}, tipo={self.tipo}, nome={self.nome})>"

    @property
    def is_dovuta(self) -> bool:
        """Check if activity is due for execution"""
        if not self.attiva:
            return False
        if self.stato in [StatoAttivita.IN_ESECUZIONE.value,
                         StatoAttivita.BLOCCATA.value,
                         StatoAttivita.SOSPESA.value]:
            return False
        if not self.prossima_esecuzione:
            return False

        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.prossima_esecuzione

    def calcola_prossima_esecuzione(self):
        """Calculate next execution time based on periodicity"""
        from datetime import datetime, timezone, timedelta

        if self.periodicita == Periodicita.SINGOLA.value:
            # One-time, no next execution after completion
            if self.stato == StatoAttivita.COMPLETATA.value:
                self.prossima_esecuzione = None
            return

        now = datetime.now(timezone.utc)
        base_time = self.ultima_esecuzione or now

        # Parse execution time
        ore, minuti = 6, 0
        if self.ora_esecuzione:
            try:
                ore, minuti = map(int, self.ora_esecuzione.split(':'))
            except:
                pass

        if self.periodicita == Periodicita.GIORNALIERA.value:
            # Next day at specified time
            next_date = base_time.date() + timedelta(days=1)
            self.prossima_esecuzione = datetime(
                next_date.year, next_date.month, next_date.day,
                ore, minuti, tzinfo=timezone.utc
            )

        elif self.periodicita == Periodicita.SETTIMANALE.value:
            # Next occurrence of specified weekday
            days_ahead = (self.giorno_settimana or 0) - base_time.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = base_time.date() + timedelta(days=days_ahead)
            self.prossima_esecuzione = datetime(
                next_date.year, next_date.month, next_date.day,
                ore, minuti, tzinfo=timezone.utc
            )

        elif self.periodicita == Periodicita.MENSILE.value:
            # Next month on specified day
            month = base_time.month + 1
            year = base_time.year
            if month > 12:
                month = 1
                year += 1
            day = min(self.giorno_mese or 1, 28)  # Safe day for all months
            self.prossima_esecuzione = datetime(
                year, month, day, ore, minuti, tzinfo=timezone.utc
            )

        elif self.periodicita == Periodicita.TRIMESTRALE.value:
            # Add 3 months
            month = base_time.month + 3
            year = base_time.year
            while month > 12:
                month -= 12
                year += 1
            day = min(self.giorno_mese or 1, 28)
            self.prossima_esecuzione = datetime(
                year, month, day, ore, minuti, tzinfo=timezone.utc
            )

    def inizia_esecuzione(self):
        """Mark activity as started"""
        from datetime import datetime, timezone
        self.stato = StatoAttivita.IN_ESECUZIONE.value
        self.ultima_esecuzione = datetime.now(timezone.utc)

    def completa_esecuzione(self, esito: dict = None):
        """Mark activity as completed"""
        import json
        from datetime import datetime, timezone

        self.stato = StatoAttivita.COMPLETATA.value
        self.esecuzioni_totali += 1
        self.esecuzioni_successo += 1
        self.errore_ultima_esecuzione = None

        if esito:
            self.esito_ultima_esecuzione = json.dumps(esito, default=str)

        # Schedule next execution
        self.calcola_prossima_esecuzione()

    def fallisci_esecuzione(self, errore: str):
        """Mark activity as failed"""
        from datetime import datetime, timezone

        self.stato = StatoAttivita.FALLITA.value
        self.esecuzioni_totali += 1
        self.esecuzioni_fallite += 1
        self.errore_ultima_esecuzione = errore

        # Schedule next execution (will retry)
        self.calcola_prossima_esecuzione()


class AttivitaSchedulataLog(Base):
    """
    Activity Execution Log

    Audit trail of activity executions.
    One record per execution attempt.
    """
    __tablename__ = "ab_attivita_schedulate_log"

    id = Column(Integer, primary_key=True, index=True)

    # Link to activity
    attivita_id = Column(
        Integer,
        ForeignKey("ab_attivita_schedulate.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Execution details
    data_esecuzione = Column(DateTime(timezone=True), nullable=False, index=True)
    data_completamento = Column(DateTime(timezone=True), nullable=True)
    durata_secondi = Column(Integer, nullable=True)

    # Result
    stato = Column(String(30), nullable=False)
    esito = Column(Text, nullable=True, comment="JSON execution result")
    errore = Column(Text, nullable=True)

    # Statistics
    elementi_processati = Column(Integer, default=0)
    elementi_successo = Column(Integer, default=0)
    elementi_errore = Column(Integer, default=0)
    elementi_saltati = Column(Integer, default=0)

    # Operator
    eseguito_da = Column(String(100), nullable=True,
                        comment="SISTEMA for automatic, username for manual")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    attivita = relationship(
        "AttivitaSchedulata",
        back_populates="log"
    )

    def __repr__(self):
        return f"<AttivitaSchedulataLog(id={self.id}, attivita={self.attivita_id}, stato={self.stato})>"
