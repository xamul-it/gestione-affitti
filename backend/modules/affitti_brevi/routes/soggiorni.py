"""
Soggiorni Routes - API endpoints for stay management

Handles the operational aspect of short-term rentals:
- Check-in / check-out
- Guest registration
- Data collection for mandatory communications
- Self-service token management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.core.database import get_db
from ..models import Soggiorno, OspiteSoggiorno, Prenotazione
from ..models.soggiorno import StatoSoggiorno
from ..schemas.soggiorno import (
    SoggiornoCreate,
    SoggiornoUpdate,
    SoggiornoResponse,
    SoggiornoListResponse,
    SoggiornoFilterParams,
    OspiteCreate,
    OspiteUpdate,
    OspiteResponse,
    CheckinRequest,
    VerificaCompletezzaResponse,
    SelfServiceTokenResponse,
)
from ..services import SoggiornoService

router = APIRouter(prefix="/soggiorni", tags=["Soggiorni"])


# ==================== Soggiorno Endpoints ====================

@router.get("/", response_model=SoggiornoListResponse)
def get_soggiorni(
    unita_immobiliare_id: Optional[int] = Query(None, description="Filter by property"),
    data_checkin_da: Optional[date] = Query(None, description="Check-in from date"),
    data_checkin_a: Optional[date] = Query(None, description="Check-in to date"),
    stato: Optional[str] = Query(None, description="Filter by status"),
    valido: Optional[bool] = Query(True, description="Filter by validity"),
    richiede_azione: Optional[bool] = Query(None, description="Filter by action required"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get list of stays with optional filters.

    Returns paginated list with computed fields:
    - notti: Number of nights
    - is_in_corso: Currently active stay
    - richiede_azione: Needs operator attention
    """
    query = db.query(Soggiorno)

    if unita_immobiliare_id is not None:
        query = query.filter(Soggiorno.unita_immobiliare_id == unita_immobiliare_id)
    if data_checkin_da is not None:
        query = query.filter(Soggiorno.data_checkin >= data_checkin_da)
    if data_checkin_a is not None:
        query = query.filter(Soggiorno.data_checkin <= data_checkin_a)
    if stato is not None:
        query = query.filter(Soggiorno.stato == stato)
    if valido is not None:
        query = query.filter(Soggiorno.valido == valido)

    totale = query.count()
    soggiorni = query.order_by(Soggiorno.data_checkin.desc()).offset(skip).limit(limit).all()

    # Apply computed fields filter if needed
    if richiede_azione is not None:
        # Filter in Python as it requires computed logic
        result = []
        for s in soggiorni:
            requires_action = _check_richiede_azione(s)
            if requires_action == richiede_azione:
                result.append(s)
        soggiorni = result

    return SoggiornoListResponse(
        soggiorni=soggiorni,
        totale=totale,
        skip=skip,
        limit=limit
    )


@router.get("/oggi")
def get_soggiorni_oggi(db: Session = Depends(get_db)):
    """
    Get today's stays overview.

    Returns:
    - checkin_oggi: Stays with check-in today
    - checkout_oggi: Stays with check-out today
    - in_corso: Currently active stays
    """
    oggi = date.today()
    service = SoggiornoService(db)

    checkin_oggi = db.query(Soggiorno).filter(
        Soggiorno.data_checkin == oggi,
        Soggiorno.valido == True
    ).all()

    checkout_oggi = db.query(Soggiorno).filter(
        Soggiorno.data_checkout == oggi,
        Soggiorno.valido == True
    ).all()

    in_corso = db.query(Soggiorno).filter(
        Soggiorno.stato == StatoSoggiorno.IN_CORSO.value,
        Soggiorno.valido == True
    ).all()

    return {
        "data": str(oggi),
        "checkin_oggi": {
            "totale": len(checkin_oggi),
            "soggiorni": checkin_oggi
        },
        "checkout_oggi": {
            "totale": len(checkout_oggi),
            "soggiorni": checkout_oggi
        },
        "in_corso": {
            "totale": len(in_corso),
            "soggiorni": in_corso
        }
    }


