"""
Scadenza Reminder Job

Daily background check across every active tenant: notifies (email only,
see the plan's Global Constraints for why) the creator and recipients of
scadenze entering the "in avvicinamento" window, and re-notifies once when
a scadenza flips to SCADUTA (ScadenzaService.update_overdue_status()
resets the notificato flag for exactly that reason).

Pattern mirrors modules/gestione_pec/services/polling_scheduler.py:
tenant discovery via public.core_tenants, one SessionLocal() per tenant
with search_path set manually (no FastAPI request context here).
"""
from __future__ import annotations

import logging
import threading
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.platform.models import Scadenza, ScadenzaDestinatario, StatoScadenza, CanaleNotifica
from app.core.platform_services.scadenza_service import ScadenzaService
from app.core.platform_services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _notify_and_mark(db: Session, scadenza: Scadenza, tipo: str, titolo: str, corpo: str) -> None:
    """
    Shared notify+mark-notified+commit logic for both the "in avvicinamento"
    and "scaduta" checks. If the scadenza has no explicit destinatari (the
    normal shape for a solo TODO), creates a real ScadenzaDestinatario row
    for the creator first — this is what lets the existing `notificato`
    tracking mechanism cover the creator-only case too, instead of
    re-notifying them every single run with nothing to record that they
    were already told.
    """
    if not scadenza.destinatari:
        creator_destinatario = ScadenzaDestinatario(
            scadenza_id=scadenza.id, user_id=scadenza.creato_da, notificato=False
        )
        db.add(creator_destinatario)
        db.flush()
        candidati = [creator_destinatario]
    else:
        candidati = scadenza.destinatari

    destinatari = [d for d in candidati if not d.notificato]
    user_ids = [d.user_id for d in destinatari]
    if not user_ids:
        return

    NotificationService(db).notify(
        user_ids=user_ids,
        tipo=tipo,
        titolo=titolo,
        corpo=corpo,
        entity_type="scadenza",
        entity_id=scadenza.id,
        link_url=f"/scadenze/{scadenza.id}",
        canali=CanaleNotifica.EMAIL,
    )

    for destinatario in destinatari:
        destinatario.mark_notified()
    db.commit()


def _check_scadenze_in_avvicinamento(db: Session, giorni_prima: int) -> None:
    """Notify (email) every ATTIVA scadenza due within [today, today+giorni_prima]
    whose recipients haven't been notified for this event yet. One failure
    is isolated to its own scadenza and never blocks the rest."""
    soglia = date.today() + timedelta(days=giorni_prima)

    scadenze = (
        db.query(Scadenza)
        .filter(
            Scadenza.stato == StatoScadenza.ATTIVA,
            Scadenza.data_scadenza >= date.today(),
            Scadenza.data_scadenza <= soglia,
        )
        .all()
    )

    for scadenza in scadenze:
        try:
            _notify_and_mark(
                db, scadenza,
                tipo="scadenza.reminder",
                titolo=f"Scadenza in avvicinamento: {scadenza.titolo}",
                corpo=f"La scadenza \"{scadenza.titolo}\" è prevista per il {scadenza.data_scadenza.isoformat()}.",
            )
        except Exception as exc:
            logger.error(
                "[ReminderJob] errore notificando scadenza id=%s: %s",
                scadenza.id, exc, exc_info=True,
            )
            db.rollback()


def _check_scadenze_scadute(db: Session) -> None:
    """
    Notify (email) every SCADUTA scadenza whose recipients haven't been
    notified about the "scaduta" event yet. A scadenza reaches this
    function's scope only once update_overdue_status() has reset its
    recipients' `notificato` flag on the ATTIVA→SCADUTA transition — that
    reset is what makes this a distinct notification from the earlier
    "in avvicinamento" one, not a duplicate. No date window: any SCADUTA
    scadenza not yet notified about being scaduta qualifies, regardless of
    how long ago it expired.
    """
    scadenze = db.query(Scadenza).filter(Scadenza.stato == StatoScadenza.SCADUTA).all()

    for scadenza in scadenze:
        try:
            _notify_and_mark(
                db, scadenza,
                tipo="scadenza.scaduta",
                titolo=f"Scadenza scaduta: {scadenza.titolo}",
                corpo=f"La scadenza \"{scadenza.titolo}\" era prevista per il {scadenza.data_scadenza.isoformat()} ed è scaduta.",
            )
        except Exception as exc:
            logger.error(
                "[ReminderJob] errore notificando scadenza scaduta id=%s: %s",
                scadenza.id, exc, exc_info=True,
            )
            db.rollback()


def run_reminder_check(tenant_schema: str) -> None:
    """Entry point called once per active tenant by ReminderScheduler."""
    from app.core.config import settings

    db = SessionLocal()
    try:
        db.execute(text(f"SET search_path TO {tenant_schema}, public"))
        db.commit()

        ScadenzaService(db).update_overdue_status()
        _check_scadenze_in_avvicinamento(db, giorni_prima=settings.REMINDER_GIORNI_PRIMA)
        _check_scadenze_scadute(db)
    except Exception as exc:
        logger.error("[ReminderJob] %s: errore durante il check: %s", tenant_schema, exc, exc_info=True)
    finally:
        db.close()


def _run_for_all_tenants() -> None:
    db = SessionLocal()
    try:
        tenants = db.execute(
            text("SELECT schema_name FROM public.core_tenants WHERE active = true OR active IS NULL")
        ).fetchall()
    except Exception as exc:
        logger.warning("[ReminderScheduler] impossibile leggere i tenant: %s", exc)
        tenants = []
    finally:
        db.close()

    for row in tenants:
        run_reminder_check(row[0])


class ReminderScheduler:
    """Global daily job (07:00) that runs the reminder check for every active tenant."""

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(
            job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600}
        )
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self.scheduler.add_job(
                func=_run_for_all_tenants,
                trigger=CronTrigger(hour=7, minute=0),
                id="scadenza_reminder_job",
                name="Scadenza Reminder Check",
                replace_existing=True,
            )
            self.scheduler.start()
            self._started = True
            logger.info("[ReminderScheduler] avviato (giornaliero alle 07:00)")

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self.scheduler.shutdown(wait=False)
            self._started = False


_reminder_scheduler: ReminderScheduler | None = None


def get_reminder_scheduler() -> ReminderScheduler:
    global _reminder_scheduler
    if _reminder_scheduler is None:
        _reminder_scheduler = ReminderScheduler()
    return _reminder_scheduler
