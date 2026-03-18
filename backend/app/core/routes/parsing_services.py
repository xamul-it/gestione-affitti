"""
Platform endpoints for parsing service configuration.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import require_permission
from app.core.platform.models import ParsingServiceConfig
from app.core.platform_services.document_type_registry import document_type_registry

router = APIRouter(prefix="/platform/parsing-services", tags=["parsing-services"])


class ParsingServiceUpsert(BaseModel):
    service_key: str
    transport_type: str = "HTTP"
    endpoint_url: str | None = None
    redis_queue: str | None = None
    timeout_seconds: int | None = 300
    enabled: bool = True
    notes: str | None = None


@router.get("", response_model=List[Dict[str, Any]])
def list_parsing_services(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("platform.admin")),
):
    services = db.query(ParsingServiceConfig).order_by(ParsingServiceConfig.service_key.asc()).all()
    return [s.to_dict() for s in services]


@router.post("", response_model=Dict[str, Any])
def upsert_parsing_service(
    payload: ParsingServiceUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("platform.admin")),
):
    if not payload.service_key:
        raise HTTPException(status_code=400, detail="service_key obbligatorio")

    record = db.query(ParsingServiceConfig).filter(
        ParsingServiceConfig.service_key == payload.service_key
    ).first()

    if not record:
        record = ParsingServiceConfig(service_key=payload.service_key)
        db.add(record)

    record.transport_type = payload.transport_type
    record.endpoint_url = payload.endpoint_url
    record.redis_queue = payload.redis_queue
    record.timeout_seconds = payload.timeout_seconds
    record.enabled = "true" if payload.enabled else "false"
    record.notes = payload.notes

    db.commit()
    db.refresh(record)
    return record.to_dict()


@router.get("/summary", response_model=Dict[str, Any])
def parsing_services_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("platform.admin")),
):
    required_services = sorted({
        t.parsing_service
        for t in document_type_registry.get_types_with_parsing()
        if t.parsing_service
    })

    configs = db.query(ParsingServiceConfig).all()
    by_key = {c.service_key: c.to_dict() for c in configs}

    result = []
    for key in required_services:
        entry = {
            "service_key": key,
            "configured": key in by_key,
            "config": by_key.get(key),
        }
        result.append(entry)

    return {
        "required_services": result,
        "configured_services": list(by_key.values()),
    }
