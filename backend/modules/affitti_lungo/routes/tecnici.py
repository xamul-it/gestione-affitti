from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import List, Optional
from app.core.database import get_db, get_tenant_schema
from ..models import Tecnico
from ..schemas.tecnici import TecnicoCreate, TecnicoUpdate, TecnicoResponse

router = APIRouter(prefix="/tecnici", tags=["Tecnici"])


@router.get("/", response_model=List[TecnicoResponse])
def get_tecnici(
    skip: int = 0,
    limit: int = 100,
    attivi_solo: bool = False,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Ottieni lista di tutti i tecnici"""
    if not tenant_schema:
        return []
    inspector = inspect(db.get_bind())
    if not inspector.has_table("tecnici", schema=tenant_schema):
        return []
    query = db.query(Tecnico)
    if attivi_solo:
        query = query.filter(Tecnico.attivo == True)
    tecnici = query.offset(skip).limit(limit).all()
    return tecnici


@router.get("/{tecnico_id}", response_model=TecnicoResponse)
def get_tecnico(
    tecnico_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Ottieni dettagli di un tecnico specifico"""
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant schema mancante")
    inspector = inspect(db.get_bind())
    if not inspector.has_table("tecnici", schema=tenant_schema):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tabella tecnici non presente")
    tecnico = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    if not tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {tecnico_id} non trovato"
        )
    return tecnico


@router.post("/", response_model=TecnicoResponse, status_code=status.HTTP_201_CREATED)
def create_tecnico(
    tecnico: TecnicoCreate,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Crea un nuovo tecnico"""
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant schema mancante")
    inspector = inspect(db.get_bind())
    if not inspector.has_table("tecnici", schema=tenant_schema):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tabella tecnici non presente")
    new_tecnico = Tecnico(**tecnico.model_dump())
    db.add(new_tecnico)
    db.commit()
    db.refresh(new_tecnico)
    return new_tecnico


@router.put("/{tecnico_id}", response_model=TecnicoResponse)
def update_tecnico(
    tecnico_id: int,
    tecnico: TecnicoUpdate,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Aggiorna un tecnico esistente"""
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant schema mancante")
    inspector = inspect(db.get_bind())
    if not inspector.has_table("tecnici", schema=tenant_schema):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tabella tecnici non presente")
    db_tecnico = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    if not db_tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {tecnico_id} non trovato"
        )

    # Aggiorna solo i campi forniti
    for field, value in tecnico.model_dump(exclude_unset=True).items():
        setattr(db_tecnico, field, value)

    db.commit()
    db.refresh(db_tecnico)
    return db_tecnico


@router.delete("/{tecnico_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tecnico(
    tecnico_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """Elimina un tecnico (soft delete - imposta attivo=False)"""
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant schema mancante")
    inspector = inspect(db.get_bind())
    if not inspector.has_table("tecnici", schema=tenant_schema):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tabella tecnici non presente")
    db_tecnico = db.query(Tecnico).filter(Tecnico.id == tecnico_id).first()
    if not db_tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {tecnico_id} non trovato"
        )

    # Soft delete
    db_tecnico.attivo = False
    db.commit()
    return None