@router.get("/richiede-azione")
def get_soggiorni_richiede_azione(db: Session = Depends(get_db)):
    """
    Get stays that require operator action.

    Includes:
    - Missing guest data before deadline
    - Incomplete documents
    - Pending check-ins
    """
    soggiorni = db.query(Soggiorno).filter(
        Soggiorno.valido == True,
        Soggiorno.stato.in_([
            StatoSoggiorno.CREATO.value,
            StatoSoggiorno.DATI_PARZIALI.value,
            StatoSoggiorno.IN_CORSO.value
        ])
    ).all()

    richiede_azione = []
    for s in soggiorni:
        motivi = _get_motivi_azione(s)
        if motivi:
            richiede_azione.append({
                "soggiorno": s,
                "motivi": motivi
            })

    return {
        "totale": len(richiede_azione),
        "soggiorni": richiede_azione
    }


@router.get("/{soggiorno_id}", response_model=SoggiornoResponse)
def get_soggiorno(soggiorno_id: int, db: Session = Depends(get_db)):
    """Get stay details with guests."""
    soggiorno = db.query(Soggiorno).filter(Soggiorno.id == soggiorno_id).first()
    if not soggiorno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soggiorno con ID {soggiorno_id} non trovato"
        )
    return soggiorno


@router.post("/", response_model=SoggiornoResponse, status_code=status.HTTP_201_CREATED)
def create_soggiorno(soggiorno: SoggiornoCreate, db: Session = Depends(get_db)):
    """
    Create a new stay manually.

    Note: Stays are typically created automatically when bookings are imported.
    Use this for manual bookings or testing.
    """
    # Verify booking exists
    prenotazione = db.query(Prenotazione).filter(
        Prenotazione.id == soggiorno.prenotazione_id
    ).first()
    if not prenotazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenotazione con ID {soggiorno.prenotazione_id} non trovata"
        )

    # Check if soggiorno already exists for this booking
    existing = db.query(Soggiorno).filter(
        Soggiorno.prenotazione_id == soggiorno.prenotazione_id,
        Soggiorno.valido == True
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Soggiorno già esistente per questa prenotazione"
        )

    new_soggiorno = Soggiorno(**soggiorno.model_dump())
    db.add(new_soggiorno)
    db.commit()
    db.refresh(new_soggiorno)
    return new_soggiorno


@router.put("/{soggiorno_id}", response_model=SoggiornoResponse)
def update_soggiorno(
    soggiorno_id: int,
    soggiorno: SoggiornoUpdate,
    db: Session = Depends(get_db)
):
    """Update stay data."""
    db_soggiorno = db.query(Soggiorno).filter(Soggiorno.id == soggiorno_id).first()
    if not db_soggiorno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soggiorno con ID {soggiorno_id} non trovato"
        )

    update_data = soggiorno.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_soggiorno, field, value)

    db.commit()
    db.refresh(db_soggiorno)
    return db_soggiorno


# ==================== Check-in / Check-out Endpoints ====================

@router.post("/{soggiorno_id}/checkin", response_model=SoggiornoResponse)
def esegui_checkin(
    soggiorno_id: int,
    request: CheckinRequest,
    db: Session = Depends(get_db)
):
    """
    Execute check-in for a stay.

    Requirements:
    - At least one guest registered
    - Main guest document data complete

    The check-in:
    - Updates stato to IN_CORSO
    - Records actual check-in timestamp
    - Triggers police communication deadline (24h)
    """
    service = SoggiornoService(db)

    try:
        soggiorno = service.esegui_checkin(
            soggiorno_id=soggiorno_id,
            numero_ospiti_effettivi=request.numero_ospiti_effettivi
        )
        return soggiorno
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{soggiorno_id}/checkout", response_model=SoggiornoResponse)
def esegui_checkout(soggiorno_id: int, db: Session = Depends(get_db)):
    """
    Execute check-out for a stay.

    The check-out:
    - Updates stato to COMPLETATO
    - Records actual check-out timestamp
    - Finalizes tourist tax calculation
    """
    service = SoggiornoService(db)

    try:
        soggiorno = service.esegui_checkout(soggiorno_id)
        return soggiorno
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Guest Registration Endpoints ====================

