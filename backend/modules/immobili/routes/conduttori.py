from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.platform_services import EntityService
from ..models import Conduttore
from ..schemas import ConduttoreCreate, ConduttoreUpdate, ConduttoreResponse

router = APIRouter(prefix="/conduttori", tags=["conduttori"])


@router.get("/", response_model=List[ConduttoreResponse])
def get_conduttori(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recupera tutti i conduttori con paginazione"""
    service = EntityService(db, Conduttore)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{conduttore_id}", response_model=ConduttoreResponse)
def get_conduttore(conduttore_id: int, db: Session = Depends(get_db)):
    """Recupera un conduttore specifico"""
    service = EntityService(db, Conduttore)
    return service.get_or_404(conduttore_id)


@router.post("/", response_model=ConduttoreResponse, status_code=status.HTTP_201_CREATED)
def create_conduttore(conduttore: ConduttoreCreate, db: Session = Depends(get_db)):
    """Registra un soggetto come conduttore (occupante), indipendentemente da un contratto d'affitto"""
    service = EntityService(db, Conduttore)

    existing = service.find_by(soggetto_id=conduttore.soggetto_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Il soggetto {conduttore.soggetto_id} è già registrato come conduttore"
        )

    return service.create(conduttore)


@router.put("/{conduttore_id}", response_model=ConduttoreResponse)
def update_conduttore(conduttore_id: int, conduttore: ConduttoreUpdate, db: Session = Depends(get_db)):
    """Aggiorna le note di un conduttore"""
    service = EntityService(db, Conduttore)
    service.get_or_404(conduttore_id)
    return service.update(conduttore_id, conduttore, partial=True)


@router.delete("/{conduttore_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conduttore(conduttore_id: int, db: Session = Depends(get_db)):
    """Elimina un conduttore (rimuove anche le assegnazioni per CASCADE)"""
    service = EntityService(db, Conduttore)
    db_conduttore = service.get_or_404(conduttore_id)
    db.delete(db_conduttore)
    db.commit()
    return None
