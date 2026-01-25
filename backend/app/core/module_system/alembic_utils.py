"""
Utilities for running module-scoped Alembic migrations.
"""
from pathlib import Path
import tempfile


def build_module_alembic_config(backend_dir: Path, migrations_dir: Path) -> Path:
    """
    Create a temporary Alembic config that scopes version_locations to a module.

    Returns the path to the temporary config file.
    """
    alembic_ini = backend_dir / "alembic.ini"
    lines = alembic_ini.read_text(encoding="utf-8").splitlines()
    output = []
    in_alembic = False
    version_set = False
    insert_after_header = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            if in_alembic and not version_set:
                output.append(f"version_locations = {migrations_dir}")
                version_set = True
            in_alembic = stripped.lower() == "[alembic]"
            insert_after_header = in_alembic
            output.append(line)
            continue

        if in_alembic and stripped.startswith("version_locations"):
            output.append(f"version_locations = {migrations_dir}")
            version_set = True
            continue

        if insert_after_header:
            output.append(f"version_locations = {migrations_dir}")
            version_set = True
            insert_after_header = False

        output.append(line)

    if in_alembic and not version_set:
        output.append(f"version_locations = {migrations_dir}")
        version_set = True

    content = "\n".join(output).rstrip() + "\n"

    temp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini")
    temp.write(content)
    temp.flush()
    temp.close()
    return Path(temp.name)
