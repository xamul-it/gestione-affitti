"""
Module System - Core infrastructure for plugin architecture.

This package provides the foundation for a modular, extensible system
where third-party and custom modules can be installed, configured, and managed.
"""
from .models import (
    Module,
    ModuleDependency,
    ModulePermission,
    ModuleHook,
    ModuleExtension,
    ModuleEndpoint,
)
from .registry import ModuleRegistry
from .loader import ModuleLoader
from .manifest import (
    parse_manifest,
    validate_manifest,
    ManifestValidationError,
    check_version_compatibility,
    extract_dependencies,
    get_manifest_summary,
)

__all__ = [
    # Models
    "Module",
    "ModuleDependency",
    "ModulePermission",
    "ModuleHook",
    "ModuleExtension",
    "ModuleEndpoint",
    # Registry
    "ModuleRegistry",
    # Loader
    "ModuleLoader",
    # Manifest
    "parse_manifest",
    "validate_manifest",
    "ManifestValidationError",
    "check_version_compatibility",
    "extract_dependencies",
    "get_manifest_summary",
]
