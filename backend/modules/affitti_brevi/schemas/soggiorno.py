"""
Soggiorno Schemas - Operational Stay Pydantic Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime


class OspiteBase(BaseModel):
    """Base schema for guest data"""
    cognome: str = Field(..., max_length=100)
    nome: str = Field(..., max_length=100)
    data_nascita: date
    sesso: Optional[str] = Field(None, max_length=1)
    luogo_nascita: Optional[str] = Field(None, max_length=200)
    provincia_nascita: Optional[str] = Field(None, max_length=2)
    stato_nascita: Optional[str] = Field(None, max_length=100)
    cittadinanza: str = Field(default="ITALIANA", max_length=100)
    indirizzo_residenza: Optional[str] = Field(None, max_length=300)
    comune_residenza: Optional[str] = Field(None, max_length=100)
    provincia_residenza: Optional[str] = Field(None, max_length=2)
    stato_residenza: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=50)
    tipo_documento: Optional[str] = Field(None, max_length=50)
    numero_documento: Optional[str] = Field(None, max_length=50)
    ente_rilascio: Optional[str] = Field(None, max_length=100)
    data_rilascio: Optional[date] = None
    data_scadenza: Optional[date] = None
    stato_rilascio: Optional[str] = Field(None, max_length=100)
    consenso_privacy: bool = False
    note: Optional[str] = None


class OspiteCreate(OspiteBase):
    """Schema for creating a guest"""
    soggiorno_id: int
    principale: bool = False
    soggetto_anagrafico_id: Optional[int] = None
    inserito_da_ospite: bool = False


class OspiteUpdate(BaseModel):
    """Schema for updating a guest"""
    cognome: Optional[str] = Field(None, max_length=100)
    nome: Optional[str] = Field(None, max_length=100)
    data_nascita: Optional[date] = None
    sesso: Optional[str] = Field(None, max_length=1)
    luogo_nascita: Optional[str] = Field(None, max_length=200)
    provincia_nascita: Optional[str] = Field(None, max_length=2)
    stato_nascita: Optional[str] = Field(None, max_length=100)
    cittadinanza: Optional[str] = Field(None, max_length=100)
    indirizzo_residenza: Optional[str] = Field(None, max_length=300)
    comune_residenza: Optional[str] = Field(None, max_length=100)
    provincia_residenza: Optional[str] = Field(None, max_length=2)
    stato_residenza: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=50)
    tipo_documento: Optional[str] = Field(None, max_length=50)
    numero_documento: Optional[str] = Field(None, max_length=50)
    ente_rilascio: Optional[str] = Field(None, max_length=100)
    data_rilascio: Optional[date] = None
    data_scadenza: Optional[date] = None
    stato_rilascio: Optional[str] = Field(None, max_length=100)
    consenso_privacy: Optional[bool] = None
    documento_verificato: Optional[bool] = None
    note: Optional[str] = None


class OspiteResponse(OspiteBase):
    """Schema for guest response"""
    id: int
    soggiorno_id: int
    soggetto_anagrafico_id: Optional[int] = None
    ruolo: str
    principale: bool
    stato_documento: str
    documento_verificato: bool
    esente_tassa: bool
    motivo_esenzione: Optional[str] = None
    inserito_da_ospite: bool
    data_inserimento_ospite: Optional[datetime] = None
    data_consenso_privacy: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed
    nome_completo: str = ""
    eta: int = 0
    is_minore: bool = False
    dati_completi_per_polizia: bool = False

    model_config = ConfigDict(from_attributes=True)


class SoggiornoBase(BaseModel):
    """Base schema for stay data"""
    prenotazione_id: int
    unita_immobiliare_id: int
    data_checkin: date
    data_checkout: date
    ora_checkin_prevista: Optional[str] = Field("15:00", max_length=5)
    ora_checkout_prevista: Optional[str] = Field("10:00", max_length=5)
    numero_ospiti_previsti: int = Field(default=1, ge=1)
    note_operative: Optional[str] = None
    note_ospite: Optional[str] = None


class SoggiornoCreate(SoggiornoBase):
    """Schema for creating a stay"""
    pass


class SoggiornoUpdate(BaseModel):
    """Schema for updating a stay"""
    data_checkin: Optional[date] = None
    data_checkout: Optional[date] = None
    ora_checkin_prevista: Optional[str] = Field(None, max_length=5)
    ora_checkout_prevista: Optional[str] = Field(None, max_length=5)
    numero_ospiti_previsti: Optional[int] = Field(None, ge=1)
    numero_ospiti_effettivi: Optional[int] = Field(None, ge=1)
    note_operative: Optional[str] = None
    note_ospite: Optional[str] = None


class SoggiornoResponse(SoggiornoBase):
    """Schema for stay response"""
    id: int
    stato: str
    valido: bool
    dati_ospiti_completi: bool
    documenti_completi: bool
    numero_ospiti_registrati: int
    numero_ospiti_effettivi: Optional[int] = None
    stato_polizia: str
    stato_istat: str
    stato_tassa_soggiorno: str
    notifica_checkin_inviata: bool
    notifica_dati_inviata: bool
    solleciti_inviati: int
    ultimo_sollecito: Optional[datetime] = None
    token_self_service: Optional[str] = None
    scadenza_token: Optional[datetime] = None
    data_ora_checkin_effettivo: Optional[datetime] = None
    data_ora_checkout_effettivo: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed
    notti: int = 0
    is_in_corso: bool = False
    is_futuro: bool = False
    is_passato: bool = False
    richiede_azione: bool = False

    # Related
    ospiti: List[OspiteResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SoggiornoListResponse(BaseModel):
    """Schema for list of stays"""
    soggiorni: List[SoggiornoResponse]
    totale: int
    skip: int
    limit: int


class SoggiornoFilterParams(BaseModel):
    """Filter parameters for stay list"""
    unita_immobiliare_id: Optional[int] = None
    data_checkin_da: Optional[date] = None
    data_checkin_a: Optional[date] = None
    stato: Optional[str] = None
    valido: Optional[bool] = True
    richiede_azione: Optional[bool] = None
    skip: int = 0
    limit: int = 100


class CheckinRequest(BaseModel):
    """Request for check-in"""
    numero_ospiti_effettivi: Optional[int] = None


class VerificaCompletezzaResponse(BaseModel):
    """Response from data completeness check"""
    completo: bool
    ospiti_registrati: int
    ospiti_previsti: int
    mancanti: List[str]


class SelfServiceTokenResponse(BaseModel):
    """Response with self-service access"""
    soggiorno_id: int
    token: str
    scadenza: datetime
    url_compilazione: str
