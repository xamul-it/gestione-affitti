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

from .similarity_matching_service import SimilarityMatchingService


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
) -> Optional[SoggettoDTO]:
    """
    Finds an existing SoggettoAnagrafico by a certain identifier (codice
    fiscale, or a complete identity document: tipo+numero+stato), or
    creates a new one if none matches.

    "Certain" means an identifier-based match only (codice_fiscale or
    numero_documento_identita) — a fuzzy name+birth-date match that happens
    to score as high as an exact match is NOT treated as certain here, to
    avoid two different people who share a common name and birth date being
    silently merged into one registry entry.

    Returns None (creates nothing) when the caller supplied neither a
    codice fiscale nor a complete identity document: creating a registry
    entry with no identifier at all would only ever produce a new,
    unlinkable duplicate on every single call, which is worse for the
    registry than simply not linking this particular guest/contact to it.
    Callers should treat None as "leave the link unset", not as an error.

    On a certain match, backfills any identifier field the existing record
    doesn't have yet with what THIS call supplied — never overwrites an
    already-populated field. Without this, a person first seen with only a
    passport number could never become findable by a codice fiscale they
    provide on a later visit.
    """
    from ..models import SoggettoAnagrafico, TipoSoggetto

    codice_fiscale = SimilarityMatchingService._normalizza(codice_fiscale)
    tipo_documento_identita = SimilarityMatchingService._normalizza(tipo_documento_identita)
    numero_documento_identita = SimilarityMatchingService._normalizza(numero_documento_identita)
    stato_rilascio_documento = SimilarityMatchingService._normalizza(stato_rilascio_documento)

    ha_documento_completo = bool(
        tipo_documento_identita and numero_documento_identita and stato_rilascio_documento
    )
    if not codice_fiscale and not ha_documento_completo:
        return None

    service = SimilarityMatchingService(db)
    candidates = service.find_similar(
        codice_fiscale=codice_fiscale,
        tipo_documento_identita=tipo_documento_identita,
        numero_documento_identita=numero_documento_identita,
        stato_rilascio_documento=stato_rilascio_documento,
        nome=nome,
        cognome=cognome,
        data_nascita=data_nascita,
        only_certain=True,
    )

    certain = [
        c for c in candidates
        if SimilarityMatchingService.MATCH_FIELD_CODICE_FISCALE in c["match_fields"]
        or SimilarityMatchingService.MATCH_FIELD_DOCUMENTO in c["match_fields"]
    ]
    if certain:
        soggetto = db.query(SoggettoAnagrafico).filter_by(id=certain[0]["soggetto_id"]).first()
        if codice_fiscale and not soggetto.codice_fiscale:
            soggetto.codice_fiscale = codice_fiscale
        if tipo_documento_identita and not soggetto.tipo_documento_identita:
            soggetto.tipo_documento_identita = tipo_documento_identita
        if numero_documento_identita and not soggetto.numero_documento_identita:
            soggetto.numero_documento_identita = numero_documento_identita
        if stato_rilascio_documento and not soggetto.stato_rilascio_documento:
            soggetto.stato_rilascio_documento = stato_rilascio_documento
        db.flush()
        return SoggettoDTO(id=soggetto.id, nome=nome, cognome=cognome, creato_ora=False)

    soggetto = SoggettoAnagrafico(
        tipo_soggetto=TipoSoggetto.PERSONA_FISICA,
        nome=nome,
        cognome=cognome,
        data_nascita=data_nascita,
        codice_fiscale=codice_fiscale,
        tipo_documento_identita=tipo_documento_identita,
        numero_documento_identita=numero_documento_identita,
        stato_rilascio_documento=stato_rilascio_documento,
    )
    db.add(soggetto)
    db.flush()
    return SoggettoDTO(id=soggetto.id, nome=nome, cognome=cognome, creato_ora=True)
