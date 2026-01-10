import { useState, useEffect } from 'react';
import { importExportAPI } from '../../../services/api';

/**
 * ImportResultsStep - Step 4: Import Execution and Results
 *
 * Executes the import and displays:
 * - Success/error statistics
 * - Detailed error list
 * - Options to start over or close
 */
function ImportResultsStep({
  file,
  fieldMapping,
  previewData,
  moduleName,
  entityName,
  useTemplate,
  onComplete,
  onStartOver,
  onClose
}) {
  const [importing, setImporting] = useState(true);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Execute import on mount
  useEffect(() => {
    executeImport();
  }, []);

  const executeImport = async () => {
    setImporting(true);
    setError(null);

    try {
      const response = await importExportAPI.importWithMapping(
        moduleName,
        entityName,
        file,
        fieldMapping,
        previewData.skipErrors || true,
        false, // saveConfig handled in mapping step
        null
      );

      const importResults = response.data;
      setResults(importResults);
      onComplete(importResults);
    } catch (err) {
      console.error('Error during import:', err);
      setError(
        err.response?.data?.detail ||
        'Errore durante l\'importazione dei dati'
      );
    } finally {
      setImporting(false);
    }
  };

  if (importing) {
    return (
      <div className="results-step">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div className="loading-text">Importazione in corso...</div>
          <div style={{ marginTop: 10, fontSize: '0.9rem', color: '#6c757d' }}>
            Questo potrebbe richiedere alcuni istanti
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-step">
        <div className="results-summary error">
          <div className="results-icon">❌</div>
          <div className="results-content">
            <h3>Importazione Fallita</h3>
            <p style={{ margin: '10px 0 0 0', color: '#721c24' }}>
              {error}
            </p>
          </div>
        </div>

        <div className="step-actions">
          <button className="btn-wizard btn-wizard-secondary" onClick={onClose}>
            Chiudi
          </button>
          <button className="btn-wizard btn-wizard-primary" onClick={executeImport}>
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  const { success, total_rows, imported, errors, error_details } = results;
  const hasErrors = errors > 0;
  const isPartialSuccess = imported > 0 && hasErrors;
  const isFullSuccess = imported > 0 && !hasErrors;
  const isCompleteFailure = imported === 0 && hasErrors;

  // Determine summary style
  let summaryClass = 'results-summary ';
  if (isFullSuccess) summaryClass += 'success';
  else if (isPartialSuccess) summaryClass += 'partial';
  else summaryClass += 'error';

  return (
    <div className="results-step">
      {/* Results Summary */}
      <div className={summaryClass}>
        <div className="results-icon">
          {isFullSuccess && '✅'}
          {isPartialSuccess && '⚠️'}
          {isCompleteFailure && '❌'}
        </div>
        <div className="results-content">
          <h3>
            {isFullSuccess && 'Importazione Completata con Successo'}
            {isPartialSuccess && 'Importazione Completata con Avvisi'}
            {isCompleteFailure && 'Importazione Fallita'}
          </h3>
          <div className="results-stats">
            <div className="results-stat">
              <span className="results-stat-value success">{imported}</span>
              <span className="results-stat-label">Importate</span>
            </div>
            {hasErrors && (
              <div className="results-stat">
                <span className="results-stat-value error">{errors}</span>
                <span className="results-stat-label">Errori</span>
              </div>
            )}
            <div className="results-stat">
              <span className="results-stat-value">{total_rows}</span>
              <span className="results-stat-label">Totali</span>
            </div>
          </div>
        </div>
      </div>

      {/* Success Message */}
      {isFullSuccess && (
        <div style={{
          background: '#d4edda',
          padding: '15px 20px',
          borderRadius: 8,
          border: '2px solid #28a745',
          color: '#155724',
          fontSize: '0.95rem'
        }}>
          <strong>Ottimo!</strong> Tutte le {imported} righe sono state importate correttamente.
        </div>
      )}

      {/* Partial Success Message */}
      {isPartialSuccess && (
        <div style={{
          background: '#fff3cd',
          padding: '15px 20px',
          borderRadius: 8,
          border: '2px solid #ffc107',
          color: '#856404',
          fontSize: '0.95rem'
        }}>
          <strong>Importazione parziale:</strong> {imported} righe importate con successo,
          ma {errors} righe hanno generato errori e sono state saltate.
        </div>
      )}

      {/* Error Details */}
      {hasErrors && error_details && error_details.length > 0 && (
        <div className="error-details">
          <h4>Dettagli Errori ({Math.min(error_details.length, 20)} su {error_details.length})</h4>
          <div className="error-list">
            {error_details.slice(0, 20).map((errorItem, index) => (
              <div key={index} className="error-item">
                <div className="error-row-number">
                  Riga {errorItem.row || index + 1}
                </div>
                <div className="error-message-text">
                  {errorItem.error || errorItem.message || 'Errore sconosciuto'}
                </div>
                {errorItem.data && (
                  <div className="error-data">
                    {Object.entries(errorItem.data).slice(0, 5).map(([key, value]) => (
                      <span key={key} className="error-data-field">
                        {key}: {String(value).length > 30
                          ? String(value).substring(0, 30) + '...'
                          : value || '(vuoto)'}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {error_details.length > 20 && (
              <div className="error-item more">
                ... e altri {error_details.length - 20} errori
              </div>
            )}
          </div>
        </div>
      )}

      {/* Download Error Report (future enhancement) */}
      {hasErrors && error_details && error_details.length > 10 && (
        <div style={{
          textAlign: 'center',
          padding: '15px',
          background: '#f8f9fa',
          borderRadius: 8,
          color: '#6c757d',
          fontSize: '0.9rem'
        }}>
          💡 Suggerimento: Correggi gli errori nel file originale e importa nuovamente
        </div>
      )}

      {/* Action Buttons */}
      <div className="step-actions">
        <button className="btn-wizard btn-wizard-secondary" onClick={onClose}>
          Chiudi
        </button>
        <button className="btn-wizard btn-wizard-primary" onClick={onStartOver}>
          Importa un Altro File
        </button>
      </div>
    </div>
  );
}

export default ImportResultsStep;
