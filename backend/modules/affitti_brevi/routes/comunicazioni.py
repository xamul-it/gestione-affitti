"""
Comunicazioni Routes

API per il dettaglio e il completamento manuale delle comunicazioni di
compliance (Polizia, tassa di soggiorno) generate da
ComplianceScadenzeService. L'invio automatico reale (Alloggiati Web) è
compito del sotto-progetto C — qui il completamento è sempre manuale.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from ..models import Comunicazione
from ..schemas.comunicazione import ComunicazioneResponse, SegnaCompletataRequest
from ..services.compliance_scadenze_service import ComplianceScadenzeService

router = APIRouter(prefix="/comunicazioni", tags=["Comunicazioni"])


@router.get("/{comunicazione_id}", response_model=ComunicazioneResponse)
def get_comunicazione(comunicazione_id: int, db: Session = Depends(get_db)):
    """Dettaglio di una comunicazione di compliance."""
    comunicazione = db.query(Comunicazione).filter(Comunicazione.id == comunicazione_id).first()
    if not comunicazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comunicazione con ID {comunicazione_id} non trovata"
        )
    return comunicazione


@router.post("/{comunicazione_id}/segna-completata", response_model=ComunicazioneResponse)
def segna_completata(
    comunicazione_id: int,
    payload: SegnaCompletataRequest,
    db: Session = Depends(get_db)
):
    """Marca la comunicazione come inviata manualmente e completa la
    scadenza core collegata."""
    service = ComplianceScadenzeService(db)
    try:
        return service.completa_comunicazione(comunicazione_id, note=payload.note)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
