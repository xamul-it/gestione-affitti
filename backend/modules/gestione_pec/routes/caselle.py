"""
Route per la gestione delle caselle PEC e degli utenti abilitati.

Tutti gli endpoint richiedono il permesso `pec.admin`.
La cifratura delle credenziali avviene qui, nel route layer,
prima del salvataggio nel database.
"""
import logging
import socket
from typing import Any

import imapclient
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth.dependencies import require_permission

from ..models.casella import PecCasella
from ..models.utente_abilitato import PecUtenteAbilitato
from ..schemas.casella import (
    CasellaCreate,
    CasellaList,
    CasellaRead,
    CasellaUpdate,
    TestConnessioneResult,
)
from ..schemas.utente_abilitato import (
    UtenteAbilitatoCreate,
    UtenteAbilitatoRead,
    UtenteAbilitatoUpdate,
)
from ..services.crypto_service import decrypt_credential, encrypt_credential

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pec/caselle",
    tags=["PEC - Caselle"],
    dependencies=[Depends(require_permission("pec.admin"))],
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_casella_or_404(casella_id: int, db: Session) -> PecCasella:
    casella = db.query(PecCasella).filter(PecCasella.id == casella_id).first()
    if not casella:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Casella PEC con ID {casella_id} non trovata",
        )
    return casella


def _get_utente_abilitato_or_404(
    casella_id: int, user_id: int, db: Session
) -> PecUtenteAbilitato:
    utente = (
        db.query(PecUtenteAbilitato)
        .filter(
            PecUtenteAbilitato.casella_id == casella_id,
            PecUtenteAbilitato.user_id == user_id,
        )
        .first()
    )
    if not utente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utente {user_id} non abilitato alla casella {casella_id}",
        )
    return utente


