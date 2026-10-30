"""
Parsed representation of an Agenzia delle Entrate catasto visura.

Fabbricati and terreni are kept apart so terreni import can be added later
without reshaping the fabbricati flow (only counted for now).
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from immobili.models.diritti_immobile import TipoDiritto


class FormatoVisura(str, Enum):
    SINTETICA = "SINTETICA"
    ANALITICA = "ANALITICA"


class VisuraFormatError(ValueError):
    """Unreadable or unsupported document; message is shown to the user."""


@dataclass
class IntestatoParsed:
    nominativo: str
    cognome: Optional[str]
    nome: Optional[str]
    ragione_sociale: Optional[str]
    codice_fiscale: Optional[str]
    persona_giuridica: bool
    data_nascita: Optional[date]
    luogo_nascita: Optional[str]
    diritto_testo: str
    tipo_diritto: TipoDiritto
    quota_percentuale: Optional[Decimal]


@dataclass
class FabbricatoParsed:
    comune: str
    codice_catastale_comune: str
    provincia: Optional[str]
    sezione_urbana: Optional[str]
    foglio: str
    particella: str
    subalterno: Optional[str]
    zona_censuaria: Optional[str]
    micro_zona: Optional[str]
    categoria: str
    classe: Optional[str]
    consistenza: Optional[str]
    vani: Optional[Decimal]
    superficie_totale: Optional[Decimal]
    superficie_escluse_aree: Optional[Decimal]
    rendita: Optional[Decimal]
    indirizzo: Optional[str]
    piano: Optional[str]
    intestati: List[IntestatoParsed] = field(default_factory=list)


@dataclass
class VisuraParsed:
    formato: FormatoVisura
    numero: str
    data: date
    soggetto_cf: Optional[str]
    fabbricati: List[FabbricatoParsed]
    terreni_count: int
    warnings: List[str] = field(default_factory=list)
