from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProprietarioBase(BaseModel):
    soggetto_id: int = Field(..., description="ID del soggetto anagrafico (anagrafica_italiana)")
    note_proprietario: Optional[str] = Field(None, max_length=500)


class ProprietarioCreate(ProprietarioBase):
    pass


class ProprietarioUpdate(BaseModel):
    note_proprietario: Optional[str] = Field(None, max_length=500)


class ProprietarioResponse(ProprietarioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
