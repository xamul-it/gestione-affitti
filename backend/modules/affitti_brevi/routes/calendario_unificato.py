"""
Calendario Unificato Routes - Unified Calendar API Endpoints

Provides the unified calendar view as specified in the analysis:
- Single calendar per property aggregating all channels
- Per-channel status visible in same view
- Conflict detection and resolution
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.core.database import get_db
from ..services import CalendarioUnificatoService
from ..schemas.calendario import (
    CalendarioOverviewResponse,
    RisolviConflittoRequest,
)

router = APIRouter(prefix="/calendario-unificato", tags=["Calendario Unificato"])
legacy_router = APIRouter(prefix="/calendario", tags=["Calendario"])


@router.get("/overview", response_model=CalendarioOverviewResponse)
@legacy_router.get("/overview", response_model=CalendarioOverviewResponse)
def get_calendario_overview(
    data_inizio: date = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fine: date = Query(..., description="End date (YYYY-MM-DD)"),
    unita_immobiliare_ids: Optional[List[int]] = Query(
        None, description="Filter by property IDs"
    ),
    include_dettagli: bool = Query(True, description="Include booking details"),
    db: Session = Depends(get_db)
):
    """
    Get unified calendar overview.

    Returns a comprehensive view of the calendar for the specified period:
    - Legend with channel colors and symbols
    - Per-property daily status for each channel
    - Aggregate status (LIBERO, OCCUPATO, NON_DISPONIBILE, CONFLITTO)
    - Detected conflicts requiring action

    The calendar follows the visual conventions from the analysis:
    - A (red) = Airbnb
    - B (blue) = Booking.com
    - D (green) = Direct
    - ○ = Available (border only)
    - ● = Booked (filled)
    - ✕ = Closed/unavailable
    """
    if data_fine < data_inizio:
        raise HTTPException(status_code=400, detail="data_fine must be >= data_inizio")

    if (data_fine - data_inizio).days > 90:
        raise HTTPException(
            status_code=400,
            detail="Period cannot exceed 90 days"
        )

    service = CalendarioUnificatoService(db)
    return service.get_calendario_overview(
        data_inizio=data_inizio,
        data_fine=data_fine,
        unita_immobiliare_ids=unita_immobiliare_ids,
        include_dettagli=include_dettagli
    )


@router.get("/disponibilita/{unita_immobiliare_id}")
@legacy_router.get("/disponibilita/{unita_immobiliare_id}")
def get_disponibilita_proprieta(
    unita_immobiliare_id: int,
    data_inizio: date = Query(..., description="Start date"),
    data_fine: date = Query(..., description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get availability for a specific property.

    Returns day-by-day availability status for the property.
    """
    if data_fine < data_inizio:
        raise HTTPException(status_code=400, detail="data_fine must be >= data_inizio")

    service = CalendarioUnificatoService(db)
    return service.get_disponibilita_proprieta(
        unita_immobiliare_id=unita_immobiliare_id,
        data_inizio=data_inizio,
        data_fine=data_fine
    )


@router.get("/conflitti")
@legacy_router.get("/conflitti")
def get_conflitti(
    data_inizio: Optional[date] = Query(None, description="Start date filter"),
    data_fine: Optional[date] = Query(None, description="End date filter"),
    unita_immobiliare_id: Optional[int] = Query(None, description="Property filter"),
    db: Session = Depends(get_db)
):
    """
    Get booking conflicts.

    Detects overlapping bookings on different channels for the same property.
    Conflicts require manual resolution (choosing which booking to keep).
    """
    service = CalendarioUnificatoService(db)
    conflitti = service.get_conflitti(
        data_inizio=data_inizio,
        data_fine=data_fine,
        unita_immobiliare_id=unita_immobiliare_id
    )

    return {
        "totale": len(conflitti),
        "conflitti": conflitti
    }


@router.post("/conflitti/risolvi")
@legacy_router.post("/conflitti/risolvi")
def risolvi_conflitto(
    request: RisolviConflittoRequest,
    db: Session = Depends(get_db)
):
    """
    Resolve a booking conflict.

    Keeps one booking and cancels the other.
    The cancelled booking's Soggiorno will be marked as invalid.

    Args:
        prenotazione_id_da_mantenere: ID of booking to keep
        prenotazione_id_da_cancellare: ID of booking to cancel

    Returns:
        Resolution result
    """
    service = CalendarioUnificatoService(db)

    try:
        result = service.risolvi_conflitto(
            prenotazione_id_da_mantenere=request.prenotazione_id_da_mantenere,
            prenotazione_id_da_cancellare=request.prenotazione_id_da_cancellare
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/oggi")
@legacy_router.get("/oggi")
def get_calendario_oggi(
    unita_immobiliare_ids: Optional[List[int]] = Query(
        None, description="Filter by property IDs"
    ),
    db: Session = Depends(get_db)
):
    """
    Get calendar status for today.

    Quick overview of today's status for all properties.
    """
    oggi = date.today()
    service = CalendarioUnificatoService(db)
    return service.get_calendario_overview(
        data_inizio=oggi,
        data_fine=oggi,
        unita_immobiliare_ids=unita_immobiliare_ids,
        include_dettagli=True
    )


@router.get("/settimana")
@legacy_router.get("/settimana")
def get_calendario_settimana(
    unita_immobiliare_ids: Optional[List[int]] = Query(
        None, description="Filter by property IDs"
    ),
    db: Session = Depends(get_db)
):
    """
    Get calendar status for current week.

    Overview from today to 7 days ahead.
    """
    oggi = date.today()
    fine = oggi + timedelta(days=7)
    service = CalendarioUnificatoService(db)
    return service.get_calendario_overview(
        data_inizio=oggi,
        data_fine=fine,
        unita_immobiliare_ids=unita_immobiliare_ids,
        include_dettagli=True
    )


@router.get("/mese")
@legacy_router.get("/mese")
def get_calendario_mese(
    anno: int = Query(..., ge=2020, le=2100, description="Year"),
    mese: int = Query(..., ge=1, le=12, description="Month"),
    unita_immobiliare_ids: Optional[List[int]] = Query(
        None, description="Filter by property IDs"
    ),
    db: Session = Depends(get_db)
):
    """
    Get calendar status for a specific month.

    Full month view for planning and overview.
    """
    from calendar import monthrange

    _, ultimo_giorno = monthrange(anno, mese)
    data_inizio = date(anno, mese, 1)
    data_fine = date(anno, mese, ultimo_giorno)

    service = CalendarioUnificatoService(db)
    return service.get_calendario_overview(
        data_inizio=data_inizio,
        data_fine=data_fine,
        unita_immobiliare_ids=unita_immobiliare_ids,
        include_dettagli=True
    )
