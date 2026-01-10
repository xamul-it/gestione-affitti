import { useState } from 'react';
import { ImportWizard } from './ImportWizard';
import './ImportButton.css';

/**
 * Reusable Import Button Component
 *
 * Platform-level component that can be used in any entity list
 * to enable advanced CSV import functionality with field mapping.
 *
 * Features:
 * - Intelligent field mapping with fuzzy matching
 * - Data validation before import
 * - Save and reuse configurations
 * - Three import modes: template, generic CSV, saved config
 *
 * Usage:
 *   <ImportButton
 *     moduleName="affitti_lungo"
 *     entityName="UnitaImmobiliare"
 *     entityLabel="Unità Immobiliari"
 *     onImportComplete={() => fetchData()}
 *   />
 */
function ImportButton({ moduleName, entityName, entityLabel, onImportComplete }) {
  const [showWizard, setShowWizard] = useState(false);

  const handleImportComplete = (result) => {
    setShowWizard(false);
    if (onImportComplete) {
      onImportComplete(result);
    }
  };

  return (
    <>
      <button
        className="btn-import"
        onClick={() => setShowWizard(true)}
        title={`Importa ${entityLabel || entityName} da CSV`}
      >
        📥 Importa
      </button>

      {showWizard && (
        <ImportWizard
          moduleName={moduleName}
          entityName={entityName}
          entityLabel={entityLabel || entityName}
          onComplete={handleImportComplete}
          onCancel={() => setShowWizard(false)}
        />
      )}
    </>
  );
}

export default ImportButton;
