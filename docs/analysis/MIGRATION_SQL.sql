-- ============================================================================
-- MIGRATION SQL - Document System Enhancement
-- ============================================================================
-- Project: Gestione Affitti
-- Date: 2026-01-31
-- Phase: 1 - Foundation
-- Description: Migrate from single-file to multi-file document structure
-- ============================================================================

-- Prerequisites:
-- 1. Backup database before running
-- 2. Test on development environment first
-- 3. Run during maintenance window
-- 4. Verify tenant schema context before execution

-- ============================================================================
-- PART 1: MODIFY EXISTING TABLES (PUBLIC SCHEMA)
-- ============================================================================

-- 1.1: Add parsing multi-file config to TipoDocumento
-- -----------------------------------------------------
ALTER TABLE public.anag_tipi_documento
  ADD COLUMN IF NOT EXISTS parsing_multi_file_config JSON
    COMMENT 'Configuration for parsing different file types (fronte, retro, etc.)';

-- Example data:
-- {
--   "fronte": {
--     "parsing_required": true,
--     "service": "mrz",
--     "config": {"format": "td1"}
--   },
--   "retro": {
--     "parsing_required": false
--   }
-- }

COMMENT ON COLUMN public.anag_tipi_documento.parsing_multi_file_config IS
  'JSON configuration for multi-file parsing. Keys are tipo_pagina values (fronte, retro, etc.)';


-- ============================================================================
-- PART 2: MODIFY DOCUMENTO TABLE (TENANT SCHEMAS)
-- ============================================================================
-- NOTE: This must be run for EACH tenant schema
-- Replace {tenant_schema} with actual schema name (e.g., tenant_test)
-- ============================================================================

-- 2.1: Add new fields to Documento table
-- ----------------------------------------
-- Run this for each tenant schema:
-- SET search_path TO {tenant_schema}, public;

ALTER TABLE anag_documenti
  ADD COLUMN IF NOT EXISTS metadata_parsato JSON
    COMMENT 'Aggregated parsed data from all files',
  ADD COLUMN IF NOT EXISTS confidence_score INTEGER
    COMMENT 'Average confidence score from all parsed files (0-100)';

-- 2.2: Make legacy fields nullable for backward compatibility
-- ------------------------------------------------------------
ALTER TABLE anag_documenti
  ALTER COLUMN nome_file DROP NOT NULL,
  ALTER COLUMN file_path DROP NOT NULL,
  ALTER COLUMN mime_type DROP NOT NULL,
  ALTER COLUMN dimensione DROP NOT NULL;

-- Add comments
COMMENT ON COLUMN anag_documenti.metadata_parsato IS
  'JSON containing merged parsed data from all document files. Example: {"codice_fiscale": "...", "nome": "...", ...}';

COMMENT ON COLUMN anag_documenti.confidence_score IS
  'Average confidence score (0-100) calculated from all parsed files';

COMMENT ON COLUMN anag_documenti.nome_file IS
  '[DEPRECATED] Use DocumentoFile relationship instead. Kept for backward compatibility during migration.';

COMMENT ON COLUMN anag_documenti.file_path IS
  '[DEPRECATED] Use DocumentoFile relationship instead. Kept for backward compatibility during migration.';


-- ============================================================================
-- PART 3: CREATE NEW TABLES (TENANT SCHEMAS)
-- ============================================================================
-- NOTE: Run for EACH tenant schema
-- SET search_path TO {tenant_schema}, public;
-- ============================================================================

-- 3.1: Create DocumentoFile table
-- --------------------------------
CREATE TABLE IF NOT EXISTS anag_documenti_files (
  id SERIAL PRIMARY KEY,
  documento_id INTEGER NOT NULL,

  -- File information
  file_path VARCHAR(500) NOT NULL
    COMMENT 'Relative path to original file (includes tenant schema prefix)',
  nome_file VARCHAR(255) NOT NULL
    COMMENT 'Original filename',
  mime_type VARCHAR(100)
    COMMENT 'MIME type (image/jpeg, application/pdf, etc.)',
  dimensione BIGINT
    COMMENT 'File size in bytes',

  -- Display and organization
  ordine INTEGER NOT NULL DEFAULT 1
    COMMENT 'Display order (1, 2, 3, ...)',
  tipo_pagina VARCHAR(50)
    COMMENT 'Page type: fronte, retro, pagina_1, pagina_2, etc.',

  -- Normalized file (cache)
  file_normalizzato_path VARCHAR(500)
    COMMENT 'Path to normalized JPEG file',
  normalizzato_width INTEGER
    COMMENT 'Width of normalized image in pixels',
  normalizzato_height INTEGER
    COMMENT 'Height of normalized image in pixels',

  -- Parsing information (optional per file)
  parsing_job_id INTEGER
    COMMENT 'FK to public.core_document_jobs if parsing was performed',
  parsing_result JSON
    COMMENT 'Parsed data extracted from this specific file',
  confidence_score INTEGER
    COMMENT 'Parsing confidence score for this file (0-100)',

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Foreign keys
  CONSTRAINT fk_documento
    FOREIGN KEY (documento_id)
    REFERENCES anag_documenti(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_parsing_job
    FOREIGN KEY (parsing_job_id)
    REFERENCES public.core_document_jobs(id)
    ON DELETE SET NULL,

  -- Constraints
  CONSTRAINT check_ordine_positive
    CHECK (ordine > 0),
  CONSTRAINT check_confidence_range
    CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 100))
);

