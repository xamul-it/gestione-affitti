from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.core.database import get_db
from ..models import CertificatoEnergetico, UnitaImmobiliare, Tecnico
from ..schemas.certificati_energetici import (
    CertificatoEnergeticoCreate,
    CertificatoEnergeticoUpdate,
    CertificatoEnergeticoResponse,
)

router = APIRouter(prefix="/certificati-energetici", tags=["Certificati Energetici"])


@router.get("/", response_model=List[CertificatoEnergeticoResponse])
def get_certificati(
    skip: int = 0,
    limit: int = 100,
    validi_solo: bool = False,
    db: Session = Depends(get_db)
):
    """Ottieni lista di tutti i certificati energetici"""
    query = db.query(CertificatoEnergetico)
    if validi_solo:
        oggi = date.today()
        query = query.filter(CertificatoEnergetico.data_scadenza >= oggi)
    certificati = query.offset(skip).limit(limit).all()
    return certificati


@router.get("/{certificato_id}", response_model=CertificatoEnergeticoResponse)
def get_certificato(certificato_id: int, db: Session = Depends(get_db)):
    """Ottieni dettagli di un certificato energetico specifico"""
    certificato = db.query(CertificatoEnergetico).filter(
        CertificatoEnergetico.id == certificato_id
    ).first()
    if not certificato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificato energetico con ID {certificato_id} non trovato"
        )
    return certificato


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[CertificatoEnergeticoResponse])
def get_certificati_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti i certificati energetici di un'unità immobiliare"""
    certificati = db.query(CertificatoEnergetico).filter(
        CertificatoEnergetico.unita_immobiliare_id == unita_immobiliare_id
    ).order_by(CertificatoEnergetico.data_emissione.desc()).all()
    return certificati


@router.get("/unita-immobiliare/{unita_immobiliare_id}/valido", response_model=CertificatoEnergeticoResponse)
def get_certificato_valido_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db)):
    """Ottieni il certificato energetico valido più recente di un'unità immobiliare"""
    oggi = date.today()
    certificato = db.query(CertificatoEnergetico).filter(
        CertificatoEnergetico.unita_immobiliare_id == unita_immobiliare_id,
        CertificatoEnergetico.data_scadenza >= oggi
    ).order_by(CertificatoEnergetico.data_emissione.desc()).first()

    if not certificato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nessun certificato energetico valido trovato per l'unità immobiliare {unita_immobiliare_id}"
        )
    return certificato


@router.post("/", response_model=CertificatoEnergeticoResponse, status_code=status.HTTP_201_CREATED)
def create_certificato(certificato: CertificatoEnergeticoCreate, db: Session = Depends(get_db)):
    """Crea un nuovo certificato energetico"""
    # Verifica che l'unità immobiliare esista
    unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.id == certificato.unita_immobiliare_id).first()
    if not unita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unità immobiliare con ID {certificato.unita_immobiliare_id} non trovato"
        )

    # Verifica che il tecnico esista
    tecnico = db.query(Tecnico).filter(Tecnico.id == certificato.tecnico_id).first()
    if not tecnico:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnico con ID {certificato.tecnico_id} non trovato"
        )

    # Verifica che data_emissione < data_scadenza
    if certificato.data_emissione >= certificato.data_scadenza:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La data di scadenza deve essere successiva alla data di emissione"
        )

    new_certificato = CertificatoEnergetico(**certificato.model_dump())
    db.add(new_certificato)
    db.commit()
    db.refresh(new_certificato)
    return new_certificato


@router.put("/{certificato_id}", response_model=CertificatoEnergeticoResponse)
def update_certificato(
    certificato_id: int,
    certificato: CertificatoEnergeticoUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna un certificato energetico esistente"""
    db_certificato = db.query(CertificatoEnergetico).filter(
        CertificatoEnergetico.id == certificato_id
    ).first()
    if not db_certificato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificato energetico con ID {certificato_id} non trovato"
        )

    # Aggiorna solo i campi forniti
    update_data = certificato.model_dump(exclude_unset=True)

    # Verifica vincoli se vengono aggiornate le date
    if "data_emissione" in update_data or "data_scadenza" in update_data:
        emissione = update_data.get("data_emissione", db_certificato.data_emissione)
        scadenza = update_data.get("data_scadenza", db_certificato.data_scadenza)
        if emissione >= scadenza:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La data di scadenza deve essere successiva alla data di emissione"
            )

    for field, value in update_data.items():
        setattr(db_certificato, field, value)

    db.commit()
    db.refresh(db_certificato)
    return db_certificato


@router.delete("/{certificato_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificato(certificato_id: int, db: Session = Depends(get_db)):
    """Elimina un certificato energetico"""
    db_certificato = db.query(CertificatoEnergetico).filter(
        CertificatoEnergetico.id == certificato_id
    ).first()
    if not db_certificato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificato energetico con ID {certificato_id} non trovato"
        )

    db.delete(db_certificato)
    db.commit()
    return None
