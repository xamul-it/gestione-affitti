"""
Sync Scheduler Service

Background scheduler for automatic iCal synchronization using APScheduler.
Runs synchronization jobs at configurable intervals (default: every 6 hours).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

from app.core.database import SessionLocal
from .ical_parser import ICalParser

logger = logging.getLogger(__name__)


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

        This function is called periodically to sync all active calendars.
        """
        logger.info("Starting scheduled iCal sync job")
        start_time = datetime.now()

        # Create database session
        db = SessionLocal()
        try:
            # Create parser and sync all calendars
            parser = ICalParser(db)
            stats = parser.sync_all_calendari()

            # Log results
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Sync job completed in {duration:.2f}s: "
                f"{stats['calendari_processed']} calendars processed, "
                f"{stats['prenotazioni_created']} created, "
                f"{stats['prenotazioni_updated']} updated, "
                f"{stats['errors']} errors"
            )

        except Exception as e:
            logger.error(f"Sync job failed: {str(e)}", exc_info=True)
        finally:
            db.close()

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

            # Run initial sync immediately
            logger.info("Running initial sync...")
            self.sync_job()

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
