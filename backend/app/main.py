import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from sqlalchemy import MetaData

# Import module system models to ensure tables are created
from app.core.module_system.models import (
    Module,
    ModuleDependency,
    ModulePermission,
    ModuleHook,
    ModuleExtension,
    ModuleEndpoint,
)

# Import auth models to ensure tables are created
from app.core.auth.models import User, Role, Permission, user_roles, role_permissions

# Add modules directory to Python path BEFORE importing from modules
import sys, os
modules_dir = os.path.join(os.path.dirname(__file__), "../modules")
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# Import platform models
from app.core.models.import_configuration import ImportConfiguration
from app.core.models.table_configuration import TableConfiguration
from app.core.models import RuoloDisponibile, SoggettoRuolo
from app.core.models.tenant import Tenant, UserTenant, TenantModule

# Import platform models
from app.core.platform.models import (
    MenuItem, Widget, UserDashboard,
    Scadenza, ScadenzaDestinatario, ScadenzaLog,
    DocumentJob, JobStatus
)

# Import module system
from app.core.module_system import ModuleRegistry, ModuleLoader

# Import platform-level routes (ONLY platform routes, NO business module routes)
from app.core.routes.import_export import router as import_export_router
from app.core.routes.table_configurations import router as table_config_router
from app.core.routes.unified_search import router as unified_search_router
from app.core.routes.admin_comuni import router as admin_comuni_router
from app.core.routes.admin_core import router as admin_core_router
from app.core.routes.scadenze import router as scadenze_router
from app.core.routes.document_parsing import router as document_parsing_router

# Import auth routes
from app.core.auth.routes import router as auth_router
from app.core.auth.routes_roles import router as roles_router
from app.core.auth.routes_roles_debug import router as roles_debug_router
from app.core.routes.document_parsing_debug import router as document_parsing_debug_router
from app.core.routes.parsing_services import router as parsing_services_router
from app.core.routes.ruoli_disponibili import router as ruoli_disponibili_router

# Import tenant routes
from app.core.routes.tenants import router as tenants_router

# Import platform routes
from app.core.platform.routes import menu as platform_menu_router
from app.core.platform.routes import dashboard as platform_dashboard_router
from affitti_lungo.routes.modules_api import router as modules_api_router

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)

def create_core_tables():
    """
    Create only core tables (prefix core_) in public schema.
    Avoids creating module tables outside tenant install.
    """
    core_metadata = MetaData()
    for table in Base.metadata.tables.values():
        if table.name.startswith("core_"):
            table.to_metadata(core_metadata)
    core_metadata.create_all(bind=engine)


# Crea le tabelle core nel database (evita tabelle moduli in public)
create_core_tables()

# IMPORTANT: Import modules in dependency order AFTER core tables are created
# to avoid creating tenant tables in public schema via create_all.
import anagrafica_italiana.models
import immobili.models
import affitti_lungo.models
import esempio_componenti.models

# Initialize module system and seed data
logger.info("Initializing module system...")
db = SessionLocal()
module_loader = None
module_registry = None

try:
    # Seed domain data in PUBLIC schema (managed by platform admin)
    from app.core.seeds import seed_all_domain_data
    from app.core.auth.init_data import init_auth_data

    logger.info("Seeding domain data in PUBLIC schema...")
    try:
        seed_results = seed_all_domain_data(db)
        total_seeded = sum(seed_results.values())
        if total_seeded > 0:
            logger.info(f"Seeded {total_seeded} domain data records in public schema")
    except Exception as e:
        logger.error(f"Error seeding domain data: {e}")

    # Initialize auth system (roles, permissions, first admin)
    logger.info("Initializing authentication system...")
    try:
        init_auth_data(db)
        logger.info("Authentication system initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing auth system: {e}")

    # Seed platform-level permissions (multi-tenant)
    logger.info("Seeding platform permissions...")
    try:
        from app.core.auth.seed_platform_permissions import seed_all_platform_permissions
        seed_all_platform_permissions(db)
        logger.info("Platform permissions seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding platform permissions: {e}")

    # Initialize module system
    module_registry = ModuleRegistry(db)
    module_dir = Path(__file__).parent.parent / settings.MODULE_DIR
    module_loader = ModuleLoader(str(module_dir), module_registry)

    # Discover and install new modules
    logger.info(f"Scanning for modules in: {module_dir}")
    installed = module_loader.install_discovered_modules()
    if installed:
        logger.info(f"Installed {len(installed)} new modules: {', '.join(installed)}")

    tenant_registered = module_loader.ensure_tenant_only_registered()
    if tenant_registered:
        logger.info("Registered %s tenant-only modules", tenant_registered)

    # Reload registered modules
    module_loader.reload_registered_modules()

    # Register module roles (dynamic role system)
    logger.info("Registering module roles...")
    try:
        from affitti_lungo.roles import register_roles as register_affitti_roles
        result = register_affitti_roles(db)
        logger.info(
            f"Affitti Lungo roles: {result['created']} created, "
            f"{result['skipped']} skipped, {len(result['errors'])} errors"
        )
    except Exception as e:
        logger.error(f"Error registering affitti_lungo roles: {e}")

