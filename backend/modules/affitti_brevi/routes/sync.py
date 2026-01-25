"""
Sync Routes - API endpoints for iCal synchronization management

Provides:
- Manual sync triggers
- Sync status monitoring
- Per-calendar sync management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional

from app.core.database import get_db
from ..models import CalendarioCanale
from ..services import ICalSyncService
from ..schemas.calendario import SyncResult, SyncAllResponse

router = APIRouter(prefix="/sync", tags=["Synchronization"])


@router.post("/all", response_model=SyncAllResponse)
def sync_all_calendari(db: Session = Depends(get_db)):
    """
    Synchronize all active calendars.

    Triggers immediate sync for all calendars with sync_attiva=True.
    Creates Soggiorno records for new bookings automatically.

    Returns:
        Summary of sync results per calendar
    """
    service = ICalSyncService(db)

    try:
        result = service.sync_all_calendari()
        return SyncAllResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/calendario/{calendario_id}", response_model=SyncResult)
def sync_single_calendario(
    calendario_id: int,
    db: Session = Depends(get_db)
):
    """
    Synchronize a specific calendar.

    Useful for testing or when you need to update a specific calendar immediately.

    Args:
        calendario_id: ID of the CalendarioCanale to sync

    Returns:
        Sync result with counts of created/updated/skipped bookings
    """
    # Verify calendar exists
    calendario = db.query(CalendarioCanale).filter(
        CalendarioCanale.id == calendario_id
    ).first()
    if not calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    if not calendario.url_ical:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Calendario non ha URL iCal configurato"
        )

    service = ICalSyncService(db)

    try:
        result = service.sync_calendario(calendario_id)
        return SyncResult(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/unita/{unita_immobiliare_id}")
def sync_calendari_unita(
    unita_immobiliare_id: int,
    db: Session = Depends(get_db)
):
    """
    Synchronize all calendars for a specific property.

    Syncs all active calendars linked to the property.

    Args:
        unita_immobiliare_id: ID of the property

    Returns:
        Summary of sync results per calendar
    """
    calendari = db.query(CalendarioCanale).filter(
        CalendarioCanale.unita_immobiliare_id == unita_immobiliare_id,
        CalendarioCanale.attivo == True,
        CalendarioCanale.sync_attiva == True
    ).all()

    if not calendari:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessun calendario attivo trovato per unità {unita_immobiliare_id}"
        )

    service = ICalSyncService(db)
    results = []

    for calendario in calendari:
        if calendario.url_ical:
            try:
                result = service.sync_calendario(calendario.id)
                results.append(result)
            except Exception as e:
                results.append({
                    "calendario_id": calendario.id,
                    "canale": calendario.canale.codice if calendario.canale else "UNKNOWN",
                    "create": 0,
                    "aggiornate": 0,
                    "saltate": 0,
                    "errore": str(e)
                })

    totale_create = sum(r.get("create", 0) for r in results)
    totale_aggiornate = sum(r.get("aggiornate", 0) for r in results)
    errori = sum(1 for r in results if r.get("errore"))

    return {
        "unita_immobiliare_id": unita_immobiliare_id,
        "calendari_processati": len(results),
        "prenotazioni_create": totale_create,
        "prenotazioni_aggiornate": totale_aggiornate,
        "errori": errori,
        "dettagli": results
    }


@router.get("/status")
def get_sync_status(db: Session = Depends(get_db)):
    """
    Get overall synchronization status.

    Returns:
        Summary of sync state for all calendars
    """
    calendari = db.query(CalendarioCanale).filter(
        CalendarioCanale.attivo == True
    ).all()

    stati = {
        "MAI_SINCRONIZZATO": 0,
        "OK": 0,
        "ERRORE": 0,
        "IN_CORSO": 0
    }

    problemi = []

    for cal in calendari:
        if not cal.ultima_sincronizzazione:
            stati["MAI_SINCRONIZZATO"] += 1
            problemi.append({
                "calendario_id": cal.id,
                "unita_immobiliare_id": cal.unita_immobiliare_id,
                "canale": cal.canale.codice if cal.canale else "UNKNOWN",
                "problema": "Mai sincronizzato"
            })
        elif cal.stato_sincronizzazione == "ERRORE":
            stati["ERRORE"] += 1
            problemi.append({
                "calendario_id": cal.id,
                "unita_immobiliare_id": cal.unita_immobiliare_id,
                "canale": cal.canale.codice if cal.canale else "UNKNOWN",
                "problema": cal.errore_sincronizzazione or "Errore sconosciuto"
            })
        elif cal.stato_sincronizzazione == "IN_CORSO":
            stati["IN_CORSO"] += 1
        else:
            stati["OK"] += 1

    return {
        "totale_calendari": len(calendari),
        "stati": stati,
        "problemi": problemi,
        "sync_attiva": sum(1 for c in calendari if c.sync_attiva)
    }


@router.get("/calendario/{calendario_id}/status")
def get_calendario_sync_status(
    calendario_id: int,
    db: Session = Depends(get_db)
):
    """
    Get sync status for a specific calendar.

    Returns detailed sync information including last sync time and errors.
    """
    calendario = db.query(CalendarioCanale).filter(
        CalendarioCanale.id == calendario_id
    ).first()

    if not calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    return {
        "calendario_id": calendario.id,
        "unita_immobiliare_id": calendario.unita_immobiliare_id,
        "canale": calendario.canale.codice if calendario.canale else None,
        "url_ical": calendario.url_ical,
        "sync_attiva": calendario.sync_attiva,
        "intervallo_sync_ore": calendario.intervallo_sync_ore,
        "stato_sincronizzazione": calendario.stato_sincronizzazione,
        "ultima_sincronizzazione": calendario.ultima_sincronizzazione,
        "errore_sincronizzazione": calendario.errore_sincronizzazione,
        "prenotazioni_importate": calendario.prenotazioni_importate
    }


@router.post("/calendario/{calendario_id}/attiva")
def attiva_sync_calendario(
    calendario_id: int,
    db: Session = Depends(get_db)
):
    """Enable automatic sync for a calendar."""
    calendario = db.query(CalendarioCanale).filter(
        CalendarioCanale.id == calendario_id
    ).first()

    if not calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    calendario.sync_attiva = True
    db.commit()

    return {"message": "Sync attivata", "calendario_id": calendario_id}


@router.post("/calendario/{calendario_id}/disattiva")
def disattiva_sync_calendario(
    calendario_id: int,
    db: Session = Depends(get_db)
):
    """Disable automatic sync for a calendar."""
    calendario = db.query(CalendarioCanale).filter(
        CalendarioCanale.id == calendario_id
    ).first()

    if not calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    calendario.sync_attiva = False
    db.commit()

    return {"message": "Sync disattivata", "calendario_id": calendario_id}


@router.post("/calendario/{calendario_id}/reset-errore")
def reset_sync_errore(
    calendario_id: int,
    db: Session = Depends(get_db)
):
    """
    Reset sync error status for a calendar.

    Use after fixing the underlying issue to clear error state.
    """
    calendario = db.query(CalendarioCanale).filter(
        CalendarioCanale.id == calendario_id
    ).first()

    if not calendario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendario con ID {calendario_id} non trovato"
        )

    calendario.stato_sincronizzazione = "MAI_SINCRONIZZATO"
    calendario.errore_sincronizzazione = None
    db.commit()

    return {"message": "Errore resettato", "calendario_id": calendario_id}
