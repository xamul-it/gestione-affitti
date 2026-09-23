from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConduttoreBase(BaseModel):
    soggetto_id: int = Field(..., description="ID del soggetto anagrafico (anagrafica_italiana)")
    note: Optional[str] = Field(None, max_length=500)


class ConduttoreCreate(ConduttoreBase):
    pass


class ConduttoreUpdate(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


class ConduttoreResponse(ConduttoreBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
