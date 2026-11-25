"""
Tenant di prova per le migrazioni (docs/superpowers/plans/2026-11-25-tenant-di-prova.md).

  nuovo      cancella e ricrea tenant_test_nuovo: schema vuoto, migrazioni
             core, tutti i moduli registrati con i dati di esempio
             (seed_test_data=True), poi confronto schema/modelli.
  evolutivo  tenant_test_evolutivo: alla prima esecuzione si crea come
             "nuovo"; dalle successive riceve solo le migrazioni (core e di
             modulo) e i moduli nuovi, come la produzione. I conteggi per
             tabella si confrontano con la fotografia dell'esecuzione
             precedente: una tabella sparita o con meno righe e' un errore,
             salvo --perdita-consentita "motivo". Poi confronto schema/modelli.
  stato      stampa versioni alembic e conteggi dei due tenant.

Lo script lavora solo su schema che iniziano per "tenant_test_": gli altri
tenant (produzione, principale, qa_test) non vengono mai toccati.

Uso (dalla cartella backend, con il venv attivo):
    python scripts/tenant_prova.py nuovo
    python scripts/tenant_prova.py evolutivo [--perdita-consentita "motivo"]
    python scripts/tenant_prova.py stato
Exit code 0 = VERDE, 1 = ROSSO.
"""
import argparse
import contextlib
import json
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

import sync_modules as sm  # noqa: E402  (sets sys.path for modules and PATH for alembic)
from sqlalchemy import create_engine, inspect as sa_inspect, text  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.tenant_tables import TENANT_ONLY_CORE_TABLES  # noqa: E402

PREFISSO = "tenant_test_"
NUOVO = "tenant_test_nuovo"
EVOLUTIVO = "tenant_test_evolutivo"
FOTOGRAFIA = "zz_prova_fotografia"
UTENTE_ADMIN = "admin"

# Differences between migrations and models that already existed when the
# check was introduced (2026-11-25). Each one needs a migration or a model
# fix; until then it is reported but does not turn the result red.
# Key: (table, kind, detail) as printed by confronta_schema.
_ENUM_TESTO = "enum del modello salvato come testo nel DB"
_JSONB = "JSONB nel DB, JSON nel modello"
_TS = "timestamp: migrazione e modello non coincidono"
DIFFERENZE_NOTE: dict[tuple[str, str, str], str] = {
    ("anag_ruoli_azienda", "tipo", "created_at: db TIMESTAMPTZ, modello TIMESTAMP"): _TS,
    ("anag_ruoli_azienda", "nullabilità", "updated_at: db True, modello False"): _TS,
    ("anag_ruoli_azienda", "tipo", "updated_at: db TIMESTAMPTZ, modello TIMESTAMP"): _TS,
    ("anag_soggetti_anagrafici", "tipo", "tipo_soggetto: db VARCHAR(50), modello ENUM"): _ENUM_TESTO,
    ("immo_assegnazioni_conduttore", "nullabilità", "created_at: db False, modello True"): _TS,
    ("immo_conduttori", "nullabilità", "created_at: db False, modello True"): _TS,
    ("immo_spese_ricorrenti", "tipo", "responsabile: db VARCHAR(20), modello ENUM"): _ENUM_TESTO,
    ("pec_audit_accessi", "tipo", "dettagli: db JSONB, modello JSON"): _JSONB,
    ("pec_messaggi", "tipo", "allegati_meta: db JSONB, modello JSON"): _JSONB,
    ("core_documenti", "tipo", "entity_type: db VARCHAR(50), modello ENUM"): _ENUM_TESTO,
    ("core_documenti", "tipo", "tipo_documento: db VARCHAR(50), modello ENUM"): _ENUM_TESTO,
    ("core_documenti", "nullabilità", "tipo_documento: db False, modello True"): _TS.replace("timestamp", "tipo_documento"),
    ("core_documenti", "nullabilità", "created_at: db False, modello True"): _TS,
}


def log(msg: str = "") -> None:
    print(msg, flush=True)


def controlla_db(url: str) -> None:
    """Never on the production database (gestione_affitti_prod)."""
    nome = url.rsplit("/", 1)[-1].split("?", 1)[0]
    if nome.endswith("_prod"):
        raise SystemExit(f"Database di produzione ({nome}): i tenant di prova vivono solo in sviluppo")


