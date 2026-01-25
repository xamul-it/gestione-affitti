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
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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
    # - Dati inseriti dall'utente (unità immobiliari, condomini, proprietari, etc.)
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
        ]
        results["anag_soggetti_anagrafici"] = len(soggetto_ids)

        def _get_or_create_proprietario(soggetto_id: int, label: str) -> int:
            proprietario_id = db.execute(
                text("SELECT id FROM immo_proprietari WHERE soggetto_id = :sid"),
                {"sid": soggetto_id},
            ).scalar()
            if proprietario_id:
                return proprietario_id
            return db.execute(
                text(
                    """
                    INSERT INTO immo_proprietari
                        (soggetto_id, note_proprietario)
                    VALUES
                        (:soggetto_id, :note)
                    RETURNING id
                    """
                ),
                {"soggetto_id": soggetto_id, "note": label},
            ).scalar()

        proprietari_ids = [
            _get_or_create_proprietario(soggetto_ids[0], "Proprietario principale"),
            _get_or_create_proprietario(soggetto_ids[1], "Comproprietario"),
            _get_or_create_proprietario(soggetto_ids[2], "Proprietario investimento"),
        ]
        results["immo_proprietari"] = len(proprietari_ids)

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
                text("SELECT id FROM immo_unita_immobiliari WHERE codice = :codice"),
                {"codice": codice},
            ).scalar()
            if unita_id:
                return unita_id
            return db.execute(
                text(
                    """
                    INSERT INTO immo_unita_immobiliari
                        (codice, tipo, condominio_id, indirizzo, citta, cap, provincia, superficie_mq, locali, categoria_catastale_id)
                    VALUES
                        (:codice, :tipo, :condominio_id, :indirizzo, 'Milano', '20100', 'MI', :superficie, :locali, :categoria_catastale_id)
                    RETURNING id
                    """
                ),
                {
                    "codice": codice,
                    "tipo": tipo,
                    "condominio_id": condominio_id,
                    "indirizzo": f"Via Roma {codice[-1]}",
                    "superficie": 85.5 if tipo == "Appartamento" else 110.0,
                    "locali": 3 if tipo == "Appartamento" else 4,
                    "categoria_catastale_id": categoria_catastale_id,
                },
            ).scalar()

        unita_ids = [
            _get_or_create_unita("UNITA-001", "Appartamento", condominio_ids[0]),
            _get_or_create_unita("UNITA-002", "Appartamento", condominio_ids[0]),
            _get_or_create_unita("UNITA-003", "Villetta", None),
        ]
        results["immo_unita_immobiliari"] = len(unita_ids)

        def _ensure_diritto(unita_id: int, proprietario_id: int, quota: float):
            exists = db.execute(
                text(
                    """
                    SELECT id FROM immo_diritti_immobile
                    WHERE unita_immobiliare_id = :unita_id AND proprietario_id = :proprietario_id
                    """
                ),
                {"unita_id": unita_id, "proprietario_id": proprietario_id},
            ).scalar()
            if exists:
                return
            db.execute(
                text(
                    """
                    INSERT INTO immo_diritti_immobile
                        (unita_immobiliare_id, proprietario_id, tipo_diritto, quota_percentuale, data_inizio)
                    VALUES
                        (:unita_id, :proprietario_id, 'PROPRIETARIO', :quota, '2025-01-01')
                    """
                ),
                {"unita_id": unita_id, "proprietario_id": proprietario_id, "quota": quota},
            )

        _ensure_diritto(unita_ids[0], proprietari_ids[0], 50.0)
        _ensure_diritto(unita_ids[0], proprietari_ids[1], 50.0)
        _ensure_diritto(unita_ids[1], proprietari_ids[2], 100.0)
        _ensure_diritto(unita_ids[2], proprietari_ids[0], 100.0)
        results["immo_diritti_immobile"] = 4

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
        if tipologia_terreno_id:
            terreno_count = db.execute(text("SELECT COUNT(*) FROM immo_terreni")).scalar() or 0
            if terreno_count == 0:
                db.execute(
                    text(
                        """
                        INSERT INTO immo_terreni
                            (codice, nome, comune, provincia, superficie, tipologia_id, attivo)
                        VALUES
                            ('TER-001', 'Terreno Agricolo', 'Milano', 'MI', 1500, :tipologia_id, TRUE),
                            ('TER-002', 'Area Edificabile', 'Milano', 'MI', 800, :tipologia_id, TRUE)
                        """
                    ),
                    {"tipologia_id": tipologia_terreno_id},
                )
                results["immo_terreni"] = 2

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

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("[IMMO] Test data seed failed: %s", exc)

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
