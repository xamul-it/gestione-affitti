from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.core.platform.models import EntityType, TipoDocumentoEnum as TipoDocumento


class DocumentoUpdate(BaseModel):
    tipo_documento: Optional[TipoDocumento] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None


class DocumentoFileOut(BaseModel):
    id: Optional[int] = None
    nome_file: Optional[str] = None
    mime_type: Optional[str] = None


class DocumentoOut(BaseModel):
    id: int
    entity_type: EntityType
    entity_id: int
    entity_label: Optional[str] = None
    tipo_documento: Optional[str] = None  # deprecated enum column
    tipo_documento_id: Optional[int] = None
    tipo_codice: Optional[str] = None
    tipo_nome: Optional[str] = None
    regime: Optional[str] = None
    descrizione: Optional[str] = None
    note: Optional[str] = None
    nome_file: Optional[str] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    dimensione: Optional[int] = None
    data_riferimento: Optional[date] = None
    stato: str = "CORRENTE"
    sostituito_da_id: Optional[int] = None
    sottotipo: Optional[str] = None
    dati: Optional[Any] = None
    data_scadenza: Optional[date] = None
    data_scadenza_effettiva: Optional[date] = None
    files: List[DocumentoFileOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


# Backward-compatible name.
DocumentoResponse = DocumentoOut


class TipoDocumentoOut(BaseModel):
    id: int
    codice: str
    nome: str
    descrizione: Optional[str] = None
    categoria: Optional[str] = None
    modulo: Optional[str] = None
    regime: str = "CUMULATIVO"
    sottotipi: Optional[List[str]] = None
    scadenza: Optional[dict] = None
    promemoria_giorni: Optional[List[int]] = None
    richiede_scadenza: bool = False
    form: Optional[str] = None
    parsing_service: Optional[str] = None
