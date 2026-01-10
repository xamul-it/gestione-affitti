# Multi-Tenancy Documentation

This directory contains all documentation related to the multi-tenancy architecture implementation in Gestione Affitti.

## Overview

Multi-tenancy is a key architectural feature that enables the platform to support multiple isolated tenant schemas within a single PostgreSQL database. Each tenant has their own data schema while sharing authentication and platform infrastructure.

## Documents

### Architecture & Design
- **MULTI_TENANT_ADVANCED_FEATURES.md** - Advanced features and capabilities of the multi-tenancy system
- **MULTI_TENANT_MIGRATION_ANALYSIS.md** - Analysis and strategy for migrating to multi-tenancy
- **MULTI_TENANT_IMPLEMENTATION_PROGRESS.md** - Progress tracking and implementation details

### Status & Management
- **MULTI_TENANT_STATUS.md** - Current status of multi-tenancy implementation

## Key Concepts

### Schema-Based Multi-Tenancy
- Each tenant gets its own PostgreSQL schema (e.g., `tenant_test`, `tenant_produzione`)
- All tables are duplicated in each tenant schema
- The `public` schema contains shared data (users, tenant metadata)

### Tenant Context Management
- JWT tokens include a `tenant_schema` claim
- TenantMiddleware extracts tenant from JWT and stores in `request.state`
- `get_db()` dependency automatically sets PostgreSQL search_path to tenant schema
- Uses Starlette's request-scoped state management (FastAPI-native approach)

### Tenant Switching Flow
```
User Login → GET /tenants/my-tenants → User Selects Tenant →
POST /tenants/switch → New JWT with tenant_schema →
All queries execute in tenant schema
```

## Implementation Files (Backend)
- `app/core/database.py` - `get_tenant_schema()` and `get_db()` dependencies
- `app/core/middleware/tenant_middleware.py` - JWT extraction and state management
- `app/core/routes/tenants.py` - Tenant switching API endpoints

## Implementation Files (Frontend)
- `frontend/src/contexts/TenantContext.jsx` - Frontend tenant state management

## Getting Started

1. Read `MULTI_TENANT_MIGRATION_ANALYSIS.md` for architecture overview
2. Review `MULTI_TENANT_IMPLEMENTATION_PROGRESS.md` for current implementation status
3. Check `MULTI_TENANT_ADVANCED_FEATURES.md` for advanced features
4. Refer to `MULTI_TENANT_STATUS.md` for status updates

## Testing Multi-Tenancy

```bash
# 1. Login and get base token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -d '{"username":"admin","password":"changeme123"}'

# 2. Switch to a specific tenant
curl -X POST "http://localhost:8000/api/v1/tenants/switch" \
  -H "Authorization: Bearer <token>" \
  -d '{"tenant_id": 1}'  # Returns token with tenant_schema

# 3. Access tenant-specific data
curl -X GET "http://localhost:8000/api/v1/anagrafica/soggetti/" \
  -H "Authorization: Bearer <tenant_token>"  # Only sees tenant's data
```

## Creating New Tenants

To add a new tenant schema manually:

```sql
-- Create new tenant schema
CREATE SCHEMA tenant_newclient;

-- Grant permissions
GRANT USAGE ON SCHEMA tenant_newclient TO your_app_user;
GRANT ALL ON ALL TABLES IN SCHEMA tenant_newclient TO your_app_user;

-- Run migrations in the new schema
SET search_path TO tenant_newclient, public;
-- Run your alembic migrations here
```

## Tenant Isolation Rules

- Data Isolation: Each tenant sees only their own data
- Schema Automatic: search_path set automatically per request
- FastAPI Native: Uses request.state for request-scoped storage
- Dependency Chain: Clean separation with get_tenant_schema → get_db
- Shared Tables: Tables in public schema (users, tenants) shared across all tenants
- Manual Creation: New tenant schemas must be created manually in PostgreSQL

## Last Updated

December 2025 - Multi-tenancy implementation verified and working

For more details, see the root-level `CLAUDE.md` file.
