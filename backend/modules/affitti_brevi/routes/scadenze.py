"""
Scadenze Routes - Using Core Platform Scadenza System

Uses app.core.platform.models.scadenza.Scadenza with affitti_brevi extension
for module-specific metadata (tipo_scadenza, ricorrente, etc.).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

# Add modules directory to path for cross-module imports
import sys
import os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from app.core.database import get_db

# Use core Scadenza model
from app.core.platform.models.scadenza import Scadenza, StatoScadenza, PrioritaScadenza

# Use affitti_brevi extension and services
from affitti_brevi.models.scadenza_ext import ScadenzaAffittiBrevi, TipoScadenzaAffittiBrevi
from affitti_brevi.models import ComunicazionePolizia, StatoComunicazione, MetodoInvio
from affitti_brevi.schemas.scadenza import (
    ScadenzaResponse,
    ScadenzaCreate,
    ScadenzaUpdate,
    ScadenzaBadgeInfo,
    ScadenzaCompletaRequest
)
from affitti_brevi.schemas.comunicazione_polizia import (
    ComunicazionePoliziaResponse,
    ComunicazionePoliziaCreate,
    ComunicazionePoliziaUpdate,
    ComunicazioneInvioRequest,
    ComunicazioneErroreRequest
)
from affitti_brevi.services.scadenza_generator import ScadenzaGenerator
from affitti_brevi.services.comunicazione_polizia_service import ComunicazionePoliziaService

router = APIRouter()


# ==================== Scadenze Endpoints (Core System) ====================

@router.get("/", response_model=List[ScadenzaResponse])
def get_scadenze(
    skip: int = 0,
    limit: int = 100,
    tipo: Optional[TipoScadenzaAffittiBrevi] = None,
    stato: Optional[StatoScadenza] = None,
    priorita: Optional[PrioritaScadenza] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni lista di tutte le scadenze del modulo affitti_brevi

    Queries core.scadenze with join to affitti_brevi extension.
    """
    query = db.query(Scadenza, ScadenzaAffittiBrevi).join(
        ScadenzaAffittiBrevi,
        Scadenza.id == ScadenzaAffittiBrevi.scadenza_id
    ).filter(
        Scadenza.modulo == "affitti_brevi"
    )

    if tipo:
        query = query.filter(ScadenzaAffittiBrevi.tipo_scadenza == tipo)
    if stato:
        query = query.filter(Scadenza.stato == stato)
    if priorita:
        query = query.filter(Scadenza.priorita == priorita)

    results = query.order_by(Scadenza.data_scadenza.desc()).offset(skip).limit(limit).all()

    # Combine core + extension data
    scadenze = []
    for scadenza, ext in results:
        scadenza_dict = {
            **scadenza.__dict__,
            "tipo_scadenza": ext.tipo_scadenza,
            "ricorrente": ext.ricorrente,
            "frequenza_giorni": ext.frequenza_giorni,
            "prossima_ricorrenza": ext.prossima_ricorrenza
        }
        scadenze.append(scadenza_dict)

    return scadenze


