"""Single upload point for immobili documents: analysis and confirmation."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .visura_import import CampoModifica

Esito = Literal["pronto", "scegli_tipo", "scegli_immobile", "scartato", "visura", "in_lettura",
                "gia_presente", "errore"]


class AnalisiDocumento(BaseModel):
    upload_token: Optional[str] = None
    nome_file: str
    esito: Esito
    tipo_codice: Optional[str] = None
    messaggio: Optional[str] = None
    unita_id: Optional[int] = None
    candidati: List[dict] = Field(default_factory=list)
    dati: dict = Field(default_factory=dict)
    differenze: List[CampoModifica] = Field(default_factory=list)
    avvisi: List[str] = Field(default_factory=list)
    job_uuid: Optional[str] = None


class RianalisiDocumento(BaseModel):
    upload_token: str
    tipo_codice: Optional[str] = None
    unita_id: Optional[int] = None


class ConfermaDocumento(BaseModel):
    upload_token: str
    tipo_codice: str
    unita_id: int
    dati: dict = Field(default_factory=dict)
    differenze: List[CampoModifica] = Field(default_factory=list)
    forza_duplicato: bool = False


class ConfermaRisultato(BaseModel):
    documento_id: int
    unita_id: int