-- 3.2: Create indexes for performance
-- ------------------------------------
CREATE INDEX IF NOT EXISTS idx_documenti_files_documento_id
  ON anag_documenti_files(documento_id);

CREATE INDEX IF NOT EXISTS idx_documenti_files_parsing_job_id
  ON anag_documenti_files(parsing_job_id)
  WHERE parsing_job_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documenti_files_ordine
  ON anag_documenti_files(documento_id, ordine);

-- 3.3: Add table comments
-- ------------------------
COMMENT ON TABLE anag_documenti_files IS
  'Individual files belonging to a document. Supports multi-page documents (e.g., fronte/retro of ID card).';

COMMENT ON COLUMN anag_documenti_files.file_path IS
  'Relative path with tenant prefix. Example: tenant_test/SOGGETTO/45/uuid_fronte.jpg';

COMMENT ON COLUMN anag_documenti_files.file_normalizzato_path IS
  'Path to normalized JPEG file (max 2048px, quality 85%). Used for viewing and parsing.';

COMMENT ON COLUMN anag_documenti_files.tipo_pagina IS
  'Identifies the type of page. Common values: "fronte", "retro", "pagina_1", "pagina_2", "unico"';


-- ============================================================================
-- PART 4: DATA MIGRATION HELPER FUNCTIONS
-- ============================================================================

-- 4.1: Function to migrate single documento
-- ------------------------------------------
CREATE OR REPLACE FUNCTION migrate_documento_to_multifile(
  p_documento_id INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
  v_doc RECORD;
  v_file_id INTEGER;
BEGIN
  -- Get documento
  SELECT * INTO v_doc
  FROM anag_documenti
  WHERE id = p_documento_id;

  IF NOT FOUND THEN
    RAISE NOTICE 'Documento % not found', p_documento_id;
    RETURN FALSE;
  END IF;

  -- Check if already migrated (has files)
  IF EXISTS (SELECT 1 FROM anag_documenti_files WHERE documento_id = p_documento_id) THEN
    RAISE NOTICE 'Documento % already migrated (has files)', p_documento_id;
    RETURN TRUE;
  END IF;

  -- Check if has legacy file_path
  IF v_doc.file_path IS NULL OR v_doc.file_path = '' THEN
    RAISE NOTICE 'Documento % has no file_path, skipping', p_documento_id;
    RETURN FALSE;
  END IF;

  -- Create DocumentoFile from legacy fields
  INSERT INTO anag_documenti_files (
    documento_id,
    file_path,
    nome_file,
    mime_type,
    dimensione,
    ordine,
    tipo_pagina,
    created_at
  ) VALUES (
    v_doc.id,
    v_doc.file_path,
    COALESCE(v_doc.nome_file, 'documento'),
    v_doc.mime_type,
    v_doc.dimensione,
    1,
    'unico',  -- Single file from legacy
    COALESCE(v_doc.created_at, NOW())
  )
  RETURNING id INTO v_file_id;

  RAISE NOTICE 'Documento % migrated → DocumentoFile %', p_documento_id, v_file_id;

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migrate_documento_to_multifile IS
  'Migrate a single documento from legacy single-file to new multi-file structure';


-- 4.2: Function to migrate all documenti in tenant
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION migrate_all_documenti()
RETURNS TABLE(
  documento_id INTEGER,
  migrated BOOLEAN,
  message TEXT
) AS $$
DECLARE
  v_doc RECORD;
  v_result BOOLEAN;
  v_count INTEGER := 0;
  v_success INTEGER := 0;
BEGIN
  FOR v_doc IN
    SELECT id FROM anag_documenti
    ORDER BY id
  LOOP
    BEGIN
      v_result := migrate_documento_to_multifile(v_doc.id);
      v_count := v_count + 1;

      IF v_result THEN
        v_success := v_success + 1;
        RETURN QUERY SELECT v_doc.id, TRUE, 'Migrated successfully'::TEXT;
      ELSE
        RETURN QUERY SELECT v_doc.id, FALSE, 'Skipped (no file or already migrated)'::TEXT;
      END IF;

    EXCEPTION WHEN OTHERS THEN
      RETURN QUERY SELECT v_doc.id, FALSE, ('Error: ' || SQLERRM)::TEXT;
    END;
  END LOOP;

  RAISE NOTICE 'Migration complete: % / % documenti migrated', v_success, v_count;
  RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migrate_all_documenti IS
  'Migrate all documenti in current schema from legacy to new multi-file structure';


-- ============================================================================
-- PART 5: VERIFICATION QUERIES
-- ============================================================================

-- 5.1: Check migration status
-- ----------------------------
-- Run this to verify migration progress:

SELECT
  'Total Documenti' AS metric,
  COUNT(*) AS count
FROM anag_documenti
UNION ALL
SELECT
  'Documenti with legacy file_path',
  COUNT(*)
FROM anag_documenti
WHERE file_path IS NOT NULL
UNION ALL
SELECT
  'Documenti with new files',
  COUNT(DISTINCT documento_id)
FROM anag_documenti_files
UNION ALL
SELECT
  'Total DocumentoFile records',
  COUNT(*)
FROM anag_documenti_files
UNION ALL
SELECT
  'Documenti pending migration',
  COUNT(*)
FROM anag_documenti d
WHERE d.file_path IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM anag_documenti_files f
    WHERE f.documento_id = d.id
  );