@router.get("/upcoming", response_model=List[ScadenzaResponse])
def get_upcoming_scadenze(
    days: int = Query(default=7, ge=1, le=90),
    tipo: Optional[TipoScadenzaAffittiBrevi] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni scadenze in arrivo entro X giorni
    """
    generator = ScadenzaGenerator(db)
    results = generator.get_upcoming_deadlines(days_ahead=days, tipo=tipo)

    scadenze = []
    for scadenza, ext in results:
        scadenza_dict = {
            **scadenza.__dict__,
            "tipo_scadenza": ext.tipo_scadenza,
            "ricorrente": ext.ricorrente,
            "frequenza_giorni": ext.frequenza_giorni,
            "prossima_ricorrenza": ext.prossima_ricorrenza
        }
        scadenze.append(scadenza_dict)

    return scadenze


@router.get("/overdue", response_model=List[ScadenzaResponse])
def get_overdue_scadenze(
    tipo: Optional[TipoScadenzaAffittiBrevi] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni scadenze scadute (data_scadenza passata e non completate)
    """
    generator = ScadenzaGenerator(db)
    results = generator.get_overdue_deadlines(tipo=tipo)

    scadenze = []
    for scadenza, ext in results:
        scadenza_dict = {
            **scadenza.__dict__,
            "tipo_scadenza": ext.tipo_scadenza,
            "ricorrente": ext.ricorrente,
            "frequenza_giorni": ext.frequenza_giorni,
            "prossima_ricorrenza": ext.prossima_ricorrenza
        }
        scadenze.append(scadenza_dict)

    return scadenze


@router.get("/badge/info", response_model=ScadenzaBadgeInfo)
def get_badge_info(
    tipo: Optional[TipoScadenzaAffittiBrevi] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni info per badge notifiche (count totale e per tipo)

    Conta scadenze:
    - In scadenza entro 7 giorni
    - Scadute e non completate
    """
    from datetime import timedelta
    from sqlalchemy import func, case

    today = date.today()
    week_ahead = today + timedelta(days=7)

    # Query with join
    query = db.query(
        ScadenzaAffittiBrevi.tipo_scadenza,
        func.count(case(
            (Scadenza.data_scadenza < today, 1)
        )).label('scadute'),
        func.count(case(
            ((Scadenza.data_scadenza >= today) & (Scadenza.data_scadenza <= week_ahead), 1)
        )).label('in_scadenza'),
        func.count(Scadenza.id).label('totale')
    ).join(
        Scadenza,
        ScadenzaAffittiBrevi.scadenza_id == Scadenza.id
    ).filter(
        Scadenza.modulo == "affitti_brevi",
        Scadenza.stato.in_([StatoScadenza.ATTIVA, StatoScadenza.SCADUTA])
    )

    if tipo:
        query = query.filter(ScadenzaAffittiBrevi.tipo_scadenza == tipo)

    results = query.group_by(ScadenzaAffittiBrevi.tipo_scadenza).all()

    # Build response
    totale_scadute = 0
    totale_in_scadenza = 0
    totale_count = 0
    per_tipo = {}

    for tipo_scad, scadute, in_scadenza, count in results:
        totale_scadute += scadute
        totale_in_scadenza += in_scadenza
        totale_count += count

        per_tipo[tipo_scad.value] = {
            "scadute": scadute,
            "in_scadenza": in_scadenza,
            "totale": count
        }

    return ScadenzaBadgeInfo(
        count=totale_count,
        scadute=totale_scadute,
        in_scadenza=totale_in_scadenza,
        per_tipo=per_tipo
    )


@router.get("/{scadenza_id}", response_model=ScadenzaResponse)
def get_scadenza(scadenza_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una scadenza specifica"""
    result = db.query(Scadenza, ScadenzaAffittiBrevi).join(
        ScadenzaAffittiBrevi,
        Scadenza.id == ScadenzaAffittiBrevi.scadenza_id
    ).filter(
        Scadenza.id == scadenza_id,
        Scadenza.modulo == "affitti_brevi"
    ).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scadenza con ID {scadenza_id} non trovata"
        )

    scadenza, ext = result
    scadenza_dict = {
        **scadenza.__dict__,
        "tipo_scadenza": ext.tipo_scadenza,
        "ricorrente": ext.ricorrente,
        "frequenza_giorni": ext.frequenza_giorni,
        "prossima_ricorrenza": ext.prossima_ricorrenza
    }

    return scadenza_dict


@router.post("/", response_model=ScadenzaResponse, status_code=status.HTTP_201_CREATED)
def create_scadenza(
    scadenza: ScadenzaCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth context
):
    """Crea una nuova scadenza affitti_brevi"""
    # Create core Scadenza
    new_scadenza = Scadenza(
        modulo="affitti_brevi",
        entity_type=scadenza.entity_type,
        entity_id=scadenza.entity_id,
        titolo=scadenza.titolo,
        descrizione=scadenza.descrizione,
        data_scadenza=scadenza.data_scadenza,
        priorita=scadenza.priorita or PrioritaScadenza.MEDIA,
        stato=StatoScadenza.ATTIVA,
        creato_da=current_user_id
    )

    db.add(new_scadenza)
    db.flush()  # Get ID

    # Create extension
    new_ext = ScadenzaAffittiBrevi(
        scadenza_id=new_scadenza.id,
        tipo_scadenza=scadenza.tipo_scadenza,
        ricorrente=scadenza.ricorrente or False,
        frequenza_giorni=scadenza.frequenza_giorni,
        prossima_ricorrenza=scadenza.prossima_ricorrenza
    )

    db.add(new_ext)
    db.commit()
    db.refresh(new_scadenza)
    db.refresh(new_ext)

    # Return combined
    scadenza_dict = {
        **new_scadenza.__dict__,
        "tipo_scadenza": new_ext.tipo_scadenza,
        "ricorrente": new_ext.ricorrente,
        "frequenza_giorni": new_ext.frequenza_giorni,
        "prossima_ricorrenza": new_ext.prossima_ricorrenza
    }

    return scadenza_dict


@router.put("/{scadenza_id}", response_model=ScadenzaResponse)
def update_scadenza(
    scadenza_id: int,
    scadenza: ScadenzaUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna una scadenza esistente"""
    # Get both core and extension
    result = db.query(Scadenza, ScadenzaAffittiBrevi).join(
        ScadenzaAffittiBrevi,
        Scadenza.id == ScadenzaAffittiBrevi.scadenza_id
    ).filter(
        Scadenza.id == scadenza_id,
        Scadenza.modulo == "affitti_brevi"
    ).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scadenza con ID {scadenza_id} non trovata"
        )

    db_scadenza, db_ext = result

    # Update core fields
    update_data = scadenza.model_dump(exclude_unset=True)
    core_fields = ['titolo', 'descrizione', 'data_scadenza', 'priorita', 'stato']
    ext_fields = ['tipo_scadenza', 'ricorrente', 'frequenza_giorni', 'prossima_ricorrenza']

    for field in core_fields:
        if field in update_data:
            setattr(db_scadenza, field, update_data[field])

    for field in ext_fields:
        if field in update_data:
            setattr(db_ext, field, update_data[field])

    db.commit()
    db.refresh(db_scadenza)
    db.refresh(db_ext)

    # Return combined
    scadenza_dict = {
        **db_scadenza.__dict__,
        "tipo_scadenza": db_ext.tipo_scadenza,
        "ricorrente": db_ext.ricorrente,
        "frequenza_giorni": db_ext.frequenza_giorni,
        "prossima_ricorrenza": db_ext.prossima_ricorrenza
    }

    return scadenza_dict


@router.delete("/{scadenza_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scadenza(scadenza_id: int, db: Session = Depends(get_db)):
    """Elimina una scadenza (CASCADE deletes extension)"""
    db_scadenza = db.query(Scadenza).filter(
        Scadenza.id == scadenza_id,
        Scadenza.modulo == "affitti_brevi"
    ).first()

    if not db_scadenza:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scadenza con ID {scadenza_id} non trovata"
        )

    db.delete(db_scadenza)  # CASCADE deletes extension
    db.commit()
    return None


@router.post("/{scadenza_id}/completa", response_model=ScadenzaResponse)
def mark_scadenza_completed(
    scadenza_id: int,
    request: ScadenzaCompletaRequest,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth context
):
    """Marca una scadenza come completata (uses core completion pattern)"""
    result = db.query(Scadenza, ScadenzaAffittiBrevi).join(
        ScadenzaAffittiBrevi,
        Scadenza.id == ScadenzaAffittiBrevi.scadenza_id
    ).filter(
        Scadenza.id == scadenza_id,
        Scadenza.modulo == "affitti_brevi"
    ).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scadenza con ID {scadenza_id} non trovata"
        )

    db_scadenza, db_ext = result

    # Use core completion pattern
    db_scadenza.stato = StatoScadenza.COMPLETATA
    db_scadenza.completato_da = current_user_id
    db_scadenza.completato_il = datetime.now()

    # Add completion note to description (core doesn't have note_completamento field)
    if request.note_completamento:
        db_scadenza.descrizione = (db_scadenza.descrizione or "") + f"\n\nNote completamento: {request.note_completamento}"

    db.commit()
    db.refresh(db_scadenza)
    db.refresh(db_ext)

    # Return combined
    scadenza_dict = {
        **db_scadenza.__dict__,
        "tipo_scadenza": db_ext.tipo_scadenza,
        "ricorrente": db_ext.ricorrente,
        "frequenza_giorni": db_ext.frequenza_giorni,
        "prossima_ricorrenza": db_ext.prossima_ricorrenza
    }

    return scadenza_dict


@router.post("/generate/police/{prenotazione_id}", response_model=ScadenzaResponse, status_code=status.HTTP_201_CREATED)
def generate_police_deadline(
    prenotazione_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth context
):
    """
    Genera scadenza comunicazione polizia per una prenotazione

    Crea deadline 24h dopo check-in using core Scadenza model
    """
    generator = ScadenzaGenerator(db, current_user_id)
    try:
        scadenza, ext = generator.generate_police_deadline_for_booking(prenotazione_id)

        # Return combined
        scadenza_dict = {
            **scadenza.__dict__,
            "tipo_scadenza": ext.tipo_scadenza,
            "ricorrente": ext.ricorrente,
            "frequenza_giorni": ext.frequenza_giorni,
            "prossima_ricorrenza": ext.prossima_ricorrenza
        }

        return scadenza_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/generate/istat", response_model=ScadenzaResponse, status_code=status.HTTP_201_CREATED)
def generate_istat_deadline(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth context
):
    """
    Genera scadenza report ISTAT per un mese

    Crea deadline ricorrente per il 15° del mese using core Scadenza model
    """
    generator = ScadenzaGenerator(db, current_user_id)
    try:
        scadenza, ext = generator.generate_istat_monthly_deadline(year, month)

        # Return combined
        scadenza_dict = {
            **scadenza.__dict__,
            "tipo_scadenza": ext.tipo_scadenza,
            "ricorrente": ext.ricorrente,
            "frequenza_giorni": ext.frequenza_giorni,
            "prossima_ricorrenza": ext.prossima_ricorrenza
        }

        return scadenza_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Comunicazioni Polizia Endpoints ====================
# These remain unchanged - they work with ComunicazionePolizia model directly

@router.get("/comunicazioni-polizia/", response_model=List[ComunicazionePoliziaResponse])
def get_comunicazioni_polizia(
    skip: int = 0,
    limit: int = 100,
    stato: Optional[StatoComunicazione] = None,
    prenotazione_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni lista di tutte le comunicazioni polizia

    - **stato**: Filtra per stato
    - **prenotazione_id**: Filtra per prenotazione specifica
    """
    query = db.query(ComunicazionePolizia)

    if stato:
        query = query.filter(ComunicazionePolizia.stato == stato)
    if prenotazione_id:
        query = query.filter(ComunicazionePolizia.prenotazione_id == prenotazione_id)

    comunicazioni = query.order_by(ComunicazionePolizia.created_at.desc()).offset(skip).limit(limit).all()
    return comunicazioni


@router.get("/comunicazioni-polizia/pending", response_model=List[ComunicazionePoliziaResponse])
def get_pending_comunicazioni(db: Session = Depends(get_db)):
    """Ottieni tutte le comunicazioni in attesa di invio"""
    service = ComunicazionePoliziaService(db)
    comunicazioni = service.get_pending_communications()
    return comunicazioni


@router.get("/comunicazioni-polizia/overdue", response_model=List[ComunicazionePoliziaResponse])
def get_overdue_comunicazioni(db: Session = Depends(get_db)):
    """Ottieni tutte le comunicazioni scadute (oltre 24h)"""
    service = ComunicazionePoliziaService(db)
    comunicazioni = service.get_overdue_communications()
    return comunicazioni


@router.get("/comunicazioni-polizia/{comunicazione_id}", response_model=ComunicazionePoliziaResponse)
def get_comunicazione_polizia(comunicazione_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una comunicazione specifica"""
    comunicazione = db.query(ComunicazionePolizia).filter(
        ComunicazionePolizia.id == comunicazione_id
    ).first()

    if not comunicazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comunicazione con ID {comunicazione_id} non trovata"
        )
    return comunicazione


@router.post("/comunicazioni-polizia/", response_model=ComunicazionePoliziaResponse, status_code=status.HTTP_201_CREATED)
def create_comunicazione_polizia(
    comunicazione: ComunicazionePoliziaCreate,
    db: Session = Depends(get_db)
):
    """Crea una nuova comunicazione polizia per una prenotazione"""
    service = ComunicazionePoliziaService(db)
    try:
        new_comunicazione = service.create_for_booking(comunicazione.prenotazione_id)
        if comunicazione.codice_struttura:
            new_comunicazione.codice_struttura = comunicazione.codice_struttura
            db.commit()
            db.refresh(new_comunicazione)
        return new_comunicazione
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/comunicazioni-polizia/{comunicazione_id}", response_model=ComunicazionePoliziaResponse)
def update_comunicazione_polizia(
    comunicazione_id: int,
    comunicazione: ComunicazionePoliziaUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna una comunicazione esistente"""
    db_comunicazione = db.query(ComunicazionePolizia).filter(
        ComunicazionePolizia.id == comunicazione_id
    ).first()

    if not db_comunicazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comunicazione con ID {comunicazione_id} non trovata"
        )

    # Update only provided fields
    update_data = comunicazione.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_comunicazione, field, value)

    db.commit()
    db.refresh(db_comunicazione)
    return db_comunicazione


@router.delete("/comunicazioni-polizia/{comunicazione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comunicazione_polizia(comunicazione_id: int, db: Session = Depends(get_db)):
    """Elimina una comunicazione polizia"""
    db_comunicazione = db.query(ComunicazionePolizia).filter(
        ComunicazionePolizia.id == comunicazione_id
    ).first()

    if not db_comunicazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comunicazione con ID {comunicazione_id} non trovata"
        )

    db.delete(db_comunicazione)
    db.commit()
    return None


@router.post("/comunicazioni-polizia/{comunicazione_id}/invio", response_model=ComunicazionePoliziaResponse)
def mark_comunicazione_sent(
    comunicazione_id: int,
    request: ComunicazioneInvioRequest,
    db: Session = Depends(get_db)
):
    """Marca una comunicazione come inviata"""
    service = ComunicazionePoliziaService(db)
    try:
        comunicazione = service.mark_sent(
            comunicazione_id,
            request.metodo_invio,
            request.numero_ricevuta,
            request.codice_struttura
        )
        return comunicazione
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/comunicazioni-polizia/{comunicazione_id}/conferma", response_model=ComunicazionePoliziaResponse)
def mark_comunicazione_confirmed(comunicazione_id: int, db: Session = Depends(get_db)):
    """Marca una comunicazione come confermata dal sistema polizia"""
    service = ComunicazionePoliziaService(db)
    try:
        comunicazione = service.mark_confirmed(comunicazione_id)
        return comunicazione
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/comunicazioni-polizia/{comunicazione_id}/errore", response_model=ComunicazionePoliziaResponse)
def mark_comunicazione_error(
    comunicazione_id: int,
    request: ComunicazioneErroreRequest,
    db: Session = Depends(get_db)
):
    """Marca una comunicazione come errore"""
    service = ComunicazionePoliziaService(db)
    try:
        comunicazione = service.mark_error(comunicazione_id, request.errore_messaggio)
        return comunicazione
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/comunicazioni-polizia/{comunicazione_id}/retry", response_model=ComunicazionePoliziaResponse)
def retry_comunicazione(comunicazione_id: int, db: Session = Depends(get_db)):
    """Resetta una comunicazione fallita per riprovare l'invio"""
    service = ComunicazionePoliziaService(db)
    try:
        comunicazione = service.retry_failed_communication(comunicazione_id)
        return comunicazione
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/comunicazioni-polizia/prenotazione/{prenotazione_id}", response_model=Optional[ComunicazionePoliziaResponse])
def get_comunicazione_by_booking(prenotazione_id: int, db: Session = Depends(get_db)):
    """Ottieni la comunicazione polizia per una specifica prenotazione"""
    service = ComunicazionePoliziaService(db)
    comunicazione = service.get_by_booking(prenotazione_id)

    if not comunicazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna comunicazione trovata per prenotazione {prenotazione_id}"
        )

    return comunicazione
