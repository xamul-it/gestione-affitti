"""
Module Loader - Dynamic module discovery and loading.

The loader scans the filesystem for modules, loads their manifests,
imports Python code dynamically, and calls module entry points.
"""
import logging
import sys
import importlib
import importlib.util
import subprocess
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.sql import func
from app.core.database import SessionLocal
from app.core.module_system.alembic_utils import build_module_alembic_config
from .manifest import parse_manifest, validate_manifest, ManifestValidationError
from .registry import ModuleRegistry
from .dependency_resolver import DependencyResolver, DependencyError

logger = logging.getLogger(__name__)


class ModuleLoader:
    """
    Handles discovery and loading of modules from the filesystem.

    Responsibilities:
    - Scan module directories
    - Load and validate manifests
    - Dynamic Python imports
    - Call module entry points
    - Register routers, hooks, extensions
    """

    def __init__(self, module_dir: str, registry: ModuleRegistry, app=None):
        """
        Initialize the module loader.

        Args:
            module_dir: Directory containing modules
            registry: ModuleRegistry instance
            app: FastAPI app instance (optional, needed for register_module)
        """
        self.module_dir = Path(module_dir)
        self.registry = registry
        self.app = app

    def _disable_invalid_module(self, technical_name: str, reason: str) -> None:
        """Disable an installed module that fails manifest validation."""
        if not technical_name:
            return
        module_record = self.registry.get_module_by_technical_name(technical_name)
        if not module_record:
            return
        if module_record.enabled:
            logger.warning("Disabling module '%s': %s", technical_name, reason)
            try:
                self.registry.disable_module(technical_name)
            except Exception as e:
                logger.warning("Failed to disable module '%s': %s", technical_name, e)
        else:
            logger.warning("Module '%s' is disabled due to invalid manifest: %s", technical_name, reason)

    def _call_seed_entry(self, module_obj: Any, entry_point: str, db) -> None:
        """Call a seed entry point, passing db when supported."""
        if not entry_point:
            raise ValueError("Seed entry point is required")

        if ':' in entry_point:
            module_path, function_name = entry_point.split(':', 1)
        else:
            module_path = entry_point
            function_name = 'register'

        current = module_obj
        if module_path:
            try:
                current = importlib.import_module(f"{module_obj.__name__}.{module_path}")
            except Exception:
                parts = module_path.split('.')
                for part in parts:
                    if not hasattr(current, part):
                        raise AttributeError(f"Seed entry point '{entry_point}' not found in module")
                    current = getattr(current, part)

        if not hasattr(current, function_name):
            raise AttributeError(f"Seed entry point function '{function_name}' not found in '{module_path}'")

        func = getattr(current, function_name)
        if not callable(func):
            raise TypeError(f"Seed entry point '{entry_point}' is not callable")

        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError):
            func(db)
            return

        if len(signature.parameters) == 0:
            func()
        else:
            func(db)

    def _run_public_schema_updates(self, module_record: Any, manifest: Dict[str, Any]) -> bool:
        """Run public schema migrations during module registration."""
        schema_target = manifest.get('schema_target')
        if schema_target not in {"public", "public + tenant"}:
            return True

        module_path = Path(module_record.install_path)
        migrations_path = manifest.get('migrations_path')
        if migrations_path:
            migrations_dir = (module_path / migrations_path).resolve()
            if not migrations_dir.exists():
                logger.warning(
                    "Module '%s' migrations_path not found: %s",
                    module_record.technical_name,
                    migrations_dir,
                )
                module_record.state = 'broken'
                module_record.enabled = False
                self.registry.db.commit()
                return False
        else:
            logger.warning(
                "Module '%s' missing migrations_path for public schema updates",
                module_record.technical_name,
            )
            module_record.state = 'broken'
            module_record.enabled = False
            self.registry.db.commit()
            return False

        backend_dir = Path(__file__).resolve().parents[3]
        config_path = build_module_alembic_config(backend_dir, migrations_dir)
        try:
            result = subprocess.run(
                [
                    "alembic",
                    "-c",
                    str(config_path),
                    "-x",
                    "schema=public",
                    "-x",
                    f"module_prefix={manifest.get('module_short_code')}",
                    "-x",
                    f"module_version_table=alembic_version_{manifest.get('module_short_code')}",
                    "upgrade",
                    "head",
                ],
                cwd=str(backend_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
        finally:
            config_path.unlink(missing_ok=True)

        if result.returncode != 0:
            logger.warning(
                "Public schema migration failed for module '%s': %s",
                module_record.technical_name,
                result.stderr.strip() or result.stdout.strip(),
            )
            module_record.state = 'broken'
            module_record.enabled = False
            self.registry.db.commit()
            return False

        seeds_path = manifest.get('seeds_path')
        if seeds_path:
            seeds_dir = (module_path / seeds_path).resolve()
            if not seeds_dir.exists():
                logger.warning(
                    "Module '%s' seeds_path not found: %s",
                    module_record.technical_name,
                    seeds_dir,
                )
                module_record.state = 'broken'
                module_record.enabled = False
                self.registry.db.commit()
                return False
        else:
            logger.warning(
                "Module '%s' missing seeds_path for public schema updates",
                module_record.technical_name,
            )
            module_record.state = 'broken'
            module_record.enabled = False
            self.registry.db.commit()
            return False

        endpoints = manifest.get('endpoints', {}) if isinstance(manifest.get('endpoints'), dict) else {}
        register_endpoint = endpoints.get('register')
        if not register_endpoint:
            logger.warning(
                "Module '%s' missing endpoints.register for public schema seeding",
                module_record.technical_name,
            )
            module_record.state = 'broken'
            module_record.enabled = False
            self.registry.db.commit()
            return False

        db = SessionLocal()
        try:
            conn = db.connection()
            conn.execute(text("SET search_path TO public"))
            module_obj = self.import_module(module_path, module_record.technical_name)
            self._call_seed_entry(module_obj, register_endpoint, db)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(
                "Public schema seeding failed for module '%s': %s",
                module_record.technical_name,
                e,
            )
            module_record.state = 'broken'
            module_record.enabled = False
            self.registry.db.commit()
            return False
        finally:
            db.close()

        return True

    def discover_modules(self) -> List[Path]:
        """
        Discover all module directories.

        Returns:
            List of paths to module directories
        """
        if not self.module_dir.exists():
            logger.warning(f"Module directory '{self.module_dir}' does not exist")
            return []

        discovered = []
        for item in self.module_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_') and not item.name.startswith('.'):
                # Check if it has a manifest file
                manifest_path = item / '__manifest__.py'
                if manifest_path.exists():
                    discovered.append(item)
                    logger.debug(f"Discovered module: {item.name}")

        logger.info(f"Discovered {len(discovered)} modules in '{self.module_dir}'")
        return discovered

    def load_module_manifest(self, module_path: Path) -> Dict[str, Any]:
        """
        Load and parse a module's manifest.

        Args:
            module_path: Path to module directory

        Returns:
            Parsed manifest dictionary

        Raises:
            ManifestValidationError: If manifest is invalid
        """
        manifest_path = module_path / '__manifest__.py'
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        try:
            manifest = parse_manifest(manifest_path)
            validate_manifest(manifest)
            return manifest
        except ManifestValidationError as e:
            technical_name = None
            try:
                technical_name = manifest.get('technical_name', module_path.name)  # type: ignore[name-defined]
            except Exception:
                technical_name = module_path.name
            self._disable_invalid_module(technical_name, str(e))
            raise
        except Exception as e:
            self._disable_invalid_module(module_path.name, str(e))
            logger.error(f"Failed to load manifest from '{manifest_path}': {e}")
            raise

    def import_module(self, module_path: Path, module_name: str) -> Any:
        """
        Dynamically import a Python module.

        Args:
            module_path: Path to module directory
            module_name: Name to use for import

        Returns:
            Imported module object
        """
        # Add module path to sys.path temporarily
        module_parent = str(module_path.parent)
        if module_parent not in sys.path:
            sys.path.insert(0, module_parent)

        try:
            # Import the module
            module = importlib.import_module(module_path.name)
            logger.debug(f"Successfully imported module '{module_name}'")
            return module
        except Exception as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            raise
        finally:
            # Clean up sys.path
            if module_parent in sys.path:
                sys.path.remove(module_parent)

    def call_entry_point(self, module_obj: Any, entry_point: str, registry: ModuleRegistry) -> None:
        """
        Call a module's entry point function.

        Args:
            module_obj: Imported module object
            entry_point: Entry point path (e.g., "backend:register" or "backend.init:setup")
            registry: ModuleRegistry to pass to entry point
        """
        if not entry_point:
            return

        try:
            # Parse entry point format: "module.path:function"
            if ':' in entry_point:
                module_path, function_name = entry_point.split(':', 1)
            else:
                # Assume just module path, look for 'register' function
                module_path = entry_point
                function_name = 'register'

            # Navigate to the module/submodule
            parts = module_path.split('.')
            current = module_obj

            for part in parts:
                if not hasattr(current, part):
                    logger.warning(f"Entry point '{entry_point}' not found in module")
                    return
                current = getattr(current, part)

            # Get the function
            if not hasattr(current, function_name):
                logger.warning(f"Entry point function '{function_name}' not found in '{module_path}'")
                return

            func = getattr(current, function_name)

            # Call the function with registry
            if callable(func):
                logger.debug(f"Calling entry point: {entry_point}")
                func(registry)
            else:
                logger.warning(f"Entry point '{entry_point}' is not callable")

        except Exception as e:
            logger.error(f"Error calling entry point '{entry_point}': {e}")
            raise

    def load_module(self, module_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load a complete module: manifest, code, and registration.

        Args:
            module_path: Path to module directory

        Returns:
            Module metadata dict if successful, None otherwise
        """
        module_name = module_path.name

        try:
            # 1. Load and validate manifest
            logger.info(f"Loading module '{module_name}'...")
            manifest = self.load_module_manifest(module_path)
            technical_name = manifest.get('technical_name', module_name)

            # 2. Check if already loaded
            if self.registry.get_module_by_technical_name(technical_name):
                logger.info(f"Module '{technical_name}' already installed, skipping")
                return None

            # 3. Import Python module
            module_obj = self.import_module(module_path, technical_name)

            # 4. Call backend entry point if specified
            backend_entry = manifest.get('backend_entry')
            if backend_entry:
                self.call_entry_point(module_obj, backend_entry, self.registry)

            # 5. Return module metadata for installation
            return {
                'technical_name': technical_name,
                'name': manifest.get('name', technical_name),
                'version': manifest.get('version', '1.0.0'),
                'install_path': str(module_path),
                'manifest': manifest,
                'author': manifest.get('author'),
                'category': manifest.get('category'),
                'license': manifest.get('license'),
                'price': manifest.get('price', 0),
                'summary': manifest.get('summary'),
                'description': manifest.get('description'),
                'website': manifest.get('website'),
                'icon': manifest.get('icon'),
                'core_version_min': manifest.get('core_version_min'),
                'core_version_max': manifest.get('core_version_max'),
            }

        except Exception as e:
            logger.error(f"Failed to load module '{module_name}': {e}")
            return None

    def install_discovered_modules(self) -> List[str]:
        """
        Discover and install all modules from filesystem with dependency resolution.

        Returns:
            List of installed module technical names
        """
        discovered = self.discover_modules()
        installed = []

        # First pass: load all manifests and build dependency graph
        modules_to_install = {}  # technical_name -> (module_path, manifest)
        resolver = DependencyResolver()

        for module_path in discovered:
            try:
                manifest = self.load_module_manifest(module_path)

                technical_name = manifest.get('technical_name', module_path.name)

                # Check if already installed
                if self.registry.get_module_by_technical_name(technical_name):
                    logger.info(f"Module '{technical_name}' already installed, skipping")
                    continue

                modules_to_install[technical_name] = (module_path, manifest)

                # Add to dependency resolver
                resolver.add_module(
                    technical_name=technical_name,
                    module_version=manifest.get('version', '1.0.0'),
                    depends=manifest.get('depends', []),
                    optional_depends=manifest.get('optional_depends', [])
                )

            except ManifestValidationError as e:
                logger.warning(f"Invalid manifest for '{module_path}': {e}")
                continue
            except Exception as e:
                logger.error(f"Failed to load manifest from '{module_path}': {e}")
                continue

        if not modules_to_install:
            logger.info("No new modules to install")
            return installed

        # Resolve dependencies and get load order
        try:
            load_order = resolver.resolve()
            logger.info(f"Module installation order: {' -> '.join(load_order)}")
        except DependencyError as e:
            logger.error(f"Dependency resolution failed: {e}")
            # Try to install without dependency resolution
            logger.warning("Attempting installation without dependency resolution...")
            load_order = list(modules_to_install.keys())

        # Second pass: install modules in dependency order
        for technical_name in load_order:
            if technical_name not in modules_to_install:
                continue

            module_path, manifest = modules_to_install[technical_name]

            try:
                module_data = self.load_module(module_path)
                if module_data:
                    # Install in registry
                    technical_name = module_data.pop('technical_name')
                    name = module_data.pop('name')
                    version = module_data.pop('version')
                    install_path = module_data.pop('install_path')
                    manifest = module_data.pop('manifest')

                    module_data["category"] = None
                    module = self.registry.install_module(
                        technical_name=technical_name,
                        name=name,
                        version=version,
                        install_path=install_path,
                        manifest=manifest,
                        **module_data
                    )

                    if not self._run_public_schema_updates(module, manifest):
                        logger.warning(
                            "Module '%s' registration halted due to public schema migration errors",
                            technical_name,
                        )
                        continue

                    if manifest.get("schema_target") == "tenant":
                        module.registered = True
                        module.registered_at = func.now()
                        self.registry.db.commit()

                    # Auto-enable if manifest says so
                    if manifest.get('auto_install', False):
                        self.registry.enable_module(module.id)

                    installed.append(technical_name)
                    logger.info(f"Module '{technical_name}' installed successfully")

            except Exception as e:
                logger.error(f"Failed to install module '{technical_name}': {e}")
                continue

        logger.info(f"Installation complete. {len(installed)} modules installed.")
        return installed

    def reload_registered_modules(self) -> None:
        """
        Reload all registered modules in dependency order.
        Useful after server restart or configuration changes.
        """
        registered_modules = self.registry.get_registered_modules()
        logger.info(f"Reloading {len(registered_modules)} registered modules...")

        if not registered_modules:
            logger.info("No registered modules to reload")
            return

        # Build dependency graph from registered modules
        resolver = DependencyResolver()
        module_map = {}  # technical_name -> module_record

        for module_record in registered_modules:
            module_map[module_record.technical_name] = module_record
            manifest = module_record.manifest

            resolver.add_module(
                technical_name=module_record.technical_name,
                module_version=module_record.version,
                depends=manifest.get('depends', []),
                optional_depends=manifest.get('optional_depends', [])
            )

        # Resolve load order
        try:
            load_order = resolver.resolve()
            logger.info(f"Module reload order: {' -> '.join(load_order)}")
        except DependencyError as e:
            logger.error(f"Dependency resolution failed during reload: {e}")
            # Fallback to database order
            logger.warning("Reloading modules in database order...")
            load_order = [m.technical_name for m in registered_modules]

        # Reload in dependency order
        for technical_name in load_order:
            if technical_name not in module_map:
                continue

            module_record = module_map[technical_name]

            try:
                module_path = Path(module_record.install_path)
                if not module_path.exists():
                    logger.error(f"Module path '{module_path}' not found for module '{technical_name}'")
                    continue

                try:
                    manifest = self.load_module_manifest(module_path)
                except ManifestValidationError as e:
                    self._disable_invalid_module(technical_name, str(e))
                    continue

                module_record.manifest = manifest
                module_record.name = manifest.get('name', module_record.name)
                module_record.version = manifest.get('version', module_record.version)
                module_record.author = manifest.get('author', module_record.author)
                module_record.category = None
                module_record.icon = manifest.get('icon', module_record.icon)
                self.registry.db.commit()

                # Import and call entry point
                module_obj = self.import_module(module_path, technical_name)

                backend_entry = manifest.get('backend_entry')
                if backend_entry:
                    self.call_entry_point(module_obj, backend_entry, self.registry)

                # Call register_module(app) if it exists (convention for route registration)
                if self.app and hasattr(module_obj, 'register_module'):
                    register_func = getattr(module_obj, 'register_module')
                    if callable(register_func):
                        logger.info(f"Calling register_module() for '{technical_name}'")
                        register_func(self.app)

                logger.info(f"Module '{technical_name}' reloaded successfully")

            except Exception as e:
                logger.error(f"Failed to reload module '{technical_name}': {e}")
                # Mark as broken
                module_record.state = 'broken'
                self.registry.db.commit()

        logger.info("Module reload complete")

    def ensure_tenant_only_registered(self) -> int:
        """
        Mark tenant-only modules as registered if installed but not registered.
        """
        updated = 0
        modules = self.registry.get_all_modules()

        for module_record in modules:
            if module_record.registered or module_record.state == "broken":
                continue

            manifest = module_record.manifest or {}
            schema_target = manifest.get("schema_target")

            if not schema_target:
                module_path = Path(module_record.install_path)
                if module_path.exists():
                    try:
                        manifest = self.load_module_manifest(module_path)
                        module_record.manifest = manifest
                        schema_target = manifest.get("schema_target")
                    except Exception as e:
                        logger.warning(
                            "Failed to refresh manifest for '%s': %s",
                            module_record.technical_name,
                            e,
                        )
                        continue

            if schema_target == "tenant":
                module_record.registered = True
                module_record.registered_at = func.now()
                if module_record.state == "broken":
                    module_record.state = "installed"
                updated += 1

        if updated:
            self.registry.db.commit()

        return updated
