"""
Tasse Routes - API endpoints for tourist tax management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from ..models import TassaSoggiornoConfig, TassaSoggiornoScaglione, TassaPrenotazione, Prenotazione
from ..schemas.tassa_soggiorno import (
    TassaSoggiornoConfigCreate,
    TassaSoggiornoConfigUpdate,
    TassaSoggiornoConfigResponse,
    TassaSoggiornoConfigWithScaglioni,
    TassaSoggiornoScaglioneCreate,
    TassaSoggiornoScaglioneUpdate,
    TassaSoggiornoScaglioneResponse,
)
from ..schemas.tassa_prenotazione import (
    TassaPrenotazioneResponse,
    TassaPrenotazioneUpdate,
    TassaCalculationRequest,
    TassaCalculationResponse,
    TassaOverrideRequest,
)
from ..services.tassa_soggiorno_calculator import TassaSoggiornoCalculator

router = APIRouter(prefix="/tasse", tags=["Tasse Soggiorno"])


# ==================== TassaSoggiornoConfig Endpoints ====================

@router.get("/config", response_model=List[TassaSoggiornoConfigResponse])
def get_configs(
    skip: int = 0,
    limit: int = 100,
    comune_id: Optional[int] = None,
    attiva: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni lista di tutte le configurazioni tassa soggiorno

    - **comune_id**: Filtra per comune specifico
    - **attiva**: Filtra solo configurazioni attive (true) o inattive (false)
    """
    query = db.query(TassaSoggiornoConfig)

    if comune_id is not None:
        query = query.filter(TassaSoggiornoConfig.comune_id == comune_id)
    if attiva is not None:
        query = query.filter(TassaSoggiornoConfig.attiva == attiva)

    configs = query.offset(skip).limit(limit).all()
    return configs


@router.get("/config/comune/{comune_id}/active", response_model=Optional[TassaSoggiornoConfigResponse])
def get_active_config_for_comune(
    comune_id: int,
    reference_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Ottieni la configurazione attiva per un comune in una data specifica

    - **reference_date**: Data di riferimento (default: oggi)
    """
    if reference_date is None:
        reference_date = date.today()

    calculator = TassaSoggiornoCalculator(db)
    config = calculator.get_active_config_for_comune(comune_id, reference_date)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna configurazione attiva trovata per comune {comune_id} alla data {reference_date}"
        )

    return config


@router.get("/config/{config_id}", response_model=TassaSoggiornoConfigResponse)
def get_config(config_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di una configurazione specifica"""
    config = db.query(TassaSoggiornoConfig).filter(TassaSoggiornoConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configurazione con ID {config_id} non trovata"
        )
    return config


@router.post("/config", response_model=TassaSoggiornoConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(config: TassaSoggiornoConfigCreate, db: Session = Depends(get_db)):
    """
    Crea una nuova configurazione tassa soggiorno

    Note:
    - Se tipo_calcolo=FISSO, deve essere presente importo_fisso
    - Se tipo_calcolo=PERCENTUALE, deve essere presente percentuale
    - Se tipo_calcolo=SCAGLIONI, gli scaglioni vanno creati separatamente
    """
    # Validate required fields based on calculation type
    if config.tipo_calcolo.value == "FISSO" and not config.importo_fisso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="importo_fisso è obbligatorio per tipo_calcolo=FISSO"
        )

    if config.tipo_calcolo.value == "PERCENTUALE" and not config.percentuale:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="percentuale è obbligatoria per tipo_calcolo=PERCENTUALE"
        )

    # Validate date range
    if config.data_fine_validita and config.data_fine_validita < config.data_inizio_validita:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="data_fine_validita deve essere successiva a data_inizio_validita"
        )

    new_config = TassaSoggiornoConfig(**config.model_dump())
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config


@router.post("/config/with-scaglioni", response_model=TassaSoggiornoConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config_with_scaglioni(
    config_data: TassaSoggiornoConfigWithScaglioni,
    db: Session = Depends(get_db)
):
    """
    Crea una nuova configurazione con scaglioni in una sola richiesta

    Utile per tipo_calcolo=SCAGLIONI dove si creano config + tiers insieme
    """
    if config_data.tipo_calcolo.value != "SCAGLIONI":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questo endpoint è solo per tipo_calcolo=SCAGLIONI"
        )

    if not config_data.scaglioni or len(config_data.scaglioni) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Almeno uno scaglione è richiesto per tipo_calcolo=SCAGLIONI"
        )

    # Create config
    config_dict = config_data.model_dump(exclude={'scaglioni'})
    new_config = TassaSoggiornoConfig(**config_dict)
    db.add(new_config)
    db.flush()  # Get ID without committing

    # Create scaglioni
    for scaglione_data in config_data.scaglioni:
        scaglione = TassaSoggiornoScaglione(
            config_id=new_config.id,
            **scaglione_data.model_dump()
        )
        db.add(scaglione)

    db.commit()
    db.refresh(new_config)
    return new_config


