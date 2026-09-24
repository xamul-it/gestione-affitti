from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
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
def get_proprietari(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recupera tutti i proprietari con paginazione"""
    service = EntityService(db, Proprietario)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{proprietario_id}", response_model=ProprietarioResponse)
def get_proprietario(proprietario_id: int, db: Session = Depends(get_db)):
    """Recupera un proprietario specifico"""
    service = EntityService(db, Proprietario)
    return service.get_or_404(proprietario_id)


@router.post("/", response_model=ProprietarioResponse, status_code=status.HTTP_201_CREATED)
def create_proprietario(proprietario: ProprietarioCreate, db: Session = Depends(get_db)):
    """Registra un soggetto come proprietario (titolare di un diritto reale su un immobile)"""
    service = EntityService(db, Proprietario)

    existing = service.find_by(soggetto_id=proprietario.soggetto_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il soggetto {proprietario.soggetto_id} è già registrato come proprietario"
        )

    return service.create(proprietario)


@router.put("/{proprietario_id}", response_model=ProprietarioResponse)
def update_proprietario(
    proprietario_id: int,
    proprietario: ProprietarioUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna le note di un proprietario"""
    service = EntityService(db, Proprietario)
    service.get_or_404(proprietario_id)
    return service.update(proprietario_id, proprietario, partial=True)


@router.delete("/{proprietario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proprietario(proprietario_id: int, db: Session = Depends(get_db)):
    """Elimina un proprietario (rimuove anche i diritti di proprietà collegati per CASCADE)"""
    service = EntityService(db, Proprietario)
    db_proprietario = service.get_or_404(proprietario_id)
    db.delete(db_proprietario)
    db.commit()
    return None
