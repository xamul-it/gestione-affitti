-- ============================================================================
-- Multi-Tenant Migration Script
-- ============================================================================
-- Description: Migrates existing single-tenant database to multi-tenant
--              schema-based architecture with two initial tenants
-- Date: 9 December 2025
-- Database: gestione_affitti
--
-- IMPORTANT:
-- 1. Backup database before running: pg_dump gestione_affitti > backup_pre_migration.sql
-- 2. Review this script completely before execution
-- 3. Test on a copy of the database first
-- 4. Run in a transaction so you can rollback if needed
-- ============================================================================

BEGIN;

-- ============================================================================
-- PHASE 1: Create Tenant Infrastructure Tables
-- ============================================================================

-- Table: tenants
-- Purpose: Registry of all tenants (logical databases) in the platform
CREATE TABLE IF NOT EXISTS public.tenants (
    id SERIAL PRIMARY KEY,
    schema_name VARCHAR(63) NOT NULL UNIQUE,
    nome_display VARCHAR(100) NOT NULL,
    descrizione VARCHAR(255),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenants_schema_name ON public.tenants(schema_name);
CREATE INDEX idx_tenants_active ON public.tenants(active);

-- Table: user_tenants
-- Purpose: Many-to-many relationship between users and tenants with metadata
CREATE TABLE IF NOT EXISTS public.user_tenants (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    access_granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_tenant UNIQUE (user_id, tenant_id)
);

CREATE INDEX idx_user_tenants_user_id ON public.user_tenants(user_id);
CREATE INDEX idx_user_tenants_tenant_id ON public.user_tenants(tenant_id);
CREATE INDEX idx_user_tenants_is_default ON public.user_tenants(is_default);

-- Table: tenant_modules
-- Purpose: Track which modules are enabled for each tenant
CREATE TABLE IF NOT EXISTS public.tenant_modules (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    module_id VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config JSONB DEFAULT '{}'::jsonb,
    installed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    disabled_at TIMESTAMP,
    CONSTRAINT uq_tenant_module UNIQUE (tenant_id, module_id)
);

CREATE INDEX idx_tenant_modules_tenant_id ON public.tenant_modules(tenant_id);
CREATE INDEX idx_tenant_modules_module_id ON public.tenant_modules(module_id);
CREATE INDEX idx_tenant_modules_enabled ON public.tenant_modules(enabled);

-- ============================================================================
-- PHASE 2: Create Initial Tenants
-- ============================================================================

-- Tenant 1: Test Data (current production data will go here)
INSERT INTO public.tenants (schema_name, nome_display, descrizione, active)
VALUES ('tenant_test', 'Dati di Test', 'Database di test con dati demo', true)
ON CONFLICT (schema_name) DO NOTHING;

-- Tenant 2: Production Data (empty initially, for user's real data)
INSERT INTO public.tenants (schema_name, nome_display, descrizione, active)
VALUES ('tenant_produzione', 'Dati di Produzione', 'Database di produzione per dati reali', true)
ON CONFLICT (schema_name) DO NOTHING;

-- ============================================================================
-- PHASE 3: Create Tenant Schemas
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS tenant_test;
CREATE SCHEMA IF NOT EXISTS tenant_produzione;

-- Grant permissions to application user
GRANT ALL ON SCHEMA tenant_test TO affitti;
GRANT ALL ON SCHEMA tenant_produzione TO affitti;
GRANT ALL ON ALL TABLES IN SCHEMA tenant_test TO affitti;
GRANT ALL ON ALL TABLES IN SCHEMA tenant_produzione TO affitti;
GRANT ALL ON ALL SEQUENCES IN SCHEMA tenant_test TO affitti;
GRANT ALL ON ALL SEQUENCES IN SCHEMA tenant_produzione TO affitti;

-- ============================================================================
-- PHASE 4: Copy Business Table Structures to Tenant Schemas
-- ============================================================================

-- Anagrafica Module Tables (5 tables)
CREATE TABLE tenant_test.soggetti_anagrafici (LIKE public.soggetti_anagrafici INCLUDING ALL);
CREATE TABLE tenant_test.ruoli_azienda (LIKE public.ruoli_azienda INCLUDING ALL);
CREATE TABLE tenant_test.ruoli_azienda_tipi (LIKE public.ruoli_azienda_tipi INCLUDING ALL);
CREATE TABLE tenant_test.ruoli_disponibili (LIKE public.ruoli_disponibili INCLUDING ALL);
CREATE TABLE tenant_test.soggetti_ruoli (LIKE public.soggetti_ruoli INCLUDING ALL);

CREATE TABLE tenant_produzione.soggetti_anagrafici (LIKE public.soggetti_anagrafici INCLUDING ALL);
CREATE TABLE tenant_produzione.ruoli_azienda (LIKE public.ruoli_azienda INCLUDING ALL);
CREATE TABLE tenant_produzione.ruoli_azienda_tipi (LIKE public.ruoli_azienda_tipi INCLUDING ALL);
CREATE TABLE tenant_produzione.ruoli_disponibili (LIKE public.ruoli_disponibili INCLUDING ALL);
CREATE TABLE tenant_produzione.soggetti_ruoli (LIKE public.soggetti_ruoli INCLUDING ALL);

-- Immobili Module Tables (10 tables)
CREATE TABLE tenant_test.unita_immobiliari (LIKE public.unita_immobiliari INCLUDING ALL);
CREATE TABLE tenant_test.condomini (LIKE public.condomini INCLUDING ALL);
CREATE TABLE tenant_test.proprietari (LIKE public.proprietari INCLUDING ALL);
CREATE TABLE tenant_test.diritti_immobile (LIKE public.diritti_immobile INCLUDING ALL);
CREATE TABLE tenant_test.certificati_energetici (LIKE public.certificati_energetici INCLUDING ALL);
CREATE TABLE tenant_test.tabelle_millesimali (LIKE public.tabelle_millesimali INCLUDING ALL);
CREATE TABLE tenant_test.millesimi_unita (LIKE public.millesimi_unita INCLUDING ALL);
CREATE TABLE tenant_test.documenti (LIKE public.documenti INCLUDING ALL);
CREATE TABLE tenant_test.platform_user_dashboards (LIKE public.platform_user_dashboards INCLUDING ALL);

CREATE TABLE tenant_produzione.unita_immobiliari (LIKE public.unita_immobiliari INCLUDING ALL);
CREATE TABLE tenant_produzione.condomini (LIKE public.condomini INCLUDING ALL);
CREATE TABLE tenant_produzione.proprietari (LIKE public.proprietari INCLUDING ALL);
CREATE TABLE tenant_produzione.diritti_immobile (LIKE public.diritti_immobile INCLUDING ALL);
CREATE TABLE tenant_produzione.certificati_energetici (LIKE public.certificati_energetici INCLUDING ALL);
CREATE TABLE tenant_produzione.tabelle_millesimali (LIKE public.tabelle_millesimali INCLUDING ALL);
CREATE TABLE tenant_produzione.millesimi_unita (LIKE public.millesimi_unita INCLUDING ALL);
CREATE TABLE tenant_produzione.documenti (LIKE public.documenti INCLUDING ALL);
CREATE TABLE tenant_produzione.platform_user_dashboards (LIKE public.platform_user_dashboards INCLUDING ALL);

-- Affitti_Lungo Module Tables (5 tables)
CREATE TABLE tenant_test.affittuari (LIKE public.affittuari INCLUDING ALL);
CREATE TABLE tenant_test.contratti (LIKE public.contratti INCLUDING ALL);
CREATE TABLE tenant_test.incassi (LIKE public.incassi INCLUDING ALL);
CREATE TABLE tenant_test.spese (LIKE public.spese INCLUDING ALL);
CREATE TABLE tenant_test.ripartizioni_spese (LIKE public.ripartizioni_spese INCLUDING ALL);
CREATE TABLE tenant_test.tecnici (LIKE public.tecnici INCLUDING ALL);

CREATE TABLE tenant_produzione.affittuari (LIKE public.affittuari INCLUDING ALL);
CREATE TABLE tenant_produzione.contratti (LIKE public.contratti INCLUDING ALL);
CREATE TABLE tenant_produzione.incassi (LIKE public.incassi INCLUDING ALL);
CREATE TABLE tenant_produzione.spese (LIKE public.spese INCLUDING ALL);
CREATE TABLE tenant_produzione.ripartizioni_spese (LIKE public.ripartizioni_spese INCLUDING ALL);
CREATE TABLE tenant_produzione.tecnici (LIKE public.tecnici INCLUDING ALL);

-- ============================================================================
-- PHASE 5: Migrate Existing Data to tenant_test
-- ============================================================================

-- Anagrafica Module
INSERT INTO tenant_test.soggetti_anagrafici SELECT * FROM public.soggetti_anagrafici;
INSERT INTO tenant_test.ruoli_azienda SELECT * FROM public.ruoli_azienda;
INSERT INTO tenant_test.ruoli_azienda_tipi SELECT * FROM public.ruoli_azienda_tipi;
INSERT INTO tenant_test.ruoli_disponibili SELECT * FROM public.ruoli_disponibili;
INSERT INTO tenant_test.soggetti_ruoli SELECT * FROM public.soggetti_ruoli;

-- Immobili Module
INSERT INTO tenant_test.unita_immobiliari SELECT * FROM public.unita_immobiliari;
INSERT INTO tenant_test.condomini SELECT * FROM public.condomini;
INSERT INTO tenant_test.proprietari SELECT * FROM public.proprietari;
INSERT INTO tenant_test.diritti_immobile SELECT * FROM public.diritti_immobile;
INSERT INTO tenant_test.certificati_energetici SELECT * FROM public.certificati_energetici;
INSERT INTO tenant_test.tabelle_millesimali SELECT * FROM public.tabelle_millesimali;
INSERT INTO tenant_test.millesimi_unita SELECT * FROM public.millesimi_unita;
INSERT INTO tenant_test.documenti SELECT * FROM public.documenti;
INSERT INTO tenant_test.platform_user_dashboards SELECT * FROM public.platform_user_dashboards;

-- Affitti_Lungo Module
INSERT INTO tenant_test.affittuari SELECT * FROM public.affittuari;
INSERT INTO tenant_test.contratti SELECT * FROM public.contratti;
INSERT INTO tenant_test.incassi SELECT * FROM public.incassi;
INSERT INTO tenant_test.spese SELECT * FROM public.spese;
INSERT INTO tenant_test.ripartizioni_spese SELECT * FROM public.ripartizioni_spese;
INSERT INTO tenant_test.tecnici SELECT * FROM public.tecnici;

-- ============================================================================
-- PHASE 6: Update Sequences in Tenant Schemas
-- ============================================================================

-- Update sequence values to match the migrated data
-- This ensures new inserts don't cause primary key conflicts

DO $$
DECLARE
    seq_record RECORD;
    max_id INTEGER;
    table_name TEXT;
BEGIN
    -- For tenant_test schema
    FOR seq_record IN
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'tenant_test'
    LOOP
        -- Derive table name from sequence name (remove _id_seq suffix)
        table_name := REPLACE(seq_record.sequence_name, '_id_seq', '');

        -- Get max ID from the corresponding table
        EXECUTE format('SELECT COALESCE(MAX(id), 0) FROM tenant_test.%I', table_name)
        INTO max_id;

        -- Set sequence to max_id + 1
        IF max_id > 0 THEN
            EXECUTE format('SELECT setval(''tenant_test.%I'', %s)',
                          seq_record.sequence_name, max_id);
        END IF;
    END LOOP;

    -- For tenant_produzione schema (all sequences start at 1, no data yet)
    FOR seq_record IN
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'tenant_produzione'
    LOOP
        EXECUTE format('SELECT setval(''tenant_produzione.%I'', 1, false)',
                      seq_record.sequence_name);
    END LOOP;
END $$;

-- ============================================================================
-- PHASE 7: Verification Queries
-- ============================================================================

-- Verify row counts match
DO $$
DECLARE
    table_name TEXT;
    public_count INTEGER;
    tenant_count INTEGER;
BEGIN
    RAISE NOTICE 'Verifying data migration...';
    RAISE NOTICE '';

    FOR table_name IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'tenant_test'
        ORDER BY tablename
    LOOP
        -- Check if table exists in public
        IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = table_name) THEN
            EXECUTE format('SELECT COUNT(*) FROM public.%I', table_name) INTO public_count;
            EXECUTE format('SELECT COUNT(*) FROM tenant_test.%I', table_name) INTO tenant_count;

            IF public_count != tenant_count THEN
                RAISE WARNING 'Mismatch in table %: public=%, tenant_test=%',
                             table_name, public_count, tenant_count;
            ELSE
                RAISE NOTICE 'OK: % rows in %', tenant_count, table_name;
            END IF;
        END IF;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE 'Verification complete!';
END $$;

-- ============================================================================
-- PHASE 8: Grant Default Access to Existing Users
-- ============================================================================

-- Give all existing users access to tenant_test (with it as default)
INSERT INTO public.user_tenants (user_id, tenant_id, is_default)
SELECT
    u.id as user_id,
    t.id as tenant_id,
    true as is_default
FROM public.users u
CROSS JOIN public.tenants t
WHERE t.schema_name = 'tenant_test'
ON CONFLICT (user_id, tenant_id) DO NOTHING;

-- ============================================================================
-- PHASE 9: Drop Public Business Tables (AFTER VERIFICATION!)
-- ============================================================================

-- IMPORTANT: Only run this section AFTER verifying the migration was successful!
-- Comment out this section initially, then uncomment and run separately after verification.

/*
-- Anagrafica Module
DROP TABLE IF EXISTS public.soggetti_ruoli CASCADE;
DROP TABLE IF EXISTS public.ruoli_disponibili CASCADE;
DROP TABLE IF EXISTS public.ruoli_azienda CASCADE;
DROP TABLE IF EXISTS public.ruoli_azienda_tipi CASCADE;
DROP TABLE IF EXISTS public.soggetti_anagrafici CASCADE;

-- Affitti_Lungo Module
DROP TABLE IF EXISTS public.ripartizioni_spese CASCADE;
DROP TABLE IF EXISTS public.tecnici CASCADE;
DROP TABLE IF EXISTS public.spese CASCADE;
DROP TABLE IF EXISTS public.incassi CASCADE;
DROP TABLE IF EXISTS public.contratti CASCADE;
DROP TABLE IF EXISTS public.affittuari CASCADE;

-- Immobili Module
DROP TABLE IF EXISTS public.platform_user_dashboards CASCADE;
DROP TABLE IF EXISTS public.documenti CASCADE;
DROP TABLE IF EXISTS public.millesimi_unita CASCADE;
DROP TABLE IF EXISTS public.tabelle_millesimali CASCADE;
DROP TABLE IF EXISTS public.certificati_energetici CASCADE;
DROP TABLE IF EXISTS public.diritti_immobile CASCADE;
DROP TABLE IF EXISTS public.proprietari CASCADE;
DROP TABLE IF EXISTS public.condomini CASCADE;
DROP TABLE IF EXISTS public.unita_immobiliari CASCADE;
*/

-- ============================================================================
-- PHASE 10: Summary
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Multi-Tenant Migration Summary';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tenants created: %', (SELECT COUNT(*) FROM public.tenants);
    RAISE NOTICE 'Schemas created: tenant_test, tenant_produzione';
    RAISE NOTICE '';
    RAISE NOTICE 'Business tables migrated to tenant_test: 20 tables';
    RAISE NOTICE 'Platform infrastructure tables in public: 3 tables (tenants, user_tenants, tenant_modules)';
    RAISE NOTICE 'Platform tables remaining in public: 18 tables';
    RAISE NOTICE 'Reference data tables remaining in public: 3 tables';
    RAISE NOTICE '';
    RAISE NOTICE 'Users granted access: %', (SELECT COUNT(*) FROM public.user_tenants);
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Verify all data migrated correctly using verification queries above';
    RAISE NOTICE '2. Update SQLAlchemy models to support dynamic schemas';
    RAISE NOTICE '3. Implement TenantService and middleware';
    RAISE NOTICE '4. Update JWT tokens to include tenant_schema';
    RAISE NOTICE '5. Test application with search_path set to tenant schemas';
    RAISE NOTICE '6. After thorough testing, uncomment and run Phase 9 to drop public tables';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
END $$;

-- Commit the transaction
COMMIT;

-- ============================================================================
-- ROLLBACK Instructions
-- ============================================================================

/*
If something goes wrong during migration, you can rollback with:

ROLLBACK;

Then restore from backup:
psql gestione_affitti < backup_pre_migration.sql
*/
