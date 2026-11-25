"""
Seeds of affitti_lungo. No public data; with seed_test_data=True the tenant
gets example data of this module: one tenant, one contract with two
payments, a direct expense and a condominium expense split by millesimi, a
technician.

Self-contained: what the examples need from the modules this one depends on
(anagrafica_italiana, immobili) is created here through their models, under
this module's own codes (AL-ESEMPIO-*), never looked up among their example
data. Idempotent: rerunning adds only what is missing
(scripts/tenant_prova.py checks it).
"""
from typing import Optional

from sqlalchemy.orm import Session

CONTRATTO = "CTR-ESEMPIO-001"
NOTA_ESEMPIO = "Dato di esempio (affitti_lungo)"


def seed_public(db):
    pass


def _soggetto(db: Session, codice_fiscale: str, **campi):
    from anagrafica_italiana.models import SoggettoAnagrafico
    soggetto = db.query(SoggettoAnagrafico).filter(SoggettoAnagrafico.codice_fiscale == codice_fiscale).first()
    if not soggetto:
        soggetto = SoggettoAnagrafico(codice_fiscale=codice_fiscale, note=NOTA_ESEMPIO, attivo=True, **campi)
        db.add(soggetto)
        db.flush()
    return soggetto


def _unita(db: Session, codice: str, condominio_id: Optional[int]):
    from immobili.models import UnitaImmobiliare
    unita = db.query(UnitaImmobiliare).filter(UnitaImmobiliare.codice == codice).first()
    if not unita:
        unita = UnitaImmobiliare(codice=codice, tipo="Appartamento", indirizzo="Via degli Esempi 10",
                                 citta="Bologna", provincia="BO", condominio_id=condominio_id,
                                 descrizione="Unità di esempio del modulo affitti_lungo")
        db.add(unita)
        db.flush()
    return unita


def _condominio_e_tabella(db: Session):
    from immobili.models import Condominio, TabellaMillesimale
    condominio = db.query(Condominio).filter(Condominio.codice == "AL-ESEMPIO-COND").first()
    if not condominio:
        condominio = Condominio(codice="AL-ESEMPIO-COND", nome="Condominio di esempio",
                                indirizzo="Via degli Esempi 10", citta="Bologna")
        db.add(condominio)
        db.flush()
    tabella = db.query(TabellaMillesimale).filter(TabellaMillesimale.condominio_id == condominio.id,
                                                  TabellaMillesimale.codice == "AL-GEN").first()
    if not tabella:
        tabella = TabellaMillesimale(condominio_id=condominio.id, nome="Spese generali", codice="AL-GEN")
        db.add(tabella)
        db.flush()
    return condominio, tabella


def seed_esempi(db: Session) -> dict:
    from immobili.models import MillesimiUnita
    from ..models import Affittuario, Contratto, Incasso, RipartizioneSpesa, Spesa, Tecnico

    if db.query(Contratto).filter(Contratto.numero_contratto == CONTRATTO).first():
        return {}
    condominio, tabella = _condominio_e_tabella(db)
    unita_1 = _unita(db, "AL-ESEMPIO-1", condominio.id)
    unita_2 = _unita(db, "AL-ESEMPIO-2", condominio.id)
    for unita, millesimi in ((unita_1, 480.0), (unita_2, 520.0)):
        db.add(MillesimiUnita(unita_immobiliare_id=unita.id, tabella_millesimale_id=tabella.id, millesimi=millesimi))

    inquilino = _soggetto(db, "SMPLLN85A41A944X", tipo_soggetto="PERSONA_FISICA",
                          nome="Elena", cognome="Esempio")
    studio = _soggetto(db, "01234560375", tipo_soggetto="PERSONA_GIURIDICA",
                       ragione_sociale="Studio Tecnico Esempio Srl", partita_iva="01234560375")
    affittuario = Affittuario(soggetto_id=inquilino.id, note_affittuario="Affittuario di esempio")
    db.add(affittuario)
    db.flush()

    contratto = Contratto(
        numero_contratto=CONTRATTO, unita_immobiliare_id=unita_2.id, affittuario_id=affittuario.id,
        uso_immobile="ABITATIVO", tipologia_contratto="LIBERO_MERCATO", durata_anni_iniziale=4,
        durata_anni_rinnovo=4, data_inizio="2025-01-01", data_fine="2028-12-31", canone_mensile=850,
        giorno_pagamento=5, deposito_cauzionale=1700, regime_fiscale="CEDOLARE_SECCA_21",
        registrazione_numero="1234 serie 3T", registrazione_data="2025-01-20",
        registrazione_agenzia="Bologna 1", stato="ATTIVO",
    )
    db.add(contratto)
    db.flush()
    for mese in ("2026-01", "2026-02"):
        db.add(Incasso(contratto_id=contratto.id, data_incasso=f"{mese}-05", importo=850,
                       mese_riferimento=mese, metodo_pagamento="Bonifico"))

    db.add(Spesa(unita_immobiliare_id=unita_2.id, data="2026-03-15", importo=180.0, categoria="MANUTENZIONE",
                 descrizione="Riparazione caldaia (esempio)", fornitore="Fornitore di esempio", pagata=1))
    condominiale = Spesa(unita_immobiliare_id=unita_1.id, tabella_millesimale_id=tabella.id, data="2026-03-15",
                         importo=300.0, categoria="AMMINISTRAZIONE", descrizione="Pulizia scale (esempio)",
                         pagata=1, spesa_condominiale=1, ripartita=1)
    db.add(condominiale)
    db.flush()
    for unita, millesimi in ((unita_1, 480.0), (unita_2, 520.0)):
        quota = round(300.0 * millesimi / 1000, 2)
        db.add(RipartizioneSpesa(spesa_id=condominiale.id, unita_immobiliare_id=unita.id, importo_ripartito=quota,
                                 millesimi_applicati=millesimi, importo_da_millesimi=quota))

    db.add(Tecnico(soggetto_id=studio.id, specializzazione="CERTIFICATORE_ENERGETICO",
                   note_tecnico="Tecnico di esempio", attivo=True))
    db.flush()
    return {"contratti": 1, "incassi": 2, "spese": 2, "ripartizioni_spese": 2, "tecnici": 1}


def seed_tenant(db: Session, tenant_id: Optional[int] = None, tenant_schema: Optional[str] = None,
                seed_test_data: bool = False) -> dict:
    if not seed_test_data:
        return {}
    risultati = seed_esempi(db)
    db.commit()
    return risultati
