#!/usr/bin/env python3
"""
manage.py - CLI for Gestione Affitti module management

Usage:
    python manage.py module install <path/to/module.zip>
    python manage.py module remove <module_name> [--keep-data | --drop-data]
    python manage.py module list
    python manage.py module info <module_name>
"""
import argparse
import importlib
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Add backend/ to sys.path so we can import app.*
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.module_system.manifest import parse_manifest, validate_manifest, ManifestValidationError


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_db():
    return SessionLocal()


def _modules_dir() -> Path:
    return settings.resolved_module_dir


def _frontend_modules_dir() -> Path | None:
    if settings.FRONTEND_MODULES_DIR:
        return Path(settings.FRONTEND_MODULES_DIR)
    # Default: ../frontend/src/modules relative to backend/
    candidate = BACKEND_DIR.parent / "frontend" / "src" / "modules"
    return candidate if candidate.exists() else None


def _load_module_record(db, module_name: str):
    from app.core.module_system.models import Module
    return db.query(Module).filter(Module.technical_name == module_name).first()


def _get_installed_module_names(db) -> list[str]:
    from app.core.module_system.models import Module
    return [m.technical_name for m in db.query(Module).filter(Module.registered == True).all()]


def _get_reverse_deps(module_name: str, db) -> list[str]:
    """Return list of installed modules that depend on module_name."""
    from app.core.module_system.models import Module
    dependents = []
    for m in db.query(Module).filter(Module.registered == True).all():
        manifest = m.manifest or {}
        deps = manifest.get("dependencies", [])
        if module_name in deps:
            dependents.append(m.technical_name)
    return dependents