-- 5.2: List documenti pending migration
-- --------------------------------------
SELECT
  d.id,
  d.entity_type,
  d.entity_id,
  d.nome_file,
  d.file_path,
  (SELECT COUNT(*) FROM anag_documenti_files f WHERE f.documento_id = d.id) AS num_files
FROM anag_documenti d
WHERE d.file_path IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM anag_documenti_files f WHERE f.documento_id = d.id
  )
ORDER BY d.id
LIMIT 100;


-- 5.3: Verify DocumentoFile integrity
-- ------------------------------------
SELECT
  d.id AS documento_id,
  d.entity_type,
  d.entity_id,
  COUNT(f.id) AS num_files,
  STRING_AGG(f.tipo_pagina, ', ' ORDER BY f.ordine) AS file_types
FROM anag_documenti d
LEFT JOIN anag_documenti_files f ON f.documento_id = d.id
GROUP BY d.id, d.entity_type, d.entity_id
HAVING COUNT(f.id) > 0
ORDER BY d.id
LIMIT 100;


-- ============================================================================
-- PART 6: ROLLBACK PLAN (IF NEEDED)
-- ============================================================================

-- ⚠️ WARNING: Only use in emergency. This will lose multi-file data!
-- Use with extreme caution.

-- 6.1: Restore legacy fields from first DocumentoFile
-- ----------------------------------------------------
/*
UPDATE anag_documenti d
SET
  nome_file = f.nome_file,
  file_path = f.file_path,
  mime_type = f.mime_type,
  dimensione = f.dimensione
FROM (
  SELECT DISTINCT ON (documento_id)
    documento_id,
    nome_file,
    file_path,
    mime_type,
    dimensione
  FROM anag_documenti_files
  ORDER BY documento_id, ordine
) f
WHERE d.id = f.documento_id
  AND d.nome_file IS NULL;
*/

-- 6.2: Drop new tables and columns
-- ---------------------------------
/*
-- Drop DocumentoFile table
DROP TABLE IF EXISTS anag_documenti_files CASCADE;

-- Drop new columns from Documento
ALTER TABLE anag_documenti
  DROP COLUMN IF EXISTS metadata_parsato,
  DROP COLUMN IF EXISTS confidence_score;

-- Make legacy fields NOT NULL again
ALTER TABLE anag_documenti
  ALTER COLUMN nome_file SET NOT NULL,
  ALTER COLUMN file_path SET NOT NULL;
*/


-- ============================================================================
-- PART 7: EXECUTION INSTRUCTIONS
-- ============================================================================

-- STEP 1: Backup Database
-- -----------------------
-- pg_dump -U postgres -d gestione_affitti > backup_before_migration_$(date +%Y%m%d).sql

-- STEP 2: Run Part 1 (PUBLIC schema)
-- -----------------------------------
-- SET search_path TO public;
-- [Execute Part 1 SQL above]

-- STEP 3: For EACH tenant schema, run Parts 2-5
-- ----------------------------------------------
-- SET search_path TO tenant_test, public;
-- [Execute Parts 2, 3, 4, 5 SQL above]

-- SET search_path TO tenant_produzione, public;
-- [Execute Parts 2, 3, 4, 5 SQL above]

-- STEP 4: Run Migration Function for each tenant
-- -----------------------------------------------
-- SET search_path TO tenant_test, public;
-- SELECT * FROM migrate_all_documenti();
-- Verify results with Part 5 queries

-- SET search_path TO tenant_produzione, public;
-- SELECT * FROM migrate_all_documenti();
-- Verify results with Part 5 queries

-- STEP 5: Verify Migration
-- -------------------------
-- Run verification queries from Part 5 for each tenant
-- Check that:
-- - No documenti pending migration
-- - All legacy documenti have corresponding DocumentoFile
-- - File counts are correct

-- STEP 6: (OPTIONAL) Cleanup Legacy Fields
-- -----------------------------------------
-- After verifying migration for 1-2 weeks in production:
-- ALTER TABLE anag_documenti
--   DROP COLUMN nome_file,
--   DROP COLUMN file_path,
--   DROP COLUMN mime_type,
--   DROP COLUMN dimensione;

-- ============================================================================
-- END OF MIGRATION SQL
-- ============================================================================
