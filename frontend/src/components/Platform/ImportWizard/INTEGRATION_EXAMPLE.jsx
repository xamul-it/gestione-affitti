/**
 * INTEGRATION EXAMPLE
 *
 * This file shows how to integrate ImportWizard into an existing entity list component.
 * Copy this pattern to add import functionality to any entity.
 */

import { useState } from 'react';
import { ImportWizard } from './components/Platform/ImportWizard';

/**
 * Example: Integrating ImportWizard into UnitaImmobiliari list
 */
function UnitaImmobiliariList() {
  const [unitaImmobiliari, setUnitaImmobiliari] = useState([]);
  const [showImportWizard, setShowImportWizard] = useState(false);
  const [loading, setLoading] = useState(false);

  // Your existing data fetching function
  const fetchUnitaImmobiliari = async () => {
    setLoading(true);
    try {
      const response = await unitaImmobiliariAPI.getAll();
      setUnitaImmobiliari(response.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle import completion
  const handleImportComplete = (results) => {
    console.log('Import completed:', results);

    // Show success message
    if (results.success && results.imported > 0) {
      alert(`Importazione completata! ${results.imported} righe importate con successo.`);
    } else if (results.errors > 0) {
      alert(`Importazione completata con avvisi. ${results.imported} importate, ${results.errors} errori.`);
    }

    // Close wizard
    setShowImportWizard(false);

    // Refresh data list
    fetchUnitaImmobiliari();
  };

  // Handle import cancel
  const handleImportCancel = () => {
    setShowImportWizard(false);
  };

  return (
    <div className="unita-immobiliari-container">
      {/* Header with Actions */}
      <div className="page-header">
        <h1>Unità Immobiliari</h1>
        <div className="actions">
          {/* Existing buttons */}
          <button className="btn-primary" onClick={() => {}}>
            + Nuova Unità
          </button>

          {/* NEW: Import Button */}
          <button
            className="btn-import"
            onClick={() => setShowImportWizard(true)}
            title="Importa da CSV/Excel"
          >
            📥 Importa
          </button>

          {/* Optional: Export button */}
          <button className="btn-export" onClick={() => {}}>
            📤 Esporta
          </button>
        </div>
      </div>

      {/* Your existing list/table */}
      <div className="list-content">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <table>
            {/* Your existing table content */}
          </table>
        )}
      </div>

      {/* NEW: Import Wizard Modal */}
      {showImportWizard && (
        <ImportWizard
          moduleName="affitti_lungo"
          entityName="UnitaImmobiliare"
          entityLabel="Unità Immobiliari"
          onComplete={handleImportComplete}
          onCancel={handleImportCancel}
        />
      )}
    </div>
  );
}

export default UnitaImmobiliariList;

/**
 * ALTERNATIVE: Using ImportButton component
 *
 * For a simpler integration, use the existing ImportButton component:
 */
import ImportButton from './components/Platform/ImportButton';

function AlternativeIntegration() {
  const [data, setData] = useState([]);

  const fetchData = async () => {
    // Your fetch logic
  };

  return (
    <div>
      <div className="page-header">
        <h1>My Entity</h1>
        <div className="actions">
          {/* Simple import button */}
          <ImportButton
            moduleName="affitti_lungo"
            entityName="UnitaImmobiliare"
            entityLabel="Unità Immobiliari"
            onImportComplete={() => fetchData()}
          />
        </div>
      </div>

      {/* Your list */}
    </div>
  );
}

/**
 * CSS for Import Button (add to your component CSS)
 */
/*
.btn-import {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-import:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
*/

/**
 * ENTITY-SPECIFIC CONFIGURATION
 *
 * For each entity, you need to specify:
 *
 * 1. moduleName: The backend module (e.g., "affitti_lungo")
 * 2. entityName: The entity class name (e.g., "UnitaImmobiliare")
 * 3. entityLabel: User-friendly name (e.g., "Unità Immobiliari")
 *
 * Examples for different entities:
 */

// Affittuari (Tenants)
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Affittuario"
  entityLabel="Affittuari"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>

// Contratti (Contracts)
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Contratto"
  entityLabel="Contratti"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>

// Spese (Expenses)
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Spesa"
  entityLabel="Spese"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>

// Proprietari (Owners)
<ImportWizard
  moduleName="affitti_lungo"
  entityName="Proprietario"
  entityLabel="Proprietari"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>

/**
 * CUSTOMIZATION OPTIONS
 *
 * You can customize the wizard behavior:
 */

// 1. Custom success handler with notifications
const handleImportComplete = (results) => {
  if (results.imported > 0) {
    // Show toast notification
    showNotification({
      type: 'success',
      message: `${results.imported} records imported successfully`
    });

    // Update specific state
    setLastImportDate(new Date());
    setImportCount(prev => prev + results.imported);
  }

  // Close and refresh
  setShowImportWizard(false);
  fetchData();
};

// 2. Conditional import button visibility
const canImport = userHasPermission('import') && !isReadOnly;

{canImport && (
  <ImportButton
    moduleName={moduleName}
    entityName={entityName}
    entityLabel={entityLabel}
    onImportComplete={handleComplete}
  />
)}

// 3. Pre-configured import (e.g., from a specific template)
const handleQuickImport = () => {
  // Open wizard with specific mode pre-selected
  setShowImportWizard(true);
  // Note: Current implementation doesn't support this,
  // but you could extend ImportUploadStep to accept initialMode prop
};

/**
 * ERROR HANDLING
 */

const handleImportComplete = (results) => {
  // Check for errors
  if (results.errors > 0) {
    const shouldRetry = confirm(
      `Import completed with ${results.errors} errors. ` +
      `${results.imported} records were imported successfully. ` +
      `Do you want to review the errors?`
    );

    if (shouldRetry) {
      // Keep wizard open to show error details
      return;
    }
  }

  // Success - close and refresh
  setShowImportWizard(false);
  fetchData();
};

/**
 * ANALYTICS/TRACKING
 */

const handleImportComplete = (results) => {
  // Track import event for analytics
  trackEvent('import_completed', {
    entity: entityName,
    rows_imported: results.imported,
    rows_failed: results.errors,
    total_rows: results.total_rows,
    success_rate: (results.imported / results.total_rows * 100).toFixed(2)
  });

  // Continue with normal flow
  setShowImportWizard(false);
  fetchData();
};
