"""
Endpoints per il monitoraggio e il controllo manuale dello scheduler di
polling PEC.

Tutti gli endpoint richiedono il permesso `pec.admin`.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pec/scheduler",
    tags=["PEC - Scheduler"],
    dependencies=[Depends(require_permission("pec.admin"))],
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_tenant_schema(request: Request) -> str:
    """
    Estrae il tenant_schema dalla request (impostato dal TenantMiddleware).
    Solleva 400 se non disponibile.
    """
    schema = getattr(request.state, "tenant_schema", None)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile determinare il tenant della richiesta",
        )
    return schema


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def get_scheduler_status() -> dict[str, Any]:
    """
    Restituisce lo stato corrente dello scheduler PEC.

    Risposta:
        - running (bool): se lo scheduler è attivo
        - jobs (list): lista dei job registrati con id, name e next_run
    """
    from gestione_pec.services.polling_scheduler import get_scheduler

    scheduler = get_scheduler()
    return scheduler.get_status()


@router.post("/trigger/{casella_id}", status_code=status.HTTP_202_ACCEPTED)
def trigger_casella(
    casella_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Avvia immediatamente il polling per una singola casella PEC.

    Il job viene eseguito in background: la risposta 202 viene restituita
    subito senza aspettare il completamento.
    """
    from gestione_pec.models.casella import PecCasella
    from gestione_pec.services.polling_scheduler import get_scheduler

    tenant_schema = _get_tenant_schema(request)

    # Verifica che la casella esista e sia attiva nel tenant corrente
    casella = (
        db.query(PecCasella)
        .filter(PecCasella.id == casella_id, PecCasella.is_attiva == True)  # noqa: E712
        .first()
    )
    if not casella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Casella PEC {casella_id} non trovata o non attiva",
        )

    scheduler = get_scheduler()
    scheduler.trigger_now(casella_id, tenant_schema)

    return {
        "ok": True,
        "message": f"Polling avviato per casella {casella_id}",
        "casella_id": casella_id,
        "tenant_schema": tenant_schema,
    }


@router.post("/trigger-all", status_code=status.HTTP_202_ACCEPTED)
def trigger_all(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Avvia immediatamente il polling per tutte le caselle attive del tenant
    corrente.

    I job vengono avviati in background: la risposta 202 viene restituita
    subito senza aspettare i completamenti.
    """
    from gestione_pec.models.casella import PecCasella
    from gestione_pec.services.polling_scheduler import get_scheduler

    tenant_schema = _get_tenant_schema(request)

    caselle = (
        db.query(PecCasella)
        .filter(PecCasella.is_attiva == True)  # noqa: E712
        .all()
    )

    scheduler = get_scheduler()
    triggered = []
    for casella in caselle:
        scheduler.trigger_now(casella.id, tenant_schema)
        triggered.append(casella.id)

    logger.info(
        "[PecScheduler] trigger-all per tenant %s: %d caselle",
        tenant_schema, len(triggered),
    )

    return {
        "ok": True,
        "message": f"Polling avviato per {len(triggered)} caselle",
        "caselle_ids": triggered,
        "tenant_schema": tenant_schema,
    }
