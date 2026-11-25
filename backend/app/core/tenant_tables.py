"""
Tables prefixed "core_" that are tenant-scoped business data (like any
module's tables), NOT shared platform data. They must be created only
inside each tenant schema via a dedicated Alembic migration
(target_schema="tenant"), never in `public` — that was the root cause of a
tenant-isolation bug where core_scadenze ended up as a single table shared
by every tenant (see docs/superpowers/plans/2026-09-18-notification-service.md).

Kept here, without imports, so scripts can read it without loading app.main.
"""
TENANT_ONLY_CORE_TABLES = frozenset({
    "core_scadenze",
    "core_scadenza_destinatari",
    "core_scadenza_log",
    "core_notifiche",
    "core_documenti",
    "core_documenti_files",
    "core_tipi_documento_overrides",
    "core_stati_documento_overrides",
    "core_relazioni",
})
