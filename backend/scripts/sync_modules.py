"""
Allinea il DB ai moduli presenti nel codice: migrazioni di modulo e dati di
base pubblici. Pensato per scripts/promote.sh, dopo `alembic -x schema=all`
(che esegue solo la catena core).

Per ogni modulo registrato, in ordine di dipendenza:
  1. migrazioni di modulo sullo schema public (se schema_target lo prevede);
  2. migrazioni di modulo su ogni tenant in cui il modulo e' installato
     (cioe' ha la sua tabella alembic_version_<codice>);
  3. seed pubblico (endpoints.register del manifest), idempotente.

Senza questo script le migrazioni e i seed di modulo girano solo alla prima
registrazione o all'installazione per tenant, quindi gli aggiornamenti non
arrivano mai a un DB gia' esistente.

Riallinea anche core_modules.install_path alla cartella moduli di questo
backend: un DB copiato da un altro ambiente punterebbe al codice di quello.

Un modulo abilitato su un tenant ma mai installato (nessuna tabella
alembic_version_<codice>) viene installato con l'installatore dell'app,
TenantModuleService.install_module_for_tenant, senza dati di esempio:
"abilitato" deve voler dire che le sue funzioni ci sono.

Di suo non cancella dati; lo fa solo una migrazione di modulo che lo dichiara
(es. immobili 2026111201_beni, azzeramento deciso dall'utente).

Uso (dalla cartella backend, con il venv attivo):
    python scripts/sync_modules.py            # esegue
    python scripts/sync_modules.py --dry-run  # mostra solo cosa farebbe
Exit code 1 se un passo fallisce.
"""
import argparse
import importlib
import inspect
import os
import runpy
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.module_system.alembic_utils import build_module_alembic_config  # noqa: E402
from app.core.platform_services.document_type_sync import sync_document_types  # noqa: E402
from app.core.platform_services.relation_type_sync import sync_relation_types  # noqa: E402

MODULE_DIR = Path(settings.resolved_module_dir)
sys.path.insert(0, str(MODULE_DIR))
# L'installatore dei moduli lancia "alembic" come comando: deve essere
# quello di questo venv anche quando lo script non e' lanciato dal venv attivo.
os.environ["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}"

PUBLIC_TARGETS = {"public", "public + tenant"}


def log(msg: str) -> None:
    print(msg, flush=True)


def load_manifest(name: str) -> dict:
    path = MODULE_DIR / name / "__manifest__.py"
    return runpy.run_path(str(path))["manifest"]


def dependency_order(manifests: dict) -> list:
    ordered, seen = [], set()

    def visit(name):
        if name in seen or name not in manifests:
            return
        seen.add(name)
        for dep in manifests[name].get("dependencies") or []:
            visit(dep)
        ordered.append(name)

    for name in sorted(manifests):
        visit(name)
    return ordered


def run_module_alembic(name: str, manifest: dict, schema: str, dry_run: bool) -> bool:
    code = manifest["module_short_code"]
    migrations_dir = (MODULE_DIR / name / manifest["migrations_path"]).resolve()
    log(f"    migrazioni {name} -> {schema}")
    if dry_run:
        return True
    config_path = build_module_alembic_config(BACKEND_DIR, migrations_dir)
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "alembic", "-c", str(config_path),
                "-x", f"schema={schema}",
                "-x", f"module_prefix={code}",
                "-x", f"module_version_table=alembic_version_{code}",
                "upgrade", "head",
            ],
            cwd=str(BACKEND_DIR), capture_output=True, text=True, timeout=300,
        )
    finally:
        config_path.unlink(missing_ok=True)
    if result.returncode != 0:
        log(f"    ERRORE migrazione {name} su {schema}:\n{result.stderr or result.stdout}")
        return False
    return True


def load_all_models(order: list) -> None:
    # Stessi import di alembic/env.py: senza tutti i modelli i mapper con
    # relazioni tra moduli (es. SoggettoAnagrafico -> User) non si configurano.
    from app.core.module_system import models as _ms  # noqa: F401
    from app.core.auth import models as _auth  # noqa: F401
    from app.core.models import import_configuration, table_configuration  # noqa: F401
    from app.core.models import tenant as _tenant  # noqa: F401
    from app.core.models import RuoloDisponibile, SoggettoRuolo  # noqa: F401
    from app.core.platform import models as _platform  # noqa: F401

    for name in order:
        try:
            importlib.import_module(f"{name}.models")
        except ModuleNotFoundError:
            pass
    from sqlalchemy.orm import configure_mappers
    configure_mappers()


