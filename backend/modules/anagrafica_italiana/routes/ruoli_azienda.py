"""
API endpoints for RuoloAzienda (Person-Company role associations)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, inspect, text
from typing import List, Optional
from datetime import date

from app.core.database import get_db, get_tenant_schema
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User

from ..models import RuoloAzienda, SoggettoAnagrafico, TipoSoggetto
from ..schemas.ruolo_azienda import (
    RuoloAziendaCreate,
    RuoloAziendaUpdate,
    RuoloAziendaResponse,
    RuoloAziendaListItem
)

router = APIRouter(prefix="/anagrafica/ruoli-azienda", tags=["Ruoli Azienda"])

def _ensure_ruoli_azienda_tables(db: Session, tenant_schema: Optional[str]) -> None:
    if not tenant_schema:
        raise HTTPException(status_code=400, detail="Tenant schema mancante")

    # Force tenant search_path for this session.
    db.execute(text(f"SET search_path TO {tenant_schema}, public"))

    inspector = inspect(db.get_bind())
    if not inspector.has_table("anag_ruoli_azienda", schema=tenant_schema):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tabella anag_ruoli_azienda non presente. Reinstalla il modulo anagrafica per il tenant.",
        )
    if not inspector.has_table("anag_soggetti_anagrafici", schema=tenant_schema):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tabella anag_soggetti_anagrafici non presente. Reinstalla il modulo anagrafica per il tenant.",
        )


@router.get("/", response_model=List[RuoloAziendaResponse])
def get_all_ruoli_azienda(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Ottieni tutti i ruoli azienda"""
    _ensure_ruoli_azienda_tables(db, tenant_schema)
    ruoli = db.query(RuoloAzienda).options(
        joinedload(RuoloAzienda.persona_fisica),
        joinedload(RuoloAzienda.persona_giuridica)
    ).offset(skip).limit(limit).all()
    return ruoli


@router.get("/soggetto/{soggetto_id}")
def get_ruoli_by_soggetto(
    soggetto_id: int,
    attivi_only: bool = False,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """
    Ottieni tutti i ruoli per un soggetto specifico.

    Restituisce un oggetto con due liste:
    - come_persona: ruoli in cui questo soggetto lavora come persona fisica
    - come_azienda: ruoli in cui questo soggetto ha dipendenti (se è un'azienda)
    """
    _ensure_ruoli_azienda_tables(db, tenant_schema)

    soggetto = db.query(SoggettoAnagrafico).filter(SoggettoAnagrafico.id == soggetto_id).first()
    if not soggetto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soggetto con ID {soggetto_id} non trovato"
        )

    # Ruoli come persona fisica (lavora in aziende)
    ruoli_come_persona_query = db.query(RuoloAzienda).options(
        joinedload(RuoloAzienda.persona_fisica),
        joinedload(RuoloAzienda.persona_giuridica),
        joinedload(RuoloAzienda.ruolo_tipo)
    ).filter(RuoloAzienda.persona_fisica_id == soggetto_id)

    if attivi_only:
        today = date.today()
        ruoli_come_persona_query = ruoli_come_persona_query.filter(
            (RuoloAzienda.data_fine == None) | (RuoloAzienda.data_fine >= today)
        )

    # Ruoli come azienda (ha dipendenti)
    ruoli_come_azienda_query = db.query(RuoloAzienda).options(
        joinedload(RuoloAzienda.persona_fisica),
        joinedload(RuoloAzienda.persona_giuridica),
        joinedload(RuoloAzienda.ruolo_tipo)
    ).filter(RuoloAzienda.persona_giuridica_id == soggetto_id)

    if attivi_only:
        today = date.today()
        ruoli_come_azienda_query = ruoli_come_azienda_query.filter(
            (RuoloAzienda.data_fine == None) | (RuoloAzienda.data_fine >= today)
        )

    ruoli_come_persona = ruoli_come_persona_query.all()
    ruoli_come_azienda = ruoli_come_azienda_query.all()

    # Converte in dict per JSON response
    return {
        "come_persona": [
            {
                "id": r.id,
                "persona_fisica_id": r.persona_fisica_id,
                "persona_giuridica_id": r.persona_giuridica_id,
                "ruolo": r.ruolo,
                "ruolo_tipo_id": r.ruolo_tipo_id,
                "ruolo_tipo_nome": r.ruolo_tipo.nome if r.ruolo_tipo else None,
                "data_inizio": r.data_inizio.isoformat() if r.data_inizio else None,
                "data_fine": r.data_fine.isoformat() if r.data_fine else None,
                "persona_fisica": {
                    "id": r.persona_fisica.id,
                    "nome_completo": r.persona_fisica.nome_completo,
                    "codice_fiscale": r.persona_fisica.codice_fiscale
                } if r.persona_fisica else None,
                "persona_giuridica": {
                    "id": r.persona_giuridica.id,
                    "ragione_sociale": r.persona_giuridica.ragione_sociale,
                    "codice_fiscale": r.persona_giuridica.codice_fiscale
                } if r.persona_giuridica else None
            }
            for r in ruoli_come_persona
        ],
        "come_azienda": [
            {
                "id": r.id,
                "persona_fisica_id": r.persona_fisica_id,
                "persona_giuridica_id": r.persona_giuridica_id,
                "ruolo": r.ruolo,
                "ruolo_tipo_id": r.ruolo_tipo_id,
                "ruolo_tipo_nome": r.ruolo_tipo.nome if r.ruolo_tipo else None,
                "data_inizio": r.data_inizio.isoformat() if r.data_inizio else None,
                "data_fine": r.data_fine.isoformat() if r.data_fine else None,
                "persona_fisica": {
                    "id": r.persona_fisica.id,
                    "nome_completo": r.persona_fisica.nome_completo,
                    "codice_fiscale": r.persona_fisica.codice_fiscale
                } if r.persona_fisica else None,
                "persona_giuridica": {
                    "id": r.persona_giuridica.id,
                    "ragione_sociale": r.persona_giuridica.ragione_sociale,
                    "codice_fiscale": r.persona_giuridica.codice_fiscale
                } if r.persona_giuridica else None
            }
            for r in ruoli_come_azienda
        ]
    }


