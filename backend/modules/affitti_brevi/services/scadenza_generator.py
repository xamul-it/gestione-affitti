"""
Scadenza Generator Service

Automatically generates deadlines for legal requirements using core.Scadenza model:
- Police communications (within 24h of check-in)
- ISTAT monthly reports (1st of each month)

Uses core scadenze table + affitti_brevi extension for module-specific metadata.
"""
from datetime import datetime, timedelta, timezone, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
import logging

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from affitti_brevi.models import Prenotazione
from affitti_brevi.models.scadenza_ext import ScadenzaAffittiBrevi, TipoScadenzaAffittiBrevi

# Use core Scadenza model
from app.core.platform.models.scadenza import Scadenza, StatoScadenza, PrioritaScadenza

logger = logging.getLogger(__name__)


class ScadenzaGenerator:
    """
    Automatic Deadline Generator using core Scadenza model

    Creates deadlines for legal compliance with proper polymorphic association.
    """

    def __init__(self, db: Session, current_user_id: int = 1):
        """
        Initialize generator

        Args:
            db: Database session
            current_user_id: ID of user creating deadlines (default: 1 for system)
        """
        self.db = db
        self.current_user_id = current_user_id

    def generate_police_deadline_for_booking(self, prenotazione_id: int) -> Tuple[Scadenza, ScadenzaAffittiBrevi]:
        """
        Generate police communication deadline for a booking

        Deadline is 24 hours from check-in date.

        Args:
            prenotazione_id: ID of booking to generate deadline for

        Returns:
            Tuple of (core Scadenza, ScadenzaAffittiBrevi extension)

        Raises:
            ValueError: If booking not found
        """
        # Get booking
        prenotazione = self.db.query(Prenotazione).filter(
            Prenotazione.id == prenotazione_id
        ).first()

        if not prenotazione:
            raise ValueError(f"Prenotazione {prenotazione_id} not found")

        # Check if deadline already exists (via extension table)
        existing_ext = self.db.query(ScadenzaAffittiBrevi).join(Scadenza).filter(
            Scadenza.modulo == "affitti_brevi",
            Scadenza.entity_type == "prenotazione",
            Scadenza.entity_id == prenotazione_id,
            ScadenzaAffittiBrevi.tipo_scadenza == TipoScadenzaAffittiBrevi.COMUNICAZIONE_POLIZIA
        ).first()

        if existing_ext:
            logger.info(f"Police deadline already exists for booking {prenotazione_id}")
            scadenza = self.db.query(Scadenza).filter(Scadenza.id == existing_ext.scadenza_id).first()
            return scadenza, existing_ext

        # Calculate deadline (24h from check-in at midnight)
        checkin_datetime = datetime.combine(
            prenotazione.data_checkin,
            datetime.min.time()
        ).replace(tzinfo=timezone.utc)

        deadline_datetime = checkin_datetime + timedelta(hours=24)

        # Create core Scadenza first
        scadenza = Scadenza(
            modulo="affitti_brevi",
            entity_type="prenotazione",
            entity_id=prenotazione_id,
            titolo=f"Comunicazione Polizia - {prenotazione.codice_prenotazione}",
            descrizione=f"Comunicare {prenotazione.numero_ospiti} ospiti entro 24h dal check-in ({prenotazione.data_checkin})",
            data_scadenza=deadline_datetime.date(),  # Core uses Date, not DateTime
            priorita=PrioritaScadenza.ALTA,  # Police is high priority
            stato=StatoScadenza.ATTIVA,
            creato_da=self.current_user_id
        )

        self.db.add(scadenza)
        self.db.flush()  # Get scadenza.id without committing

        # Create extension with affitti_brevi-specific metadata
        scadenza_ext = ScadenzaAffittiBrevi(
            scadenza_id=scadenza.id,
            tipo_scadenza=TipoScadenzaAffittiBrevi.COMUNICAZIONE_POLIZIA,
            ricorrente=False
        )

        self.db.add(scadenza_ext)
        self.db.commit()
        self.db.refresh(scadenza)
        self.db.refresh(scadenza_ext)

        logger.info(f"Police deadline created for booking {prenotazione_id}: {deadline_datetime}")
        return scadenza, scadenza_ext

    def generate_istat_monthly_deadline(self, year: int, month: int) -> Tuple[Scadenza, ScadenzaAffittiBrevi]:
        """
        Generate ISTAT monthly report deadline

        Deadline is 15th of the month (for previous month's data).

        Args:
            year: Year
            month: Month (1-12) - the month the report is DUE, not the data month

        Returns:
            Tuple of (core Scadenza, ScadenzaAffittiBrevi extension)
        """
        # ISTAT reports are due on the 15th of the month for previous month
        # e.g., January data is due by February 15th
        deadline_date = date(year, month, 15)

        # Calculate data month (previous month)
        if month == 1:
            data_month = 12
            data_year = year - 1
        else:
            data_month = month - 1
            data_year = year

        # Check if deadline already exists
        existing_ext = self.db.query(ScadenzaAffittiBrevi).join(Scadenza).filter(
            Scadenza.modulo == "affitti_brevi",
            Scadenza.entity_type == "report_istat",
            Scadenza.data_scadenza == deadline_date,
            ScadenzaAffittiBrevi.tipo_scadenza == TipoScadenzaAffittiBrevi.REPORT_ISTAT
        ).first()

        if existing_ext:
            logger.info(f"ISTAT deadline already exists for {year}-{month:02d}")
            scadenza = self.db.query(Scadenza).filter(Scadenza.id == existing_ext.scadenza_id).first()
            return scadenza, existing_ext

        # Calculate next recurrence (next month, 15th)
        if month == 12:
            next_month_date = date(year + 1, 1, 15)
        else:
            next_month_date = date(year, month + 1, 15)

        # Create core Scadenza
        scadenza = Scadenza(
            modulo="affitti_brevi",
            entity_type="report_istat",  # Generic entity type for ISTAT reports
            entity_id=None,  # Not linked to specific entity
            titolo=f"Report ISTAT - Dati {data_year}-{data_month:02d}",
            descrizione=f"Invio report ISTAT per i dati del mese {data_year}-{data_month:02d}. Scadenza: {deadline_date}",
            data_scadenza=deadline_date,
            priorita=PrioritaScadenza.MEDIA,
            stato=StatoScadenza.ATTIVA,
            creato_da=self.current_user_id
        )

        self.db.add(scadenza)
        self.db.flush()

        # Create extension with recurrence info
        scadenza_ext = ScadenzaAffittiBrevi(
            scadenza_id=scadenza.id,
            tipo_scadenza=TipoScadenzaAffittiBrevi.REPORT_ISTAT,
            ricorrente=True,
            frequenza_giorni=30,  # Approximately monthly
            prossima_ricorrenza=next_month_date
        )

        self.db.add(scadenza_ext)
        self.db.commit()
        self.db.refresh(scadenza)
        self.db.refresh(scadenza_ext)

        logger.info(f"ISTAT deadline created for data {data_year}-{data_month:02d}, due {deadline_date}")
        return scadenza, scadenza_ext

    def mark_police_deadline_completed(self, prenotazione_id: int, note: str = None) -> Optional[Scadenza]:
        """
        Mark police communication deadline as completed

        Args:
            prenotazione_id: Booking ID
            note: Completion notes

        Returns:
            Updated Scadenza or None if not found
        """
        # Find scadenza via extension
        scadenza_ext = self.db.query(ScadenzaAffittiBrevi).join(Scadenza).filter(
            Scadenza.modulo == "affitti_brevi",
            Scadenza.entity_type == "prenotazione",
            Scadenza.entity_id == prenotazione_id,
            ScadenzaAffittiBrevi.tipo_scadenza == TipoScadenzaAffittiBrevi.COMUNICAZIONE_POLIZIA
        ).first()

        if not scadenza_ext:
            logger.warning(f"No police deadline found for booking {prenotazione_id}")
            return None

        scadenza = self.db.query(Scadenza).filter(Scadenza.id == scadenza_ext.scadenza_id).first()
        if not scadenza:
            logger.error(f"Core scadenza {scadenza_ext.scadenza_id} not found (data inconsistency)")
            return None

        # Mark as completed (core model pattern)
        scadenza.stato = StatoScadenza.COMPLETATA
        scadenza.completato_da = self.current_user_id
        scadenza.completato_il = datetime.now(timezone.utc)

        # Note: Core doesn't have note_completamento field
        # Could add to description or use ScadenzaLog
        if note:
            scadenza.descrizione = (scadenza.descrizione or "") + f"\n\nNote completamento: {note}"

        self.db.commit()
        self.db.refresh(scadenza)

        logger.info(f"Police deadline {scadenza.id} marked as completed for booking {prenotazione_id}")
        return scadenza

    def generate_next_istat_recurrence(self, scadenza_id: int) -> Optional[Tuple[Scadenza, ScadenzaAffittiBrevi]]:
        """
        Generate next recurrence for ISTAT deadline

        Args:
            scadenza_id: ID of completed ISTAT deadline

        Returns:
            Tuple of (new Scadenza, extension) or None if error
        """
        # Get current deadline and extension
        current = self.db.query(Scadenza).filter(Scadenza.id == scadenza_id).first()
        if not current:
            logger.warning(f"Scadenza {scadenza_id} not found")
            return None

        current_ext = self.db.query(ScadenzaAffittiBrevi).filter(
            ScadenzaAffittiBrevi.scadenza_id == scadenza_id
        ).first()

        if not current_ext or current_ext.tipo_scadenza != TipoScadenzaAffittiBrevi.REPORT_ISTAT:
            logger.warning(f"Invalid ISTAT deadline {scadenza_id}")
            return None

        if not current_ext.ricorrente:
            logger.warning(f"Deadline {scadenza_id} is not recurring")
            return None

        # Get next occurrence date
        next_date = current_ext.prossima_ricorrenza
        if not next_date:
            logger.error(f"No next recurrence set for deadline {scadenza_id}")
            return None

        # Calculate data month (15th is deadline for previous month's data)
        data_month = next_date.month - 1 if next_date.month > 1 else 12
        data_year = next_date.year if next_date.month > 1 else next_date.year - 1

        # Calculate next-next recurrence
        if next_date.month == 12:
            next_next_date = date(next_date.year + 1, 1, 15)
        else:
            next_next_date = date(next_date.year, next_date.month + 1, 15)

        # Update current extension's next recurrence
        current_ext.prossima_ricorrenza = next_next_date
        self.db.commit()

        # Create new deadline for next month
        new_scadenza = Scadenza(
            modulo="affitti_brevi",
            entity_type="report_istat",
            entity_id=None,
            titolo=f"Report ISTAT - Dati {data_year}-{data_month:02d}",
            descrizione=f"Invio report ISTAT per i dati del mese {data_year}-{data_month:02d}. Scadenza: {next_date}",
            data_scadenza=next_date,
            priorita=PrioritaScadenza.MEDIA,
            stato=StatoScadenza.ATTIVA,
            creato_da=self.current_user_id
        )

        self.db.add(new_scadenza)
        self.db.flush()

        new_ext = ScadenzaAffittiBrevi(
            scadenza_id=new_scadenza.id,
            tipo_scadenza=TipoScadenzaAffittiBrevi.REPORT_ISTAT,
            ricorrente=True,
            frequenza_giorni=30,
            prossima_ricorrenza=next_next_date
        )

        self.db.add(new_ext)
        self.db.commit()
        self.db.refresh(new_scadenza)
        self.db.refresh(new_ext)

        logger.info(f"Next ISTAT deadline created for data {data_year}-{data_month:02d}, due {next_date}")
        return new_scadenza, new_ext

    def get_upcoming_deadlines(
        self,
        days_ahead: int = 7,
        tipo: Optional[TipoScadenzaAffittiBrevi] = None
    ) -> List[Tuple[Scadenza, ScadenzaAffittiBrevi]]:
        """
        Get upcoming deadlines within specified days

        Args:
            days_ahead: Number of days to look ahead (default: 7)
            tipo: Filter by affitti_brevi deadline type (optional)

        Returns:
            List of tuples (Scadenza, ScadenzaAffittiBrevi)
        """
        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        query = self.db.query(Scadenza, ScadenzaAffittiBrevi).join(
            ScadenzaAffittiBrevi,
            Scadenza.id == ScadenzaAffittiBrevi.scadenza_id
        ).filter(
            Scadenza.modulo == "affitti_brevi",
            Scadenza.stato == StatoScadenza.ATTIVA,
            Scadenza.data_scadenza >= today,
            Scadenza.data_scadenza <= future_date
        )

        if tipo:
            query = query.filter(ScadenzaAffittiBrevi.tipo_scadenza == tipo)

        results = query.order_by(Scadenza.data_scadenza).all()
        return results

    def get_overdue_deadlines(
        self,
        tipo: Optional[TipoScadenzaAffittiBrevi] = None
    ) -> List[Tuple[Scadenza, ScadenzaAffittiBrevi]]:
        """
        Get overdue deadlines

        Args:
            tipo: Filter by affitti_brevi deadline type (optional)

        Returns:
            List of tuples (Scadenza, ScadenzaAffittiBrevi)
        """
        today = date.today()

        query = self.db.query(Scadenza, ScadenzaAffittiBrevi).join(
            ScadenzaAffittiBrevi,
            Scadenza.id == ScadenzaAffittiBrevi.scadenza_id
        ).filter(
            Scadenza.modulo == "affitti_brevi",
            Scadenza.stato.in_([StatoScadenza.ATTIVA, StatoScadenza.SCADUTA]),
            Scadenza.data_scadenza < today
        )

        if tipo:
            query = query.filter(ScadenzaAffittiBrevi.tipo_scadenza == tipo)

        results = query.order_by(Scadenza.data_scadenza).all()
        return results
