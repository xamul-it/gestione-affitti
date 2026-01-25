"""
Module Registry - Central management for installed modules.

The registry tracks all installed modules, their state, and provides
methods for installation, enabling, disabling, and uninstalling modules.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Module, ModuleDependency, ModulePermission, ModuleHook, ModuleExtension, ModuleEndpoint

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Central registry for managing modules.

    Responsibilities:
    - Track installed modules
    - Manage module state (enabled/disabled)
    - Register routers, hooks, and extension points
    - Validate dependencies
    """

    def __init__(self, db: Session):
        """
        Initialize the module registry.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._loaded_modules: Dict[str, Any] = {}  # Cache for loaded module objects
        self._routers = []  # Registered routers
        self._hooks: Dict[str, List] = {}  # Registered hooks by name
        self._extensions: Dict[str, List] = {}  # Registered extensions by point

    def get_all_modules(self) -> List[Module]:
        """Get all installed modules."""
        return self.db.query(Module).all()

    def get_registered_modules(self) -> List[Module]:
        """Get only registered modules."""
        return self.db.query(Module).filter(Module.registered == True).all()

    def get_module_by_id(self, module_id: int) -> Optional[Module]:
        """Get module by ID."""
        return self.db.query(Module).filter(Module.id == module_id).first()

    def get_module_by_technical_name(self, technical_name: str) -> Optional[Module]:
        """Get module by technical name."""
        return self.db.query(Module).filter(Module.technical_name == technical_name).first()

    def install_module(
        self,
        technical_name: str,
        name: str,
        version: str,
        install_path: str,
        manifest: Dict[str, Any],
        **kwargs
    ) -> Module:
        """
        Install a new module.

        Args:
            technical_name: Unique technical identifier
            name: Human-readable name
            version: Module version
            install_path: Filesystem path to module
            manifest: Full manifest dictionary
            **kwargs: Additional module attributes

        Returns:
            Created Module instance
        """
        # Check if already installed
        existing = self.get_module_by_technical_name(technical_name)
        if existing:
            raise ValueError(f"Module '{technical_name}' is already installed")

        # Create module record
        module = Module(
            technical_name=technical_name,
            name=name,
            version=version,
            install_path=install_path,
            manifest=manifest,
            state='installed',
            enabled=False,
            registered=False,
            **kwargs
        )

        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)

        logger.info(f"Module '{technical_name}' v{version} installed successfully")
        return module

    def enable_module(self, technical_name_or_id) -> Module:
        """
        Platform-level enablement is deprecated. Use tenant modules instead.
        """
        raise ValueError("Platform module enablement is not supported")

    def disable_module(self, technical_name_or_id) -> Module:
        """
        Platform-level disablement is deprecated. Use tenant modules instead.
        """
        raise ValueError("Platform module disablement is not supported")

    def uninstall_module(self, module_id: int) -> None:
        """
        Uninstall a module.

        Args:
            module_id: Module ID to uninstall
        """
        module = self.get_module_by_id(module_id)
        if not module:
            raise ValueError(f"Module with ID {module_id} not found")

        if module.registered:
            raise ValueError(f"Cannot uninstall registered module '{module.technical_name}'. Unregister it first.")

        # TODO: Check if other modules depend on this one
        # TODO: Clean up module data from filesystem
        # TODO: Run module uninstall hooks

        self.db.delete(module)
        self.db.commit()

        # Remove from cache
        self._loaded_modules.pop(module.technical_name, None)

        logger.info(f"Module '{module.technical_name}' uninstalled")

    def register_router(self, module_technical_name: str, router: Any) -> None:
        """
        Register a FastAPI router from a module.

        Args:
            module_technical_name: Module's technical name
            router: FastAPI APIRouter instance
        """
        self._routers.append({
            'module': module_technical_name,
            'router': router
        })
        logger.debug(f"Router registered for module '{module_technical_name}'")

    def get_routers(self) -> List[Any]:
        """Get all registered routers."""
        return [r['router'] for r in self._routers]

    def register_hook(self, module_technical_name: str, hook_name: str, handler: callable, order: int = 0) -> None:
        """
        Register a hook handler.

        Args:
            module_technical_name: Module's technical name
            hook_name: Hook name (e.g., "contratto.before_create")
            handler: Callable hook handler
            order: Execution order (lower runs first)
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        self._hooks[hook_name].append({
            'module': module_technical_name,
            'handler': handler,
            'order': order
        })

        # Sort by order
        self._hooks[hook_name].sort(key=lambda x: x['order'])

        logger.debug(f"Hook '{hook_name}' registered for module '{module_technical_name}'")

    def get_hooks(self, hook_name: str) -> List[callable]:
        """
        Get all handlers for a specific hook.

        Args:
            hook_name: Hook name

        Returns:
            List of hook handlers
        """
        hooks = self._hooks.get(hook_name, [])
        return [h['handler'] for h in hooks]

    def register_extension(self, module_technical_name: str, extension_point: str, config: Dict[str, Any]) -> None:
        """
        Register an extension point.

        Args:
            module_technical_name: Module's technical name
            extension_point: Extension point name (e.g., "immobile.detail.tabs")
            config: Extension configuration (label, component, etc.)
        """
        if extension_point not in self._extensions:
            self._extensions[extension_point] = []

        self._extensions[extension_point].append({
            'module': module_technical_name,
            'config': config
        })

        # Sort by order if specified
        self._extensions[extension_point].sort(key=lambda x: x['config'].get('order', 0))

        logger.debug(f"Extension point '{extension_point}' registered for module '{module_technical_name}'")

    def get_extensions(self, extension_point: str) -> List[Dict[str, Any]]:
        """
        Get all extensions for a specific extension point.

        Args:
            extension_point: Extension point name

        Returns:
            List of extension configurations
        """
        extensions = self._extensions.get(extension_point, [])
        return [e['config'] for e in extensions]

    def has_permission(self, module_technical_name: str, permission: str) -> bool:
        """
        Check if a module has a specific permission.

        Args:
            module_technical_name: Module's technical name
            permission: Permission to check

        Returns:
            True if module has permission, False otherwise
        """
        module = self.get_module_by_technical_name(module_technical_name)
        if not module:
            return False

        # Check if permission is granted
        perm = self.db.query(ModulePermission).filter(
            ModulePermission.module_id == module.id,
            ModulePermission.permission == permission,
            ModulePermission.granted == True
        ).first()

        return perm is not None

    def load_installed_modules(self) -> None:
        """
        Load all registered modules.
        This should be called at application startup.
        """
        registered_modules = self.get_registered_modules()
        logger.info(f"Loading {len(registered_modules)} registered modules...")

        for module in registered_modules:
            try:
                self._load_module(module)
            except Exception as e:
                logger.error(f"Failed to load module '{module.technical_name}': {e}")
                # Mark module as broken
                module.state = 'broken'
                self.db.commit()

        logger.info(f"Module loading complete. {len(self._loaded_modules)} modules loaded.")

    def _load_module(self, module: Module) -> None:
        """
        Load a single module.

        Args:
            module: Module instance to load
        """
        # This is a placeholder - will be implemented with ModuleLoader
        logger.debug(f"Loading module '{module.technical_name}'...")
        self._loaded_modules[module.technical_name] = module
