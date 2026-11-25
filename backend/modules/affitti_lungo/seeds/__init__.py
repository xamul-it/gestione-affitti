"""
Seeds of affitti_lungo. No public data; with seed_test_data=True the tenant
gets example data on top of the immobili ones (UNITA-001/002, the example
tenant of UNITA-002, the SP-GEN table): one tenant, one contract with a
payment, a direct and a condominium expense split by millesimi, a technician.

Idempotent: rerunning adds only what is missing (scripts/tenant_prova.py
checks it). Without the immobili example data nothing is created.
"""
import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CONTRATTO = "CTR-ESEMPIO-001"


def seed_public(db):
    pass


def _bene(db: Session, codice: str) -> Optional[int]:
    return db.execute(text("SELECT id FROM immo_beni WHERE codice = :c"), {"c": codice}).scalar()


def _affittuario(db: Session, soggetto_id: int) -> int:
    affittuario_id = db.execute(text("SELECT id FROM affittuari WHERE soggetto_id = :s"), {"s": soggetto_id}).scalar()
    if affittuario_id:
        return affittuario_id
    return db.execute(text(
        "INSERT INTO affittuari (soggetto_id, note_affittuario) VALUES (:s, 'Affittuario di esempio') RETURNING id"
    ), {"s": soggetto_id}).scalar()


def _spesa(db: Session, unita_id: int, descrizione: str, categoria: str, importo: float,
           tabella_id: Optional[int] = None) -> Optional[int]:
    """Example expense; returns its id only when created now."""
    if db.execute(text("SELECT 1 FROM spese WHERE descrizione = :d"), {"d": descrizione}).first():
        return None
    return db.execute(text(
        "INSERT INTO spese (unita_immobiliare_id, tabella_millesimale_id, data, importo, categoria, descrizione, "
        "fornitore, pagata, spesa_condominiale, ripartita) "
        "VALUES (:u, :t, '2026-03-15', :i, :c, :d, 'Fornitore di esempio', 1, :cond, :cond) RETURNING id"
    ), {"u": unita_id, "t": tabella_id, "i": importo, "c": categoria, "d": descrizione,
        "cond": 1 if tabella_id else 0}).scalar()


def seed_esempi(db: Session) -> dict:
    risultati = {}
    unita_1, unita_2 = _bene(db, "UNITA-001"), _bene(db, "UNITA-002")
    conduttore = db.execute(text(
        "SELECT c.soggetto_id FROM immo_conduttori c JOIN immo_assegnazioni_conduttore a ON a.conduttore_id = c.id "
        "WHERE a.bene_id = :b ORDER BY a.id LIMIT 1"), {"b": unita_2}).scalar() if unita_2 else None
    if not (unita_1 and unita_2 and conduttore):
        logger.info("[AFFITTI_LUNGO] immobili example data missing: no example data")
        return risultati

    affittuario = _affittuario(db, conduttore)
    contratto = db.execute(text("SELECT id FROM contratti WHERE numero_contratto = :n"), {"n": CONTRATTO}).scalar()
    if not contratto:
        contratto = db.execute(text(
            "INSERT INTO contratti (numero_contratto, unita_immobiliare_id, affittuario_id, uso_immobile, "
            "tipologia_contratto, durata_anni_iniziale, durata_anni_rinnovo, data_inizio, data_fine, "
            "canone_mensile, giorno_pagamento, deposito_cauzionale, regime_fiscale, adeguamento_istat, "
            "registrazione_numero, registrazione_data, registrazione_agenzia, stato) "
            "VALUES (:n, :u, :a, 'ABITATIVO', 'LIBERO_MERCATO', 4, 4, '2025-01-01', '2028-12-31', 850, 5, 1700, "
            "'CEDOLARE_SECCA_21', false, '1234 serie 3T', '2025-01-20', 'Milano 1', 'ATTIVO') RETURNING id"
        ), {"n": CONTRATTO, "u": unita_2, "a": affittuario}).scalar()
        risultati["contratti"] = 1
    for mese in ("2026-01", "2026-02"):
        if not db.execute(text("SELECT 1 FROM incassi WHERE contratto_id = :c AND mese_riferimento = :m"),
                          {"c": contratto, "m": mese}).first():
            db.execute(text(
                "INSERT INTO incassi (contratto_id, data_incasso, importo, mese_riferimento, metodo_pagamento) "
                "VALUES (:c, :d, 850, :m, 'Bonifico')"), {"c": contratto, "d": f"{mese}-05", "m": mese})

    _spesa(db, unita_2, "Riparazione caldaia (esempio)", "MANUTENZIONE", 180.0)
    tabella = db.execute(text("SELECT id FROM immo_tabelle_millesimali WHERE codice = 'SP-GEN' LIMIT 1")).scalar()
    if tabella:
        spesa = _spesa(db, unita_1, "Pulizia scale (esempio)", "AMMINISTRAZIONE", 300.0, tabella)
        if spesa:
            for unita, millesimi in ((unita_1, 480.0), (unita_2, 520.0)):
                db.execute(text(
                    "INSERT INTO ripartizioni_spese (spesa_id, unita_immobiliare_id, importo_ripartito, "
                    "millesimi_applicati, importo_da_millesimi) VALUES (:s, :u, :i, :m, :i)"
                ), {"s": spesa, "u": unita, "i": round(300.0 * millesimi / 1000, 2), "m": millesimi})

    tecnico_soggetto = db.execute(text(
        "SELECT id FROM anag_soggetti_anagrafici WHERE ragione_sociale IS NOT NULL ORDER BY id LIMIT 1")).scalar()
    if tecnico_soggetto and not db.execute(text("SELECT 1 FROM tecnici WHERE soggetto_id = :s"),
                                           {"s": tecnico_soggetto}).first():
        db.execute(text(
            "INSERT INTO tecnici (soggetto_id, specializzazione, note_tecnico, attivo) "
            "VALUES (:s, 'CERTIFICATORE_ENERGETICO', 'Tecnico di esempio', true)"), {"s": tecnico_soggetto})
    return risultati


def seed_tenant(db: Session, tenant_id: Optional[int] = None, tenant_schema: Optional[str] = None,
                seed_test_data: bool = False) -> dict:
    if not seed_test_data:
        return {}
    risultati = seed_esempi(db)
    db.commit()
    return risultati
