"""Schemas of the role relations API (/api/v1/relazioni)."""
from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class TipoRelazioneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codice: str
    nome: str
    modulo: str
    fonte: str
    entity_types: Optional[List[str]] = None
    scadenza: Optional[Dict[str, Any]] = None
    unico_per_oggetto: bool = False
    sottotipi_fonte: Optional[str] = None


class RelazioneOut(BaseModel):
    soggetto_id: int
    tipo: str
    tipo_nome: str
    modulo: str
    fonte: str
    relazione_id: Optional[int] = None
    record_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    sottotipo: Optional[str] = None
    descrizione: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    data_scadenza: Optional[date] = None
    corrente: bool


class RelazioneIn(BaseModel):
    soggetto_id: int
    tipo: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    sottotipo: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    data_scadenza: Optional[date] = None
    note: Optional[str] = None
    dati: Optional[Dict[str, Any]] = None


class RelazioneUpdate(BaseModel):
    sottotipo: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    data_scadenza: Optional[date] = None
    note: Optional[str] = None
    dati: Optional[Dict[str, Any]] = None


class RelazioneCoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    soggetto_id: int
    ruolo_id: int
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    sottotipo: Optional[str] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    data_scadenza: Optional[date] = None
    scadenza_id: Optional[int] = None
    note: Optional[str] = None
    dati: Optional[Dict[str, Any]] = None
