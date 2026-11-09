from pydantic import BaseModel
from typing import Optional
from datetime import date
from ..models import ClasseEnergetica


class CertificatoEnergeticoBase(BaseModel):
    unita_immobiliare_id: int
    tecnico_id: int
    classe_energetica: ClasseEnergetica
    indice_prestazione_energetica: Optional[float] = None
    data_emissione: date
    data_scadenza: date
    numero_protocollo: Optional[str] = None
    file_path: Optional[str] = None
    note: Optional[str] = None


class CertificatoEnergeticoCreate(CertificatoEnergeticoBase):
    pass


class CertificatoEnergeticoUpdate(BaseModel):
    unita_immobiliare_id: Optional[int] = None
    tecnico_id: Optional[int] = None
    classe_energetica: Optional[ClasseEnergetica] = None
    indice_prestazione_energetica: Optional[float] = None
    data_emissione: Optional[date] = None
    data_scadenza: Optional[date] = None
    numero_protocollo: Optional[str] = None
    file_path: Optional[str] = None
    note: Optional[str] = None


class CertificatoEnergeticoResponse(BaseModel):
    """An APE document in the old certificate shape (see routes/certificati_energetici.py)."""
    id: int
    unita_immobiliare_id: int
    tecnico_id: Optional[int] = None
    classe_energetica: Optional[str] = None
    indice_prestazione_energetica: Optional[float] = None
    data_emissione: Optional[date] = None
    data_scadenza: Optional[date] = None
    numero_protocollo: Optional[str] = None
    file_path: Optional[str] = None
    note: Optional[str] = None
