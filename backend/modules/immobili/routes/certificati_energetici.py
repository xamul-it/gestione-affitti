"""
Energy certificates, read from the core APE documents.

Since the 2026-11-09 document types spec the APE is a core document (type
APE, regime SOSTITUTIVO, scadenza 10 years): the old table
immo_certificati_energetici is migrated by immobili.post_sync and kept
read-only. These endpoints keep the old response shape for existing
consumers; writes go through /documenti (tipo APE).
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db
from app.core.platform.models import Documento, EntityType, TipoDocumento
from app.core.platform_services.documento_service import DocumentoService
from ..schemas.certificati_energetici import CertificatoEnergeticoResponse

router = APIRouter(prefix="/certificati-energetici", tags=["Certificati Energetici"])

_GONE = "I certificati energetici sono documenti: usa /documenti con tipo APE"


def _query(db: Session):
    return (
        db.query(Documento)
        .join(TipoDocumento, TipoDocumento.id == Documento.tipo_documento_id)
        .options(selectinload(Documento.files), joinedload(Documento.tipo))
        .filter(
            TipoDocumento.codice == "APE",
            Documento.entity_type == EntityType.IMMOBILE,
            Documento.stato == "CORRENTE",
        )
    )


def _out(documento: Documento) -> CertificatoEnergeticoResponse:
    dati = documento.dati or {}
    return CertificatoEnergeticoResponse(
        id=documento.id,
        unita_immobiliare_id=documento.entity_id,
        tecnico_id=dati.get("tecnico_id"),
        classe_energetica=dati.get("classe"),
        indice_prestazione_energetica=dati.get("ep_gl_nren"),
        data_emissione=documento.data_riferimento,
        data_scadenza=DocumentoService(None, None, None).scadenza_effettiva(documento),
        numero_protocollo=dati.get("codice_identificativo"),
        file_path=documento.file_path,
        note=documento.note,
    )


@router.get("/", response_model=List[CertificatoEnergeticoResponse])
def get_certificati(skip: int = 0, limit: int = 100, validi_solo: bool = False, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """APE in vigore di tutte le unità."""
    result = [_out(d) for d in _query(db).order_by(Documento.data_riferimento.desc()).all()]
    if validi_solo:
        oggi = date.today()
        result = [c for c in result if c.data_scadenza and c.data_scadenza >= oggi]
    return result[skip: skip + min(limit, 500)]


@router.get("/{certificato_id}", response_model=CertificatoEnergeticoResponse)
def get_certificato(certificato_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """Un APE (id del documento)."""
    documento = _query(db).filter(Documento.id == certificato_id).first()
    if documento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificato energetico con ID {certificato_id} non trovato",
        )
    return _out(documento)


@router.get("/unita-immobiliare/{unita_immobiliare_id}", response_model=List[CertificatoEnergeticoResponse])
def get_certificati_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """APE in vigore dell'unità (lo storico è in /documenti/{id}/storico)."""
    return [_out(d) for d in _query(db).filter(Documento.entity_id == unita_immobiliare_id).all()]


@router.get("/unita-immobiliare/{unita_immobiliare_id}/valido", response_model=CertificatoEnergeticoResponse)
def get_certificato_valido_by_unita_immobiliare(unita_immobiliare_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documenti.read")),
):
    """APE in vigore e non scaduto (né decaduto) dell'unità."""
    oggi = date.today()
    for documento in _query(db).filter(Documento.entity_id == unita_immobiliare_id).all():
        out = _out(documento)
        if out.data_scadenza and out.data_scadenza >= oggi:
            return out
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Nessun certificato energetico valido trovato per l'unità immobiliare {unita_immobiliare_id}",
    )


@router.post("/", status_code=status.HTTP_410_GONE)
def create_certificato():
    raise HTTPException(status_code=status.HTTP_410_GONE, detail=_GONE)


@router.put("/{certificato_id}", status_code=status.HTTP_410_GONE)
def update_certificato(certificato_id: int):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail=_GONE)


@router.delete("/{certificato_id}", status_code=status.HTTP_410_GONE)
def delete_certificato(certificato_id: int):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail=_GONE)
