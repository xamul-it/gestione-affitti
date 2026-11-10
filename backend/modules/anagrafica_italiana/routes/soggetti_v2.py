"""
API Routes per Soggetti Anagrafici - Versione 2 con sistema ruoli dinamici.

Usa il sistema di registrazione dinamica dei ruoli invece di hardcodare
i ruoli specifici (proprietario, affittuario, tecnico).
"""
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, inspect
from app.core.auth.dependencies import require_permission
from app.core.database import get_db, get_tenant_schema
from ..models import SoggettoAnagrafico, TipoSoggetto
from app.core.models import RuoloDisponibile, SoggettoRuolo
from app.core.platform_services import relazioni_query
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/anagrafica/soggetti-v2", tags=["Soggetti Anagrafici V2"])

# attribute name -> the table it's backed by, for the has_table() pre-check below
_ROLE_RELATIONSHIPS = {
    "proprietari": "immo_proprietari",
    "affittuari": "affittuari",
    "tecnici": "tecnici",
    "conduttori": "immo_conduttori",
}


def _has_role_records(db: Session, soggetto: SoggettoAnagrafico, tenant_schema: Optional[str]) -> bool:
    """
    Whether this soggetto has any role-specialization record linked to it
    (Proprietario/Affittuario/Tecnico/Conduttore — the hardcoded per-module
    role tables, not the newer dynamic SoggettoRuolo registry, which nothing
    in immobili/affitti_lungo currently populates when creating these roles).

    A module's role table may not exist at all in a given tenant schema if
    that module isn't enabled there. Checked via inspector.has_table() up
    front rather than attempting the query and catching a ProgrammingError:
    get_db() issues `SET search_path` as the first statement of the
    session's transaction, so a mid-request rollback (e.g. from a caught
    ProgrammingError) undoes that SET along with it, silently reverting the
    rest of the request to the wrong schema.
    """
    if not tenant_schema:
        return False
    inspector = inspect(db.get_bind())
    for attr, table_name in _ROLE_RELATIONSHIPS.items():
        if not inspector.has_table(table_name, schema=tenant_schema):
            continue
        if len(getattr(soggetto, attr)) > 0:
            return True
    return False


# Schemas
class RuoloInfo(BaseModel):
    """Informazioni su un ruolo assegnato a un soggetto"""
    codice: str
    nome: str
    modulo: str
    record_id: Optional[int] = None


class RuoloRelazione(BaseModel):
    """Ruolo ricavato dalle relazioni: n = relazioni correnti (0 = solo cessate)."""
    codice: str
    nome: str
    modulo: str
    n: int


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
    ruoli: List[Union[RuoloRelazione, RuoloInfo]] = []

    class Config:
        from_attributes = True


class SoggettoAnagra_ficoV2Create(BaseModel):
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


class SoggettoAnagra_ficoV2Update(BaseModel):
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


# Routes
@router.get("/", response_model=List[SoggettoAnagra_ficoV2Response])
def get_all_soggetti_v2(
    skip: int = 0,
    limit: int = 100,
    attivo: Optional[bool] = None,
    attivi_solo: Optional[bool] = None,
    ruolo: Optional[str] = Query(None, description="Solo i soggetti con una relazione di questo tipo"),
    ruolo_anche_cessati: bool = Query(False, description="Con ruolo: includi le relazioni cessate"),
    db: Session = Depends(get_db),
    tenant_schema=Depends(get_tenant_schema),
    current_user=Depends(require_permission("soggetto.view")),
):
    """
    Soggetti anagrafici con i ruoli ricavati dalle relazioni (core_relazioni e
    tabelle dei moduli, vedi app.core.platform_services.relazioni_query).
    """
    schema = tenant_schema if isinstance(tenant_schema, str) else None
    permessi = current_user.get_permissions()
    query = db.query(SoggettoAnagrafico)

    if attivi_solo:
        attivo = True
    if attivo is not None:
        query = query.filter(SoggettoAnagrafico.attivo == attivo)
    if ruolo:
        query = query.filter(SoggettoAnagrafico.id.in_(
            relazioni_query.soggetti_con_ruolo(db, schema, ruolo, permessi=permessi,
                                               solo_correnti=not ruolo_anche_cessati)
        ))

    soggetti = query.order_by(SoggettoAnagrafico.id).offset(skip).limit(limit).all()
    ruoli = relazioni_query.ruoli_per_soggetti(db, schema, [s.id for s in soggetti], permessi=permessi)

    return [
        SoggettoAnagra_ficoV2Response(
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
            ruoli=[RuoloRelazione(**r) for r in ruoli.get(soggetto.id, [])],
        )
        for soggetto in soggetti
    ]


@router.get("/{soggetto_id}", response_model=SoggettoAnagra_ficoV2Response)
def get_soggetto_v2(soggetto_id: int, db: Session = Depends(get_db), _user=Depends(require_permission("soggetto.view"))):
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

@router.get("/{soggetto_id}/ruoli", response_model=List[RuoloInfo])
def get_soggetto_ruoli_v2(soggetto_id: int, db: Session = Depends(get_db), _user=Depends(require_permission("soggetto.view"))):
    soggetto = db.query(SoggettoAnagrafico).options(
        joinedload(SoggettoAnagrafico.ruoli_assegnati).joinedload(SoggettoRuolo.ruolo)
    ).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    return [
        RuoloInfo(
            codice=assegnazione.ruolo.codice,
            nome=assegnazione.ruolo.nome_display,
            modulo=assegnazione.ruolo.modulo_id,
            record_id=assegnazione.record_specializzazione_id
        )
        for assegnazione in soggetto.ruoli_assegnati
        if assegnazione.attivo
    ]


