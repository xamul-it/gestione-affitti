from pydantic import BaseModel, Field, model_validator
from typing import Optional
from decimal import Decimal
from datetime import date, datetime


class SpesaRicorrenteBase(BaseModel):
    tipo_spesa: str = Field(..., max_length=50, description="es. IMU, TARI, UTENZA_LUCE, UTENZA_GAS, UTENZA_ACQUA, ALTRO")
    responsabile: str = Field(..., description="PROPRIETARIO o CONDUTTORE")
    periodo: str = Field(..., max_length=50, description="es. '2026', '2026-T2'")
    rata: Optional[str] = Field(None, max_length=50, description="es. ACCONTO, SALDO, UNICA")
    importo: Decimal = Field(..., gt=0)
    data_scadenza: date
    note: Optional[str] = None


class SpesaRicorrenteCreate(SpesaRicorrenteBase):
    unita_immobiliare_id: Optional[int] = None
    condominio_id: Optional[int] = None

    # Notify recipients of the auto-created reminder (see route), same
    # convention as ScadenzaCreate.destinatari_ids.
    destinatari_ids: Optional[list[int]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _exactly_one_target(self):
        if bool(self.unita_immobiliare_id) == bool(self.condominio_id):
            raise ValueError(
                "Specificare esattamente uno tra unita_immobiliare_id e condominio_id"
            )
        return self


class SpesaRicorrenteUpdate(BaseModel):
    tipo_spesa: Optional[str] = Field(None, max_length=50)
    responsabile: Optional[str] = None
    periodo: Optional[str] = Field(None, max_length=50)
    rata: Optional[str] = Field(None, max_length=50)
    importo: Optional[Decimal] = Field(None, gt=0)
    data_scadenza: Optional[date] = None
    note: Optional[str] = None


class SegnaPagatoRequest(BaseModel):
    data_pagamento: Optional[date] = Field(None, description="Default: oggi")
    note: Optional[str] = None


class DuplicaSpesaRequest(BaseModel):
    periodo: str = Field(..., max_length=50, description="Nuovo periodo, es. '2027'")
    data_scadenza: date
    importo: Optional[Decimal] = Field(None, gt=0, description="Default: stesso importo dell'originale")
    rata: Optional[str] = Field(None, max_length=50, description="Default: stessa rata dell'originale")


class SpesaRicorrenteResponse(SpesaRicorrenteBase):
    id: int
    unita_immobiliare_id: Optional[int] = None
    condominio_id: Optional[int] = None
    pagato: bool
    data_pagamento: Optional[date] = None
    scadenza_id: Optional[int] = None

    class Config:
        from_attributes = True
