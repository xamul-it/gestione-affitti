"""
Manifest Parser - Load and validate module manifests.

Manifests are Python dictionaries in __manifest__.py files that describe
module metadata, dependencies, permissions, and entry points.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ManifestValidationError(Exception):
    """Raised when a manifest fails validation."""
    pass


# Required fields in manifest
REQUIRED_FIELDS = [
    'name',
    'technical_name',
    'version',
]

# Optional fields with defaults
DEFAULT_VALUES = {
    'author': 'Unknown',
    'category': 'Other',
    'icon': None,
    'license': 'LGPL-3',
    'price': 0.0,
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': [],
    'optional_depends': [],
    'permissions': [],
    'models': [],
    'routers': [],
    'routes': [],
    'extensions': {},
    'data': [],
}


def parse_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Parse a module manifest file.

    The manifest is a Python dictionary literal in __manifest__.py.
    We use eval() with restricted globals for safety.

    Args:
        manifest_path: Path to __manifest__.py file

    Returns:
        Parsed manifest dictionary

    Raises:
        FileNotFoundError: If manifest file doesn't exist
        SyntaxError: If manifest file has syntax errors
        ManifestValidationError: If manifest content is invalid
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    try:
        # Read manifest file
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Execute manifest file to extract 'manifest' variable
        # Using exec() to support full Python files with docstrings and assignments
        namespace = {}
        exec(content, {"__builtins__": {}}, namespace)

        # Extract the 'manifest' variable
        if 'manifest' not in namespace:
            raise ManifestValidationError("Manifest file must define a 'manifest' variable")

        manifest = namespace['manifest']

        if not isinstance(manifest, dict):
            raise ManifestValidationError("Manifest must be a dictionary")

        # Apply default values
        for key, default_value in DEFAULT_VALUES.items():
            if key not in manifest:
                manifest[key] = default_value

        logger.debug(f"Manifest parsed successfully: {manifest.get('name')}")
        return manifest

    except SyntaxError as e:
        logger.error(f"Syntax error in manifest '{manifest_path}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error parsing manifest '{manifest_path}': {e}")
        raise ManifestValidationError(f"Invalid manifest: {e}")


def validate_manifest(manifest: Dict[str, Any]) -> None:
    """
    Validate a parsed manifest.

    Checks:
    - Required fields present
    - Field types correct
    - Version format valid
    - Dependencies format valid

    Args:
        manifest: Parsed manifest dictionary

    Raises:
        ManifestValidationError: If validation fails
    """
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in manifest:
            raise ManifestValidationError(f"Required field '{field}' missing from manifest")

        if not manifest[field]:
            raise ManifestValidationError(f"Required field '{field}' cannot be empty")

    # Validate technical_name format (slug)
    technical_name = manifest['technical_name']
    if not technical_name.replace('_', '').replace('-', '').isalnum():
        raise ManifestValidationError(
            f"Invalid technical_name '{technical_name}'. Must be alphanumeric with underscores/hyphens only"
        )

    # Validate version format (basic check)
    version = manifest['version']
    if not any(c.isdigit() for c in version):
        raise ManifestValidationError(f"Invalid version format: '{version}'")

    # Validate depends is a list
    if not isinstance(manifest.get('depends', []), list):
        raise ManifestValidationError("'depends' must be a list")

    # Validate optional_depends is a list
    if not isinstance(manifest.get('optional_depends', []), list):
        raise ManifestValidationError("'optional_depends' must be a list")

    # Validate permissions is a list
    if not isinstance(manifest.get('permissions', []), list):
        raise ManifestValidationError("'permissions' must be a list")

    # Validate routers is a list
    if not isinstance(manifest.get('routers', []), list):
        raise ManifestValidationError("'routers' must be a list")

    # Validate extensions is a dict
    if not isinstance(manifest.get('extensions', {}), dict):
        raise ManifestValidationError("'extensions' must be a dictionary")

    # Validate boolean fields
    for bool_field in ['installable', 'auto_install', 'application']:
        if not isinstance(manifest.get(bool_field, False), bool):
            raise ManifestValidationError(f"'{bool_field}' must be a boolean")

    # Validate price is numeric
    if not isinstance(manifest.get('price', 0), (int, float)):
        raise ManifestValidationError("'price' must be a number")

    logger.debug(f"Manifest validation passed for '{manifest['name']}'")


def get_manifest_summary(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a summary of key manifest information.

    Args:
        manifest: Parsed manifest dictionary

    Returns:
        Dictionary with summary info
    """
    return {
        'name': manifest.get('name'),
        'technical_name': manifest.get('technical_name'),
        'version': manifest.get('version'),
        'author': manifest.get('author'),
        'category': manifest.get('category'),
        'license': manifest.get('license'),
        'price': manifest.get('price', 0),
        'summary': manifest.get('summary', ''),
        'depends': manifest.get('depends', []),
        'permissions': manifest.get('permissions', []),
    }


def check_version_compatibility(manifest: Dict[str, Any], core_version: str) -> bool:
    """
    Check if module is compatible with current core version.

    Args:
        manifest: Parsed manifest dictionary
        core_version: Current core version string

    Returns:
        True if compatible, False otherwise
    """
    min_version = manifest.get('core_version_min')
    max_version = manifest.get('core_version_max')

    if not min_version and not max_version:
        # No version constraints
        return True

    # Simple version comparison (could use packaging.version for more robust comparison)
    try:
        core_parts = [int(x) for x in core_version.split('.')]

        if min_version:
            min_parts = [int(x) for x in min_version.split('.')]
            if core_parts < min_parts:
                return False

        if max_version:
            max_parts = [int(x) for x in max_version.split('.')]
            if core_parts >= max_parts:
                return False

        return True

    except (ValueError, AttributeError):
        logger.warning(f"Could not parse version strings for compatibility check")
        return True  # Assume compatible if can't parse


def extract_dependencies(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract and parse dependency list from manifest.

    Args:
        manifest: Parsed manifest dictionary

    Returns:
        List of dependency dicts with 'name' and 'version_constraint'
    """
    dependencies = []

    for dep in manifest.get('depends', []):
        if isinstance(dep, str):
            # Parse format: "module_name" or "module_name:>=1.0.0"
            if ':' in dep:
                name, constraint = dep.split(':', 1)
            else:
                name = dep
                constraint = None

            dependencies.append({
                'depends_on': name,
                'version_constraint': constraint,
                'optional': False
            })

    for dep in manifest.get('optional_depends', []):
        if isinstance(dep, str):
            if ':' in dep:
                name, constraint = dep.split(':', 1)
            else:
                name = dep
                constraint = None

            dependencies.append({
                'depends_on': name,
                'version_constraint': constraint,
                'optional': True
            })

    return dependencies