@router.get("/ruoli/disponibili", response_model=List[dict])
def get_ruoli_disponibili(db: Session = Depends(get_db), _user=Depends(require_permission("soggetto.view"))):
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


@router.post("/", response_model=SoggettoAnagra_ficoV2Response, status_code=201)
def create_soggetto_v2(
    soggetto: SoggettoAnagra_ficoV2Create,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("soggetto.create")),
):
    if soggetto.codice_fiscale:
        existing = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.codice_fiscale == soggetto.codice_fiscale
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Codice fiscale {soggetto.codice_fiscale} già esistente"
            )

    if soggetto.partita_iva:
        existing = db.query(SoggettoAnagrafico).filter(
            SoggettoAnagrafico.partita_iva == soggetto.partita_iva
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Partita IVA {soggetto.partita_iva} già esistente"
            )

    db_soggetto = SoggettoAnagrafico(**soggetto.model_dump())
    db.add(db_soggetto)
    db.commit()
    db.refresh(db_soggetto)

    return SoggettoAnagra_ficoV2Response(
        id=db_soggetto.id,
        tipo_soggetto=db_soggetto.tipo_soggetto,
        codice_fiscale=db_soggetto.codice_fiscale,
        partita_iva=db_soggetto.partita_iva,
        nome=db_soggetto.nome,
        cognome=db_soggetto.cognome,
        data_nascita=db_soggetto.data_nascita,
        luogo_nascita=db_soggetto.luogo_nascita,
        ragione_sociale=db_soggetto.ragione_sociale,
        email=db_soggetto.email,
        telefono=db_soggetto.telefono,
        cellulare=db_soggetto.cellulare,
        pec=db_soggetto.pec,
        indirizzo=db_soggetto.indirizzo,
        citta=db_soggetto.citta,
        cap=db_soggetto.cap,
        provincia=db_soggetto.provincia,
        note=db_soggetto.note,
        attivo=db_soggetto.attivo,
        ruoli=[],
    )


@router.put("/{soggetto_id}", response_model=SoggettoAnagra_ficoV2Response)
def update_soggetto_v2(
    soggetto_id: int,
    soggetto_update: SoggettoAnagra_ficoV2Update,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("soggetto.edit")),
):
    db_soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not db_soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    update_data = soggetto_update.model_dump(exclude_unset=True)

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

    for field, value in update_data.items():
        setattr(db_soggetto, field, value)

    db.commit()
    db.refresh(db_soggetto)

    ruoli = [
        RuoloInfo(
            codice=assegnazione.ruolo.codice,
            nome=assegnazione.ruolo.nome_display,
            modulo=assegnazione.ruolo.modulo_id,
            record_id=assegnazione.record_specializzazione_id
        )
        for assegnazione in db_soggetto.ruoli_assegnati
        if assegnazione.attivo
    ]

    return SoggettoAnagra_ficoV2Response(
        id=db_soggetto.id,
        tipo_soggetto=db_soggetto.tipo_soggetto,
        codice_fiscale=db_soggetto.codice_fiscale,
        partita_iva=db_soggetto.partita_iva,
        nome=db_soggetto.nome,
        cognome=db_soggetto.cognome,
        data_nascita=db_soggetto.data_nascita,
        luogo_nascita=db_soggetto.luogo_nascita,
        ragione_sociale=db_soggetto.ragione_sociale,
        email=db_soggetto.email,
        telefono=db_soggetto.telefono,
        cellulare=db_soggetto.cellulare,
        pec=db_soggetto.pec,
        indirizzo=db_soggetto.indirizzo,
        citta=db_soggetto.citta,
        cap=db_soggetto.cap,
        provincia=db_soggetto.provincia,
        note=db_soggetto.note,
        attivo=db_soggetto.attivo,
        ruoli=ruoli,
    )


@router.delete("/{soggetto_id}", status_code=204)
def delete_soggetto_v2(
    soggetto_id: int,
    db: Session = Depends(get_db),
    tenant_schema: Optional[str] = Depends(get_tenant_schema),
    _user=Depends(require_permission("soggetto.delete")),
):
    db_soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()

    if not db_soggetto:
        raise HTTPException(status_code=404, detail="Soggetto non trovato")

    from app.core.platform_services.relazione_service import RelazioneService
    if RelazioneService(db, tenant_schema if isinstance(tenant_schema, str) else None).conta_per_soggetto(soggetto_id):
        raise HTTPException(
            status_code=400,
            detail="Impossibile eliminare: l'anagrafica ha relazioni (amministratore, ruoli in azienda...). Chiudile o eliminale prima.",
        )

    if _has_role_records(db, db_soggetto, tenant_schema):
        raise HTTPException(
            status_code=400,
            detail="Impossibile eliminare: il soggetto ha ruoli attivi (proprietario, affittuario, tecnico o conduttore). Eliminare prima i ruoli.",
        )

    db.delete(db_soggetto)
    db.commit()

    return None
