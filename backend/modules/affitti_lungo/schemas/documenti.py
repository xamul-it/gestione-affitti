from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models import EntityType, TipoDocumento


class DocumentoBase(BaseModel):
    entity_type: EntityType
    entity_id: int
    tipo_documento: TipoDocumento
    descrizione: Optional[str] = None
    note: Optional[str] = None


class DocumentoCreate(DocumentoBase):
    pass


class DocumentoUpdate(BaseModel):
    tipo_documento: Optional[TipoDocumento] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None


class DocumentoResponse(DocumentoBase):
    id: int
    nome_file: str
    file_path: str
    mime_type: Optional[str] = None
    dimensione: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
