"""
Schemas for the "import da visura catastale" proposal.

The proposal is built server-side (preview), edited/deselected in the UI and
sent back for apply; ids ("s0", "u0") are local to one proposal.
"""
from datetime import date
from typing import Any, List, Literal, Optional

from pydantic import BaseModel

from ..models.diritti_immobile import TipoDiritto
from ..services.visura.models import FormatoVisura

Azione = Literal["crea", "aggiorna", "invariato"]


class SoggettoProposta(BaseModel):
    key: str
    azione: Azione
    soggetto_id: Optional[int] = None
    persona_giuridica: bool
    nominativo: str
    cognome: Optional[str] = None
    nome: Optional[str] = None
    ragione_sociale: Optional[str] = None
    codice_fiscale: Optional[str] = None
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = None
    campi_da_completare: List[str] = []
    selezionato: bool = True


class CampoModifica(BaseModel):
    campo: str
    attuale: Any = None
    nuovo: Any = None
    selezionato: bool = True


class DirittoProposta(BaseModel):
    soggetto_key: str
    nominativo: str
    tipo_diritto: TipoDiritto
    quota_percentuale: Optional[float] = None
    note: str
    azione: Literal["crea", "invariato"]
    selezionato: bool = True


class UnitaProposta(BaseModel):
    key: str
    azione: Azione
    unita_id: Optional[int] = None
    foglio: str
    particella: str
    subalterno: Optional[str] = None
    sezione_urbana: Optional[str] = None
    tipo: Optional[str] = None
    indirizzo: str
    citta: str
    provincia: Optional[str] = None
    cap: Optional[str] = None
    piano: Optional[str] = None
    superficie_mq: Optional[float] = None
    locali: Optional[int] = None
    rendita_catastale: Optional[float] = None
    categoria_catastale_id: Optional[int] = None
    categoria: str
    note_catastali: str
    modifiche: List[CampoModifica] = []
    diritti: List[DirittoProposta] = []
    avvisi: List[str] = []
    selezionato: bool = True


class VisuraProposta(BaseModel):
    upload_token: Optional[str] = None
    formato: FormatoVisura
    numero_visura: str
    data_visura: date
    soggetti: List[SoggettoProposta]
    unita: List[UnitaProposta]
    avvisi: List[str] = []


class VisuraApplyRequest(BaseModel):
    upload_token: str
    proposta: VisuraProposta


class VisuraImportResult(BaseModel):
    soggetti_creati: int
    soggetti_aggiornati: int
    unita_create: List[int]
    unita_aggiornate: List[int]
    diritti_creati: int
    documenti_allegati: int
