"""
Dependency Resolver - Resolves module dependencies and load order.

Handles:
- Topological sorting for correct load order
- Version constraint checking
- Circular dependency detection
- Missing dependency detection
"""
import logging
from typing import List, Dict, Set, Tuple, Optional
from packaging import version
import re

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when dependency resolution fails."""
    pass


class CircularDependencyError(DependencyError):
    """Raised when circular dependencies are detected."""
    pass


class MissingDependencyError(DependencyError):
    """Raised when required dependency is not found."""
    pass


class VersionConstraintError(DependencyError):
    """Raised when version constraints cannot be satisfied."""
    pass


class DependencyResolver:
    """
    Resolves module dependencies and determines load order.

    Usage:
        resolver = DependencyResolver()

        # Add modules
        resolver.add_module('core', '1.0.0', [])
        resolver.add_module('plugin_a', '1.0.0', ['core:>=1.0.0'])
        resolver.add_module('plugin_b', '1.0.0', ['core:>=1.0.0', 'plugin_a:^1.0.0'])

        # Resolve
        load_order = resolver.resolve()
        # Returns: ['core', 'plugin_a', 'plugin_b']
    """

    def __init__(self):
        """Initialize dependency resolver."""
        self.modules: Dict[str, Dict] = {}
        self.dependencies: Dict[str, List[Tuple[str, str]]] = {}

    def add_module(
        self,
        technical_name: str,
        module_version: str,
        depends: List[str],
        optional_depends: Optional[List[str]] = None
    ) -> None:
        """
        Add a module to the dependency graph.

        Args:
            technical_name: Module technical name
            module_version: Module version
            depends: List of required dependencies in format 'module:constraint'
            optional_depends: List of optional dependencies
        """
        self.modules[technical_name] = {
            'version': module_version,
            'depends': depends or [],
            'optional_depends': optional_depends or []
        }

        # Parse dependencies
        self.dependencies[technical_name] = []

        for dep in (depends or []):
            dep_name, constraint = self._parse_dependency(dep)
            self.dependencies[technical_name].append((dep_name, constraint))

    def _parse_dependency(self, dep_string: str) -> Tuple[str, str]:
        """
        Parse dependency string.

        Formats supported:
        - 'module_name' (no version constraint)
        - 'module_name:>=1.0.0'
        - 'module_name:^1.0.0' (semver caret)
        - 'module_name:~1.0.0' (semver tilde)
        - 'module_name:1.0.0' (exact version)

        Args:
            dep_string: Dependency string

        Returns:
            Tuple of (module_name, version_constraint)
        """
        if ':' in dep_string:
            name, constraint = dep_string.split(':', 1)
            return name.strip(), constraint.strip()
        else:
            return dep_string.strip(), '*'

    def check_version_constraint(
        self,
        module_version: str,
        constraint: str
    ) -> bool:
        """
        Check if module version satisfies constraint.

        Args:
            module_version: Actual module version
            constraint: Version constraint

        Returns:
            True if constraint is satisfied
        """
        if constraint == '*' or not constraint:
            return True

        try:
            ver = version.parse(module_version)

            # Handle semver caret (^1.2.3 means >=1.2.3 <2.0.0)
            if constraint.startswith('^'):
                base_version = constraint[1:]
                base = version.parse(base_version)
                major_limit = version.parse(f"{base.major + 1}.0.0")
                return ver >= base and ver < major_limit

            # Handle semver tilde (~1.2.3 means >=1.2.3 <1.3.0)
            elif constraint.startswith('~'):
                base_version = constraint[1:]
                base = version.parse(base_version)
                minor_limit = version.parse(f"{base.major}.{base.minor + 1}.0")
                return ver >= base and ver < minor_limit

            # Handle comparison operators
            elif constraint.startswith('>='):
                return ver >= version.parse(constraint[2:])
            elif constraint.startswith('<='):
                return ver <= version.parse(constraint[2:])
            elif constraint.startswith('>'):
                return ver > version.parse(constraint[1:])
            elif constraint.startswith('<'):
                return ver < version.parse(constraint[1:])
            elif constraint.startswith('==') or constraint.startswith('='):
                constraint_ver = constraint.lstrip('=')
                return ver == version.parse(constraint_ver)
            elif constraint.startswith('!='):
                return ver != version.parse(constraint[2:])

            # Exact match
            else:
                return ver == version.parse(constraint)

        except Exception as e:
            logger.warning(f"Failed to parse version constraint '{constraint}': {e}")
            return False

    def validate_dependencies(self) -> List[str]:
        """
        Validate all dependencies exist and versions match.

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []

        for module_name, deps in self.dependencies.items():
            for dep_name, constraint in deps:
                # Check if dependency exists
                if dep_name not in self.modules:
                    errors.append(
                        f"Module '{module_name}' requires '{dep_name}' which is not installed"
                    )
                    continue

                # Check version constraint
                dep_version = self.modules[dep_name]['version']
                if not self.check_version_constraint(dep_version, constraint):
                    errors.append(
                        f"Module '{module_name}' requires '{dep_name}:{constraint}' "
                        f"but version {dep_version} is installed"
                    )

        return errors

    def detect_circular_dependencies(self) -> Optional[List[str]]:
        """
        Detect circular dependencies using DFS.

        Returns:
            List forming circular dependency path, or None if no cycles
        """
        visited = set()
        rec_stack = set()
        path = []

        def visit(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Visit all dependencies
            if node in self.dependencies:
                for dep_name, _ in self.dependencies[node]:
                    if dep_name not in self.modules:
                        continue

                    if dep_name not in visited:
                        cycle = visit(dep_name)
                        if cycle:
                            return cycle
                    elif dep_name in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dep_name)
                        return path[cycle_start:] + [dep_name]

            path.pop()
            rec_stack.remove(node)
            return None

        # Check each module
        for module_name in self.modules:
            if module_name not in visited:
                cycle = visit(module_name)
                if cycle:
                    return cycle

        return None

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort to determine load order.

        Uses Kahn's algorithm for stable sorting.

        Returns:
            List of module names in load order

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        # Build in-degree map
        in_degree = {name: 0 for name in self.modules}

        # Count incoming edges
        for module_name, deps in self.dependencies.items():
            for dep_name, _ in deps:
                if dep_name in self.modules:
                    in_degree[module_name] += 1

        # Queue of modules with no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort queue for stable ordering
            queue.sort()

            # Take module with no remaining dependencies
            current = queue.pop(0)
            result.append(current)

            # Remove edges from current
            for module_name, deps in self.dependencies.items():
                for dep_name, _ in deps:
                    if dep_name == current:
                        in_degree[module_name] -= 1
                        if in_degree[module_name] == 0:
                            queue.append(module_name)

        # Check if all modules were processed
        if len(result) != len(self.modules):
            # Circular dependency exists
            cycle = self.detect_circular_dependencies()
            if cycle:
                cycle_str = ' -> '.join(cycle)
                raise CircularDependencyError(
                    f"Circular dependency detected: {cycle_str}"
                )
            else:
                # Some other issue
                missing = set(self.modules.keys()) - set(result)
                raise DependencyError(
                    f"Could not resolve dependencies for modules: {missing}"
                )

        return result

    def resolve(self, skip_validation: bool = False) -> List[str]:
        """
        Resolve dependencies and return load order.

        Args:
            skip_validation: Skip dependency validation (for testing)

        Returns:
            List of module names in correct load order

        Raises:
            DependencyError: If dependencies cannot be resolved
        """
        logger.info(f"Resolving dependencies for {len(self.modules)} modules...")

        # 1. Validate dependencies
        if not skip_validation:
            errors = self.validate_dependencies()
            if errors:
                error_msg = "\n".join(errors)
                raise MissingDependencyError(
                    f"Dependency validation failed:\n{error_msg}"
                )

        # 2. Check for circular dependencies and sort
        try:
            load_order = self.topological_sort()
            logger.info(f"Load order resolved: {' -> '.join(load_order)}")
            return load_order

        except CircularDependencyError as e:
            logger.error(str(e))
            raise

        except Exception as e:
            logger.error(f"Failed to resolve dependencies: {e}")
            raise DependencyError(f"Dependency resolution failed: {e}")

    def get_dependency_tree(self, module_name: str, depth: int = 0) -> str:
        """
        Get a formatted dependency tree for a module.

        Args:
            module_name: Module to show tree for
            depth: Current depth (for recursion)

        Returns:
            Formatted tree string
        """
        indent = "  " * depth
        result = f"{indent}{module_name} ({self.modules[module_name]['version']})\n"

        if module_name in self.dependencies:
            for dep_name, constraint in self.dependencies[module_name]:
                if dep_name in self.modules:
                    result += self.get_dependency_tree(dep_name, depth + 1)
                else:
                    result += f"{indent}  {dep_name}:{constraint} [MISSING]\n"

        return result