# ---------------------------------------------------------------------------
# Caselle CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[CasellaList])
def list_caselle(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[PecCasella]:
    """Restituisce l'elenco compatto delle caselle PEC."""
    return db.query(PecCasella).offset(skip).limit(limit).all()


@router.post("/", response_model=CasellaRead, status_code=status.HTTP_201_CREATED)
def create_casella(
    payload: CasellaCreate,
    db: Session = Depends(get_db),
) -> CasellaRead:
    """Crea una nuova casella PEC cifrando le credenziali prima del salvataggio."""
    # Verifica unicità indirizzo PEC
    existing = (
        db.query(PecCasella)
        .filter(PecCasella.indirizzo_pec == payload.indirizzo_pec)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Casella PEC con indirizzo '{payload.indirizzo_pec}' già esistente",
        )

    data = payload.model_dump(exclude={"username", "password"})
    data["username_enc"] = encrypt_credential(payload.username)
    data["password_enc"] = encrypt_credential(payload.password)

    casella = PecCasella(**data)
    db.add(casella)
    db.commit()
    db.refresh(casella)
    return CasellaRead.from_orm_with_display(casella)


@router.get("/{casella_id}", response_model=CasellaRead)
def get_casella(
    casella_id: int,
    db: Session = Depends(get_db),
) -> CasellaRead:
    """Restituisce il dettaglio di una casella PEC."""
    casella = _get_casella_or_404(casella_id, db)
    return CasellaRead.from_orm_with_display(casella)


@router.put("/{casella_id}", response_model=CasellaRead)
def update_casella(
    casella_id: int,
    payload: CasellaUpdate,
    db: Session = Depends(get_db),
) -> CasellaRead:
    """Aggiorna una casella PEC. Cifra le credenziali se fornite in chiaro."""
    casella = _get_casella_or_404(casella_id, db)

    update_data = payload.model_dump(exclude_unset=True, exclude={"username", "password"})

    # Verifica unicità indirizzo PEC se viene aggiornato
    if "indirizzo_pec" in update_data and update_data["indirizzo_pec"] != casella.indirizzo_pec:
        existing = (
            db.query(PecCasella)
            .filter(PecCasella.indirizzo_pec == update_data["indirizzo_pec"])
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Casella PEC con indirizzo '{update_data['indirizzo_pec']}' già esistente",
            )

    # Aggiorna credenziali cifrate solo se fornite
    if payload.username is not None:
        update_data["username_enc"] = encrypt_credential(payload.username)
    if payload.password is not None:
        update_data["password_enc"] = encrypt_credential(payload.password)

    for field, value in update_data.items():
        setattr(casella, field, value)

    db.commit()
    db.refresh(casella)
    return CasellaRead.from_orm_with_display(casella)


@router.delete("/{casella_id}")
def delete_casella(
    casella_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Soft delete: disattiva la casella PEC (is_attiva=False)."""
    casella = _get_casella_or_404(casella_id, db)
    casella.is_attiva = False
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Test connessione IMAP
# ---------------------------------------------------------------------------


@router.post("/{casella_id}/test-connessione", response_model=TestConnessioneResult)
def test_connessione(
    casella_id: int,
    db: Session = Depends(get_db),
) -> TestConnessioneResult:
    """
    Tenta una connessione IMAP con le credenziali decifrate della casella.
    Timeout 10 secondi. Non modifica lo stato della casella.
    """
    casella = _get_casella_or_404(casella_id, db)

    try:
        username = decrypt_credential(casella.username_enc)
        password = decrypt_credential(casella.password_enc)
    except Exception as exc:
        logger.error("Errore decifratura credenziali casella %s: %s", casella_id, exc)
        return TestConnessioneResult(
            successo=False,
            messaggio="Errore interno: impossibile decifrare le credenziali",
            num_messaggi=None,
        )

    try:
        with imapclient.IMAPClient(
            host=casella.imap_host,
            port=casella.imap_port,
            ssl=casella.imap_ssl,
            timeout=10,
        ) as client:
            client.login(username, password)
            inbox_info = client.select_folder(casella.imap_folder, readonly=True)
            num_messages = inbox_info.get(b"EXISTS", 0)
        return TestConnessioneResult(
            successo=True,
            messaggio="Connessione riuscita",
            num_messaggi=num_messages,
        )
    except (socket.timeout, socket.gaierror) as exc:
        return TestConnessioneResult(
            successo=False,
            messaggio=f"Errore di rete: {exc}",
            num_messaggi=None,
        )
    except Exception as exc:
        return TestConnessioneResult(
            successo=False,
            messaggio=str(exc),
            num_messaggi=None,
        )


# ---------------------------------------------------------------------------
# Utenti abilitati
# ---------------------------------------------------------------------------


@router.get("/{casella_id}/utenti", response_model=list[UtenteAbilitatoRead])
def list_utenti_abilitati(
    casella_id: int,
    db: Session = Depends(get_db),
) -> list[PecUtenteAbilitato]:
    """Restituisce gli utenti abilitati a una casella PEC."""
    _get_casella_or_404(casella_id, db)
    return (
        db.query(PecUtenteAbilitato)
        .filter(PecUtenteAbilitato.casella_id == casella_id)
        .all()
    )


@router.post(
    "/{casella_id}/utenti",
    response_model=UtenteAbilitatoRead,
    status_code=status.HTTP_201_CREATED,
)
def add_utente_abilitato(
    casella_id: int,
    payload: UtenteAbilitatoCreate,
    db: Session = Depends(get_db),
) -> PecUtenteAbilitato:
    """Abilita un utente a una casella PEC."""
    _get_casella_or_404(casella_id, db)

    existing = (
        db.query(PecUtenteAbilitato)
        .filter(
            PecUtenteAbilitato.casella_id == casella_id,
            PecUtenteAbilitato.user_id == payload.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Utente {payload.user_id} già abilitato alla casella {casella_id}",
        )

    utente = PecUtenteAbilitato(
        casella_id=casella_id,
        **payload.model_dump(),
    )
    db.add(utente)
    db.commit()
    db.refresh(utente)
    return utente


@router.put("/{casella_id}/utenti/{user_id}", response_model=UtenteAbilitatoRead)
def update_utente_abilitato(
    casella_id: int,
    user_id: int,
    payload: UtenteAbilitatoUpdate,
    db: Session = Depends(get_db),
) -> PecUtenteAbilitato:
    """Aggiorna i permessi di un utente abilitato a una casella PEC."""
    utente = _get_utente_abilitato_or_404(casella_id, user_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(utente, field, value)

    db.commit()
    db.refresh(utente)
    return utente


@router.delete("/{casella_id}/utenti/{user_id}")
def remove_utente_abilitato(
    casella_id: int,
    user_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Rimuove l'abilitazione di un utente a una casella PEC."""
    utente = _get_utente_abilitato_or_404(casella_id, user_id, db)
    db.delete(utente)
    db.commit()
    return {"ok": True}
