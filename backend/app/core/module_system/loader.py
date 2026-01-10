"""
Module Loader - Dynamic module discovery and loading.

The loader scans the filesystem for modules, loads their manifests,
imports Python code dynamically, and calls module entry points.
"""
import logging
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional
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
        except Exception as e:
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
                manifest_path = module_path / '__manifest__.py'
                manifest = parse_manifest(manifest_path)
                validate_manifest(manifest)

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

                    module = self.registry.install_module(
                        technical_name=technical_name,
                        name=name,
                        version=version,
                        install_path=install_path,
                        manifest=manifest,
                        **module_data
                    )

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

    def reload_enabled_modules(self) -> None:
        """
        Reload all enabled modules in dependency order.
        Useful after server restart or configuration changes.
        """
        enabled_modules = self.registry.get_enabled_modules()
        logger.info(f"Reloading {len(enabled_modules)} enabled modules...")

        if not enabled_modules:
            logger.info("No enabled modules to reload")
            return

        # Build dependency graph from enabled modules
        resolver = DependencyResolver()
        module_map = {}  # technical_name -> module_record

        for module_record in enabled_modules:
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
            load_order = [m.technical_name for m in enabled_modules]

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

                # Import and call entry point
                module_obj = self.import_module(module_path, technical_name)

                manifest = module_record.manifest
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