@contextlib.contextmanager
def spia_fallback():
    """Collect the tables the installer creates from the models because a migration did not.

    install_module_for_tenant falls back to the SQLAlchemy metadata when a
    manifest table is missing after the migrations: the schema would then
    match the models by construction and hide the broken migration.
    """
    from app.core.services.tenant_module_service import TenantModuleService
    originale = TenantModuleService._create_module_tables_from_metadata
    create: list[str] = []

    def spia(module_id, *args, **kwargs):
        tabelle = originale(module_id, *args, **kwargs)
        create.extend(f"{module_id}: {t}" for t in tabelle or [])
        return tabelle

    TenantModuleService._create_module_tables_from_metadata = staticmethod(spia)
    try:
        yield create
    finally:
        TenantModuleService._create_module_tables_from_metadata = staticmethod(originale)


def _installa(engine, tenant_id: int, nome_modulo: str, motivo: str) -> bool:
    from app.core.services.tenant_module_service import TenantModuleService
    log(f"  installa {nome_modulo} ({motivo})")
    with spia_fallback() as create, Session(engine) as db:
        try:
            TenantModuleService.install_module_for_tenant(
                tenant_id, nome_modulo, db, run_migrations=True, seed_test_data=True)
            db.commit()
        except Exception as exc:  # report every module, then fail
            db.rollback()
            log(f"  ERRORE installazione {nome_modulo}: {exc}")
            return False
    for t in create:
        log(f"  ERRORE tabella creata dai modelli, la migrazione non la crea: {t}")
    return not create


def _controlla_nome(schema: str) -> None:
    if not schema.startswith(PREFISSO) or not schema.replace("_", "").isalnum():
        raise SystemExit(f"Schema non ammesso: {schema} (solo {PREFISSO}*)")


def _moduli(engine):
    with engine.connect() as conn:
        registrati = [r[0] for r in conn.execute(text(
            "SELECT technical_name FROM public.core_modules WHERE registered AND state <> 'broken'"
        ))]
    manifests = {n: sm.load_manifest(n) for n in registrati if (sm.MODULE_DIR / n / "__manifest__.py").exists()}
    return manifests, sm.dependency_order(manifests)


