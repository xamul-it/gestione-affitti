-- ============================================
-- MIGRATION: 003 - Complete spese schema
-- Description: Add missing columns for condominium expense distribution
-- Date: 2025-11-27
-- Author: QA Bug Fix
-- ============================================

BEGIN;

-- ============================================
-- 1. ADD MISSING COLUMNS
-- ============================================

-- Foreign key to tabella_millesimale (for condominium expenses)
ALTER TABLE spese ADD COLUMN IF NOT EXISTS
    tabella_millesimale_id INTEGER;

-- Flags for condominium expense management
ALTER TABLE spese ADD COLUMN IF NOT EXISTS
    spesa_condominiale INTEGER DEFAULT 0;  -- 0 = direct expense, 1 = condominium expense to distribute

ALTER TABLE spese ADD COLUMN IF NOT EXISTS
    ripartita INTEGER DEFAULT 0;  -- 0 = not distributed, 1 = distributed

-- ============================================
-- 2. ADD FOREIGN KEY CONSTRAINT
-- ============================================

-- Add constraint only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_spese_tabella_millesimale'
    ) THEN
        ALTER TABLE spese
            ADD CONSTRAINT fk_spese_tabella_millesimale
            FOREIGN KEY (tabella_millesimale_id)
            REFERENCES tabelle_millesimali(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================
-- 3. CREATE INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_spese_tabella_millesimale_id
    ON spese(tabella_millesimale_id);

CREATE INDEX IF NOT EXISTS idx_spese_condominiale
    ON spese(spesa_condominiale);

CREATE INDEX IF NOT EXISTS idx_spese_ripartita
    ON spese(ripartita);

CREATE INDEX IF NOT EXISTS idx_spese_data
    ON spese(data);

CREATE INDEX IF NOT EXISTS idx_spese_categoria
    ON spese(categoria);

CREATE INDEX IF NOT EXISTS idx_spese_pagata
    ON spese(pagata);

-- ============================================
-- 4. CONVERT NUMERIC TYPES (if needed)
-- ============================================

-- Convert Float to Numeric(10,2) for better precision
ALTER TABLE spese
    ALTER COLUMN importo TYPE NUMERIC(10, 2)
    USING importo::NUMERIC(10, 2);

-- ============================================
-- 5. ADD COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON COLUMN spese.tabella_millesimale_id IS 'FK to tabella_millesimali. NULL = direct expense, NOT NULL = condominium expense to be distributed';
COMMENT ON COLUMN spese.spesa_condominiale IS '0 = spesa diretta immobile, 1 = spesa condominiale da ripartire tra proprietari';
COMMENT ON COLUMN spese.ripartita IS '0 = non ancora ripartita, 1 = già ripartita in ripartizioni_spese';

COMMIT;

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Run this to verify the migration:
-- \d spese
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'spese'
-- ORDER BY ordinal_position;