@router.put("/config/{config_id}", response_model=TassaSoggiornoConfigResponse)
def update_config(
    config_id: int,
    config: TassaSoggiornoConfigUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna una configurazione esistente"""
    db_config = db.query(TassaSoggiornoConfig).filter(TassaSoggiornoConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configurazione con ID {config_id} non trovata"
        )

    # Update only provided fields
    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """
    Elimina una configurazione

    Note: Questo elimina anche tutti gli scaglioni associati (cascade)
    """
    db_config = db.query(TassaSoggiornoConfig).filter(TassaSoggiornoConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configurazione con ID {config_id} non trovata"
        )

    db.delete(db_config)
    db.commit()
    return None


# ==================== TassaSoggiornoScaglione Endpoints ====================

@router.get("/config/{config_id}/scaglioni", response_model=List[TassaSoggiornoScaglioneResponse])
def get_scaglioni(config_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti gli scaglioni per una configurazione"""
    # Verify config exists
    config = db.query(TassaSoggiornoConfig).filter(TassaSoggiornoConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configurazione con ID {config_id} non trovata"
        )

    scaglioni = db.query(TassaSoggiornoScaglione).filter(
        TassaSoggiornoScaglione.config_id == config_id
    ).order_by(TassaSoggiornoScaglione.notte_da).all()

    return scaglioni


@router.post("/config/{config_id}/scaglioni", response_model=TassaSoggiornoScaglioneResponse, status_code=status.HTTP_201_CREATED)
def create_scaglione(
    config_id: int,
    scaglione: TassaSoggiornoScaglioneCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuovo scaglione per una configurazione"""
    # Verify config exists
    config = db.query(TassaSoggiornoConfig).filter(TassaSoggiornoConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configurazione con ID {config_id} non trovata"
        )

    # Validate night range
    if scaglione.notte_a and scaglione.notte_a < scaglione.notte_da:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="notte_a deve essere >= notte_da"
        )

    # Override config_id from path
    scaglione_dict = scaglione.model_dump()
    scaglione_dict['config_id'] = config_id

    new_scaglione = TassaSoggiornoScaglione(**scaglione_dict)
    db.add(new_scaglione)
    db.commit()
    db.refresh(new_scaglione)
    return new_scaglione


@router.put("/scaglioni/{scaglione_id}", response_model=TassaSoggiornoScaglioneResponse)
def update_scaglione(
    scaglione_id: int,
    scaglione: TassaSoggiornoScaglioneUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna uno scaglione esistente"""
    db_scaglione = db.query(TassaSoggiornoScaglione).filter(
        TassaSoggiornoScaglione.id == scaglione_id
    ).first()

    if not db_scaglione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scaglione con ID {scaglione_id} non trovato"
        )

    # Update only provided fields
    update_data = scaglione.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_scaglione, field, value)

    db.commit()
    db.refresh(db_scaglione)
    return db_scaglione


@router.delete("/scaglioni/{scaglione_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scaglione(scaglione_id: int, db: Session = Depends(get_db)):
    """Elimina uno scaglione"""
    db_scaglione = db.query(TassaSoggiornoScaglione).filter(
        TassaSoggiornoScaglione.id == scaglione_id
    ).first()

    if not db_scaglione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scaglione con ID {scaglione_id} non trovato"
        )

    db.delete(db_scaglione)
    db.commit()
    return None


# ==================== Tax Calculation Endpoints ====================

