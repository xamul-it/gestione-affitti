from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from ..models import DirittoImmobile, Bene, Proprietario
from ..schemas import (
    DirittoImmobileCreate,
    DirittoImmobileUpdate,
    DirittoImmobileResponse,
)

router = APIRouter(prefix="/diritti-immobile", tags=["diritti-immobile"])


@router.get("/", response_model=List[DirittoImmobileResponse])
def get_diritti(
    bene_id: Optional[int] = Query(None),
    proprietario_id: Optional[int] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.view"))
):
    """Recupera tutti i diritti con filtri opzionali"""
    query = db.query(DirittoImmobile)

    if bene_id:
        query = query.filter(DirittoImmobile.bene_id == bene_id)
    if proprietario_id:
        query = query.filter(DirittoImmobile.proprietario_id == proprietario_id)

    return query.order_by(DirittoImmobile.bene_id, DirittoImmobile.tipo_diritto).all()


@router.get("/bene/{bene_id}", response_model=List[DirittoImmobileResponse])
def get_diritti_by_bene(bene_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.view"))):
    """Recupera tutti i diritti di un bene (unità o terreno)"""
    # Verifica che il bene esista
    bene = db.query(Bene).filter(Bene.id == bene_id).first()
    if not bene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bene non trovato"
        )

    return db.query(DirittoImmobile).filter(
        DirittoImmobile.bene_id == bene_id
    ).all()


@router.get("/proprietario/{proprietario_id}", response_model=List[DirittoImmobileResponse])
def get_diritti_by_proprietario(proprietario_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.view"))):
    """Recupera tutti i diritti di un proprietario specifico"""
    # Verifica che il proprietario esista
    proprietario = db.query(Proprietario).filter(Proprietario.id == proprietario_id).first()
    if not proprietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proprietario non trovato"
        )

    return db.query(DirittoImmobile).filter(
        DirittoImmobile.proprietario_id == proprietario_id
    ).all()


@router.get("/{diritto_id}", response_model=DirittoImmobileResponse)
def get_diritto(diritto_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.view"))):
    """Recupera un diritto specifico"""
    diritto = db.query(DirittoImmobile).filter(DirittoImmobile.id == diritto_id).first()
    if not diritto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diritto non trovato"
        )
    return diritto


@router.post("/", response_model=DirittoImmobileResponse, status_code=status.HTTP_201_CREATED)
def create_diritto(diritto: DirittoImmobileCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.create"))):
    """Crea un nuovo diritto su un bene"""
    # Verifica che il bene esista
    bene = db.query(Bene).filter(Bene.id == diritto.bene_id).first()
    if not bene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bene non trovato"
        )

    # Verifica che il proprietario esista
    proprietario = db.query(Proprietario).filter(Proprietario.id == diritto.proprietario_id).first()
    if not proprietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proprietario non trovato"
        )

    db_diritto = DirittoImmobile(**diritto.model_dump())
    db.add(db_diritto)
    db.commit()
    db.refresh(db_diritto)
    return db_diritto


@router.put("/{diritto_id}", response_model=DirittoImmobileResponse)
def update_diritto(
    diritto_id: int,
    diritto: DirittoImmobileUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.edit"))
):
    """Aggiorna un diritto"""
    db_diritto = db.query(DirittoImmobile).filter(DirittoImmobile.id == diritto_id).first()
    if not db_diritto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diritto non trovato"
        )

    for key, value in diritto.model_dump(exclude_unset=True).items():
        setattr(db_diritto, key, value)

    db.commit()
    db.refresh(db_diritto)
    return db_diritto


@router.delete("/{diritto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diritto(diritto_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("proprietario.delete"))):
    """Elimina un diritto"""
    db_diritto = db.query(DirittoImmobile).filter(DirittoImmobile.id == diritto_id).first()
    if not db_diritto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diritto non trovato"
        )

    db.delete(db_diritto)
    db.commit()
    return None
