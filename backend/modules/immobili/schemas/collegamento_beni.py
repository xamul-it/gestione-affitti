"""Links between beni as seen from one of the two (GET/POST/PUT /beni/{id}/collegamenti)."""
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, model_validator

from .bene import BeneResponse

Lato = Literal["PRINCIPALE", "COLLEGATO"]


class CollegamentoCreate(BaseModel):
    altro_bene_id: int
    tipo: str
    # Side of the bene in the route: from the box, questo_e="COLLEGATO".
    questo_e: Lato = "PRINCIPALE"
    data_inizio: Optional[date] = None
    note: Optional[str] = None


class CollegamentoUpdate(BaseModel):
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = None

    @model_validator(mode="after")
    def _date_in_ordine(self):
        if self.data_inizio and self.data_fine and self.data_fine < self.data_inizio:
            raise ValueError("La data di fine precede quella di inizio")
        return self


class CollegamentoOut(BaseModel):
    id: int
    tipo: str
    questo_e: Lato
    etichetta: str
    altro_bene: BeneResponse
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = None
    aperto: bool


class CollegamentiBeneResponse(BaseModel):
    collegamenti: List[CollegamentoOut]
    avvisi: List[str]
