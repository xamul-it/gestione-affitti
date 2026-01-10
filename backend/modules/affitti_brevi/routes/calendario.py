"""
Calendario Routes - Multi-platform calendar view endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Optional
from datetime import date, timedelta
from app.core.database import get_db
from ..models import CalendarioIcal, Prenotazione, BloccoCalendario
from ..models.prenotazione import StatoPrenotazione
from ..services.cache_service import get_cache, cache_key

router = APIRouter(prefix="/calendario", tags=["Calendario"])


@router.get("/overview")
def get_calendar_overview(
    data_inizio: date = Query(..., description="Start date (YYYY-MM-DD)"),
    data_fine: date = Query(..., description="End date (YYYY-MM-DD)"),
    immobile_ids: Optional[List[int]] = Query(None, description="Filter by property IDs"),
    db: Session = Depends(get_db)
):
    """
    Get multi-platform calendar overview

    Returns a matrix of property × date × platform with booking status.
    Each cell contains the status: PRENOTATO, LIBERO, or CHIUSO.

    Args:
        data_inizio: Start date for calendar view
        data_fine: End date for calendar view
        immobile_ids: Optional list of property IDs to filter

    Returns:
        List of calendar entries with date, immobile_id, portale, stato, and booking info
    """

    # Check cache first (1 hour TTL)
    cache = get_cache()
    immobile_key = ','.join(str(id) for id in sorted(immobile_ids)) if immobile_ids else 'all'
    cache_k = cache_key('calendario', 'overview', data_inizio.isoformat(), data_fine.isoformat(), immobile_key)

    cached_result = cache.get(cache_k)
    if cached_result is not None:
        return cached_result

    # Generate date range
    date_range = []
    current_date = data_inizio
    while current_date <= data_fine:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    # Get all calendario configurations (active properties with iCal configs)
    query = db.query(CalendarioIcal).filter(CalendarioIcal.attivo == True)

    if immobile_ids:
        query = query.filter(CalendarioIcal.unita_immobiliare_id.in_(immobile_ids))

    calendari = query.all()

    # Build result
    result = []

    for calendario in calendari:
        for current_date in date_range:
            # Check for booking on this date/property/platform
            prenotazione = db.query(Prenotazione).filter(
                Prenotazione.unita_immobiliare_id == calendario.unita_immobiliare_id,
                Prenotazione.portale_origine.in_([
                    calendario.portale.value.replace('_', '_') if hasattr(calendario.portale, 'value') else calendario.portale
                ]),
                Prenotazione.data_checkin <= current_date,
                Prenotazione.data_checkout > current_date,
                Prenotazione.stato != StatoPrenotazione.CANCELLATA
            ).first()

            # Check for calendar block on this date/property/platform
            blocco = db.query(BloccoCalendario).filter(
                BloccoCalendario.immobile_id == calendario.unita_immobiliare_id,
                or_(
                    BloccoCalendario.portale == calendario.portale.value if hasattr(calendario.portale, 'value') else calendario.portale,
                    BloccoCalendario.portale == 'TUTTI'
                ),
                BloccoCalendario.data_inizio <= current_date,
                BloccoCalendario.data_fine >= current_date
            ).first()

            # Determine status
            if prenotazione:
                stato = "PRENOTATO"
                entry = {
                    "data": current_date.isoformat(),
                    "immobile_id": calendario.unita_immobiliare_id,
                    "portale": calendario.portale.value if hasattr(calendario.portale, 'value') else calendario.portale,
                    "stato": stato,
                    "prenotazione_id": prenotazione.id,
                    "codice_prenotazione": prenotazione.codice_prenotazione,
                    "numero_ospiti": prenotazione.numero_ospiti,
                    "prezzo_totale": float(prenotazione.prezzo_totale) if prenotazione.prezzo_totale else None
                }
            elif blocco:
                stato = "CHIUSO"
                entry = {
                    "data": current_date.isoformat(),
                    "immobile_id": calendario.unita_immobiliare_id,
                    "portale": calendario.portale.value if hasattr(calendario.portale, 'value') else calendario.portale,
                    "stato": stato,
                    "blocco_id": blocco.id,
                    "tipo_blocco": blocco.tipo_blocco.value if hasattr(blocco.tipo_blocco, 'value') else blocco.tipo_blocco,
                    "motivo": blocco.motivo
                }
            else:
                stato = "LIBERO"
                entry = {
                    "data": current_date.isoformat(),
                    "immobile_id": calendario.unita_immobiliare_id,
                    "portale": calendario.portale.value if hasattr(calendario.portale, 'value') else calendario.portale,
                    "stato": stato
                }

            result.append(entry)

    # Cache result for 1 hour (3600 seconds)
    cache.set(cache_k, result, ttl_seconds=3600)

    return result


@router.get("/conflicts")
def get_calendar_conflicts(
    data_inizio: Optional[date] = Query(None, description="Start date for conflict detection"),
    data_fine: Optional[date] = Query(None, description="End date for conflict detection"),
    immobile_id: Optional[int] = Query(None, description="Filter by property ID"),
    db: Session = Depends(get_db)
):
    """
    Detect booking conflicts (same property booked on multiple platforms for same date)

    Returns a list of conflicts with details about overlapping bookings.

    Args:
        data_inizio: Optional start date for conflict detection
        data_fine: Optional end date for conflict detection
        immobile_id: Optional property ID to check

    Returns:
        List of conflicts with property, date, and conflicting bookings
    """

    # Query for overlapping bookings
    query = db.query(Prenotazione).filter(
        Prenotazione.stato != StatoPrenotazione.CANCELLATA
    )

    if immobile_id:
        query = query.filter(Prenotazione.unita_immobiliare_id == immobile_id)

    if data_inizio:
        query = query.filter(Prenotazione.data_checkout > data_inizio)

    if data_fine:
        query = query.filter(Prenotazione.data_checkin < data_fine)

    prenotazioni = query.order_by(
        Prenotazione.unita_immobiliare_id,
        Prenotazione.data_checkin
    ).all()

    # Detect conflicts
    conflicts = []
    checked = set()

    for i, pren1 in enumerate(prenotazioni):
        for pren2 in prenotazioni[i+1:]:
            # Skip if different properties
            if pren1.unita_immobiliare_id != pren2.unita_immobiliare_id:
                continue

            # Skip if same platform (not a conflict, just duplicate data)
            if pren1.portale_origine == pren2.portale_origine:
                continue

            # Check for date overlap
            if pren1.data_checkin < pren2.data_checkout and pren2.data_checkin < pren1.data_checkout:
                conflict_key = tuple(sorted([pren1.id, pren2.id]))

                if conflict_key not in checked:
                    checked.add(conflict_key)

                    # Calculate overlap period
                    overlap_start = max(pren1.data_checkin, pren2.data_checkin)
                    overlap_end = min(pren1.data_checkout, pren2.data_checkout)
                    overlap_days = (overlap_end - overlap_start).days

                    conflicts.append({
                        "immobile_id": pren1.unita_immobiliare_id,
                        "overlap_start": overlap_start.isoformat(),
                        "overlap_end": overlap_end.isoformat(),
                        "overlap_days": overlap_days,
                        "prenotazioni": [
                            {
                                "id": pren1.id,
                                "codice": pren1.codice_prenotazione,
                                "portale": pren1.portale_origine.value if hasattr(pren1.portale_origine, 'value') else pren1.portale_origine,
                                "checkin": pren1.data_checkin.isoformat(),
                                "checkout": pren1.data_checkout.isoformat(),
                                "stato": pren1.stato.value if hasattr(pren1.stato, 'value') else pren1.stato
                            },
                            {
                                "id": pren2.id,
                                "codice": pren2.codice_prenotazione,
                                "portale": pren2.portale_origine.value if hasattr(pren2.portale_origine, 'value') else pren2.portale_origine,
                                "checkin": pren2.data_checkin.isoformat(),
                                "checkout": pren2.data_checkout.isoformat(),
                                "stato": pren2.stato.value if hasattr(pren2.stato, 'value') else pren2.stato
                            }
                        ]
                    })

    return {
        "total_conflicts": len(conflicts),
        "conflicts": conflicts
    }


@router.post("/resolve-conflict/{prenotazione_id}")
def resolve_conflict(
    prenotazione_id: int,
    action: str = Query(..., description="Action: 'keep' or 'cancel'"),
    db: Session = Depends(get_db)
):
    """
    Resolve a booking conflict by canceling one of the conflicting bookings

    Args:
        prenotazione_id: ID of the booking to act on
        action: 'keep' (do nothing) or 'cancel' (cancel this booking)

    Returns:
        Updated booking status
    """

    prenotazione = db.query(Prenotazione).filter(Prenotazione.id == prenotazione_id).first()

    if not prenotazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenotazione {prenotazione_id} not found"
        )

    if action == "cancel":
        prenotazione.stato = StatoPrenotazione.CANCELLATA
        db.commit()
        db.refresh(prenotazione)

        return {
            "prenotazione_id": prenotazione_id,
            "action": "canceled",
            "nuovo_stato": prenotazione.stato.value if hasattr(prenotazione.stato, 'value') else prenotazione.stato
        }
    elif action == "keep":
        return {
            "prenotazione_id": prenotazione_id,
            "action": "kept",
            "stato": prenotazione.stato.value if hasattr(prenotazione.stato, 'value') else prenotazione.stato
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Use 'keep' or 'cancel'"
        )
