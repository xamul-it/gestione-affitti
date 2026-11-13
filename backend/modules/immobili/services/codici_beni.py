"""Codes are unique among all beni (units and land parcels)."""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import Bene


def verifica_codice_libero(db: Session, codice: Optional[str], escludi_id: Optional[int] = None) -> None:
    """400 if another bene already uses `codice`."""
    if not codice:
        return
    query = db.query(Bene.id).filter(Bene.codice == codice)
    if escludi_id is not None:
        query = query.filter(Bene.id != escludi_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Codice '{codice}' già usato da un altro bene",
        )