@router.get("/{soggiorno_id}/ospiti", response_model=List[OspiteResponse])
def get_ospiti_soggiorno(soggiorno_id: int, db: Session = Depends(get_db)):
    """Get all guests for a stay."""
    soggiorno = db.query(Soggiorno).filter(Soggiorno.id == soggiorno_id).first()
    if not soggiorno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soggiorno con ID {soggiorno_id} non trovato"
        )

    ospiti = db.query(OspiteSoggiorno).filter(
        OspiteSoggiorno.soggiorno_id == soggiorno_id
    ).order_by(OspiteSoggiorno.principale.desc(), OspiteSoggiorno.id).all()

    return ospiti


@router.post("/{soggiorno_id}/ospiti", response_model=OspiteResponse, status_code=status.HTTP_201_CREATED)
def registra_ospite(
    soggiorno_id: int,
    ospite: OspiteCreate,
    db: Session = Depends(get_db)
):
    """
    Register a guest for a stay.

    The first guest is automatically set as principale (main guest).
    Main guest requires complete document data for police communication.
    """
    service = SoggiornoService(db)

    try:
        nuovo_ospite = service.registra_ospite(
            soggiorno_id=soggiorno_id,
            dati_ospite=ospite.model_dump(),
            principale=ospite.principale
        )
        return nuovo_ospite
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{soggiorno_id}/ospiti/{ospite_id}", response_model=OspiteResponse)
def update_ospite(
    soggiorno_id: int,
    ospite_id: int,
    ospite: OspiteUpdate,
    db: Session = Depends(get_db)
):
    """Update guest data."""
    db_ospite = db.query(OspiteSoggiorno).filter(
        OspiteSoggiorno.id == ospite_id,
        OspiteSoggiorno.soggiorno_id == soggiorno_id
    ).first()

    if not db_ospite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ospite con ID {ospite_id} non trovato per soggiorno {soggiorno_id}"
        )

    update_data = ospite.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ospite, field, value)

    # Update stato_documento based on completeness
    if _dati_documento_completi(db_ospite):
        db_ospite.stato_documento = "COMPLETO"
    elif db_ospite.tipo_documento or db_ospite.numero_documento:
        db_ospite.stato_documento = "PARZIALE"

    db.commit()
    db.refresh(db_ospite)
    return db_ospite


@router.delete("/{soggiorno_id}/ospiti/{ospite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ospite(
    soggiorno_id: int,
    ospite_id: int,
    db: Session = Depends(get_db)
):
    """Remove a guest from a stay."""
    db_ospite = db.query(OspiteSoggiorno).filter(
        OspiteSoggiorno.id == ospite_id,
        OspiteSoggiorno.soggiorno_id == soggiorno_id
    ).first()

    if not db_ospite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ospite con ID {ospite_id} non trovato per soggiorno {soggiorno_id}"
        )

    # Don't allow deleting main guest if other guests exist
    if db_ospite.principale:
        other_guests = db.query(OspiteSoggiorno).filter(
            OspiteSoggiorno.soggiorno_id == soggiorno_id,
            OspiteSoggiorno.id != ospite_id
        ).count()
        if other_guests > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Non è possibile rimuovere l'ospite principale se ci sono altri ospiti registrati"
            )

    db.delete(db_ospite)
    db.commit()
    return None


# ==================== Data Verification Endpoints ====================

@router.get("/{soggiorno_id}/verifica-completezza", response_model=VerificaCompletezzaResponse)
def verifica_completezza(soggiorno_id: int, db: Session = Depends(get_db)):
    """
    Verify data completeness for a stay.

    Returns:
    - completo: True if all required data is present
    - ospiti_registrati: Number of registered guests
    - ospiti_previsti: Expected number of guests
    - mancanti: List of missing data items
    """
    service = SoggiornoService(db)

    try:
        result = service.verifica_completezza_dati(soggiorno_id)
        return VerificaCompletezzaResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== Self-Service Token Endpoints ====================

