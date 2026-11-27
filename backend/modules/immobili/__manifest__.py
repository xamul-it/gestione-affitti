"""
Manifest for Immobili (Real Estate Properties) Module

Conforme agli standard di architettura moduli v1.0
"""

IMMOBILE = ["IMMOBILE"]
RELAZIONE = ["RELAZIONE"]
IMMOBILE_E_RELAZIONE = ["IMMOBILE", "RELAZIONE"]
# Tenancies and assignments also go on a raggruppamento (inherited by its beni); rights only on beni.
BENE_O_RAMO = ["IMMOBILE", "RAGGRUPPAMENTO"]

# Relation types on beni (units and land parcels), by family: (codice, nome, descrizione).
DIRITTI_REALI = [
    ("proprieta", "Proprietà", "Titolare del diritto di proprietà sul bene"),
    ("nuda_proprieta", "Nuda proprietà", "Titolare della nuda proprietà (art. 978 c.c.)"),
    ("usufrutto", "Usufrutto", "Titolare dell'usufrutto (art. 978 c.c.)"),
    ("uso", "Uso", "Titolare del diritto di uso (art. 1021 c.c.)"),
    ("abitazione", "Abitazione", "Titolare del diritto di abitazione (art. 1022 c.c.)"),
    ("superficie", "Superficie", "Titolare del diritto di superficie (art. 952 c.c.)"),
    ("enfiteusi", "Enfiteusi", "Enfiteuta (art. 957 c.c.)"),
    ("diritto_reale_altro", "Altro diritto reale", "Altro diritto reale di godimento"),
]
GODIMENTO = [
    ("conduttore", "Conduttore", "Chi occupa o usa il bene in locazione, con o senza contratto"),
    ("affittuario_agrario", "Affittuario agrario", "Chi coltiva il fondo in affitto agrario"),
    ("comodatario", "Comodatario",
     "Chi usa il bene in comodato; estremi di registrazione in dati (registrazione_data, "
     "registrazione_ufficio, registrazione_numero)"),
    ("godimento_altro", "Altro godimento", "Altro titolo di godimento del bene"),
]
INCARICHI = [
    ("manutentore", "Manutentore", "Incaricato della manutenzione del bene"),
    ("terzo_responsabile_impianto", "Terzo responsabile impianto",
     "Terzo responsabile dell'impianto termico (DPR 74/2013)"),
    ("responsabile_impianto", "Responsabile impianto", "Responsabile dell'impianto termico"),
    ("tecnico_incaricato", "Tecnico incaricato", "Tecnico incaricato (catasto, pratiche edilizie, APE)"),
    ("incarico_altro", "Altro incarico", "Altro incarico sul bene"),
]

