"""Catastal changes log: compare a bene (unit or land parcel) with the new values and record each change."""
from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Bene, Terreno, VariazioneCatastale

CAMPI_CATASTALI = (
    "categoria_catastale_id", "rendita_catastale", "superficie_mq",
    "foglio", "particella", "subalterno", "indirizzo", "piano",
)

# Land parcel: surface is the sum of its portions, computed by the server.
CAMPI_CATASTALI_TERRENO = (
    "sezione_catastale", "foglio", "particella", "subalterno", "indirizzo", "superficie_mq",
)


def _text(value) -> Optional[str]:
    return None if value is None else str(value)


def registra_variazioni(
    db: Session,
    unita: Bene,
    nuovi: dict,
    *,
    origine: str,
    documento_id: Optional[int],
    data_riferimento: date,
    utente_id: Optional[int],
) -> List[VariazioneCatastale]:
    """Write one row per catastal field whose value changes. Does not set the attributes."""
    rows = []
    campi = CAMPI_CATASTALI_TERRENO if isinstance(unita, Terreno) else CAMPI_CATASTALI
    for campo in campi:
        if campo not in nuovi:
            continue
        prima, dopo = getattr(unita, campo), nuovi[campo]
        if prima == dopo:
            continue
        rows.append(VariazioneCatastale(
            bene_id=unita.id, documento_id=documento_id, origine=origine, campo=campo,
            valore_precedente=_text(prima), valore_nuovo=_text(dopo),
            data_riferimento=data_riferimento, utente_id=utente_id,
        ))
    db.add_all(rows)
    return rows
