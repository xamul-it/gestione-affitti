from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.platform_services import EntityService
from ..models import Proprietario
from ..schemas import (
    ProprietarioCreate,
    ProprietarioUpdate,
    ProprietarioResponse,
)

router = APIRouter(prefix="/proprietari", tags=["proprietari"])


@router.get("/", response_model=List[ProprietarioResponse])
def get_proprietari(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = False,
    db: Session = Depends(get_db)
):
    """Recupera tutti i proprietari con paginazione"""
    service = EntityService(db, Proprietario)

    # Usa filtri se necessario
    filters = {"attivo": True} if attivi_solo else None

    # Usa EntityService con paginazione e ordinamento
    return service.get_all(
        skip=skip,
        limit=limit,
        filters=filters,
        order_by="cognome"
    )


@router.get("/{proprietario_id}", response_model=ProprietarioResponse)
def get_proprietario(proprietario_id: int, db: Session = Depends(get_db)):
    """Recupera un proprietario specifico"""
    service = EntityService(db, Proprietario)
    # EntityService.get_or_404 solleva automaticamente HTTPException
    return service.get_or_404(proprietario_id)


@router.post("/", response_model=ProprietarioResponse, status_code=status.HTTP_201_CREATED)
def create_proprietario(proprietario: ProprietarioCreate, db: Session = Depends(get_db)):
    """Crea un nuovo proprietario"""
    service = EntityService(db, Proprietario)

    # Verifica se il codice fiscale esiste già usando EntityService
    existing = service.find_by(codice_fiscale=proprietario.codice_fiscale)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codice fiscale già esistente"
        )

    # Usa EntityService per creare
    return service.create(proprietario)


@router.put("/{proprietario_id}", response_model=ProprietarioResponse)
def update_proprietario(
    proprietario_id: int,
    proprietario: ProprietarioUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna un proprietario"""
    service = EntityService(db, Proprietario)

    # Verifica che esista
    db_proprietario = service.get_or_404(proprietario_id)

    # Verifica codice fiscale duplicato (escluso se stesso)
    if proprietario.codice_fiscale and proprietario.codice_fiscale != db_proprietario.codice_fiscale:
        existing = service.find_by(codice_fiscale=proprietario.codice_fiscale)
        if existing and existing.id != proprietario_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Codice fiscale già esistente"
            )

    # Usa EntityService per aggiornare (partial=True per PATCH behavior)
    return service.update(proprietario_id, proprietario, partial=True)


@router.delete("/{proprietario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proprietario(proprietario_id: int, db: Session = Depends(get_db)):
    """Elimina un proprietario (soft delete)"""
    service = EntityService(db, Proprietario)

    # Verifica che esista
    db_proprietario = service.get_or_404(proprietario_id)

    # Soft delete: aggiorna il campo attivo
    db_proprietario.attivo = False
    db.commit()
    return None
