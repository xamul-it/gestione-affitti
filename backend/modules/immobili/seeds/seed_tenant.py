"""
Seed Tenant - Dati iniziali per ogni tenant del modulo immobili.

Questo file contiene i dati che vengono popolati nello schema TENANT
durante l'installazione del modulo per un tenant (endpoints.install).

Attualmente il modulo immobili non richiede dati di seed per tenant,
ma questo file è predisposto per future espansioni.

Esempi di dati che potrebbero essere aggiunti:
- Configurazioni di default per il tenant
- Mapping tipo_immobile -> categoria predefiniti
- Override predefiniti per tipologie terreno
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def seed_terreni_demo(db: Session, tipologia_id: Optional[int]) -> int:
    """Two demo land parcels (bene + terreno + one portion) if the tenant has none."""
    if db.execute(text("SELECT COUNT(*) FROM immo_terreni")).scalar():
        return 0
    creati = 0
    for codice, nome, qualita, superficie in (
        ("TER-001", "Terreno Agricolo", "SEMINATIVO", 1500),
        ("TER-002", "Area Edificabile", "ENTE URBANO", 800),
    ):
        if db.execute(text("SELECT 1 FROM immo_beni WHERE codice = :c"), {"c": codice}).first():
            continue
        bene_id = db.execute(text(
            "INSERT INTO immo_beni (tipo_bene, codice, comune, provincia) "
            "VALUES ('TERRENO', :codice, 'Milano', 'MI') RETURNING id"
        ), {"codice": codice}).scalar()
        db.execute(text(
            "INSERT INTO immo_terreni (id, nome, tipologia_id, superficie_mq) "
            "VALUES (:id, :nome, :tipologia_id, :superficie)"
        ), {"id": bene_id, "nome": nome, "tipologia_id": tipologia_id, "superficie": superficie})
        db.execute(text(
            "INSERT INTO immo_terreni_porzioni (terreno_id, qualita, superficie_mq) "
            "VALUES (:id, :qualita, :superficie)"
        ), {"id": bene_id, "qualita": qualita, "superficie": superficie})
        creati += 1
    return creati


def _categoria(db: Session, codice: str) -> Optional[int]:
    return db.execute(text("SELECT id FROM public.immo_categorie_catastali WHERE codice = :c"), {"c": codice}).scalar()


def _unita_demo(db: Session, codice: str, tipo: str, categoria: str, indirizzo: str, comune: str) -> int:
    bene_id = db.execute(text("SELECT id FROM immo_beni WHERE codice = :c"), {"c": codice}).scalar()
    if bene_id:
        return bene_id
    bene_id = db.execute(text(
        "INSERT INTO immo_beni (tipo_bene, codice, indirizzo, comune) VALUES ('UNITA', :c, :i, :comune) RETURNING id"
    ), {"c": codice, "i": indirizzo, "comune": comune}).scalar()
    db.execute(text(
        "INSERT INTO immo_unita_immobiliari (id, tipo, categoria_catastale_id) VALUES (:id, :tipo, :cat)"
    ), {"id": bene_id, "tipo": tipo, "cat": _categoria(db, categoria)})
    return bene_id


def _bene_id(db: Session, codice: str) -> Optional[int]:
    return db.execute(text("SELECT id FROM immo_beni WHERE codice = :c"), {"c": codice}).scalar()


def _collega(db: Session, principale: int, collegato: int, tipo: str) -> None:
    if db.execute(text(
        "SELECT 1 FROM immo_beni_collegamenti WHERE bene_id = :p AND bene_collegato_id = :c AND tipo = :t"
    ), {"p": principale, "c": collegato, "t": tipo}).first():
        return
    db.execute(text(
        "INSERT INTO immo_beni_collegamenti (bene_id, bene_collegato_id, tipo, data_inizio) "
        "VALUES (:p, :c, :t, '2020-01-01')"
    ), {"p": principale, "c": collegato, "t": tipo})


def _relazione(db: Session, tenant_schema: Optional[str], bene_id: int, soggetto_id: int, tipo: str,
               quota: Optional[str] = None, data_inizio: date = date(2020, 1, 1)) -> None:
    """Example relation on a bene, skipped when the same one is already open."""
    from immobili.services.relazioni_bene import crea_relazione_bene
    esiste = db.execute(text(
        "SELECT 1 FROM core_relazioni r JOIN core_ruoli_disponibili t ON t.id = r.ruolo_id "
        "WHERE r.entity_type = 'IMMOBILE' AND r.entity_id = :b AND r.soggetto_id = :s "
        "AND t.codice = :t AND t.modulo_id = 'immobili' AND r.data_fine IS NULL"
    ), {"b": bene_id, "s": soggetto_id, "t": tipo}).first()
    if esiste:
        return
    crea_relazione_bene(db, tenant_schema, None, bene_id, soggetto_id, tipo, quota=quota, data_inizio=data_inizio)


def seed_beni_demo(db: Session, tenant_schema: Optional[str], soggetto_ids: list, unita_ids: list) -> dict:
    """Beni features of phase 1-2b: tenant, usufruct, pertinenza, building on a parcel, recurring cost.

    Needs the demo units (UNITA-*) and land parcels (TER-*) already created.
    """
    box = _unita_demo(db, "BOX-001", "Box", "C/6", "Via Roma 1", "Milano")
    fabbricato = _unita_demo(db, "FAB-001", "Fabbricato rurale", "A/3", "Località Campi", "Milano")
    _relazione(db, tenant_schema, box, soggetto_ids[0], "proprieta", "1/1")
    _relazione(db, tenant_schema, fabbricato, soggetto_ids[2], "proprieta", "1/1")
    _collega(db, unita_ids[0], box, "PERTINENZA")
    terreno, area = _bene_id(db, "TER-001"), _bene_id(db, "TER-002")
    if area:
        _collega(db, area, fabbricato, "FABBRICATO_SU_PARTICELLA")
    _relazione(db, tenant_schema, unita_ids[1], soggetto_ids[3], "conduttore", data_inizio=date(2025, 1, 1))
    if terreno:
        # Nudo proprietario + usufruttuario + tenant farming the land.
        _relazione(db, tenant_schema, terreno, soggetto_ids[1], "nuda_proprieta", "1/1")
        _relazione(db, tenant_schema, terreno, soggetto_ids[2], "usufrutto", "1/1")
        _relazione(db, tenant_schema, terreno, soggetto_ids[3], "conduttore", data_inizio=date(2025, 1, 1))
    if not db.execute(text("SELECT 1 FROM immo_spese_ricorrenti WHERE bene_id = :b"), {"b": unita_ids[0]}).first():
        db.execute(text(
            "INSERT INTO immo_spese_ricorrenti (bene_id, tipo_spesa, responsabile, periodo, rata, importo, data_scadenza) "
            "VALUES (:b, 'IMU', 'PROPRIETARIO', '2026', 'ACCONTO', 420.50, '2026-06-16')"
        ), {"b": unita_ids[0]})
    return {"immo_beni_collegamenti": 2, "core_relazioni": 5, "immo_spese_ricorrenti": 1}


def seed_tenant_data(
    db: Session,
    tenant_id: Optional[int] = None,
    tenant_schema: Optional[str] = None,
    seed_test_data: bool = False,
) -> dict:
    """
    Seed initial data for a specific tenant.

    This function is called by the core during module installation (endpoints.install).
    It populates tenant-specific initial data in the tenant schema.

    Signature supports multiple calling conventions:
    - seed_tenant_data(db)
    - seed_tenant_data(db, tenant_id)
    - seed_tenant_data(db, tenant_id, tenant_schema)

    Args:
        db: Database session (search_path should already be set to tenant_schema, public)
        tenant_id: Optional tenant ID
        tenant_schema: Optional tenant schema name
        seed_test_data: If True, generate sample test data

    Returns:
        Dictionary with counts of seeded records per table
    """
    logger.info(f"[IMMO] Starting tenant seed for tenant_id={tenant_id}, schema={tenant_schema}...")

    results = {}

    # Attualmente nessun dato di seed per tenant
    # Il modulo immobili utilizza principalmente:
    # - Dati pubblici (categorie catastali, tipologie terreno) condivisi tra tutti i tenant
    # - Dati inseriti dall'utente (unità immobiliari, condomini, etc.)
    if not seed_test_data:
        logger.info(f"[IMMO] Tenant seed completed: {results}")
        return results

    try:
        from sqlalchemy import inspect

        inspector = inspect(db.get_bind())
        if tenant_schema and not inspector.has_table("immo_unita_immobiliari", schema=tenant_schema):
            logger.warning("[IMMO] Tenant tables missing; skipping test data seed.")
            return results

        def _get_or_create_soggetto(codice_fiscale: str, nome: str, cognome: str, email: str) -> int:
            soggetto_id = db.execute(
                text("SELECT id FROM anag_soggetti_anagrafici WHERE codice_fiscale = :cf"),
                {"cf": codice_fiscale},
            ).scalar()
            if soggetto_id:
                return soggetto_id
            return db.execute(
                text(
                    """
                    INSERT INTO anag_soggetti_anagrafici
                        (tipo_soggetto, nome, cognome, codice_fiscale, email, attivo)
                    VALUES
                        ('PERSONA_FISICA', :nome, :cognome, :cf, :email, TRUE)
                    RETURNING id
                    """
                ),
                {"nome": nome, "cognome": cognome, "cf": codice_fiscale, "email": email},
            ).scalar()

        base_cf = f"TSTTEN{(tenant_id or 0):06d}"
        soggetto_ids = [
            _get_or_create_soggetto(f"{base_cf}0001", "Mario", "Rossi", f"mario.rossi+{tenant_id or 0}@example.test"),
            _get_or_create_soggetto(f"{base_cf}0002", "Lucia", "Bianchi", f"lucia.bianchi+{tenant_id or 0}@example.test"),
            _get_or_create_soggetto(f"{base_cf}0003", "Paolo", "Verdi", f"paolo.verdi+{tenant_id or 0}@example.test"),
            _get_or_create_soggetto(f"{base_cf}0004", "Giulia", "Neri", f"giulia.neri+{tenant_id or 0}@example.test"),
        ]
        results["anag_soggetti_anagrafici"] = len(soggetto_ids)

        def _get_or_create_condominio(codice: str, nome: str, indirizzo: str) -> int:
            condominio_id = db.execute(
                text("SELECT id FROM immo_condomini WHERE codice = :codice"),
                {"codice": codice},
            ).scalar()
            if condominio_id:
                return condominio_id
            return db.execute(
                text(
                    """
                    INSERT INTO immo_condomini
                        (codice, nome, indirizzo, citta, cap, provincia, attivo)
                    VALUES
                        (:codice, :nome, :indirizzo, 'Milano', '20100', 'MI', TRUE)
                    RETURNING id
                    """
                ),
                {"codice": codice, "nome": nome, "indirizzo": indirizzo},
            ).scalar()

        condominio_ids = [
            _get_or_create_condominio("COND-001", "Condominio Centro", "Via Roma 1"),
            _get_or_create_condominio("COND-002", "Condominio Navigli", "Via Navigli 22"),
        ]
        results["immo_condomini"] = len(condominio_ids)

        categoria_catastale_id = db.execute(
            text("SELECT id FROM public.immo_categorie_catastali ORDER BY id LIMIT 1")
        ).scalar()

        def _get_or_create_unita(codice: str, tipo: str, condominio_id: Optional[int]) -> int:
            unita_id = db.execute(
                text("SELECT id FROM immo_beni WHERE codice = :codice"),
                {"codice": codice},
            ).scalar()
            if unita_id:
                return unita_id
            # The unit's id is the id of its bene (immo_beni).
            bene_id = db.execute(
                text(
                    """
                    INSERT INTO immo_beni (tipo_bene, codice, indirizzo, comune, cap, provincia)
                    VALUES ('UNITA', :codice, :indirizzo, 'Milano', '20100', 'MI')
                    RETURNING id
                    """
                ),
                {"codice": codice, "indirizzo": f"Via Roma {codice[-1]}"},
            ).scalar()
            db.execute(
                text(
                    """
                    INSERT INTO immo_unita_immobiliari
                        (id, tipo, condominio_id, superficie_mq, locali, categoria_catastale_id)
                    VALUES
                        (:id, :tipo, :condominio_id, :superficie, :locali, :categoria_catastale_id)
                    """
                ),
                {
                    "id": bene_id,
                    "tipo": tipo,
                    "condominio_id": condominio_id,
                    "superficie": 85.5 if tipo == "Appartamento" else 110.0,
                    "locali": 3 if tipo == "Appartamento" else 4,
                    "categoria_catastale_id": categoria_catastale_id,
                },
            )
            return bene_id

        unita_ids = [
            _get_or_create_unita("UNITA-001", "Appartamento", condominio_ids[0]),
            _get_or_create_unita("UNITA-002", "Appartamento", condominio_ids[0]),
            _get_or_create_unita("UNITA-003", "Villetta", None),
        ]
        results["immo_unita_immobiliari"] = len(unita_ids)

        # Rights as core relations (diritti_reali family): shares as fractions.
        for unita, soggetto, quota in (
            (unita_ids[0], soggetto_ids[0], "1/2"),
            (unita_ids[0], soggetto_ids[1], "1/2"),
            (unita_ids[1], soggetto_ids[2], "1/1"),
            (unita_ids[2], soggetto_ids[0], "1/1"),
        ):
            _relazione(db, tenant_schema, unita, soggetto, "proprieta", quota, date(2025, 1, 1))
        results["core_relazioni_diritti"] = 4

        def _ensure_certificato(unita_id: int, tecnico_id: int, classe: str, protocollo: str):
            exists = db.execute(
                text(
                    """
                    SELECT id FROM immo_certificati_energetici
                    WHERE unita_immobiliare_id = :unita_id AND numero_protocollo = :protocollo
                    """
                ),
                {"unita_id": unita_id, "protocollo": protocollo},
            ).scalar()
            if exists:
                return
            db.execute(
                text(
                    """
                    INSERT INTO immo_certificati_energetici
                        (unita_immobiliare_id, tecnico_id, classe_energetica, indice_prestazione_energetica, data_emissione, data_scadenza, numero_protocollo)
                    VALUES
                        (:unita_id, :tecnico_id, :classe, 85.0, '2025-01-10', '2035-01-10', :protocollo)
                    """
                ),
                {"unita_id": unita_id, "tecnico_id": tecnico_id, "classe": classe, "protocollo": protocollo},
            )

        _ensure_certificato(unita_ids[0], 1, "B", "APE-2025-0001")
        _ensure_certificato(unita_ids[1], 2, "A2", "APE-2025-0002")
        _ensure_certificato(unita_ids[2], 1, "C", "APE-2025-0003")
        results["immo_certificati_energetici"] = 3

        tipologia_terreno_id = db.execute(
            text("SELECT id FROM public.immo_tipologie_terreno ORDER BY id LIMIT 1")
        ).scalar()
        creati = seed_terreni_demo(db, tipologia_terreno_id)
        if creati:
            results["immo_terreni"] = creati

        def _get_or_create_tabella(condominio_id: int, codice: str, nome: str, tipo: str, perc_millesimi: float, perc_consumo: float, perc_occupanti: float) -> int:
            tabella_id = db.execute(
                text(
                    "SELECT id FROM immo_tabelle_millesimali WHERE condominio_id = :cid AND codice = :codice"
                ),
                {"cid": condominio_id, "codice": codice},
            ).scalar()
            if tabella_id:
                return tabella_id
            return db.execute(
                text(
                    """
                    INSERT INTO immo_tabelle_millesimali
                        (condominio_id, nome, codice, tipo_ripartizione, percentuale_millesimi, percentuale_consumo, percentuale_occupanti, attiva)
                    VALUES
                        (:condominio_id, :nome, :codice, :tipo, :perc_millesimi, :perc_consumo, :perc_occupanti, TRUE)
                    RETURNING id
                    """
                ),
                {
                    "condominio_id": condominio_id,
                    "nome": nome,
                    "codice": codice,
                    "tipo": tipo,
                    "perc_millesimi": perc_millesimi,
                    "perc_consumo": perc_consumo,
                    "perc_occupanti": perc_occupanti,
                },
            ).scalar()

        def _ensure_millesimi(unita_id: int, tabella_id: int, millesimi: float, piano: int, occupanti: int, consumo: float | None = None, unita_misura: str | None = None):
            exists = db.execute(
                text(
                    """
                    SELECT id FROM immo_millesimi_unita
                    WHERE unita_immobiliare_id = :unita_id AND tabella_millesimale_id = :tabella_id
                    """
                ),
                {"unita_id": unita_id, "tabella_id": tabella_id},
            ).scalar()
            if exists:
                return
            db.execute(
                text(
                    """
                    INSERT INTO immo_millesimi_unita
                        (unita_immobiliare_id, tabella_millesimale_id, millesimi, piano, numero_occupanti, consumo, unita_misura_consumo)
                    VALUES
                        (:unita_id, :tabella_id, :millesimi, :piano, :occupanti, :consumo, :unita_misura)
                    """
                ),
                {
                    "unita_id": unita_id,
                    "tabella_id": tabella_id,
                    "millesimi": millesimi,
                    "piano": piano,
                    "occupanti": occupanti,
                    "consumo": consumo,
                    "unita_misura": unita_misura,
                },
            )

        tabella_generale_id = _get_or_create_tabella(condominio_ids[0], "SP-GEN", "Spese Generali", "MILLESIMI", 100, 0, 0)
        tabella_riscaldamento_id = _get_or_create_tabella(condominio_ids[0], "RISC", "Riscaldamento", "MILLESIMI_CONSUMO", 30, 70, 0)
        tabella_ascensore_id = _get_or_create_tabella(condominio_ids[0], "ASC", "Ascensore", "MILLESIMI_PIANO", 100, 0, 0)
        tabella_acqua_id = _get_or_create_tabella(condominio_ids[0], "ACQ", "Acqua", "OCCUPANTI", 0, 0, 100)

        if tabella_generale_id:
            _ensure_millesimi(unita_ids[0], tabella_generale_id, 480.0, 2, 2)
            _ensure_millesimi(unita_ids[1], tabella_generale_id, 520.0, 1, 3)
        if tabella_riscaldamento_id:
            _ensure_millesimi(unita_ids[0], tabella_riscaldamento_id, 480.0, 2, 2, consumo=1200.0, unita_misura="kWh")
            _ensure_millesimi(unita_ids[1], tabella_riscaldamento_id, 520.0, 1, 3, consumo=900.0, unita_misura="kWh")
        if tabella_ascensore_id:
            _ensure_millesimi(unita_ids[0], tabella_ascensore_id, 480.0, 2, 2)
            _ensure_millesimi(unita_ids[1], tabella_ascensore_id, 520.0, 1, 3)
        if tabella_acqua_id:
            _ensure_millesimi(unita_ids[0], tabella_acqua_id, 0.0, 2, 2, consumo=120.0, unita_misura="mc")
            _ensure_millesimi(unita_ids[1], tabella_acqua_id, 0.0, 1, 3, consumo=150.0, unita_misura="mc")

        results["immo_tabelle_millesimali"] = 4
        results["immo_millesimi_unita"] = 8

        results.update(seed_beni_demo(db, tenant_schema, soggetto_ids, unita_ids))

        db.commit()
    except Exception as exc:
        # Example data that fail must fail the install: the test tenants
        # (scripts/tenant_prova.py) rely on them.
        db.rollback()
        logger.error("[IMMO] Test data seed failed: %s", exc)
        raise

    logger.info(f"[IMMO] Tenant seed completed: {results}")
    return results


def seed_default_tipo_mappings(db: Session) -> int:
    """
    Esempio di seed per mapping tipo_immobile -> categoria_catastale predefiniti.

    Questa funzione è un placeholder per mostrare come aggiungere seed tenant.
    Non è attualmente attiva.

    Args:
        db: Database session

    Returns:
        Number of mappings seeded
    """
    # Mappings predefiniti comuni
    DEFAULT_MAPPINGS = [
        # (tipo_immobile, codice_categoria)
        ("appartamento", "A/2"),
        ("villa", "A/8"),
        ("box", "C/6"),
        ("cantina", "C/2"),
        ("negozio", "C/1"),
        ("ufficio", "A/10"),
        ("garage", "C/6"),
        ("magazzino", "C/2"),
        ("laboratorio", "C/3"),
    ]

    # Verifica se già esistono mappings
    result = db.execute(text("SELECT COUNT(*) FROM immo_tipo_immobile_categoria_map"))
    if result.scalar() > 0:
        logger.info("[IMMO] Default mappings already exist, skipping")
        return 0

    seeded = 0
    for tipo, codice_cat in DEFAULT_MAPPINGS:
        try:
            # Trova l'ID della categoria catastale
            result = db.execute(
                text("SELECT id FROM public.immo_categorie_catastali WHERE codice = :codice"),
                {"codice": codice_cat}
            )
            cat_id = result.scalar()

            if cat_id:
                db.execute(
                    text("""
                        INSERT INTO immo_tipo_immobile_categoria_map
                        (tipo_immobile, categoria_catastale_id, confidence_score, is_user_defined)
                        VALUES (:tipo, :cat_id, 1.0, false)
                    """),
                    {"tipo": tipo, "cat_id": cat_id}
                )
                seeded += 1
        except Exception as e:
            logger.warning(f"[IMMO] Error seeding mapping {tipo}: {e}")

    db.commit()
    return seeded