@router.get("/{ruolo_id}", response_model=RuoloAziendaResponse)
def get_ruolo_azienda(
    ruolo_id: int,
    current_user: User = Depends(require_permission("soggetto.view")),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Ottieni un ruolo azienda specifico"""
    _ensure_ruoli_azienda_tables(db, tenant_schema)
    ruolo = db.query(RuoloAzienda).options(
        joinedload(RuoloAzienda.persona_fisica),
        joinedload(RuoloAzienda.persona_giuridica)
    ).filter(RuoloAzienda.id == ruolo_id).first()

    if not ruolo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruolo azienda con ID {ruolo_id} non trovato"
        )

    return ruolo


@router.post("/", response_model=RuoloAziendaResponse, status_code=status.HTTP_201_CREATED)
def create_ruolo_azienda(
    ruolo_data: RuoloAziendaCreate,
    current_user: User = Depends(require_permission("soggetto.create")),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Crea un nuovo ruolo azienda (associazione persona-azienda)"""
    _ensure_ruoli_azienda_tables(db, tenant_schema)

    # Valida che persona_fisica sia effettivamente una persona fisica
    persona = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == ruolo_data.persona_fisica_id
    ).first()
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona fisica con ID {ruolo_data.persona_fisica_id} non trovata"
        )
    if persona.tipo_soggetto != TipoSoggetto.PERSONA_FISICA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il soggetto {persona.id} non è una persona fisica"
        )

    # Valida che persona_giuridica sia effettivamente un'azienda
    azienda = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == ruolo_data.persona_giuridica_id
    ).first()
    if not azienda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Azienda con ID {ruolo_data.persona_giuridica_id} non trovata"
        )
    if azienda.tipo_soggetto != TipoSoggetto.PERSONA_GIURIDICA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il soggetto {azienda.id} non è una persona giuridica"
        )

    # Valida date
    if ruolo_data.data_inizio and ruolo_data.data_fine:
        if ruolo_data.data_fine < ruolo_data.data_inizio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La data di fine non può essere precedente alla data di inizio"
            )

    # Crea il ruolo
    nuovo_ruolo = RuoloAzienda(**ruolo_data.model_dump())
    db.add(nuovo_ruolo)
    db.commit()
    db.refresh(nuovo_ruolo)

    # Ricarica con relationships
    ruolo = db.query(RuoloAzienda).options(
        joinedload(RuoloAzienda.persona_fisica),
        joinedload(RuoloAzienda.persona_giuridica)
    ).filter(RuoloAzienda.id == nuovo_ruolo.id).first()

    return ruolo


@router.put("/{ruolo_id}", response_model=RuoloAziendaResponse)
def update_ruolo_azienda(
    ruolo_id: int,
    ruolo_update: RuoloAziendaUpdate,
    current_user: User = Depends(require_permission("soggetto.update")),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Aggiorna un ruolo azienda esistente"""
    _ensure_ruoli_azienda_tables(db, tenant_schema)
    ruolo = db.query(RuoloAzienda).filter(RuoloAzienda.id == ruolo_id).first()

    if not ruolo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruolo azienda con ID {ruolo_id} non trovato"
        )

    # Valida date se fornite
    data_inizio = ruolo_update.data_inizio if ruolo_update.data_inizio is not None else ruolo.data_inizio
    data_fine = ruolo_update.data_fine if ruolo_update.data_fine is not None else ruolo.data_fine

    if data_inizio and data_fine:
        if data_fine < data_inizio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La data di fine non può essere precedente alla data di inizio"
            )

    # Aggiorna solo i campi forniti
    update_data = ruolo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ruolo, field, value)

    db.commit()
    db.refresh(ruolo)

    # Ricarica con relationships
    ruolo = db.query(RuoloAzienda).options(
        joinedload(RuoloAzienda.persona_fisica),
        joinedload(RuoloAzienda.persona_giuridica)
    ).filter(RuoloAzienda.id == ruolo_id).first()

    return ruolo


@router.delete("/{ruolo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ruolo_azienda(
    ruolo_id: int,
    current_user: User = Depends(require_permission("soggetto.delete")),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Elimina un ruolo azienda"""
    _ensure_ruoli_azienda_tables(db, tenant_schema)
    ruolo = db.query(RuoloAzienda).filter(RuoloAzienda.id == ruolo_id).first()

    if not ruolo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ruolo azienda con ID {ruolo_id} non trovato"
        )

    db.delete(ruolo)
    db.commit()

    return None
