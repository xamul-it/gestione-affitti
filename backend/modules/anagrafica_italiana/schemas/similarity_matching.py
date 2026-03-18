"""
Schemas for Similarity Matching API.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class FindSimilarRequest(BaseModel):
    """
    Request schema for finding similar anagrafiche.

    Used in POST /anagrafica/soggetti/find-similar
    """
    codice_fiscale: Optional[str] = None
    nome: Optional[str] = None
    cognome: Optional[str] = None
    data_nascita: Optional[date] = None
    exclude_id: Optional[int] = None  # Exclude this soggetto from results
    threshold: Optional[float] = 0.50  # Minimum similarity score

    class Config:
        json_schema_extra = {
            "example": {
                "codice_fiscale": "RSSMRA80A01H501Z",
                "nome": "Mario",
                "cognome": "Rossi",
                "data_nascita": "1980-01-01",
                "threshold": 0.50
            }
        }
