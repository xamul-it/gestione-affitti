from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from ..models.contratti import StatoContratto, UsoImmobile, TipologiaContratto, RegimeFiscale


class ContrattoBase(BaseModel):
    numero_contratto: str = Field(..., max_length=50)
    unita_immobiliare_id: int
    affittuario_id: int
    uso_immobile: UsoImmobile = UsoImmobile.ABITATIVO
    tipologia_contratto: TipologiaContratto
    durata_anni_iniziale: int = Field(..., ge=1, le=99)
    durata_anni_rinnovo: Optional[int] = Field(None, ge=1, le=99)
    data_inizio: date
    data_fine: date
    canone_mensile: Decimal
    giorno_pagamento: int = Field(default=1, ge=1, le=31)
    deposito_cauzionale: Optional[Decimal] = None
    regime_fiscale: RegimeFiscale = RegimeFiscale.ORDINARIO_IRPEF
    adeguamento_istat: bool = False
    percentuale_istat: Optional[Decimal] = Field(None, ge=0, le=100)
    data_ultimo_adeguamento: Optional[date] = None
    registrazione_numero: Optional[str] = Field(None, max_length=100)
    registrazione_data: Optional[date] = None
    registrazione_agenzia: Optional[str] = Field(None, max_length=200)
    stato: StatoContratto = StatoContratto.ATTIVO
    note: Optional[str] = None


class ContrattoCreate(ContrattoBase):
    pass


class ContrattoUpdate(BaseModel):
    numero_contratto: Optional[str] = Field(None, max_length=50)
    unita_immobiliare_id: Optional[int] = None
    affittuario_id: Optional[int] = None
    uso_immobile: Optional[UsoImmobile] = None
    tipologia_contratto: Optional[TipologiaContratto] = None
    durata_anni_iniziale: Optional[int] = Field(None, ge=1, le=99)
    durata_anni_rinnovo: Optional[int] = Field(None, ge=1, le=99)
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    canone_mensile: Optional[Decimal] = None
    giorno_pagamento: Optional[int] = Field(None, ge=1, le=31)
    deposito_cauzionale: Optional[Decimal] = None
    regime_fiscale: Optional[RegimeFiscale] = None
    adeguamento_istat: Optional[bool] = None
    percentuale_istat: Optional[Decimal] = Field(None, ge=0, le=100)
    data_ultimo_adeguamento: Optional[date] = None
    registrazione_numero: Optional[str] = Field(None, max_length=100)
    registrazione_data: Optional[date] = None
    registrazione_agenzia: Optional[str] = Field(None, max_length=200)
    stato: Optional[StatoContratto] = None
    note: Optional[str] = None


class ContrattoResponse(ContrattoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
