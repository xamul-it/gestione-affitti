"""
Sync Routes - API endpoints for iCal synchronization management
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from app.core.database import get_db
from ..services.ical_parser import ICalParser
from ..services.sync_scheduler import get_scheduler

router = APIRouter(prefix="/sync", tags=["Synchronization"])


@router.post("/trigger", response_model=Dict)
def trigger_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger manual iCal synchronization for all active calendars

    Starts a background sync job immediately without waiting for scheduled time.
    """
    try:
        # Get scheduler and trigger manual sync
        scheduler = get_scheduler()

        if not scheduler.is_running:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Sync scheduler is not running"
            )

        scheduler.trigger_manual_sync()

        return {
            "message": "Manual sync triggered successfully",
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger sync: {str(e)}"
        )


@router.post("/calendario/{calendario_id}", response_model=Dict)
def sync_calendario(calendario_id: int, db: Session = Depends(get_db)):
    """
    Synchronize a specific calendario iCal

    Runs synchronization immediately for the specified calendar only.
    Useful for testing or when you need to update a specific calendar.

    Args:
        calendario_id: ID of the calendario to sync
    """
    try:
        parser = ICalParser(db)
        created, updated, error = parser.sync_calendario(calendario_id)

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "calendario_id": calendario_id,
            "prenotazioni_created": created,
            "prenotazioni_updated": updated,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/status", response_model=Dict)
def get_sync_status():
    """
    Get synchronization scheduler status

    Returns information about the scheduler state and next scheduled run.
    """
    try:
        scheduler = get_scheduler()
        status_info = scheduler.get_status()

        return {
            "scheduler": status_info,
            "message": "Scheduler running" if status_info['is_running'] else "Scheduler stopped"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.post("/start", response_model=Dict)
def start_sync_scheduler(interval_hours: int = 6):
    """
    Start the sync scheduler

    Args:
        interval_hours: Sync interval in hours (default: 6)
    """
    try:
        scheduler = get_scheduler(interval_hours)

        if scheduler.is_running:
            return {
                "message": "Scheduler already running",
                "status": scheduler.get_status()
            }

        scheduler.start()

        return {
            "message": f"Scheduler started (interval: {interval_hours} hours)",
            "status": scheduler.get_status()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scheduler: {str(e)}"
        )


@router.post("/stop", response_model=Dict)
def stop_sync_scheduler():
    """
    Stop the sync scheduler

    Stops all scheduled sync jobs.
    """
    try:
        scheduler = get_scheduler()

        if not scheduler.is_running:
            return {
                "message": "Scheduler not running",
                "status": scheduler.get_status()
            }

        scheduler.stop()

        return {
            "message": "Scheduler stopped",
            "status": scheduler.get_status()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop scheduler: {str(e)}"
        )
