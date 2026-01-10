"""
Pydantic schemas for RuoloAzienda (Person-Company role associations)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class RuoloAziendaBase(BaseModel):
    """Base schema for RuoloAzienda"""
    persona_fisica_id: int = Field(..., description="ID della persona fisica")
    persona_giuridica_id: int = Field(..., description="ID dell'azienda (persona giuridica)")
    ruolo: str = Field(..., min_length=1, max_length=100, description="Nome del ruolo (es: Amministratore, Segretaria)")
    data_inizio: Optional[date] = Field(None, description="Data di inizio del ruolo")
    data_fine: Optional[date] = Field(None, description="Data di fine del ruolo (null se attivo)")


class RuoloAziendaCreate(RuoloAziendaBase):
    """Schema for creating a new RuoloAzienda"""
    pass


class RuoloAziendaUpdate(BaseModel):
    """Schema for updating a RuoloAzienda"""
    ruolo: Optional[str] = Field(None, min_length=1, max_length=100)
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None


class SoggettoBasic(BaseModel):
    """Schema minimo per soggetto (per evitare loop circolari)"""
    id: int
    tipo_soggetto: str
    codice_fiscale: Optional[str] = None
    partita_iva: Optional[str] = None
    nome: Optional[str] = None
    cognome: Optional[str] = None
    ragione_sociale: Optional[str] = None

    class Config:
        from_attributes = True

    @property
    def nome_completo(self):
        """Restituisce il nome completo del soggetto"""
        if self.tipo_soggetto == "PERSONA_FISICA":
            return f"{self.nome or ''} {self.cognome or ''}".strip()
        else:
            return self.ragione_sociale or ""


class RuoloAziendaResponse(RuoloAziendaBase):
    """Schema for RuoloAzienda response with full details"""
    id: int
    persona_fisica: SoggettoBasic
    persona_giuridica: SoggettoBasic
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RuoloAziendaListItem(BaseModel):
    """Schema for RuoloAzienda in lists (lighter version)"""
    id: int
    persona_fisica_id: int
    persona_giuridica_id: int
    ruolo: str
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None

    # Info della controparte (se visto dalla persona mostra azienda e viceversa)
    controparte_id: Optional[int] = None
    controparte_nome: Optional[str] = None
    controparte_tipo: Optional[str] = None

    class Config:
        from_attributes = True