manifest = {
    # Campi obbligatori
    "name": "Immobili",
    "technical_name": "immobili",
    "version": "2025022002",
    "module_short_code": "IMMO",  # 4 caratteri - usato come prefisso per tutte le tabelle
    "schema_target": "public + tenant",  # Tabelle sia in public che in tenant schema
    "migrations_path": "migrations/",
    "seeds_path": "seeds/",
    "endpoints": {
        "register": ":register",  # Funzione in __init__.py per registrazione modulo (crea tabelle public + seed)
        "install": ":install",    # Funzione in __init__.py per installazione su tenant (crea tabelle tenant)
        "post_sync": ":post_sync",  # Allineamento dati per tenant dopo migrazioni e tipologie (sync_modules.py)
    },

    # Tipi di relazione soggetto -> oggetto (spec 2026-11-10-relazioni-ruoli-soggetti)
    "relation_types": [
        *[
            {"codice": c, "nome": n, "descrizione": d, "entity_types": IMMOBILE, "fonte": "CORE",
             "permesso_oggetto": "immobile.view", "famiglia": "diritti_reali",
             "ammette_quota": True, "solo_beni": True}
            for c, n, d in DIRITTI_REALI
        ],
        *[
            {"codice": c, "nome": n, "descrizione": d, "entity_types": BENE_O_RAMO, "fonte": "CORE",
             "permesso_oggetto": "immobile.view", "famiglia": "godimento"}
            for c, n, d in GODIMENTO
        ],
        *[
            {"codice": c, "nome": n, "descrizione": d, "entity_types": BENE_O_RAMO, "fonte": "CORE",
             "permesso_oggetto": "immobile.view", "famiglia": "incarichi"}
            for c, n, d in INCARICHI
        ],
        {
            "codice": "amministratore_condominio",
            "nome": "Amministratore condominio",
            "descrizione": "Incarico annuale, rinnovato per eguale durata (art. 1129 c.c.)",
            "entity_types": ["CONDOMINIO"],
            "scadenza": {"mesi": 12, "da": "data_inizio"},
            "promemoria_giorni": [60, 30],
            "unico_per_oggetto": True,
            "permesso_oggetto": "condominio.view",
        },
    ],

    # Per-object visibility of the relations on beni: the permission depends on the bene type.
    # A raggruppamento is seen with immobile.view or terreno.view (one row each).
    "object_permissions": {
        "IMMOBILE": "immobili.services.relazioni_bene:permessi_vista",
        "RAGGRUPPAMENTO": "immobili.services.relazioni_bene:permessi_vista_raggruppamenti",
    },
    # Relations on a ramo are inherited by every bene below it: writing them needs the edit
    # permission of each bene type found there (immobile.edit and/or terreno.edit).
    "object_edit_permissions": {
        "RAGGRUPPAMENTO": "immobili.services.relazioni_bene:permessi_modifica_raggruppamenti",
    },

    # Campi opzionali
    "author": "Gestione Affitti Team",
    "sequence": 20,
    "license": "proprietary",
    "installable": True,
    "auto_install": False,
    "application": True,

    # Dipendenze
    "dependencies": ["anagrafica_italiana"],

    # Document types of this module (spec 2026-11-09 tipologie documentali).
    # Synced into public.core_tipi_documento by document_type_sync.
    # SOSTITUTIVO: a newer document supersedes the previous one (kept as
    # history); CUMULATIVO: documents accumulate.
    "document_types": [
        {"codice": "VISURA_CATASTALE", "nome": "Visura catastale",
         "descrizione": "Visura catastale Agenzia delle Entrate",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO",
         "form": "immobili.visura"},
        {"codice": "PLANIMETRIA_CATASTALE", "nome": "Planimetria catastale",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO"},
        {"codice": "VARIAZIONE_CATASTALE", "nome": "Variazione catastale",
         "descrizione": "DOCFA, voltura, frazionamento, fusione, tipo mappale e relative ricevute",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "CUMULATIVO",
         "sottotipi": ["DOCFA", "VOLTURA", "FRAZIONAMENTO", "FUSIONE", "TIPO_MAPPALE"]},
        {"codice": "APE", "nome": "Attestato di prestazione energetica",
         "descrizione": "Valido 10 anni dalla data di emissione",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO",
         "scadenza": {"mesi": 120, "da": "data_riferimento"}, "promemoria_giorni": [90, 30],
         "form": "immobili.ape"},
        {"codice": "ATTO_PROVENIENZA", "nome": "Atto di provenienza",
         "categoria": "immobiliare", "entity_types": IMMOBILE_E_RELAZIONE, "regime": "CUMULATIVO",
         "sottotipi": ["COMPRAVENDITA", "SUCCESSIONE", "DONAZIONE"]},
        {"codice": "CONFORMITA_IMPIANTO", "nome": "Dichiarazione di conformità impianto",
         "descrizione": "DM 37/2008",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO",
         "sottotipi": ["ELETTRICO", "GAS", "TERMICO", "IDRICO"]},
        {"codice": "LIBRETTO_IMPIANTO", "nome": "Libretto impianto termico / controllo",
         "descrizione": "Indicare come scadenza la data del prossimo controllo",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "CUMULATIVO",
         "scadenza": {"manuale": True}, "promemoria_giorni": [90, 30]},
        {"codice": "AGIBILITA", "nome": "Agibilità / abitabilità",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO"},
        {"codice": "TITOLO_EDILIZIO", "nome": "Titolo edilizio",
         "descrizione": "Permesso di costruire, SCIA, CILA, condono",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "CUMULATIVO"},
        {"codice": "POLIZZA_FABBRICATO", "nome": "Polizza assicurativa fabbricato",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO",
         "scadenza": {"manuale": True}, "promemoria_giorni": [90, 30]},
        # Land parcels (spec beni catastali, obiettivo 8).
        {"codice": "ESTRATTO_MAPPA", "nome": "Estratto di mappa",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO"},
        {"codice": "CDU", "nome": "Certificato di destinazione urbanistica",
         "descrizione": "Valido un anno dal rilascio (L. 47/1985 art. 18)",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "SOSTITUTIVO",
         "scadenza": {"mesi": 12, "da": "data_riferimento"}, "promemoria_giorni": [30]},
        {"codice": "CONTRATTO_AFFITTO_AGRARIO", "nome": "Contratto di affitto agrario",
         "categoria": "immobiliare", "entity_types": IMMOBILE_E_RELAZIONE, "regime": "CUMULATIVO"},
        # Documents attached to a relation (a right, a tenancy): entity_type RELAZIONE.
        {"codice": "CONTRATTO_COMODATO", "nome": "Contratto di comodato",
         "categoria": "immobiliare", "entity_types": RELAZIONE, "regime": "CUMULATIVO"},
        {"codice": "DELEGA_TERZO_RESPONSABILE", "nome": "Delega di terzo responsabile",
         "descrizione": "Delega della gestione dell'impianto termico a un terzo responsabile",
         "categoria": "immobiliare", "entity_types": RELAZIONE, "regime": "CUMULATIVO"},
        {"codice": "ALTRO_IMMOBILE", "nome": "Altro documento",
         "categoria": "immobiliare", "entity_types": IMMOBILE, "regime": "CUMULATIVO"},
    ],
    "optional_depends": [],

    # Models forniti dal modulo (con prefisso immo_)
    "models": [
        # Domain data (public schema)
        "immo_categorie_catastali",
        "immo_tipologie_terreno",
        # Tenant data
        "immo_tipologie_terreno_overrides",
        "immo_terreni",
        "immo_terreni_porzioni",
        "immo_raggruppamenti",
        "immo_beni",
        "immo_beni_collegamenti",
        "immo_unita_immobiliari",
        "immo_condomini",
        "immo_certificati_energetici",
        "immo_tabelle_millesimali",
        "immo_millesimi_unita",
        "immo_tipo_immobile_categoria_map",
    ],

    # Public domain tables required for registration
    "public_tables": [
        "immo_categorie_catastali",
        "immo_tipologie_terreno",
    ],

    # Tenant schema tables (created during tenant install)
    "tenant_tables": [
        "immo_condomini",
        "immo_raggruppamenti",
        "immo_beni",
        "immo_beni_collegamenti",
        "immo_unita_immobiliari",
        "immo_certificati_energetici",
        "immo_tabelle_millesimali",
        "immo_millesimi_unita",
        "immo_tipologie_terreno_overrides",
        "immo_terreni",
        "immo_terreni_porzioni",
        "immo_tipo_immobile_categoria_map",
        "immo_spese_ricorrenti",
    ],

    # DDL for override tables (reference public domain tables, created directly in tenant schema)
    "override_tables_ddl": {
        "immo_tipologie_terreno_overrides": """
            CREATE TABLE IF NOT EXISTS {schema}.immo_tipologie_terreno_overrides (
                id SERIAL PRIMARY KEY,
                tipologia_id INTEGER NOT NULL REFERENCES public.immo_tipologie_terreno(id) ON DELETE CASCADE,
                codice VARCHAR(20),
                nome VARCHAR(100),
                descrizione TEXT,
                attivo BOOLEAN,
                is_deleted BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ,
                UNIQUE(tipologia_id)
            )
        """,
    },

    # API prefix
    "api_prefix": "/immobili",

    # Permissions
    "permissions": [
        "immobile.view",
        "immobile.create",
        "immobile.edit",
        "immobile.delete",
        "condominio.view",
        "condominio.create",
        "condominio.edit",
        "condominio.delete",
        "certificato_energetico.view",
        "certificato_energetico.create",
        "certificato_energetico.edit",
        "certificato_energetico.delete",
        "terreno.view",
        "terreno.create",
        "terreno.edit",
        "terreno.delete",
        "spesa_ricorrente.view",
        "spesa_ricorrente.create",
        "spesa_ricorrente.edit",
        "spesa_ricorrente.delete",
    ],

    # Dashboard widgets
    "widgets": [
        {
            "id": "immobili.stats",
            "title": "Statistiche Immobili",
            "component": "ImmobiliStatsWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "required_permission": "immobile.view",
        },
        {
            "id": "immobili.certificati_scadenza",
            "title": "Certificati in Scadenza",
            "component": "CertificatiScadenzaWidget",
            "default_width": 6,
            "default_height": 4,
            "category": "alerts",
            "required_permission": "certificato_energetico.view",
        },
    ],

    # Menu items
    "menu_items": [
        {
            "id": "immobili.unita",
            "label": "Unità Immobiliari",
            "path": "/unita-immobiliari",
            "icon": "building",
            "order_index": 10,
            "required_permission": "immobile.view"
        },
        {
            "id": "immobili.terreni",
            "label": "Terreni",
            "path": "/terreni",
            "icon": "leaf",
            "order_index": 15,
            "required_permission": "terreno.view"
        },
        {
            "id": "immobili.raggruppamenti",
            "label": "Raggruppamenti",
            "path": "/raggruppamenti",
            "icon": "folder",
            "order_index": 17,
            "required_permission": "immobile.view"
        },
        {
            "id": "immobili.proprietari",
            "label": "Proprietari",
            "path": "/proprietari",
            "icon": "user",
            "order_index": 20,
            "required_permission": "immobile.view"
        },
        {
            "id": "immobili.condomini",
            "label": "Condomini",
            "path": "/condomini",
            "icon": "building-2",
            "order_index": 30,
            "required_permission": "condominio.view"
        },
        {
            "id": "immobili.conduttori",
            "label": "Conduttori",
            "path": "/conduttori",
            "icon": "user-check",
            "order_index": 25,
            "required_permission": "immobile.view"
        },
        {
            "id": "immobili.documenti",
            "label": "Documenti",
            "path": "/immobili/documenti",
            "icon": "file-text",
            "order_index": 27,
            "required_permission": "documenti.read"
        },
        {
            "id": "immobili.certificati",
            "label": "Certificati Energetici",
            "path": "/immobili/documenti?tipo=APE",
            "icon": "zap",
            "order_index": 40,
            "required_permission": "documenti.read"
        },
        {
            "id": "immobili.categorie_catastali",
            "label": "Categorie Catastali",
            "path": "/categorie-catastali",
            "icon": "list",
            "order_index": 90,
            "required_permission": "platform.admin",
            "is_domain_data": True,
        },
        {
            "id": "immobili.tipologie_terreno",
            "label": "Tipologie Terreno",
            "path": "/tipologie-terreno",
            "icon": "leaf",
            "order_index": 95,
            "required_permission": "platform.admin",
            "is_domain_data": True,
        },
    ],
}