except Exception as e:
    logger.error(f"Failed to initialize module system: {e}")
    module_registry = None
    module_loader = None
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(modules_api_router, prefix=settings.API_V1_STR)
# Set app instance in module loader (needed for register_module calls)
logger.info(f"Setting app in module_loader: loader={module_loader}, registry={module_registry}")
if module_loader:
    module_loader.app = app
    logger.info("App instance set in module_loader")

# Reload registered modules again to call register_module(app) for route registration
if module_loader and module_registry:
    logger.info("Reloading registered modules with app instance for route registration...")
    module_loader.reload_registered_modules()
else:
    logger.warning(f"Skipping module reload: loader={module_loader}, registry={module_registry}")

# Initialize unified search registry with all module entities
logger.info("Initializing unified search registry...")
try:
    from app.core.platform_services.search_registry_init import init_search_registry
    init_search_registry()
    logger.info("Unified search registry initialized successfully")
except Exception as e:
    logger.error(f"Error initializing search registry: {e}")

# Configurazione CORS con supporto dinamico per rete locale
from starlette.middleware.cors import CORSMiddleware as StarletteMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
import re

class DynamicCORSMiddleware(StarletteMiddleware):
    """
    CORS Middleware che accetta dinamicamente origini dalla rete locale.

    In aggiunta alle origini configurate, accetta automaticamente:
    - localhost su porte 3000 e 5173
    - IP della rete locale 192.168.x.x su porte 3000 e 5173
    """

    def __init__(self, app: ASGIApp, **options):
        # Pattern per IP rete locale con porte comuni dev
        self.local_network_pattern = re.compile(
            r'^https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}):(3000|5173)$'
        )
        super().__init__(app, **options)

    def is_allowed_origin(self, origin: str) -> bool:
        # Prima controlla le origini configurate
        if origin in self.allow_origins:
            return True

        # Poi controlla se matcha il pattern rete locale
        if self.local_network_pattern.match(origin):
            logger.info(f"✅ CORS: Allowing local network origin: {origin}")
            return True

        return False

