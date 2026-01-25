"""
API Routes per Soggetti Anagrafici.

Gestisce la tabella centralizzata dei soggetti anagrafici con informazioni sui ruoli.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, inspect
from app.core.database import get_db, get_tenant_schema
from ..models import SoggettoAnagrafico, TipoSoggetto
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/anagrafica/soggetti", tags=["Soggetti Anagrafici"])


def _get_role_tables(db: Session, tenant_schema: Optional[str]) -> dict:
    if not tenant_schema:
        return {"proprietari": False, "affittuari": False, "tecnici": False}
    inspector = inspect(db.get_bind())
    return {
        "proprietari": inspector.has_table("immo_proprietari", schema=tenant_schema),
        "affittuari": inspector.has_table("affittuari", schema=tenant_schema),
        "tecnici": inspector.has_table("tecnici", schema=tenant_schema),
    }


def _build_ruoli_info(soggetto: SoggettoAnagrafico, tables: dict) -> "RuoliInfo":
    proprietario = tables.get("proprietari") and len(soggetto.proprietari) > 0
    affittuario = tables.get("affittuari") and len(soggetto.affittuari) > 0
    tecnico = tables.get("tecnici") and len(soggetto.tecnici) > 0
    tecnico_specializzazione = (
        soggetto.tecnici[0].specializzazione.value
        if tecnico and len(soggetto.tecnici) > 0
        else None
    )
    return RuoliInfo(
        proprietario=bool(proprietario),
        affittuario=bool(affittuario),
        tecnico=bool(tecnico),
        tecnico_specializzazione=tecnico_specializzazione,
    )


# Schemas
class SoggettoAnagra_ficoBase(BaseModel):
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


class SoggettoAnagra_ficoCreate(SoggettoAnagra_ficoBase):
    pass


class SoggettoAnagra_ficoUpdate(BaseModel):
    tipo_soggetto: Optional[TipoSoggetto] = None
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
    attivo: Optional[bool] = None


class RuoliInfo(BaseModel):
    """Informazioni sui ruoli di un soggetto"""
    proprietario: bool = False
    affittuario: bool = False
    tecnico: bool = False
    tecnico_specializzazione: Optional[str] = None


class SoggettoAnagra_ficoResponse(SoggettoAnagra_ficoBase):
    id: int
    ruoli: RuoliInfo

    class Config:
        from_attributes = True


# Routes
@router.get("/", response_model=List[SoggettoAnagra_ficoResponse])
def get_all_soggetti(
    skip: int = 0,
    limit: int = 100,
    attivo: Optional[bool] = None,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """
    Ottiene tutti i soggetti anagrafici con informazioni sui ruoli.

    Per ogni soggetto restituisce:
    - Dati anagrafici completi
    - Ruoli attivi (proprietario, affittuario, tecnico)
    """
    query = db.query(SoggettoAnagrafico)

    if attivo is not None:
        query = query.filter(SoggettoAnagrafico.attivo == attivo)

    soggetti = query.offset(skip).limit(limit).all()

    # Arricchisci con informazioni sui ruoli
    result = []
    role_tables = _get_role_tables(db, tenant_schema)
    for soggetto in soggetti:
        ruoli = _build_ruoli_info(soggetto, role_tables)

        soggetto_dict = {
            "id": soggetto.id,
            "tipo_soggetto": soggetto.tipo_soggetto,
            "codice_fiscale": soggetto.codice_fiscale,
            "partita_iva": soggetto.partita_iva,
            "nome": soggetto.nome,
            "cognome": soggetto.cognome,
            "data_nascita": soggetto.data_nascita,
            "luogo_nascita": soggetto.luogo_nascita,
            "ragione_sociale": soggetto.ragione_sociale,
            "email": soggetto.email,
            "telefono": soggetto.telefono,
            "cellulare": soggetto.cellulare,
            "pec": soggetto.pec,
            "indirizzo": soggetto.indirizzo,
            "citta": soggetto.citta,
            "cap": soggetto.cap,
            "provincia": soggetto.provincia,
            "note": soggetto.note,
            "attivo": soggetto.attivo,
            "ruoli": ruoli
        }

        result.append(soggetto_dict)

    return result




@router.get("/{soggetto_id}", response_model=SoggettoAnagra_ficoResponse)
def get_soggetto(
    soggetto_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """
    Ottiene un soggetto specifico con tutti i suoi ruoli.

    Restituisce dati anagrafici completi e informazioni dettagliate sui ruoli attivi.
    """
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    role_tables = _get_role_tables(db, tenant_schema)
    ruoli = _build_ruoli_info(soggetto, role_tables)

    return {
        "id": soggetto.id,
        "tipo_soggetto": soggetto.tipo_soggetto,
        "codice_fiscale": soggetto.codice_fiscale,
        "partita_iva": soggetto.partita_iva,
        "nome": soggetto.nome,
        "cognome": soggetto.cognome,
        "data_nascita": soggetto.data_nascita,
        "luogo_nascita": soggetto.luogo_nascita,
        "ragione_sociale": soggetto.ragione_sociale,
        "email": soggetto.email,
        "telefono": soggetto.telefono,
        "cellulare": soggetto.cellulare,
        "pec": soggetto.pec,
        "indirizzo": soggetto.indirizzo,
        "citta": soggetto.citta,
        "cap": soggetto.cap,
        "provincia": soggetto.provincia,
        "note": soggetto.note,
        "attivo": soggetto.attivo,
        "ruoli": ruoli
    }




@router.get("/search/", response_model=List[SoggettoAnagra_ficoResponse])
def search_soggetti(
    q: str = Query(..., min_length=2, description="Testo da cercare (min 2 caratteri)"),
    limit: int = Query(20, le=100, description="Numero massimo di risultati"),
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """
    Ricerca soggetti per nome, cognome, ragione sociale o codice fiscale.

    Utile per autocomplete e selezione rapida nei form.
    """
    search_pattern = f"%{q}%"

    soggetti = db.query(SoggettoAnagrafico).filter(
        or_(
            SoggettoAnagrafico.nome.ilike(search_pattern),
            SoggettoAnagrafico.cognome.ilike(search_pattern),
            SoggettoAnagrafico.ragione_sociale.ilike(search_pattern),
            SoggettoAnagrafico.codice_fiscale.ilike(search_pattern),
            SoggettoAnagrafico.partita_iva.ilike(search_pattern)
        )
    ).filter(
        SoggettoAnagrafico.attivo == True
    ).limit(limit).all()

    # Arricchisci con ruoli
    result = []
    role_tables = _get_role_tables(db, tenant_schema)
    for soggetto in soggetti:
        ruoli = _build_ruoli_info(soggetto, role_tables)

        soggetto_dict = {
            "id": soggetto.id,
            "tipo_soggetto": soggetto.tipo_soggetto,
            "codice_fiscale": soggetto.codice_fiscale,
            "partita_iva": soggetto.partita_iva,
            "nome": soggetto.nome,
            "cognome": soggetto.cognome,
            "data_nascita": soggetto.data_nascita,
            "luogo_nascita": soggetto.luogo_nascita,
            "ragione_sociale": soggetto.ragione_sociale,
            "email": soggetto.email,
            "telefono": soggetto.telefono,
            "cellulare": soggetto.cellulare,
            "pec": soggetto.pec,
            "indirizzo": soggetto.indirizzo,
            "citta": soggetto.citta,
            "cap": soggetto.cap,
            "provincia": soggetto.provincia,
            "note": soggetto.note,
            "attivo": soggetto.attivo,
            "ruoli": ruoli
        }

        result.append(soggetto_dict)

    return result




@router.post("/", response_model=SoggettoAnagra_ficoResponse, status_code=201)
def create_soggetto(
    soggetto: SoggettoAnagra_ficoCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuovo soggetto anagrafico.
    """

    # Verifica unicità CF
    if soggetto.codice_fiscale:
        existing = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.codice_fiscale == soggetto.codice_fiscale
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Codice fiscale {soggetto.codice_fiscale} già esistente"
            )

    # Verifica unicità P.IVA
    if soggetto.partita_iva:
        existing = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.partita_iva == soggetto.partita_iva
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Partita IVA {soggetto.partita_iva} già esistente"
            )

    # Crea soggetto
    db_soggetto = SoggettoAnagrafico(**soggetto.model_dump())
    db.add(db_soggetto)
    db.commit()
    db.refresh(db_soggetto)

    # Restituisci con ruoli vuoti
    return {
        **db_soggetto.__dict__,
        "ruoli": RuoliInfo()
    }




