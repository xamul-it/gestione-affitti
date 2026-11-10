"""
Per-tenant module gate: a business module's API answers only for tenants
where the module is enabled (core_tenant_modules).

Routes are mounted once for every tenant, in several ways (register_module,
get_routers/ROUTERS auto-discovery, the module registry) and some modules
have no URL prefix of their own (affitti_lungo, gestione_pec mount on
/api/v1). So a route belongs to the module of its endpoint's Python package
(immobili.routes.condomini -> immobili), not to a URL prefix.

Each module route's ASGI app is wrapped by a check that runs after routing
and after TenantMiddleware has put tenant_schema in the request state:
- no tenant in the request (login, public links): no check, the route's own
  authentication decides;
- unknown tenant, or module not enabled for it: 403.
Platform routes (app.*) are never gated.

ModuleGateMiddleware wraps routes added after startup (module reloads) too.
No cache: the enabled modules are read per request (one indexed query), so
disabling a module takes effect immediately.
"""
from functools import lru_cache
from typing import Optional, Set

from fastapi.routing import APIRoute
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine


@lru_cache(maxsize=1)
def _moduli_noti() -> frozenset:
    root = settings.resolved_module_dir
    if not root.exists():
        return frozenset()
    return frozenset(d.name for d in root.iterdir()
                     if d.is_dir() and not d.name.startswith("_") and (d / "__manifest__.py").exists())


def modulo_della_rotta(route) -> Optional[str]:
    """Business module owning the route, from its endpoint's package; None for platform routes."""
    parts = (getattr(getattr(route, "endpoint", None), "__module__", "") or "").split(".")
    if parts[0] == "modules" and len(parts) > 1:
        parts = parts[1:]
    return parts[0] if parts[0] in _moduli_noti() else None


def moduli_attivi_tenant(tenant_schema: str) -> Optional[Set[str]]:
    """Enabled modules of the tenant; None when the tenant doesn't exist."""
    with engine.connect() as conn:
        tenant_id = conn.execute(text("SELECT id FROM public.core_tenants WHERE schema_name = :s"),
                                 {"s": tenant_schema}).scalar()
        if tenant_id is None:
            return None
        rows = conn.execute(text(
            "SELECT module_id FROM public.core_tenant_modules WHERE tenant_id = :t AND enabled IS TRUE"
        ), {"t": tenant_id})
        return {r[0] for r in rows}


def _protetta(asgi_app, modulo: str):
    async def gate(scope, receive, send):
        if scope["type"] == "http":
            tenant_schema = (scope.get("state") or {}).get("tenant_schema")
            if tenant_schema:
                attivi = await run_in_threadpool(moduli_attivi_tenant, tenant_schema)
                if attivi is None or modulo not in attivi:
                    response = JSONResponse(
                        {"detail": f"Modulo {modulo} non attivo per questo tenant"}, status_code=403)
                    await response(scope, receive, send)
                    return
        await asgi_app(scope, receive, send)

    gate.modulo_gate = modulo
    return gate


def proteggi_rotte(app) -> int:
    """Wrap every not yet wrapped module route; returns how many were wrapped."""
    n = 0
    for route in app.router.routes:
        if not isinstance(route, APIRoute) or getattr(route.app, "modulo_gate", None):
            continue
        modulo = modulo_della_rotta(route)
        if modulo:
            route.app = _protetta(route.app, modulo)
            n += 1
    return n


class ModuleGateMiddleware:
    """Pure ASGI: makes sure routes mounted after startup are gated too."""

    def __init__(self, app, fastapi_app):
        self.app = app
        self.fastapi_app = fastapi_app
        self._n_rotte = -1

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            n = len(self.fastapi_app.router.routes)
            if n != self._n_rotte:
                proteggi_rotte(self.fastapi_app)
                self._n_rotte = n
        await self.app(scope, receive, send)