app.add_middleware(
    DynamicCORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenant context
# Extracts tenant_schema from JWT and sets it in thread-local storage
# SQLAlchemy event listener in database.py applies search_path automatically
from app.core.middleware.tenant_middleware import TenantMiddleware
app.add_middleware(TenantMiddleware)


# Startup event: registra menu e widget del modulo Affitti
@app.on_event("startup")
async def register_module_resources():
    """Registra menu items e widget dei moduli al startup"""
    if os.getenv("REGISTER_MENUS_ON_STARTUP", "").lower() not in {"1", "true", "yes"}:
        logger.info("Skipping menu/widget registration at startup (REGISTER_MENUS_ON_STARTUP not enabled)")
        return

    import httpx

    async with httpx.AsyncClient() as client:
        # Registra menu items della PIATTAFORMA
        try:
            PLATFORM_MENU = [
                {
                    "id": "platform.admin",
                    "label": "Amministrazione",
                    "path": "#",
                    "icon": "settings",
                    "order_index": 100,
                    "required_permission": "platform.admin"
                },
                {
                    "id": "platform.admin.modules",
                    "label": "Gestione Moduli",
                    "path": "/admin/modules",
                    "icon": "package",
                    "parent_id": "platform.admin",
                    "order_index": 1,
                    "required_permission": "platform.admin"
                },
                {
                    "id": "platform.admin.users",
                    "label": "Utenti e Permessi",
                    "path": "/admin/users",
                    "icon": "users",
                    "parent_id": "platform.admin",
                    "order_index": 2,
                    "required_permission": "platform.admin"
                },
                {
                    "id": "platform.admin.roles_debug",
                    "label": "Debug Ruoli",
                    "path": "/admin/roles-debug",
                    "icon": "shield-check",
                    "parent_id": "platform.admin",
                    "order_index": 3,
                    "required_permission": "platform.admin"
                },
                {
                    "id": "platform.admin.parsing_services",
                    "label": "Servizi Parsing",
                    "path": "/admin/parsing-services",
                    "icon": "settings",
                    "parent_id": "platform.admin",
                    "order_index": 4,
                    "required_permission": "platform.admin"
                },
                {
                    "id": "platform.admin.data",
                    "label": "Amministrazione Dati",
                    "path": "/admin/data",
                    "icon": "list",
                    "parent_id": "platform.admin",
                    "order_index": 5,
                    "required_permission": "platform.admin"
                },
                {
                    "id": "platform.admin.database",
                    "label": "Gestione Database",
                    "path": "/admin/database",
                    "icon": "database",
                    "parent_id": "platform.admin",
                    "order_index": 6,
                    "required_permission": "platform.admin"
                }
                # Scadenze removed - it's a CORE SERVICE (badge in TopBar), not a menu page
            ]

            logger.info("Registering platform menu items...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/menu/register",
                json={
                    "module_id": "platform",
                    "items": PLATFORM_MENU
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['items_registered']} platform menu items")
            else:
                logger.error(f"❌ Failed to register platform menu items: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️  Could not register platform menu items: {e}")

        # Registra modulo ANAGRAFICA_ITALIANA
        try:
            from anagrafica_italiana import MENU_ITEMS as ANAGRAFICA_MENU, WIDGETS as ANAGRAFICA_WIDGETS

            logger.info("Registering menu items for anagrafica_italiana module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/menu/register",
                json={
                    "module_id": "anagrafica_italiana",
                    "items": ANAGRAFICA_MENU
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['items_registered']} menu items for anagrafica_italiana")
            else:
                logger.error(f"❌ Failed to register menu items: HTTP {response.status_code}")

            # Registra widget anagrafica
            logger.info("Registering widgets for anagrafica_italiana module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/dashboard/register-widgets",
                json={
                    "module_id": "anagrafica_italiana",
                    "widgets": ANAGRAFICA_WIDGETS
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['widgets_registered']} widgets for anagrafica_italiana")
            else:
                logger.error(f"❌ Failed to register widgets: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️  Could not register anagrafica_italiana resources: {e}")

        # Registra modulo IMMOBILI
        try:
            from immobili import MENU_ITEMS as IMMOBILI_MENU, WIDGETS as IMMOBILI_WIDGETS

            logger.info("Registering menu items for immobili module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/menu/register",
                json={
                    "module_id": "immobili",
                    "items": IMMOBILI_MENU
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['items_registered']} menu items for immobili")
            else:
                logger.error(f"❌ Failed to register menu items: HTTP {response.status_code}")

            # Registra widget immobili
            logger.info("Registering widgets for immobili module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/dashboard/register-widgets",
                json={
                    "module_id": "immobili",
                    "widgets": IMMOBILI_WIDGETS
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['widgets_registered']} widgets for immobili")
            else:
                logger.error(f"❌ Failed to register widgets: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️  Could not register immobili menu items: {e}")

        # Registra modulo AFFITTI_LUNGO
        try:
            from affitti_lungo import MENU_ITEMS as AFFITTI_MENU, WIDGETS as AFFITTI_WIDGETS

            logger.info("Registering menu items for affitti_lungo module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/menu/register",
                json={
                    "module_id": "affitti_lungo",
                    "items": AFFITTI_MENU
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['items_registered']} menu items for affitti_lungo")
            else:
                logger.error(f"❌ Failed to register menu items: HTTP {response.status_code}")

            # Registra widget affitti
            logger.info("Registering widgets for affitti_lungo module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/dashboard/register-widgets",
                json={
                    "module_id": "affitti_lungo",
                    "widgets": AFFITTI_WIDGETS
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['widgets_registered']} widgets for affitti_lungo")
            else:
                logger.error(f"❌ Failed to register widgets: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️  Could not register affitti_lungo resources: {e}")

        # Registra modulo AFFITTI_BREVI
        try:
            from affitti_brevi import MENU_ITEMS as AFFITTI_BREVI_MENU, WIDGETS as AFFITTI_BREVI_WIDGETS

            logger.info("Registering menu items for affitti_brevi module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/menu/register",
                json={
                    "module_id": "affitti_brevi",
                    "items": AFFITTI_BREVI_MENU
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['items_registered']} menu items for affitti_brevi")
            else:
                logger.error(f"❌ Failed to register menu items: HTTP {response.status_code}")

            # Registra widget affitti_brevi
            logger.info("Registering widgets for affitti_brevi module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/dashboard/register-widgets",
                json={
                    "module_id": "affitti_brevi",
                    "widgets": AFFITTI_BREVI_WIDGETS
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['widgets_registered']} widgets for affitti_brevi")
            else:
                logger.error(f"❌ Failed to register widgets: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️  Could not register affitti_brevi resources: {e}")

        # Registra modulo ESEMPIO_COMPONENTI
        try:
            from esempio_componenti import MENU_ITEMS as ESEMPIO_MENU, WIDGETS as ESEMPIO_WIDGETS

            logger.info("Registering menu items for esempio_componenti module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/menu/register",
                json={
                    "module_id": "esempio_componenti",
                    "items": ESEMPIO_MENU
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['items_registered']} menu items for esempio_componenti")
            else:
                logger.error(f"❌ Failed to register menu items: HTTP {response.status_code}")

            # Registra widget esempio_componenti
            logger.info("Registering widgets for esempio_componenti module...")
            response = await client.post(
                f"http://localhost:8000{settings.API_V1_STR}/platform/dashboard/register-widgets",
                json={
                    "module_id": "esempio_componenti",
                    "widgets": ESEMPIO_WIDGETS
                },
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Registered {result['widgets_registered']} widgets for esempio_componenti")
            else:
                logger.error(f"❌ Failed to register widgets: HTTP {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️  Could not register esempio_componenti resources: {e}")


@app.get("/")
def root():
    return {
        "message": "Benvenuto nell'API Gestione Affitti",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Registrazione auth routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(roles_router, prefix=settings.API_V1_STR)
app.include_router(roles_debug_router, prefix=settings.API_V1_STR)
app.include_router(document_parsing_debug_router, prefix=settings.API_V1_STR)
app.include_router(parsing_services_router, prefix=settings.API_V1_STR)
app.include_router(ruoli_disponibili_router, prefix=settings.API_V1_STR)

# Registrazione tenant routers (multi-tenant system)
app.include_router(tenants_router, prefix=settings.API_V1_STR)

# Registrazione platform routers
app.include_router(platform_menu_router.router, prefix=settings.API_V1_STR)
app.include_router(platform_dashboard_router.router, prefix=settings.API_V1_STR)

# Platform-level routers (admin, import/export, scadenze, tables, search)
app.include_router(import_export_router, prefix=settings.API_V1_STR, tags=["Platform"])
app.include_router(table_config_router, prefix=settings.API_V1_STR, tags=["Platform"])
app.include_router(unified_search_router, prefix=settings.API_V1_STR, tags=["Search"])
app.include_router(admin_comuni_router, prefix=settings.API_V1_STR, tags=["Admin"])
app.include_router(admin_core_router, prefix=settings.API_V1_STR, tags=["Admin"])
app.include_router(scadenze_router, prefix=settings.API_V1_STR)
app.include_router(document_parsing_router, prefix=settings.API_V1_STR)

# ====================================================================
# AUTO-DISCOVERY: Register all module routers dynamically
# ====================================================================
logger.info("🔍 Auto-discovering module routers...")
module_names = ["anagrafica_italiana", "immobili", "affitti_lungo", "affitti_brevi", "esempio_componenti"]
total_routers_registered = 0
modules_dir = Path(__file__).parent.parent / settings.MODULE_DIR
if str(modules_dir) not in sys.path:
    sys.path.insert(0, str(modules_dir))

for module_name in module_names:
    try:
        # Dynamically import the module
        module = __import__(module_name)

        # Check if module has ROUTERS attribute
        if hasattr(module, 'get_routers'):
            routers = module.get_routers()
            logger.info(f"📦 Module '{module_name}': Found {len(routers)} routers (lazy)")
        elif hasattr(module, 'ROUTERS'):
            routers = module.ROUTERS
            logger.info(f"📦 Module '{module_name}': Found {len(routers)} routers")
        else:
            routers = []
            logger.warning(f"⚠️  Module '{module_name}' has no routers")

        # Register each router
        for router in routers:
            app.include_router(router, prefix=settings.API_V1_STR)
            router_name = getattr(router, 'prefix', 'unknown')
            logger.info(f"  ✅ Registered: {router_name}")
            total_routers_registered += 1
    except ImportError as e:
        logger.error(f"❌ Failed to import module '{module_name}': {e}")
    except Exception as e:
        logger.error(f"❌ Error registering routers from '{module_name}': {e}")

logger.info(f"✨ Auto-discovery complete: {total_routers_registered} routers registered from {len(module_names)} modules")

# Registrazione routers dinamici dal ModuleRegistry (legacy system - può essere rimosso in futuro)
if module_registry:
    logger.info("Checking ModuleRegistry for additional routers...")
    module_routers = module_registry.get_routers()
    if module_routers:
        for router in module_routers:
            app.include_router(router, prefix=settings.API_V1_STR)
            logger.info(f"Registered module router from registry: {router.prefix}")
        logger.info(f"Total registry routers: {len(module_routers)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
