"""
Affitti Brevi Module - Short-Term Rental Management

This module provides comprehensive management for short-term rentals including:
- iCal synchronization from Booking.com, Airbnb, Vrbo
- Multi-platform calendar with conflict detection
- Guest and booking management
- Tourist tax calculation
- Legal deadline management (Police, ISTAT)
"""
from .__manifest__ import manifest

__all__ = ["manifest"]

def register_module(app):
    """Called by module loader to register routes and services"""
    from .routes import calendari, prenotazioni, ospiti, sync, calendario, tasse, scadenze
    from .services.sync_scheduler import start_scheduler

    # Register routes
    app.include_router(calendari.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])
    app.include_router(prenotazioni.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])
    app.include_router(ospiti.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])
    app.include_router(sync.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])
    app.include_router(calendario.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])
    app.include_router(tasse.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])
    app.include_router(scadenze.router, prefix="/api/v1/affitti-brevi", tags=["affitti_brevi"])

    # Start iCal sync scheduler (default: every 6 hours)
    try:
        start_scheduler(interval_hours=6)
        print("[Affitti Brevi] iCal sync scheduler started (interval: 6 hours)")
    except Exception as e:
        print(f"[Affitti Brevi] Warning: Failed to start sync scheduler: {str(e)}")

    print("[Affitti Brevi] Module registered successfully!")
