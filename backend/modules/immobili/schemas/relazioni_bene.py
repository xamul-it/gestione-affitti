"""Relations of a bene seen from the bene (GET/POST /beni/{id}/relazioni)."""
from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RelazioneBeneCreate(BaseModel):
    soggetto_id: int
    tipo: str
    quota: Optional[str] = None  # fraction "n/d"
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = None
    dati: Optional[Dict[str, Any]] = None


class Provenienza(BaseModel):
    """The ramo an inherited relation comes from."""
    raggruppamento_id: int
    nome: str
    tipo: str


class RelazioneBeneOut(BaseModel):
    id: int
    tipo: str
    tipo_nome: str
    soggetto_id: int
    soggetto_nome: str
    quota_numeratore: Optional[int] = None
    quota_denominatore: Optional[int] = None
    quota: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = None
    dati: Optional[Dict[str, Any]] = None
    provenienza: Optional[Provenienza] = None  # None = the object's own relation


class RelazioniBeneResponse(BaseModel):
    diritti_reali: List[RelazioneBeneOut]
    godimento: List[RelazioneBeneOut]
    incarichi: List[RelazioneBeneOut]


class RelazioneBeneCreata(BaseModel):
    relazione: RelazioneBeneOut
    avvisi: List[str]
