"""
Client for anagrafica_italiana's public service layer, per the
module-communication architecture
(docs/superpowers/specs/2026-09-14-module-communication-architecture-design.md).

Today (DEPLOY_MODE=monolith, the only supported mode) this is a direct
in-process call — the "shortcut" described in that spec. If affitti_brevi is
ever deployed separately from anagrafica_italiana, this is the one place
that would switch to an HTTP call instead; nothing else in this module
should import anagrafica_italiana directly for this purpose.
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session


def trova_o_crea_soggetto(
    db: Session,
    *,
    nome: str,
    cognome: str,
    data_nascita: Optional[date] = None,
    tipo_documento_identita: Optional[str] = None,
    numero_documento_identita: Optional[str] = None,
    stato_rilascio_documento: Optional[str] = None,
) -> int:
    """Finds-or-creates a SoggettoAnagrafico in the shared registry and returns its id."""
    from anagrafica_italiana.services.public_api import trova_o_crea_soggetto as _impl

    dto = _impl(
        db,
        nome=nome,
        cognome=cognome,
        data_nascita=data_nascita,
        tipo_documento_identita=tipo_documento_identita,
        numero_documento_identita=numero_documento_identita,
        stato_rilascio_documento=stato_rilascio_documento,
    )
    return dto.id