@router.post("/{soggiorno_id}/genera-token", response_model=SelfServiceTokenResponse)
def genera_token_self_service(
    soggiorno_id: int,
    validita_ore: int = Query(72, ge=1, le=168, description="Token validity in hours"),
    db: Session = Depends(get_db)
):
    """
    Generate self-service token for guest data entry.

    Allows guests to enter their own data via a web form.
    Token expires after the specified validity period.

    Args:
        validita_ore: Token validity in hours (default: 72, max: 168)

    Returns:
        Token and URL for guest self-service access
    """
    service = SoggiornoService(db)

    try:
        result = service.genera_token_self_service(
            soggiorno_id=soggiorno_id,
            validita_ore=validita_ore
        )
        return SelfServiceTokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{soggiorno_id}/invalida-token", response_model=SoggiornoResponse)
def invalida_token(soggiorno_id: int, db: Session = Depends(get_db)):
    """
    Invalidate self-service token.

    Use when you need to revoke guest access to data entry.
    """
    soggiorno = db.query(Soggiorno).filter(Soggiorno.id == soggiorno_id).first()
    if not soggiorno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soggiorno con ID {soggiorno_id} non trovato"
        )

    soggiorno.token_self_service = None
    soggiorno.scadenza_token = None

    db.commit()
    db.refresh(soggiorno)
    return soggiorno


# ==================== Notification Endpoints ====================

@router.post("/{soggiorno_id}/invia-notifica-checkin")
def invia_notifica_checkin(soggiorno_id: int, db: Session = Depends(get_db)):
    """
    Send check-in notification to guest.

    Sends email with:
    - Self-service link for data entry
    - Check-in time and instructions
    """
    service = SoggiornoService(db)

    try:
        result = service.invia_notifica_checkin(soggiorno_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{soggiorno_id}/invia-sollecito")
def invia_sollecito_dati(soggiorno_id: int, db: Session = Depends(get_db)):
    """
    Send reminder for missing guest data.

    Sends reminder email to guest if data is incomplete.
    Tracks number of reminders sent.
    """
    service = SoggiornoService(db)

    try:
        result = service.invia_sollecito(soggiorno_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Helper Functions ====================

def _check_richiede_azione(soggiorno: Soggiorno) -> bool:
    """Check if a stay requires operator action."""
    if soggiorno.stato in [StatoSoggiorno.COMPLETATO.value, StatoSoggiorno.CANCELLATO.value]:
        return False

    if not soggiorno.dati_ospiti_completi:
        return True

    if soggiorno.stato == StatoSoggiorno.CREATO.value and soggiorno.data_checkin <= date.today():
        return True

    return False


def _get_motivi_azione(soggiorno: Soggiorno) -> List[str]:
    """Get list of reasons why action is required."""
    motivi = []

    if not soggiorno.dati_ospiti_completi:
        motivi.append("Dati ospiti incompleti")

    if soggiorno.numero_ospiti_registrati < soggiorno.numero_ospiti_previsti:
        motivi.append(f"Ospiti mancanti: {soggiorno.numero_ospiti_previsti - soggiorno.numero_ospiti_registrati}")

    if soggiorno.stato == StatoSoggiorno.CREATO.value and soggiorno.data_checkin <= date.today():
        motivi.append("Check-in in attesa")

    if soggiorno.stato_polizia == "SCADUTO":
        motivi.append("Comunicazione polizia scaduta")

    return motivi


def _dati_documento_completi(ospite: OspiteSoggiorno) -> bool:
    """Check if guest document data is complete."""
    required_fields = [
        ospite.tipo_documento,
        ospite.numero_documento,
        ospite.luogo_nascita,
        ospite.data_nascita,
        ospite.cittadinanza
    ]
    return all(f is not None for f in required_fields)
