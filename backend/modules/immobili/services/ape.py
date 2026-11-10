"""Energy class of units, read from their current APE (the APE is the only source)."""
from typing import Dict, Iterable

from sqlalchemy.orm import Session

from app.core.platform.models import Documento, EntityType, TipoDocumento


def classi_da_ape(db: Session, unita_ids: Iterable[int]) -> Dict[int, str]:
    ids = list(unita_ids)
    if not ids:
        return {}
    rows = (db.query(Documento.entity_id, Documento.dati)
            .join(TipoDocumento, TipoDocumento.id == Documento.tipo_documento_id)
            .filter(TipoDocumento.codice == "APE", Documento.entity_type == EntityType.IMMOBILE,
                    Documento.entity_id.in_(ids), Documento.stato == "CORRENTE"))
    return {entity_id: (dati or {}).get("classe") for entity_id, dati in rows if (dati or {}).get("classe")}