@router.post("/calculate", response_model=TassaCalculationResponse)
def calculate_tax(
    request: TassaCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calcola la tassa di soggiorno per una prenotazione

    - **prenotazione_id**: ID della prenotazione da calcolare
    - **force_recalculate**: Se True, ricalcola anche se già esiste

    Returns: TassaPrenotazione con breakdown dettagliato
    """
    # Verify booking exists
    prenotazione = db.query(Prenotazione).filter(Prenotazione.id == request.prenotazione_id).first()
    if not prenotazione:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prenotazione con ID {request.prenotazione_id} non trovata"
        )

    # Check if already calculated
    existing_tassa = db.query(TassaPrenotazione).filter(
        TassaPrenotazione.prenotazione_id == request.prenotazione_id
    ).first()

    if existing_tassa and not request.force_recalculate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tassa già calcolata per questa prenotazione. Usa force_recalculate=true per ricalcolare"
        )

    # Calculate tax
    calculator = TassaSoggiornoCalculator(db)
    try:
        tassa = calculator.create_or_update_tassa(request.prenotazione_id)

        # Get config used
        comune_id = 1  # TODO: Get from prenotazione.unita_immobiliare.comune_id
        config = calculator.get_active_config_for_comune(comune_id, prenotazione.data_checkin)

        return TassaCalculationResponse(
            tassa=tassa,
            calculation_breakdown=tassa.dettaglio_calcolo,
            config_used={
                "id": config.id,
                "comune_nome": config.comune_nome,
                "tipo_calcolo": config.tipo_calcolo.value,
                "importo_fisso": float(config.importo_fisso) if config.importo_fisso else None,
                "percentuale": float(config.percentuale) if config.percentuale else None,
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== TassaPrenotazione Endpoints ====================

@router.get("/prenotazioni", response_model=List[TassaPrenotazioneResponse])
def get_tasse_prenotazioni(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Ottieni lista di tutte le tasse calcolate"""
    tasse = db.query(TassaPrenotazione).offset(skip).limit(limit).all()
    return tasse


@router.get("/prenotazioni/{prenotazione_id}", response_model=TassaPrenotazioneResponse)
def get_tassa_prenotazione(prenotazione_id: int, db: Session = Depends(get_db)):
    """Ottieni la tassa calcolata per una prenotazione"""
    tassa = db.query(TassaPrenotazione).filter(
        TassaPrenotazione.prenotazione_id == prenotazione_id
    ).first()

    if not tassa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna tassa calcolata per prenotazione {prenotazione_id}"
        )

    return tassa


@router.put("/prenotazioni/{prenotazione_id}", response_model=TassaPrenotazioneResponse)
def update_tassa_prenotazione(
    prenotazione_id: int,
    tassa: TassaPrenotazioneUpdate,
    db: Session = Depends(get_db)
):
    """
    Aggiorna una tassa esistente

    Note: Preferire l'endpoint /override per override manuali
    """
    db_tassa = db.query(TassaPrenotazione).filter(
        TassaPrenotazione.prenotazione_id == prenotazione_id
    ).first()

    if not db_tassa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna tassa trovata per prenotazione {prenotazione_id}"
        )

    # Update only provided fields
    update_data = tassa.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tassa, field, value)

    db.commit()
    db.refresh(db_tassa)
    return db_tassa


@router.post("/prenotazioni/{prenotazione_id}/override", response_model=TassaPrenotazioneResponse)
def override_tassa(
    prenotazione_id: int,
    override_request: TassaOverrideRequest,
    db: Session = Depends(get_db)
):
    """
    Override manuale dell'importo tassa

    Consente di sovrascrivere la tassa calcolata con un importo manuale
    e registrare il motivo dell'override
    """
    db_tassa = db.query(TassaPrenotazione).filter(
        TassaPrenotazione.prenotazione_id == prenotazione_id
    ).first()

    if not db_tassa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna tassa trovata per prenotazione {prenotazione_id}. Calcolare prima la tassa"
        )

    db_tassa.importo_manuale = override_request.importo_manuale
    db_tassa.note_manuale = override_request.note_manuale

    db.commit()
    db.refresh(db_tassa)
    return db_tassa


@router.delete("/prenotazioni/{prenotazione_id}/override", response_model=TassaPrenotazioneResponse)
def remove_override(prenotazione_id: int, db: Session = Depends(get_db)):
    """
    Rimuove l'override manuale e ripristina l'importo calcolato
    """
    db_tassa = db.query(TassaPrenotazione).filter(
        TassaPrenotazione.prenotazione_id == prenotazione_id
    ).first()

    if not db_tassa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessuna tassa trovata per prenotazione {prenotazione_id}"
        )

    db_tassa.importo_manuale = None
    db_tassa.note_manuale = None

    db.commit()
    db.refresh(db_tassa)
    return db_tassa
