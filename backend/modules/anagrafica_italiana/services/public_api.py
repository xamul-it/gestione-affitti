"""
Public API — the surface other modules use to find-or-create a
SoggettoAnagrafico, per the module-communication architecture
(docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md).

Other modules call the functions here — directly, in-process, since
DEPLOY_MODE is "monolith" today — instead of importing SoggettoAnagrafico
or SimilarityMatchingService directly. Returns DTOs, never raw ORM objects.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session


@dataclass
class SoggettoDTO:
    id: int
    nome: Optional[str]
    cognome: Optional[str]
    creato_ora: bool  # True if a new SoggettoAnagrafico was just created by this call


def trova_o_crea_soggetto(
    db: Session,
    *,
    nome: str,
    cognome: str,
    data_nascita: Optional[date] = None,
    codice_fiscale: Optional[str] = None,
    tipo_documento_identita: Optional[str] = None,
    numero_documento_identita: Optional[str] = None,
    stato_rilascio_documento: Optional[str] = None,
) -> SoggettoDTO:
    """
    Finds an existing SoggettoAnagrafico by a certain identifier (codice
    fiscale or identity document), or creates a new one if none matches.

    "Certain" means an identifier-based match only (codice_fiscale or
    numero_documento_identita) — a fuzzy name+birth-date match that happens
    to score as high as an exact match is NOT treated as certain here, to
    avoid two different people who share a common name and birth date being
    silently merged into one registry entry.
    """
    from ..models import SoggettoAnagrafico, TipoSoggetto
    from .similarity_matching_service import SimilarityMatchingService

    service = SimilarityMatchingService(db)
    candidates = service.find_similar(
        codice_fiscale=codice_fiscale,
        tipo_documento_identita=tipo_documento_identita,
        numero_documento_identita=numero_documento_identita,
        stato_rilascio_documento=stato_rilascio_documento,
        nome=nome,
        cognome=cognome,
        data_nascita=data_nascita,
    )

    certain = [
        c for c in candidates
        if "codice_fiscale" in c["match_fields"] or "numero_documento_identita" in c["match_fields"]
    ]
    if certain:
        return SoggettoDTO(id=certain[0]["soggetto_id"], nome=nome, cognome=cognome, creato_ora=False)

    soggetto = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome=nome,
        cognome=cognome,
        data_nascita=data_nascita,
        codice_fiscale=codice_fiscale.upper() if codice_fiscale else None,
        tipo_documento_identita=tipo_documento_identita,
        numero_documento_identita=numero_documento_identita.upper() if numero_documento_identita else None,
        stato_rilascio_documento=stato_rilascio_documento,
    )
    db.add(soggetto)
    db.flush()
    return SoggettoDTO(id=soggetto.id, nome=nome, cognome=cognome, creato_ora=True)
