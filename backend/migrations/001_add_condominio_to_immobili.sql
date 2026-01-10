-- Migration: Add condominio_id column to immobili table
-- Date: 2025-11-27
-- Description: Adds foreign key relationship between immobili and condomini

BEGIN;

-- Check if condomini table exists, if not create it
CREATE TABLE IF NOT EXISTS condomini (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    codice VARCHAR(50) UNIQUE NOT NULL,
    indirizzo VARCHAR(255),
    citta VARCHAR(100),
    cap VARCHAR(10),
    provincia VARCHAR(2),

    -- Amministratore details
    amministratore_nome VARCHAR(255),
    amministratore_cognome VARCHAR(255),
    amministratore_email VARCHAR(255),
    amministratore_telefono VARCHAR(50),
    amministratore_pec VARCHAR(255),

    -- Bank details
    iban VARCHAR(34),
    banca VARCHAR(255),

    -- Metadata
    note TEXT,
    attivo INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Add condominio_id column to immobili if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'immobili' AND column_name = 'condominio_id'
    ) THEN
        ALTER TABLE immobili ADD COLUMN condominio_id INTEGER;

        -- Add foreign key constraint
        ALTER TABLE immobili
            ADD CONSTRAINT fk_immobili_condominio
            FOREIGN KEY (condominio_id)
            REFERENCES condomini(id)
            ON DELETE SET NULL;

        -- Add index for performance
        CREATE INDEX idx_immobili_condominio_id ON immobili(condominio_id);

        RAISE NOTICE 'Column condominio_id added successfully to immobili table';
    ELSE
        RAISE NOTICE 'Column condominio_id already exists in immobili table';
    END IF;
END $$;

-- Create other required tables if they don't exist
CREATE TABLE IF NOT EXISTS tabelle_millesimali (
    id SERIAL PRIMARY KEY,
    condominio_id INTEGER NOT NULL REFERENCES condomini(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    descrizione TEXT,
    tipo_ripartizione VARCHAR(50) NOT NULL,

    -- Percentages for mixed distribution types
    percentuale_millesimi FLOAT DEFAULT 100.0,
    percentuale_consumo FLOAT DEFAULT 0.0,
    percentuale_occupanti FLOAT DEFAULT 0.0,

    attiva INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_percentuali_sum CHECK (
        (percentuale_millesimi + percentuale_consumo + percentuale_occupanti) = 100.0
    )
);

CREATE TABLE IF NOT EXISTS millesimi_immobile (
    id SERIAL PRIMARY KEY,
    immobile_id INTEGER NOT NULL REFERENCES immobili(id) ON DELETE CASCADE,
    tabella_millesimale_id INTEGER NOT NULL REFERENCES tabelle_millesimali(id) ON DELETE CASCADE,
    millesimi FLOAT NOT NULL,

    -- Additional fields for special distribution types
    piano INTEGER,
    numero_occupanti INTEGER DEFAULT 0,
    consumo FLOAT DEFAULT 0.0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(immobile_id, tabella_millesimale_id)
);

CREATE TABLE IF NOT EXISTS ripartizioni_spese (
    id SERIAL PRIMARY KEY,
    spesa_id INTEGER NOT NULL REFERENCES spese(id) ON DELETE CASCADE,
    immobile_id INTEGER NOT NULL REFERENCES immobili(id) ON DELETE CASCADE,

    importo_ripartito FLOAT NOT NULL,

    -- Breakdown for transparency
    millesimi_applicati FLOAT,
    importo_da_millesimi FLOAT,
    importo_da_consumo FLOAT,
    importo_da_occupanti FLOAT,
    importo_da_personalizzato FLOAT,

    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(spesa_id, immobile_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_tabelle_millesimali_condominio ON tabelle_millesimali(condominio_id);
CREATE INDEX IF NOT EXISTS idx_millesimi_immobile_immobile ON millesimi_immobile(immobile_id);
CREATE INDEX IF NOT EXISTS idx_millesimi_immobile_tabella ON millesimi_immobile(tabella_millesimale_id);
CREATE INDEX IF NOT EXISTS idx_ripartizioni_spese_spesa ON ripartizioni_spese(spesa_id);
CREATE INDEX IF NOT EXISTS idx_ripartizioni_spese_immobile ON ripartizioni_spese(immobile_id);

-- Add search optimization indexes for the search functionality
CREATE INDEX IF NOT EXISTS idx_immobili_indirizzo_lower ON immobili(LOWER(indirizzo));
CREATE INDEX IF NOT EXISTS idx_immobili_citta_lower ON immobili(LOWER(citta));
CREATE INDEX IF NOT EXISTS idx_affittuari_nome_lower ON affittuari(LOWER(nome));
CREATE INDEX IF NOT EXISTS idx_affittuari_cognome_lower ON affittuari(LOWER(cognome));
CREATE INDEX IF NOT EXISTS idx_affittuari_email_lower ON affittuari(LOWER(email));

COMMIT;

-- Verify the migration
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'immobili' AND column_name = 'condominio_id'
    ) THEN
        RAISE NOTICE '✓ Migration successful: condominio_id column exists';
    ELSE
        RAISE EXCEPTION '✗ Migration failed: condominio_id column not found';
    END IF;
END $$;