def call_seed(name: str, entry_point: str, db) -> None:
    module_path, _, func_name = entry_point.partition(":")
    func_name = func_name or "register"
    target = importlib.import_module(f"{name}.{module_path}" if module_path else name)
    func = getattr(target, func_name)
    if len(inspect.signature(func).parameters) == 0:
        func()
    else:
        func(db)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        registered = conn.execute(text(
            "SELECT technical_name, install_path, state FROM public.core_modules WHERE registered"
        )).all()
        tenant_ids = {r[0]: r[1] for r in conn.execute(text(
            "SELECT schema_name, id FROM public.core_tenants ORDER BY schema_name"
        ))}
        tenants = list(tenant_ids)
        enabled = {(r[0], r[1]) for r in conn.execute(text(
            "SELECT t.schema_name, tm.module_id FROM public.core_tenant_modules tm "
            "JOIN public.core_tenants t ON t.id = tm.tenant_id WHERE tm.enabled"
        ))}
        version_tables = {(r[0], r[1].lower()) for r in conn.execute(text(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_name ILIKE 'alembic_version_%'"
        ))}

    manifests, install_paths = {}, {}
    for name, install_path, state in registered:
        if state == "broken":
            log(f"  ATTENZIONE: modulo {name} in stato 'broken', saltato")
            continue
        if not (MODULE_DIR / name / "__manifest__.py").exists():
            log(f"  ATTENZIONE: modulo registrato {name} non presente in {MODULE_DIR}, saltato")
            continue
        manifests[name] = load_manifest(name)
        install_paths[name] = install_path
    order = dependency_order(manifests)
    ok = True

    log(f"==> Moduli ({MODULE_DIR}): {', '.join(order)}")

    stale = {n: p for n, p in install_paths.items() if Path(p) != MODULE_DIR / n}
    for name, path in stale.items():
        log(f"  install_path {name}: {path} -> {MODULE_DIR / name}")
    if stale and not args.dry_run:
        with engine.begin() as conn:
            for name in stale:
                conn.execute(
                    text("UPDATE public.core_modules SET install_path = :p WHERE technical_name = :n"),
                    {"p": str(MODULE_DIR / name), "n": name},
                )

    to_install = []
    for name in order:
        manifest = manifests[name]
        if not manifest.get("migrations_path") or not manifest.get("module_short_code"):
            continue
        code = manifest["module_short_code"].lower()
        log(f"  {name}")
        if manifest.get("schema_target") in PUBLIC_TARGETS:
            ok &= run_module_alembic(name, manifest, "public", args.dry_run)
        for schema in tenants:
            if (schema, f"alembic_version_{code}") in version_tables:
                ok &= run_module_alembic(name, manifest, schema, args.dry_run)
            elif (schema, name) in enabled:
                to_install.append((schema, name))

    if not ok:
        log("==> Migrazioni di modulo fallite: installazioni e seed pubblici non eseguiti")
        return 1

    from sqlalchemy.orm import Session

    if to_install:
        log("==> Installazione moduli abilitati ma mai installati")
        for schema, name in to_install:
            log(f"  {name} -> {schema}")
        if not args.dry_run:
            load_all_models(order)
            from app.core.services.tenant_module_service import TenantModuleService
            for schema, name in to_install:  # in ordine di dipendenza
                with Session(engine) as db:
                    try:
                        TenantModuleService.install_module_for_tenant(
                            tenant_ids[schema], name, db, run_migrations=True, seed_test_data=False,
                        )
                        db.commit()
                    except Exception as exc:
                        db.rollback()
                        log(f"  ERRORE installazione {name} su {schema}: {exc}")
                        ok = False
            if not ok:
                log("==> Installazioni fallite: seed pubblici non eseguiti")
                return 1

    log("==> Tipologie documentali")
    # complete=True deactivates also unowned legacy types: only safe when
    # every registered module's manifest was read.
    complete = len(manifests) == len(registered)
    declared = sum(len(m.get("document_types") or []) for m in manifests.values())
    log(f"  {declared} tipologie dichiarate da {len(manifests)} moduli (completo: {complete})")
    if not args.dry_run:
        load_all_models(order)
        with Session(engine) as db:
            try:
                db.execute(text("SET search_path TO public"))
                report = sync_document_types(db, manifests, complete=complete)
                db.commit()
                log(f"  create {report.creati or '-'}; aggiornate {report.aggiornati or '-'}; "
                    f"disattivate {report.disattivati or '-'}")
                for e in report.errori:
                    log(f"  ERRORE tipologia {e}")
                    ok = False
            except Exception as exc:
                db.rollback()
                log(f"  ERRORE sync tipologie: {exc}")
                ok = False

    log("==> Tipi di relazione")
    declared = sum(len(m.get("relation_types") or []) for m in manifests.values())
    log(f"  {declared} tipi dichiarati da {len(manifests)} moduli (completo: {complete})")
    if not args.dry_run:
        load_all_models(order)
        with Session(engine) as db:
            try:
                db.execute(text("SET search_path TO public"))
                report = sync_relation_types(db, manifests, complete=complete)
                db.commit()
                log(f"  creati {report.creati or '-'}; aggiornati {report.aggiornati or '-'}; "
                    f"disattivati {report.disattivati or '-'}")
                for e in report.errori:
                    log(f"  ERRORE tipo di relazione {e}")
                    ok = False
            except Exception as exc:
                db.rollback()
                log(f"  ERRORE sync tipi di relazione: {exc}")
                ok = False

    log("==> Permessi dei moduli")
    # Additive only: creates missing manifest permissions and grants them to
    # the admin roles; never removes a permission or a grant.
    if not args.dry_run:
        from app.core.auth.seed_platform_permissions import sync_module_permissions
        for name in order:
            with Session(engine) as db:
                try:
                    db.execute(text("SET search_path TO public"))
                    res = sync_module_permissions(db, manifests[name])
                    if res["permissions_created"] or res["roles_updated"]:
                        log(f"  {name}: creati {res['permissions_created']}, ruoli aggiornati {res['roles_updated']}")
                except Exception as exc:
                    db.rollback()
                    log(f"  ERRORE permessi {name}: {exc}")
                    ok = False

    log("==> Seed pubblici")
    seeds = [
        (n, (manifests[n].get("endpoints") or {}).get("register"))
        for n in order
        if manifests[n].get("schema_target") in PUBLIC_TARGETS
    ]
    seeds = [(n, e) for n, e in seeds if e]
    for name, entry in seeds:
        log(f"  {name}: {entry}")
    if not args.dry_run and seeds:
        load_all_models(order)
        for name, entry in seeds:
            with Session(engine) as db:
                try:
                    db.execute(text("SET search_path TO public"))
                    call_seed(name, entry, db)
                    db.commit()
                except Exception as exc:  # un seed rotto non deve bloccare gli altri
                    db.rollback()
                    log(f"  ERRORE seed {name}: {exc}")
                    ok = False

    # Per-tenant data alignment after migrations and document types (e.g.
    # immobili: old energy certificates -> APE documents, history, scadenze).
    # Idempotent; only on tenants where the module is installed.
    log("==> Allineamento dati per tenant (post_sync)")
    installed = {(s, n) for s, n in to_install}
    hooks = []
    for name in order:
        entry = (manifests[name].get("endpoints") or {}).get("post_sync")
        code = (manifests[name].get("module_short_code") or "").lower()
        if not entry:
            continue
        for schema in tenants:
            if (schema, f"alembic_version_{code}") in version_tables or (schema, name) in installed:
                hooks.append((name, entry, schema))
    for name, entry, schema in hooks:
        log(f"  {name} -> {schema}")
    if not args.dry_run and hooks:
        load_all_models(order)
        for name, entry, schema in hooks:
            module_path, _, func_name = entry.partition(":")
            target = importlib.import_module(f"{name}.{module_path}" if module_path else name)
            with Session(engine) as db:
                try:
                    db.execute(text(f"SET search_path TO {schema}, public"))
                    report = getattr(target, func_name)(db, schema)
                    db.commit()
                    log(f"    {report}")
                except Exception as exc:
                    db.rollback()
                    log(f"  ERRORE post_sync {name} su {schema}: {exc}")
                    ok = False
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