def _esiste_schema(engine, schema: str) -> bool:
    with engine.connect() as conn:
        return bool(conn.execute(text(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = :s"), {"s": schema}).scalar())


def _alembic_core(schema: str) -> bool:
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "-x", f"schema={schema}", "upgrade", "head"],
        cwd=str(BACKEND_DIR), capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        log(f"  ERRORE migrazioni core su {schema}:\n{r.stderr or r.stdout}")
    return r.returncode == 0


def cancella(engine, schema: str) -> None:
    _controlla_nome(schema)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM public.core_tenants WHERE schema_name = :s"), {"s": schema})
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


def crea(engine, schema: str, nome: str) -> bool:
    """New tenant with every registered module and its example data."""
    _controlla_nome(schema)
    manifests, ordine = _moduli(engine)
    sm.load_all_models(ordine)
    from app.core.models.tenant import Tenant
    from app.core.services.tenant_module_service import TenantModuleService
    from app.core.services.tenant_service import TenantService

    with Session(engine) as db:
        tenant = Tenant(schema_name=schema, nome_display=nome,
                        descrizione="Tenant di prova delle migrazioni (scripts/tenant_prova.py)")
        db.add(tenant)
        db.commit()
        TenantService.create_tenant_schema(tenant, db)
        tenant_id = tenant.id
        admin_id = db.execute(text("SELECT id FROM public.core_users WHERE username = :u"),
                              {"u": UTENTE_ADMIN}).scalar()
        if admin_id:
            TenantService.grant_user_access(admin_id, tenant_id, False, db)
            db.commit()

    log(f"  migrazioni core -> {schema}")
    if not _alembic_core(schema):
        return False
    ok = True
    for nome_modulo in ordine:
        ok &= _installa(engine, tenant_id, nome_modulo, "dati di esempio")
    return ok


def _tabelle(conn, schema: str) -> list[str]:
    return [r[0] for r in conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = :s AND table_type = 'BASE TABLE' ORDER BY table_name"), {"s": schema})]


def conteggi(engine, schema: str) -> dict[str, int]:
    with engine.connect() as conn:
        return {
            t: conn.execute(text(f'SELECT count(*) FROM "{schema}"."{t}"')).scalar()
            for t in _tabelle(conn, schema)
            if not t.startswith("alembic_version") and t != FOTOGRAFIA
        }


def versioni(engine, schema: str) -> dict[str, str]:
    with engine.connect() as conn:
        out = {}
        for t in _tabelle(conn, schema):
            if t.startswith("alembic_version"):
                out[t] = ",".join(r[0] for r in conn.execute(text(f'SELECT version_num FROM "{schema}"."{t}"')))
        return out


def salva_fotografia(engine, schema: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(
            f'CREATE TABLE IF NOT EXISTS "{schema}".{FOTOGRAFIA} ('
            "id SERIAL PRIMARY KEY, eseguito_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
            "conteggi JSONB NOT NULL, versioni JSONB NOT NULL, nota TEXT)"))
        conn.execute(text(
            f'INSERT INTO "{schema}".{FOTOGRAFIA} (conteggi, versioni) VALUES (CAST(:c AS jsonb), CAST(:v AS jsonb))'),
            {"c": json.dumps(conteggi(engine, schema)), "v": json.dumps(versioni(engine, schema))})


def ultima_fotografia(engine, schema: str):
    with engine.connect() as conn:
        if not conn.execute(text("SELECT to_regclass(:t)"), {"t": f"{schema}.{FOTOGRAFIA}"}).scalar():
            return None
        r = conn.execute(text(
            f'SELECT conteggi, versioni, eseguito_at FROM "{schema}".{FOTOGRAFIA} ORDER BY id DESC LIMIT 1')).first()
        return r


def _tipo(tipo) -> str:
    """Comparable type name: 'VARCHAR(50)', 'INTEGER', 'NUMERIC(12, 2)'..."""
    try:
        s = tipo.compile(dialect=postgresql.dialect())
    except Exception:
        s = str(tipo)
    s = s.upper().replace("CHARACTER VARYING", "VARCHAR").replace("TIMESTAMP WITHOUT TIME ZONE", "TIMESTAMP")
    s = s.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ").replace("DOUBLE PRECISION", "FLOAT")
    if s.startswith("ENUM") or (hasattr(tipo, "enums") and getattr(tipo, "enums", None)):
        return "ENUM"
    return s


def confronta_schema(engine, schema: str, manifests: dict) -> list[tuple[str, str, str]]:
    """Differences between the tenant schema and the SQLAlchemy models."""
    from app.core.database import Base
    differenze = []
    attese = set()
    for m in manifests.values():
        attese |= set(m.get("tenant_tables") or [])
    insp = sa_inspect(engine)
    presenti = set(insp.get_table_names(schema=schema))
    for t in sorted(attese - presenti):
        differenze.append((t, "tabella mancante", "dichiarata dal manifest"))

    for nome, tabella in sorted(Base.metadata.tables.items()):
        if tabella.schema is not None:
            continue
        if nome not in presenti:
            # Every module is installed here: a tenant model without its table
            # is a table no migration creates in a new tenant. core_* models
            # without a schema are platform tables (public) unless listed.
            di_tenant = not nome.startswith("core_") or nome in TENANT_ONLY_CORE_TABLES
            if di_tenant and nome not in attese:
                differenze.append((nome, "tabella del modello mancante", "nessuna migrazione la crea"))
            continue
        db_col = {c["name"]: c for c in insp.get_columns(nome, schema=schema)}
        for col in tabella.columns:
            c = db_col.get(col.name)
            if c is None:
                differenze.append((nome, "colonna mancante", col.name))
                continue
            if bool(c["nullable"]) != bool(col.nullable) and not col.primary_key:
                differenze.append((nome, "nullabilità", f"{col.name}: db {c['nullable']}, modello {col.nullable}"))
            if _tipo(c["type"]) != _tipo(col.type):
                differenze.append((nome, "tipo", f"{col.name}: db {_tipo(c['type'])}, modello {_tipo(col.type)}"))
        for extra in sorted(set(db_col) - {c.name for c in tabella.columns}):
            differenze.append((nome, "colonna in più", extra))

        db_fk = {(tuple(f["constrained_columns"]), f["referred_table"]) for f in insp.get_foreign_keys(nome, schema=schema)}
        for fk in tabella.foreign_key_constraints:
            chiave = (tuple(c.name for c in fk.columns), fk.referred_table.name)
            if chiave not in db_fk:
                differenze.append((nome, "chiave esterna mancante", f"{','.join(chiave[0])} -> {chiave[1]}"))

        db_idx = {tuple(i["column_names"]) for i in insp.get_indexes(nome, schema=schema)}
        db_idx |= {tuple(u["column_names"]) for u in insp.get_unique_constraints(nome, schema=schema)}
        db_idx_nomi = {i["name"] for i in insp.get_indexes(nome, schema=schema)}
        pk = tuple(insp.get_pk_constraint(nome, schema=schema).get("constrained_columns") or [])
        for idx in tabella.indexes:
            colonne = tuple(c.name for c in idx.columns)
            if idx.name not in db_idx_nomi and colonne not in db_idx and colonne != pk:
                differenze.append((nome, "indice mancante", f"{idx.name} ({','.join(colonne)})"))
    return differenze


def stampa_differenze(differenze) -> bool:
    nuove = [d for d in differenze if d not in DIFFERENZE_NOTE]
    note = [d for d in differenze if d in DIFFERENZE_NOTE]
    if not differenze:
        log("  schema = modelli")
    for d in nuove:
        log(f"  DIFFERENZA {d[0]}: {d[1]} {d[2]}")
    if note:
        log(f"  {len(note)} differenze note (DIFFERENZE_NOTE), non bloccanti")
    return not nuove


def perdite(prima: dict[str, int], dopo: dict[str, int]) -> list[str]:
    """Tables gone or with fewer rows than in the previous photograph."""
    out = []
    for t, n in sorted(prima.items()):
        if t not in dopo:
            if n:
                out.append(f"{t}: tabella sparita ({n} righe)")
        elif dopo[t] < n:
            out.append(f"{t}: {n} -> {dopo[t]} righe")
    return out


def tabelle_vuote_sparite(prima: dict[str, int], dopo: dict[str, int]) -> list[str]:
    return [t for t, n in sorted(prima.items()) if t not in dopo and not n]


def _migra(engine, schema: str) -> tuple[bool, list[str]]:
    """Core chain and module chains; returns the modules not installed yet."""
    manifests, ordine = _moduli(engine)
    log(f"  migrazioni core -> {schema}")
    ok = _alembic_core(schema)
    vers = versioni(engine, schema)
    da_installare = []
    for nome in ordine:
        m = manifests[nome]
        if not m.get("migrations_path") or not m.get("module_short_code"):
            continue
        if f"alembic_version_{m['module_short_code'].lower()}" in {k.lower() for k in vers}:
            ok &= sm.run_module_alembic(nome, m, schema, False)
        else:
            da_installare.append(nome)
    return ok, da_installare


def _installa_nuovi(engine, schema: str, moduli: list[str]) -> bool:
    if not moduli:
        return True
    _, ordine = _moduli(engine)
    sm.load_all_models(ordine)
    with engine.connect() as conn:
        tenant_id = conn.execute(text("SELECT id FROM public.core_tenants WHERE schema_name = :s"),
                                 {"s": schema}).scalar()
    ok = True
    for nome in moduli:
        ok &= _installa(engine, tenant_id, nome, "nuovo modulo, dati di esempio")
    return ok


def riesegui_esempi(engine, schema: str) -> bool:
    """Rerun every installed module's example data (they must only add what is missing)."""
    _, ordine = _moduli(engine)
    sm.load_all_models(ordine)
    from app.core.services.tenant_module_service import TenantModuleService
    with engine.connect() as conn:
        tenant_id = conn.execute(text("SELECT id FROM public.core_tenants WHERE schema_name = :s"),
                                 {"s": schema}).scalar()
        installati = {r[0] for r in conn.execute(text(
            "SELECT module_id FROM public.core_tenant_modules WHERE tenant_id = :t"), {"t": tenant_id})}
    ok = True
    for nome in ordine:
        if nome not in installati:
            continue
        with Session(engine) as db:
            try:
                db.execute(text(f'SET search_path TO "{schema}", public'))
                if TenantModuleService.reseed_test_data_for_tenant(tenant_id, nome, db) is False:
                    raise RuntimeError("install entry point failed")
                db.commit()
            except Exception as exc:
                db.rollback()
                log(f"  ERRORE dati di esempio {nome}: {exc}")
                ok = False
    return ok


def non_idempotenti(prima: dict[str, int], dopo: dict[str, int]) -> list[str]:
    """Tables that grew when the example data ran a second time."""
    return [f"{t}: {prima.get(t, 0)} -> {n}" for t, n in sorted(dopo.items()) if n > prima.get(t, 0)]


def cmd_nuovo(engine) -> bool:
    log(f"==> {NUOVO}: da zero")
    cancella(engine, NUOVO)
    ok = crea(engine, NUOVO, "Prova: creazione da zero")
    if ok:
        prima = conteggi(engine, NUOVO)
        ok = riesegui_esempi(engine, NUOVO)
        for riga in non_idempotenti(prima, conteggi(engine, NUOVO)):
            log(f"  ESEMPI NON IDEMPOTENTI {riga}")
            ok = False
    manifests, ordine = _moduli(engine)
    sm.load_all_models(ordine)
    ok &= stampa_differenze(confronta_schema(engine, NUOVO, manifests))
    vuote = [t for t, n in conteggi(engine, NUOVO).items() if n == 0]
    log(f"  tabelle senza dati di esempio: {len(vuote)}" + (f" ({', '.join(vuote)})" if vuote else ""))
    return ok


def cmd_evolutivo(engine, perdita_consentita) -> bool:
    log(f"==> {EVOLUTIVO}: aggiornamento continuo")
    if not _esiste_schema(engine, EVOLUTIVO):
        log("  non esiste: lo creo con i dati di esempio (prima fotografia)")
        ok = crea(engine, EVOLUTIVO, "Prova: aggiornamento continuo")
        if ok:
            salva_fotografia(engine, EVOLUTIVO)
        manifests, ordine = _moduli(engine)
        sm.load_all_models(ordine)
        return ok and stampa_differenze(confronta_schema(engine, EVOLUTIVO, manifests))

    precedente = ultima_fotografia(engine, EVOLUTIVO)
    ok, nuovi_moduli = _migra(engine, EVOLUTIVO)
    # Counted before installing new modules: their example rows must not
    # cover rows lost by a migration.
    dopo = conteggi(engine, EVOLUTIVO)
    vers_dopo = versioni(engine, EVOLUTIVO)
    if precedente is None:
        log("  nessuna fotografia precedente: salvo la prima")
    else:
        prima, vers_prima, quando = precedente
        log(f"  confronto con la fotografia del {quando:%Y-%m-%d %H:%M}")
        for t, v in sorted(vers_dopo.items()):
            if vers_prima.get(t) != v:
                log(f"  {t}: {vers_prima.get(t) or '-'} -> {v}")
        perse = perdite(prima, dopo)
        for t in tabelle_vuote_sparite(prima, dopo):
            log(f"  tabella vuota sparita (rinominata o tolta) {t}")
        for t in sorted(set(dopo) - set(prima)):
            log(f"  tabella nuova {t}: {dopo[t]} righe")
        for p in perse:
            log(f"  PERDITA {p}")
        if perse and not perdita_consentita:
            ok = False
        elif perse:
            log(f"  perdite consentite: {perdita_consentita}")
        if not perse:
            log("  nessuna tabella o riga persa")
    if ok:
        ok = _installa_nuovi(engine, EVOLUTIVO, nuovi_moduli)
    if ok:
        # Example data added to the modules since the last run.
        prima_esempi = conteggi(engine, EVOLUTIVO)
        ok = riesegui_esempi(engine, EVOLUTIVO)
        for riga in non_idempotenti(prima_esempi, conteggi(engine, EVOLUTIVO)):
            log(f"  esempi aggiunti {riga}")
    if ok:
        salva_fotografia(engine, EVOLUTIVO)
        if perdita_consentita:
            with engine.begin() as conn:
                conn.execute(text(f'UPDATE "{EVOLUTIVO}".{FOTOGRAFIA} SET nota = :n WHERE id = '
                                  f'(SELECT max(id) FROM "{EVOLUTIVO}".{FOTOGRAFIA})'), {"n": perdita_consentita})
    manifests, ordine = _moduli(engine)
    sm.load_all_models(ordine)
    return stampa_differenze(confronta_schema(engine, EVOLUTIVO, manifests)) and ok


def cmd_stato(engine) -> bool:
    for schema in (NUOVO, EVOLUTIVO):
        log(f"==> {schema}")
        if not _esiste_schema(engine, schema):
            log("  non esiste")
            continue
        for t, v in sorted(versioni(engine, schema).items()):
            log(f"  {t}: {v}")
        c = conteggi(engine, schema)
        log(f"  {len(c)} tabelle, {sum(c.values())} righe; vuote: {sum(1 for n in c.values() if n == 0)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Tenant di prova per le migrazioni")
    parser.add_argument("comando", choices=["nuovo", "evolutivo", "stato"])
    parser.add_argument("--perdita-consentita", metavar="MOTIVO",
                        help="evolutivo: accetta righe o tabelle perse, col motivo")
    args = parser.parse_args()
    controlla_db(settings.DATABASE_URL)
    engine = create_engine(settings.DATABASE_URL)
    if args.comando == "nuovo":
        ok = cmd_nuovo(engine)
    elif args.comando == "evolutivo":
        ok = cmd_evolutivo(engine, args.perdita_consentita)
    else:
        ok = cmd_stato(engine)
    log("ESITO: VERDE" if ok else "ESITO: ROSSO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
