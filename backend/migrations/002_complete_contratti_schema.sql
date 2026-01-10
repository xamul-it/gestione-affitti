-- ============================================
-- MIGRATION: 002 - Complete contratti schema
-- Description: Add missing columns to contratti table
-- Date: 2025-11-27
-- Author: QA Bug Fix
-- ============================================

BEGIN;

-- ============================================
-- 1. CREATE ENUM TYPES (IF NOT EXISTS)
-- ============================================

-- Uso Immobile ENUM
DO $$ BEGIN
    CREATE TYPE usoimmobile AS ENUM (
        'ABITATIVO',
        'COMMERCIALE',
        'UFFICIO',
        'MAGAZZINO',
        'ALTRO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Tipologia Contratto ENUM
DO $$ BEGIN
    CREATE TYPE tipologiacontratto AS ENUM (
        'LIBERO_MERCATO',
        'CANONE_CONCORDATO',
        'TRANSITORIO',
        'STUDENTI',
        'FORESTERIA',
        'COMMERCIALE_LIBERO',
        'ALTRO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Regime Fiscale ENUM
DO $$ BEGIN
    CREATE TYPE regimefiscale AS ENUM (
        'ORDINARIO_IRPEF',
        'CEDOLARE_SECCA_21',
        'CEDOLARE_SECCA_10'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================
-- 2. ADD MISSING COLUMNS
-- ============================================

-- Uso immobile (REQUIRED - default ABITATIVO)
ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    uso_immobile usoimmobile DEFAULT 'ABITATIVO' NOT NULL;

-- Tipologia contratto (REQUIRED - default LIBERO_MERCATO)
ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    tipologia_contratto tipologiacontratto DEFAULT 'LIBERO_MERCATO' NOT NULL;

-- Durata contratto
ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    durata_anni_iniziale INTEGER DEFAULT 4 NOT NULL;

ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    durata_anni_rinnovo INTEGER;

-- Regime fiscale (REQUIRED - default ORDINARIO_IRPEF)
ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    regime_fiscale regimefiscale DEFAULT 'ORDINARIO_IRPEF' NOT NULL;

-- Adeguamento ISTAT
ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    adeguamento_istat BOOLEAN DEFAULT false;

ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    percentuale_istat NUMERIC(5, 2);

ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    data_ultimo_adeguamento DATE;

-- Registrazione agenzia
ALTER TABLE contratti ADD COLUMN IF NOT EXISTS
    registrazione_agenzia VARCHAR(200);

-- ============================================
-- 3. CONVERT NUMERIC TYPES (if needed)
-- ============================================

-- Convert Float to Numeric(10,2) for better precision
ALTER TABLE contratti
    ALTER COLUMN canone_mensile TYPE NUMERIC(10, 2)
    USING canone_mensile::NUMERIC(10, 2);

ALTER TABLE contratti
    ALTER COLUMN deposito_cauzionale TYPE NUMERIC(10, 2)
    USING deposito_cauzionale::NUMERIC(10, 2);

-- ============================================
-- 4. CREATE INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_contratti_uso_immobile
    ON contratti(uso_immobile);

CREATE INDEX IF NOT EXISTS idx_contratti_tipologia
    ON contratti(tipologia_contratto);

CREATE INDEX IF NOT EXISTS idx_contratti_regime_fiscale
    ON contratti(regime_fiscale);

CREATE INDEX IF NOT EXISTS idx_contratti_data_inizio
    ON contratti(data_inizio);

CREATE INDEX IF NOT EXISTS idx_contratti_data_fine
    ON contratti(data_fine);

-- ============================================
-- 5. REMOVE DEFAULTS (allow application to set them)
-- ============================================

-- After initial data migration, remove defaults to let app control
ALTER TABLE contratti ALTER COLUMN uso_immobile DROP DEFAULT;
ALTER TABLE contratti ALTER COLUMN tipologia_contratto DROP DEFAULT;
ALTER TABLE contratti ALTER COLUMN durata_anni_iniziale DROP DEFAULT;
ALTER TABLE contratti ALTER COLUMN regime_fiscale DROP DEFAULT;

COMMIT;

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Run this to verify the migration:
-- \d contratti
