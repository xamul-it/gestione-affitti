"""
Single upload point for unit documents (/immobili/documenti).
POST /analizza    multipart file -> AnalisiDocumento (nothing saved but the temp upload)
GET  /analizza/{token}  analysis of a scan read by the OCR service
POST /rianalizza  token + chosen type/unit -> AnalisiDocumento
POST /conferma    token + confirmed choices -> document saved on the unit
Spec: docs/superpowers/specs/2026-11-10-caricamento-unico-documenti-immobili-design.md
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth.dependencies import require_permission
from app.core.auth.models import User
from app.core.database import get_db, get_tenant_schema

from ..schemas.caricamento_documenti import (
    AnalisiDocumento, ConfermaDocumento, ConfermaRisultato, RianalisiDocumento,
)
from ..services import upload_temporanei
from ..services.lettura_documenti import caricamento

router = APIRouter(prefix="/unita-immobiliari/caricamento-documenti", tags=["Caricamento documenti immobili"])

REQUIRED_PERMISSIONS = ["documenti.write", "immobile.edit"]
MAX_SIZE = 20 * 1024 * 1024


def _tenant(tenant_schema: Optional[str]) -> str:
    if not tenant_schema:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant schema mancante")
    return tenant_schema


def _permessi(user: User) -> set:
    return {"*"} if user.is_superuser else set(user.get_permissions())


@router.post("/analizza", response_model=AnalisiDocumento)
def analizza(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission(REQUIRED_PERMISSIONS)),
):
    tenant_schema = _tenant(tenant_schema)
    content = file.file.read(MAX_SIZE + 1)
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=422, detail="File troppo grande (massimo 20 MB)")
    return caricamento.analizza_contenuto(db, tenant_schema, _permessi(current_user), current_user.id, content,
                                          file.filename or "documento", file.content_type)


@router.get("/analizza/{upload_token}", response_model=AnalisiDocumento)
def stato_analisi(
    upload_token: str,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission(REQUIRED_PERMISSIONS)),
):
    try:
        return caricamento.stato_analisi(db, _tenant(tenant_schema), _permessi(current_user), upload_token)
    except caricamento.CaricamentoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/rianalizza", response_model=AnalisiDocumento)
def rianalizza(
    body: RianalisiDocumento,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission(REQUIRED_PERMISSIONS)),
):
    try:
        return caricamento.rianalizza(db, _tenant(tenant_schema), _permessi(current_user),
                                      body.upload_token, body.tipo_codice, body.unita_id)
    except caricamento.CaricamentoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("/conferma", response_model=ConfermaRisultato)
def conferma(
    body: ConfermaDocumento,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    current_user: User = Depends(require_permission(REQUIRED_PERMISSIONS)),
):
    tenant_schema = _tenant(tenant_schema)
    try:
        documento = caricamento.conferma(db, tenant_schema, current_user.id, body)
        db.commit()
    except caricamento.CaricamentoError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    upload_temporanei.elimina(tenant_schema, body.upload_token)
    return ConfermaRisultato(documento_id=documento.id, unita_id=body.unita_id)