@router.put("/{soggetto_id}", response_model=SoggettoAnagra_ficoResponse)
def update_soggetto(
    soggetto_id: int,
    soggetto_update: SoggettoAnagra_ficoUpdate,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """
    Aggiorna i dati anagrafici di un soggetto.

    L'aggiornamento si riflette automaticamente su tutti i ruoli del soggetto.
    """
    db_soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not db_soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Aggiorna solo i campi forniti
    update_data = soggetto_update.model_dump(exclude_unset=True)

    # Verifica unicità CF se modificato
    if "codice_fiscale" in update_data and update_data["codice_fiscale"]:
        existing = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.codice_fiscale == update_data["codice_fiscale"],
            SoggettoAnagrafico.id != soggetto_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Codice fiscale {update_data['codice_fiscale']} già esistente"
            )

    # Verifica unicità P.IVA se modificata
    if "partita_iva" in update_data and update_data["partita_iva"]:
        existing = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.partita_iva == update_data["partita_iva"],
            SoggettoAnagrafico.id != soggetto_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Partita IVA {update_data['partita_iva']} già esistente"
            )

    # Applica aggiornamenti
    for field, value in update_data.items():
        setattr(db_soggetto, field, value)

    db.commit()
    db.refresh(db_soggetto)

    # Restituisci con ruoli
    role_tables = _get_role_tables(db, tenant_schema)
    ruoli = _build_ruoli_info(db_soggetto, role_tables)

    return {
        **db_soggetto.__dict__,
        "ruoli": ruoli
    }




@router.delete("/{soggetto_id}", status_code=204)
def delete_soggetto(
    soggetto_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
):
    """
    Elimina un soggetto anagrafico.

    ATTENZIONE: Elimina anche tutti i ruoli associati (proprietario, affittuario, tecnico)
    grazie al CASCADE. Usare con cautela.
    """
    db_soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not db_soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    # Verifica se ha ruoli attivi
    role_tables = _get_role_tables(db, tenant_schema)
    has_roles = (
        (role_tables.get("proprietari") and len(db_soggetto.proprietari) > 0) or
        (role_tables.get("affittuari") and len(db_soggetto.affittuari) > 0) or
        (role_tables.get("tecnici") and len(db_soggetto.tecnici) > 0)
    )

    if has_roles:
        raise HTTPException(
            status_code=400,
            detail="Impossibile eliminare: il soggetto ha ruoli attivi. Eliminare prima i ruoli o disattivare il soggetto."
        )

    db.delete(db_soggetto)
    db.commit()

    return None
