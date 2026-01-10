-- Migration: Add Scadenzario (Universal Deadline/Reminder System)
-- Date: 2025-12-10
-- Description: Creates platform-level tables for deadline tracking and reminders
--              Supports entity attachment (polymorphic) and standalone TODOs
--              Includes multi-recipient support and full audit logging

BEGIN;

-- =============================================================================
-- TABLE: scadenze
-- Main deadline/reminder table with polymorphic entity association
-- =============================================================================
CREATE TABLE IF NOT EXISTS scadenze (
    id SERIAL PRIMARY KEY,

    -- Entity polymorphic association (NULL for standalone TODOs)
    modulo VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id INTEGER,

    -- Scadenza details
    titolo VARCHAR(200) NOT NULL,
    descrizione TEXT,
    data_scadenza DATE NOT NULL,

    -- Classification
    priorita VARCHAR(20) NOT NULL DEFAULT 'MEDIA' CHECK (priorita IN ('BASSA', 'MEDIA', 'ALTA')),
    stato VARCHAR(20) NOT NULL DEFAULT 'ATTIVA' CHECK (stato IN ('ATTIVA', 'SCADUTA', 'COMPLETATA', 'POSTICIPATA', 'CANCELLATA')),

    -- Creator tracking
    creato_da INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    creato_il TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Modification tracking
    modificato_il TIMESTAMP,

    -- Completion tracking
    completato_da INTEGER REFERENCES users(id) ON DELETE SET NULL,
    completato_il TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scadenze_entity ON scadenze(modulo, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_scadenze_stato ON scadenze(stato);
CREATE INDEX IF NOT EXISTS idx_scadenze_data ON scadenze(data_scadenza);
CREATE INDEX IF NOT EXISTS idx_scadenze_stato_data ON scadenze(stato, data_scadenza);
CREATE INDEX IF NOT EXISTS idx_scadenze_creator ON scadenze(creato_da);

-- Add comments for documentation
COMMENT ON TABLE scadenze IS 'Universal deadline/reminder system - supports entity attachment and standalone TODOs';
COMMENT ON COLUMN scadenze.modulo IS 'Module name (e.g., affitti_lungo, immobili) - NULL for TODO';
COMMENT ON COLUMN scadenze.entity_type IS 'Entity type (e.g., contratto, immobile) - NULL for TODO';
COMMENT ON COLUMN scadenze.entity_id IS 'Entity ID - NULL for TODO';
COMMENT ON COLUMN scadenze.titolo IS 'Short title/summary';
COMMENT ON COLUMN scadenze.descrizione IS 'Detailed description/notes';
COMMENT ON COLUMN scadenze.data_scadenza IS 'Due date';
COMMENT ON COLUMN scadenze.priorita IS 'Priority level: BASSA, MEDIA, ALTA';
COMMENT ON COLUMN scadenze.stato IS 'Current state: ATTIVA, SCADUTA, COMPLETATA, POSTICIPATA, CANCELLATA';

-- =============================================================================
-- TABLE: scadenza_destinatari
-- Multi-recipient support with notification tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS scadenza_destinatari (
    id SERIAL PRIMARY KEY,

    -- Foreign keys
    scadenza_id INTEGER NOT NULL REFERENCES scadenze(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification tracking
    notificato BOOLEAN NOT NULL DEFAULT FALSE,
    notificato_il TIMESTAMP,

    -- Prevent duplicate recipients
    CONSTRAINT uq_scadenza_user UNIQUE (scadenza_id, user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_destinatari_scadenza ON scadenza_destinatari(scadenza_id);
CREATE INDEX IF NOT EXISTS idx_destinatari_user ON scadenza_destinatari(user_id);
CREATE INDEX IF NOT EXISTS idx_destinatari_notificato ON scadenza_destinatari(notificato);

-- Add comments for documentation
COMMENT ON TABLE scadenza_destinatari IS 'Multi-recipient support for scadenze with notification tracking';
COMMENT ON COLUMN scadenza_destinatari.notificato IS 'Has user been notified?';
COMMENT ON COLUMN scadenza_destinatari.notificato_il IS 'When was notification sent?';

-- =============================================================================
-- TABLE: scadenza_log
-- Full audit trail for all scadenza changes
-- =============================================================================
CREATE TABLE IF NOT EXISTS scadenza_log (
    id SERIAL PRIMARY KEY,

    -- Foreign keys
    scadenza_id INTEGER NOT NULL REFERENCES scadenze(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Action details
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    azione VARCHAR(50) NOT NULL,

    -- Field change details (optional)
    campo_modificato VARCHAR(100),
    valore_precedente TEXT,
    valore_nuovo TEXT,

    -- Optional notes
    note TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_log_scadenza ON scadenza_log(scadenza_id);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON scadenza_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_azione ON scadenza_log(azione);

-- Add comments for documentation
COMMENT ON TABLE scadenza_log IS 'Audit trail for all scadenza changes and actions';
COMMENT ON COLUMN scadenza_log.azione IS 'Action type: CREATA, MODIFICATA, STATO_CAMBIATO, COMPLETATA, POSTICIPATA, CANCELLATA, etc.';
COMMENT ON COLUMN scadenza_log.campo_modificato IS 'Which field was changed (if applicable)';
COMMENT ON COLUMN scadenza_log.valore_precedente IS 'Value before change';
COMMENT ON COLUMN scadenza_log.valore_nuovo IS 'Value after change';

COMMIT;

-- =============================================================================
-- Migration Success
-- =============================================================================
-- You can verify the migration with:
--   SELECT COUNT(*) FROM scadenze;
--   SELECT COUNT(*) FROM scadenza_destinatari;
--   SELECT COUNT(*) FROM scadenza_log;
