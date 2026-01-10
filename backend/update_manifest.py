"""
Quick script to update module manifests in database.
Run this after making changes to __manifest__.py files.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.module_system import ModuleRegistry
from app.core.module_system.manifest import parse_manifest

def update_module_manifest(technical_name: str):
    """Update a module's manifest in the database from its __manifest__.py file."""
    db = SessionLocal()
    try:
        registry = ModuleRegistry(db)

        # Get module record
        module = registry.get_module_by_technical_name(technical_name)
        if not module:
            print(f"❌ Module '{technical_name}' not found in database")
            return False

        # Load manifest from file
        manifest_path = Path(module.install_path) / '__manifest__.py'
        if not manifest_path.exists():
            print(f"❌ Manifest file not found: {manifest_path}")
            return False

        manifest = parse_manifest(manifest_path)

        # Update database
        module.manifest = manifest
        module.name = manifest.get('name', module.name)
        module.version = manifest.get('version', module.version)
        module.summary = manifest.get('summary')
        module.description = manifest.get('description')
        module.icon = manifest.get('icon')

        db.commit()
        print(f"✅ Updated manifest for '{technical_name}'")
        print(f"   - Name: {module.name}")
        print(f"   - Version: {module.version}")
        print(f"   - Frontend routes: {len(manifest.get('frontend_routes', []))}")
        print(f"   - Menu items: {len(manifest.get('menu_items', []))}")
        return True

    except Exception as e:
        print(f"❌ Error updating manifest: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def update_all_manifests():
    db = SessionLocal()
    try:
        registry = ModuleRegistry(db)
        modules = registry.get_all_modules()
        return [module.technical_name for module in modules]
    finally:
        db.close()

if __name__ == '__main__':
    print("Updating module manifests...")
    print()

    targets = sys.argv[1:] or update_all_manifests()
    if not targets:
        print("No modules found to update.")
        sys.exit(0)

    for technical_name in targets:
        update_module_manifest(technical_name)
        print()

    print("Done!")
