"""
Sync Scheduler Service

Background scheduler for automatic iCal synchronization using APScheduler.
Runs synchronization jobs at configurable intervals (default: every 6 hours).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from .ical_sync_service import ICalSyncService

logger = logging.getLogger(__name__)

_EMPTY_STATS = {
    'calendari_processati': 0,
    'prenotazioni_create': 0,
    'prenotazioni_aggiornate': 0,
    'prenotazioni_saltate': 0,
    'errori': 0,
    'dettagli': [],
}


def _sync_tenant(tenant_schema: str) -> dict:
    """
    Run the iCal sync for one tenant.

    Uses ICalSyncService (the implementation routes/sync.py's manual
    "sync now" endpoints also use, and the one SyncAllResponse/SyncResult
    are actually shaped for) rather than the older, parallel ICalParser —
    which targets model/field names (CalendarioIcal.portale,
    Prenotazione.calendario_ical_id/portale_origine) that predate the
    Canale/CalendarioCanale refactor and no longer exist, so any call
    through it fails immediately.

    Binds to a single, explicitly-checked-out Connection for its whole
    lifetime rather than the engine directly: a Session bound to the
    engine returns its connection to the pool on every commit/rollback,
    and the next statement can then land on a *different* pooled
    connection that still carries a stale search_path from a previous
    tenant's run (same hazard app.core.platform_services.
    scadenza_reminder_job.run_reminder_check documents and avoids the
    same way).
    """
    if not tenant_schema.replace('_', '').replace('-', '').isalnum():
        logger.error("Invalid tenant schema, skipping sync: %s", tenant_schema)
        return {**_EMPTY_STATS, 'errori': 1}

    connection = engine.connect()
    try:
        connection.execute(text(f"SET search_path TO {tenant_schema}, public"))
        connection.commit()

        db = Session(bind=connection)
        try:
            return ICalSyncService(db).sync_all_calendari()
        finally:
            db.close()
    except Exception as e:
        logger.error("iCal sync failed for tenant %s: %s", tenant_schema, e, exc_info=True)
        return {**_EMPTY_STATS, 'errori': 1}
    finally:
        connection.close()


def _get_active_tenant_schemas() -> list:
    """Schemas of active tenants that actually have affitti_brevi enabled."""
    from app.core.services.tenant_service import TenantService

    db = SessionLocal()
    try:
        db.connection().execute(text("SET search_path TO public"))
        rows = db.execute(
            text("SELECT id, schema_name FROM public.core_tenants WHERE active = true OR active IS NULL")
        ).fetchall()
        schemas = []
        for tenant_id, schema_name in rows:
            try:
                if "affitti_brevi" in TenantService.get_enabled_modules(tenant_id, db):
                    schemas.append(schema_name)
            except Exception as e:
                logger.warning("Could not check enabled modules for tenant %s: %s", schema_name, e)
        return schemas
    except Exception as e:
        logger.warning("Could not list tenants for iCal sync: %s", e)
        return []
    finally:
        db.close()


class SyncScheduler:
    """
    Background scheduler for iCal synchronization

    Manages automatic sync jobs and provides methods for manual triggering.
    """

    def __init__(self, interval_hours: int = 6):
        """
        Initialize scheduler

        Args:
            interval_hours: Sync interval in hours (default: 6)
        """
        self.scheduler = BackgroundScheduler()
        self.interval_hours = interval_hours
        self.is_running = False

    def sync_job(self):
        """
        Sync job executed by scheduler

        This function is called periodically to sync all active calendars,
        for every active tenant (this is a single global scheduler, not a
        per-request session — it must iterate tenants itself).
        """
        logger.info("Starting scheduled iCal sync job")
        start_time = datetime.now()

        totals = dict(_EMPTY_STATS)
        del totals['dettagli']
        for tenant_schema in _get_active_tenant_schemas():
            stats = _sync_tenant(tenant_schema)
            for key in totals:
                totals[key] += stats.get(key, 0)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Sync job completed in {duration:.2f}s: "
            f"{totals['calendari_processati']} calendars processed, "
            f"{totals['prenotazioni_create']} created, "
            f"{totals['prenotazioni_aggiornate']} updated, "
            f"{totals['errori']} errors"
        )

    def start(self):
        """
        Start the scheduler

        Begins periodic sync jobs at the configured interval.
        """
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        try:
            # Add sync job with interval trigger
            self.scheduler.add_job(
                func=self.sync_job,
                trigger=IntervalTrigger(hours=self.interval_hours),
                id='ical_sync_job',
                name='iCal Synchronization',
                replace_existing=True,
                max_instances=1,  # Only one sync job at a time
                coalesce=True,  # Combine missed runs
            )

            # Start scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info(f"Sync scheduler started (interval: {self.interval_hours} hours)")

            # Run an initial sync soon, but as a one-off job on the
            # scheduler's own background thread rather than calling
            # sync_job() synchronously here: this method is now invoked
            # from register_module(app), which runs at app.main import
            # time (before any ASGI server is listening, and before any
            # process — including the test suite's app fixture — has
            # asked for one) rather than only when the app actually
            # starts serving, so blocking here on real network I/O across
            # every configured calendar would block that import instead.
            self.scheduler.add_job(
                func=self.sync_job,
                id='ical_sync_job_initial',
                name='iCal Synchronization (initial)',
                replace_existing=True,
            )

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """
        Stop the scheduler

        Stops all scheduled jobs and shuts down the scheduler.
        """
        if not self.is_running:
            logger.warning("Scheduler not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Sync scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}", exc_info=True)
            raise

    def trigger_manual_sync(self):
        """
        Trigger a manual sync immediately

        Runs sync job in the background without waiting for scheduled time.
        """
        if not self.is_running:
            logger.warning("Scheduler not running, cannot trigger manual sync")
            return

        try:
            # Add one-off job
            self.scheduler.add_job(
                func=self.sync_job,
                id='manual_sync_job',
                name='Manual iCal Sync',
                replace_existing=True,
            )
            logger.info("Manual sync triggered")
        except Exception as e:
            logger.error(f"Failed to trigger manual sync: {str(e)}", exc_info=True)
            raise

    def get_next_run_time(self) -> datetime:
        """
        Get the next scheduled run time

        Returns:
            Datetime of next scheduled run or None if scheduler not running
        """
        if not self.is_running:
            return None

        job = self.scheduler.get_job('ical_sync_job')
        if job and job.next_run_time:
            return job.next_run_time
        return None

    def get_status(self) -> dict:
        """
        Get scheduler status information

        Returns:
            Dictionary with scheduler status
        """
        next_run = self.get_next_run_time()

        return {
            'is_running': self.is_running,
            'interval_hours': self.interval_hours,
            'next_run_time': next_run.isoformat() if next_run else None,
            'jobs': len(self.scheduler.get_jobs()) if self.is_running else 0
        }


# Global scheduler instance
_scheduler_instance = None


def get_scheduler(interval_hours: int = 6) -> SyncScheduler:
    """
    Get or create global scheduler instance

    Args:
        interval_hours: Sync interval in hours (default: 6)

    Returns:
        Global SyncScheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SyncScheduler(interval_hours)
    return _scheduler_instance


def start_scheduler(interval_hours: int = 6):
    """
    Start the global scheduler

    Args:
        interval_hours: Sync interval in hours (default: 6)
    """
    scheduler = get_scheduler(interval_hours)
    scheduler.start()


def stop_scheduler():
    """
    Stop the global scheduler
    """
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None
