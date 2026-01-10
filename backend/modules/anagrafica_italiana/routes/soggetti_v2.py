"""
API Routes per Soggetti Anagrafici - Versione 2 con sistema ruoli dinamici.

Usa il sistema di registrazione dinamica dei ruoli invece di hardcodare
i ruoli specifici (proprietario, affittuario, tecnico).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.core.database import get_db
from ..models import SoggettoAnagrafico, TipoSoggetto
from app.core.models import RuoloDisponibile, SoggettoRuolo
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/anagrafica/soggetti-v2", tags=["Soggetti Anagrafici V2"])


# Schemas
class RuoloInfo(BaseModel):
    """Informazioni su un ruolo assegnato a un soggetto"""
    codice: str
    nome: str
    modulo: str
    record_id: Optional[int] = None


class SoggettoAnagra_ficoV2Response(BaseModel):
    """Response con sistema ruoli dinamici"""
    id: int
    tipo_soggetto: TipoSoggetto
    codice_fiscale: Optional[str] = None
    partita_iva: Optional[str] = None
    nome: Optional[str] = None
    cognome: Optional[str] = None
    data_nascita: Optional[date] = None
    luogo_nascita: Optional[str] = None
    ragione_sociale: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    cellulare: Optional[str] = None
    pec: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    provincia: Optional[str] = None
    note: Optional[str] = None
    attivo: bool = True
    ruoli: List[RuoloInfo] = []

    class Config:
        from_attributes = True


# Routes
@router.get("/v2/", response_model=List[SoggettoAnagra_ficoV2Response])
def get_all_soggetti_v2(
    skip: int = 0,
    limit: int = 100,
    attivo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Ottiene tutti i soggetti anagrafici con sistema ruoli dinamici.

    Per ogni soggetto restituisce:
    - Dati anagrafici completi
    - Lista di tutti i ruoli assegnati (dinamici, da qualsiasi modulo)

    Questa è la versione V2 che usa il sistema di ruoli modulare.
    """
    query = db.query(SoggettoAnagrafico).options(
        joinedload(SoggettoAnagrafico.ruoli_assegnati).joinedload(SoggettoRuolo.ruolo)
    )

    if attivo is not None:
        query = query.filter(SoggettoAnagrafico.attivo == attivo)

    soggetti = query.offset(skip).limit(limit).all()

    # Costruisci response con ruoli dinamici
    result = []
    for soggetto in soggetti:
        # Ottieni tutti i ruoli attivi
        ruoli = [
            RuoloInfo(
                codice=assegnazione.ruolo.codice,
                nome=assegnazione.ruolo.nome_display,
                modulo=assegnazione.ruolo.modulo_id,
                record_id=assegnazione.record_specializzazione_id
            )
            for assegnazione in soggetto.ruoli_assegnati
            if assegnazione.attivo
        ]

        soggetto_dict = SoggettoAnagra_ficoV2Response(
            id=soggetto.id,
            tipo_soggetto=soggetto.tipo_soggetto,
            codice_fiscale=soggetto.codice_fiscale,
            partita_iva=soggetto.partita_iva,
            nome=soggetto.nome,
            cognome=soggetto.cognome,
            data_nascita=soggetto.data_nascita,
            luogo_nascita=soggetto.luogo_nascita,
            ragione_sociale=soggetto.ragione_sociale,
            email=soggetto.email,
            telefono=soggetto.telefono,
            cellulare=soggetto.cellulare,
            pec=soggetto.pec,
            indirizzo=soggetto.indirizzo,
            citta=soggetto.citta,
            cap=soggetto.cap,
            provincia=soggetto.provincia,
            note=soggetto.note,
            attivo=soggetto.attivo,
            ruoli=ruoli
        )

        result.append(soggetto_dict)

    return result


@router.get("/v2/{soggetto_id}", response_model=SoggettoAnagra_ficoV2Response)
def get_soggetto_v2(soggetto_id: int, db: Session = Depends(get_db)):
    """
    Ottiene un soggetto specifico con tutti i suoi ruoli (sistema dinamico).

    Restituisce dati anagrafici completi e lista di tutti i ruoli assegnati,
    indipendentemente dal modulo che li ha registrati.
    """
    soggetto = db.query(SoggettoAnagrafico).options(
        joinedload(SoggettoAnagrafico.ruoli_assegnati).joinedload(SoggettoRuolo.ruolo)
    ).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Ottieni ruoli attivi
    ruoli = [
        RuoloInfo(
            codice=assegnazione.ruolo.codice,
            nome=assegnazione.ruolo.nome_display,
            modulo=assegnazione.ruolo.modulo_id,
            record_id=assegnazione.record_specializzazione_id
        )
        for assegnazione in soggetto.ruoli_assegnati
        if assegnazione.attivo
    ]

    return SoggettoAnagra_ficoV2Response(
        id=soggetto.id,
        tipo_soggetto=soggetto.tipo_soggetto,
        codice_fiscale=soggetto.codice_fiscale,
        partita_iva=soggetto.partita_iva,
        nome=soggetto.nome,
        cognome=soggetto.cognome,
        data_nascita=soggetto.data_nascita,
        luogo_nascita=soggetto.luogo_nascita,
        ragione_sociale=soggetto.ragione_sociale,
        email=soggetto.email,
        telefono=soggetto.telefono,
        cellulare=soggetto.cellulare,
        pec=soggetto.pec,
        indirizzo=soggetto.indirizzo,
        citta=soggetto.citta,
        cap=soggetto.cap,
        provincia=soggetto.provincia,
        note=soggetto.note,
        attivo=soggetto.attivo,
        ruoli=ruoli
    )


@router.get("/v2/ruoli/disponibili", response_model=List[dict])
def get_ruoli_disponibili(db: Session = Depends(get_db)):
    """
    Ottiene tutti i ruoli disponibili nella piattaforma.

    Utile per capire quali ruoli possono essere assegnati ai soggetti.
    """
    ruoli = db.query(RuoloDisponibile).filter(
        RuoloDisponibile.attivo == True
    ).all()

    return [
        {
            "id": ruolo.id,
            "codice": ruolo.codice,
            "nome": ruolo.nome_display,
            "descrizione": ruolo.descrizione,
            "modulo": ruolo.modulo_id,
            "tabella_specializzazione": ruolo.tabella_specializzazione
        }
        for ruolo in ruoli
    ]