def _run_module_migrations(module_record, schema: str = "all"):
    """Run alembic migrations for the module."""
    manifest = module_record.manifest or {}
    migrations_path = manifest.get("migrations_path")
    module_prefix = manifest.get("module_short_code")
    schema_target = manifest.get("schema_target", "tenant")

    if not migrations_path or not module_prefix:
        print(f"  [migrations] skipped: missing migrations_path or module_short_code")
        return True

    install_path = Path(module_record.install_path)
    migrations_dir = (install_path / migrations_path).resolve()
    if not migrations_dir.exists():
        print(f"  [migrations] skipped: migrations dir not found: {migrations_dir}")
        return True

    from app.core.module_system.alembic_utils import build_module_alembic_config
    config_path = build_module_alembic_config(BACKEND_DIR, migrations_dir)

    # Determine which schemas to migrate
    if schema == "all":
        if schema_target == "public":
            schemas = ["public"]
        elif schema_target == "tenant":
            schemas = _get_all_tenant_schemas()
        else:  # "public + tenant"
            schemas = ["public"] + _get_all_tenant_schemas()
    else:
        schemas = [schema]

    success = True
    try:
        for s in schemas:
            print(f"  [migrations] running on schema={s} prefix={module_prefix}")
            result = subprocess.run(
                [
                    "alembic", "-c", str(config_path),
                    "-x", f"schema={s}",
                    "-x", f"module_prefix={module_prefix}",
                    "-x", f"module_version_table=alembic_version_{module_prefix}",
                    "upgrade", "head",
                ],
                cwd=str(BACKEND_DIR),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                print(f"  [migrations] FAILED on {s}:\n{result.stderr.strip() or result.stdout.strip()}")
                success = False
            else:
                print(f"  [migrations] OK on {s}")
    finally:
        config_path.unlink(missing_ok=True)

    return success


def _get_all_tenant_schemas() -> list[str]:
    from app.core.models.tenant import Tenant
    db = _get_db()
    try:
        return [t.schema_name for t in db.query(Tenant).all()]
    finally:
        db.close()


def _print_table(headers: list[str], rows: list[list]):
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_install(args):
    zip_path = Path(args.zip_path)
    if not zip_path.exists():
        print(f"Error: file not found: {zip_path}")
        sys.exit(1)
    if not zipfile.is_zipfile(zip_path):
        print(f"Error: not a valid ZIP file: {zip_path}")
        sys.exit(1)

    print(f"Installing module from: {zip_path}")

    # ── 1. Validate ZIP structure ─────────────────────────────────────────
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Find top-level directory
        top_dirs = {n.split("/")[0] for n in names if "/" in n}
        if len(top_dirs) != 1:
            print(f"Error: ZIP must contain exactly one top-level directory (found: {top_dirs})")
            sys.exit(1)
        module_dir_name = top_dirs.pop()

        # Check manifest
        manifest_zpath = f"{module_dir_name}/__manifest__.py"
        if manifest_zpath not in names:
            print(f"Error: missing {manifest_zpath} in ZIP")
            sys.exit(1)

        manifest_src = zf.read(manifest_zpath).decode("utf-8")

    # Parse manifest from ZIP
    ns: dict = {}
    exec(manifest_src, ns)
    manifest = ns.get("manifest", {})
    if not manifest:
        print("Error: manifest dict not found in __manifest__.py")
        sys.exit(1)

    try:
        validate_manifest(manifest)
    except ManifestValidationError as e:
        print(f"Error: invalid manifest: {e}")
        sys.exit(1)

    module_name = manifest["technical_name"]
    version = manifest.get("version", "unknown")
    print(f"  Module: {manifest.get('name')} ({module_name}) v{version}")

    # ── 2. Check dependencies ─────────────────────────────────────────────
    db = _get_db()
    try:
        installed = set(_get_installed_module_names(db))
        missing_deps = [d for d in manifest.get("dependencies", []) if d not in installed]
        if missing_deps:
            print(f"Error: missing dependencies: {', '.join(missing_deps)}")
            print("Install them first.")
            sys.exit(1)
    finally:
        db.close()

    # ── 3. Extract backend ────────────────────────────────────────────────
    install_dir = _modules_dir() / module_name
    backup_dir = None
    if install_dir.exists():
        backup_dir = install_dir.parent / f"{module_name}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"  Backing up existing install to: {backup_dir.name}")
        shutil.move(str(install_dir), str(backup_dir))

    print(f"  Extracting backend to: {install_dir}")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if not member.startswith(f"{module_dir_name}/frontend/"):
                    target = _modules_dir() / member
                    if member.endswith("/"):
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(zf.read(member))
        # Rename extracted dir to module_name (in case they differ)
        extracted = _modules_dir() / module_dir_name
        if extracted != install_dir:
            extracted.rename(install_dir)
    except Exception as e:
        print(f"Error extracting ZIP: {e}")
        if backup_dir:
            shutil.move(str(backup_dir), str(install_dir))
        sys.exit(1)

    # ── 4. Extract frontend ───────────────────────────────────────────────
    frontend_dir = _frontend_modules_dir()
    frontend_extracted = False
    if frontend_dir:
        with zipfile.ZipFile(zip_path) as zf:
            frontend_members = [n for n in zf.namelist() if n.startswith(f"{module_dir_name}/frontend/")]
            if frontend_members:
                target_fe = frontend_dir / module_name
                target_fe.mkdir(parents=True, exist_ok=True)
                for member in frontend_members:
                    rel = member[len(f"{module_dir_name}/frontend/"):]
                    if not rel:
                        continue
                    target = target_fe / rel
                    if member.endswith("/"):
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(zf.read(member))
                print(f"  Frontend assets extracted to: {target_fe}")
                frontend_extracted = True

    # ── 5. Register in DB ─────────────────────────────────────────────────
    db = _get_db()
    try:
        from app.core.module_system.models import Module
        from sqlalchemy.sql import func

        record = db.query(Module).filter(Module.technical_name == module_name).first()
        if record:
            record.manifest = manifest
            record.name = manifest.get("name", module_name)
            record.version = version
            record.install_path = str(install_dir)
            record.state = "installed"
        else:
            record = Module(
                technical_name=module_name,
                name=manifest.get("name", module_name),
                version=version,
                install_path=str(install_dir),
                manifest=manifest,
                state="installed",
                registered=False,
                created_at=func.now(),
            )
            db.add(record)
        db.commit()
        db.refresh(record)
        print(f"  Registered in DB: {module_name}")
    except Exception as e:
        print(f"Error registering module in DB: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

    # ── 6. Run migrations ─────────────────────────────────────────────────
    if not args.no_migrate:
        print("  Running migrations...")
        db = _get_db()
        try:
            record = _load_module_record(db, module_name)
            ok = _run_module_migrations(record, schema="all")
            if not ok:
                print("Warning: some migrations failed. Check logs.")
        finally:
            db.close()

    # ── 7. Summary ────────────────────────────────────────────────────────
    print()
    print(f"✅ Module '{module_name}' installed successfully.")
    if backup_dir:
        print(f"   Previous version backed up at: {backup_dir}")
    if frontend_extracted:
        print()
        print("⚠️  ACTION REQUIRED: rebuild the frontend to activate changes:")
        print(f"      cd {BACKEND_DIR.parent / 'frontend'} && npm run build")
        print("   Or restart dev server: npm run dev")
    print()
    print("Restart the backend to activate the module:")
    print("   ./start.sh  or  python app/main.py")


def cmd_remove(args):
    module_name = args.module_name

    # Determine data mode
    if args.drop_data and args.keep_data:
        print("Error: cannot use both --keep-data and --drop-data")
        sys.exit(1)
    drop_data = args.drop_data  # default is keep_data

    db = _get_db()
    try:
        record = _load_module_record(db, module_name)
        if not record:
            print(f"Error: module '{module_name}' is not installed")
            sys.exit(1)

        # ── 1. Check reverse dependencies ──────────────────────────────
        dependents = _get_reverse_deps(module_name, db)
        if dependents:
            print(f"Error: cannot remove '{module_name}' — required by: {', '.join(dependents)}")
            print("Remove dependent modules first.")
            sys.exit(1)

        # ── 2. Confirm if drop_data ─────────────────────────────────────
        if drop_data:
            confirm = input(
                f"\n⚠️  This will DROP all database tables for '{module_name}' in ALL tenant schemas.\n"
                f"   Data will be PERMANENTLY lost.\n"
                f"   Type the module name to confirm: "
            )
            if confirm.strip() != module_name:
                print("Aborted.")
                sys.exit(0)

        manifest = record.manifest or {}
        tenant_tables = manifest.get("tenant_tables", [])

        # ── 3. Drop data (optional) ─────────────────────────────────────
        if drop_data and tenant_tables:
            from sqlalchemy import text
            tenant_schemas = _get_all_tenant_schemas()
            for schema in tenant_schemas:
                print(f"  Dropping tables in schema '{schema}'...")
                for table in reversed(tenant_tables):
                    try:
                        db.execute(text("SET LOCAL lock_timeout = '5s'"))
                        db.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE'))
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        print(f"    Warning: could not drop {schema}.{table}: {e}")

        # ── 4. Deregister from DB ───────────────────────────────────────
        from app.core.module_system.models import Module
        record.registered = False
        record.state = "uninstalled"
        db.commit()
        print(f"  Deregistered '{module_name}' from DB")

        # ── 5. Move files ───────────────────────────────────────────────
        install_path = Path(record.install_path)
        if install_path.exists():
            backup_path = install_path.parent / f"{module_name}.removed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(str(install_path), str(backup_path))
            print(f"  Module files moved to: {backup_path.name}")
        else:
            print(f"  Module files not found at: {install_path}")

        # ── 6. Frontend notice ──────────────────────────────────────────
        frontend_dir = _frontend_modules_dir()
        if frontend_dir:
            fe_path = frontend_dir / module_name
            if fe_path.exists():
                print()
                print(f"⚠️  Remove frontend module files manually:")
                print(f"      rm -rf {fe_path}")

    finally:
        db.close()

    print()
    print(f"✅ Module '{module_name}' removed.")
    print("Restart the backend to apply changes:")
    print("   ./start.sh  or  python app/main.py")


def cmd_list(args):
    db = _get_db()
    try:
        from app.core.module_system.models import Module
        modules = db.query(Module).order_by(Module.technical_name).all()
        if not modules:
            print("No modules installed.")
            return
        rows = []
        for m in modules:
            manifest = m.manifest or {}
            deps = ", ".join(manifest.get("dependencies", [])) or "—"
            rows.append([
                m.technical_name,
                m.version or "—",
                "✅" if m.registered else "❌",
                m.state or "—",
                deps,
            ])
        _print_table(["Module", "Version", "Registered", "State", "Dependencies"], rows)
    finally:
        db.close()


def cmd_info(args):
    db = _get_db()
    try:
        record = _load_module_record(db, args.module_name)
        if not record:
            print(f"Module '{args.module_name}' not found.")
            sys.exit(1)
        manifest = record.manifest or {}
        print(f"Name:          {record.name}")
        print(f"Technical:     {record.technical_name}")
        print(f"Version:       {record.version}")
        print(f"State:         {record.state}")
        print(f"Registered:    {record.registered}")
        print(f"Install path:  {record.install_path}")
        print(f"Dependencies:  {', '.join(manifest.get('dependencies', [])) or '—'}")
        print(f"Schema target: {manifest.get('schema_target', '—')}")
        tenant_tables = manifest.get("tenant_tables", [])
        print(f"Tenant tables: {len(tenant_tables)}")
        if tenant_tables:
            for t in tenant_tables:
                print(f"  - {t}")
    finally:
        db.close()


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Gestione Affitti module manager",
    )
    sub = parser.add_subparsers(dest="command")

    # module subcommand
    module_parser = sub.add_parser("module", help="Module management")
    module_sub = module_parser.add_subparsers(dest="subcommand")

    # module install
    install_parser = module_sub.add_parser("install", help="Install a module from a ZIP file")
    install_parser.add_argument("zip_path", help="Path to the module ZIP file")
    install_parser.add_argument("--no-migrate", action="store_true", help="Skip running migrations")

    # module remove
    remove_parser = module_sub.add_parser("remove", help="Remove an installed module")
    remove_parser.add_argument("module_name", help="Technical name of the module")
    data_group = remove_parser.add_mutually_exclusive_group()
    data_group.add_argument("--keep-data", action="store_true", default=True,
                            help="Keep database tables (default)")
    data_group.add_argument("--drop-data", action="store_true",
                            help="Drop database tables (IRREVERSIBLE)")

    # module list
    module_sub.add_parser("list", help="List installed modules")

    # module info
    info_parser = module_sub.add_parser("info", help="Show details about a module")
    info_parser.add_argument("module_name", help="Technical name of the module")

    args = parser.parse_args()

    if args.command == "module":
        if args.subcommand == "install":
            cmd_install(args)
        elif args.subcommand == "remove":
            cmd_remove(args)
        elif args.subcommand == "list":
            cmd_list(args)
        elif args.subcommand == "info":
            cmd_info(args)
        else:
            module_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
