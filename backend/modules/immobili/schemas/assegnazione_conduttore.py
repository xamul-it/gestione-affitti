from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class AssegnazioneConduttoreBase(BaseModel):
    bene_id: int
    conduttore_id: int
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = Field(None, description="NULL = tuttora in corso")
    note: Optional[str] = Field(None, max_length=500)


class AssegnazioneConduttoreCreate(AssegnazioneConduttoreBase):
    pass


class AssegnazioneConduttoreUpdate(BaseModel):
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)


class AssegnazioneConduttoreResponse(AssegnazioneConduttoreBase):
    id: int
    # Who the conduttore is, so lists can show a name without one call per row.
    soggetto_id: Optional[int] = None
    conduttore_nome: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
