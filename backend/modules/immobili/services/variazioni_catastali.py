"""Catastal changes log: compare a unit with the new values and record each change."""
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import UnitaImmobiliare, VariazioneCatastale

CAMPI_CATASTALI = (
    "categoria_catastale_id", "rendita_catastale", "superficie_mq",
    "foglio", "particella", "subalterno", "indirizzo", "piano",
)


def _text(value) -> Optional[str]:
    return None if value is None else str(value)


def registra_variazioni(
    db: Session,
    unita: UnitaImmobiliare,
    nuovi: dict,
    *,
    origine: str,
    documento_id: Optional[int],
    data_riferimento: date,
    utente_id: Optional[int],
) -> List[VariazioneCatastale]:
    """Write one row per catastal field whose value changes. Does not set the attributes."""
    rows = []
    for campo in CAMPI_CATASTALI:
        if campo not in nuovi:
            continue
        prima, dopo = getattr(unita, campo), nuovi[campo]
        if prima == dopo:
            continue
        rows.append(VariazioneCatastale(
            unita_immobiliare_id=unita.id, documento_id=documento_id, origine=origine, campo=campo,
            valore_precedente=_text(prima), valore_nuovo=_text(dopo),
            data_riferimento=data_riferimento, utente_id=utente_id,
        ))
    db.add_all(rows)
    return rows
