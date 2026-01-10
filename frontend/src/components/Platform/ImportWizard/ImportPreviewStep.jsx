import { useState, useEffect } from 'react';
import { importExportAPI } from '../../../services/api';

/**
 * ImportPreviewStep - Step 3: Preview and Validation
 *
 * Shows:
 * - Statistics (total, valid, invalid rows)
 * - Preview table with first rows
 * - Validation errors
 * - Import options (skip errors, stop on error)
 */
function ImportPreviewStep({
  file,
  fieldMapping,
  moduleName,
  entityName,
  useTemplate,
  onBack,
  onNext
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [skipErrors, setSkipErrors] = useState(true);

  // Load preview data on mount
  useEffect(() => {
    loadPreviewData();
  }, []);

  const loadPreviewData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await importExportAPI.previewImport(
        moduleName,
        entityName,
        file,
        fieldMapping
      );

      setPreviewData(response.data);
    } catch (err) {
      console.error('Error loading preview:', err);
      setError(
        err.response?.data?.detail ||
        'Errore durante il caricamento dell\'anteprima'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (!previewData) return;

    onNext({
      ...previewData,
      skipErrors
    });
  };

  if (loading) {
    return (
      <div className="preview-step">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <div className="loading-text">Analisi e validazione dati in corso...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="preview-step">
        <div className="error-message">
          <div className="error-message-icon">⚠️</div>
          <div>
            <strong>Errore:</strong> {error}
          </div>
        </div>

        <div className="step-actions">
          <button className="btn-wizard btn-wizard-secondary" onClick={onBack}>
            ← Indietro
          </button>
          <button className="btn-wizard btn-wizard-primary" onClick={loadPreviewData}>
            Riprova
          </button>
        </div>
      </div>
    );
  }

  if (!previewData) {
    return null;
  }

  const { total_rows, valid_rows, invalid_rows, preview_data } = previewData;
  const hasErrors = invalid_rows > 0;
  const canProceed = valid_rows > 0;

  // Get displayed columns (from first row of preview data)
  const displayColumns = preview_data && preview_data.length > 0
    ? Object.keys(preview_data[0].mapped_data || {})
    : [];

  return (
    <div className="preview-step">
      {/* Statistics Cards */}
      <div className="preview-stats">
        <div className="preview-stat-card total">
          <div className="stat-icon">📊</div>
          <div className="stat-value">{total_rows}</div>
          <div className="stat-label">Righe Totali</div>
        </div>

        <div className="preview-stat-card valid">
          <div className="stat-icon">✓</div>
          <div className="stat-value">{valid_rows}</div>
          <div className="stat-label">Righe Valide</div>
        </div>

        <div className="preview-stat-card invalid">
          <div className="stat-icon">✗</div>
          <div className="stat-value">{invalid_rows}</div>
          <div className="stat-label">Righe con Errori</div>
        </div>
      </div>

      {/* Import Options */}
      {hasErrors && (
        <div className="preview-options">
          <div className="preview-option">
            <input
              type="checkbox"
              id="skip-errors"
              checked={skipErrors}
              onChange={(e) => setSkipErrors(e.target.checked)}
            />
            <label htmlFor="skip-errors">
              Importa solo le righe valide (salta gli errori)
            </label>
          </div>

          {!skipErrors && (
            <div style={{
              marginTop: 10,
              padding: '10px 15px',
              background: '#fff3cd',
              borderRadius: 6,
              fontSize: '0.9rem',
              color: '#856404'
            }}>
              L'importazione si interromperà alla prima riga con errori.
              Nessun dato verrà importato.
            </div>
          )}
        </div>
      )}

      {/* Preview Table */}
      <div>
        <h3 style={{ marginTop: 0, marginBottom: 15, color: '#2c3e50' }}>
          Anteprima Dati (prime {Math.min(preview_data.length, 20)} righe)
        </h3>

        <div className="preview-table-container">
          <table className="preview-table">
            <thead>
              <tr>
                <th style={{ width: 60 }}>Riga</th>
                <th style={{ width: 100 }}>Stato</th>
                {displayColumns.slice(0, 5).map(col => (
                  <th key={col}>{col}</th>
                ))}
                {displayColumns.length > 5 && (
                  <th>... ({displayColumns.length - 5} altri)</th>
                )}
              </tr>
            </thead>
            <tbody>
              {preview_data.slice(0, 20).map((row, index) => {
                const isValid = row.validation_status === 'valid';
                return (
                  <tr key={index} className={!isValid ? 'invalid' : ''}>
                    <td>{row.row_number}</td>
                    <td>
                      <span className={`row-status ${isValid ? 'valid' : 'invalid'}`}>
                        {isValid ? '✓ Valido' : '✗ Errore'}
                      </span>
                    </td>
                    {displayColumns.slice(0, 5).map(col => {
                      const value = row.mapped_data[col];
                      const displayValue = value === null || value === undefined || value === ''
                        ? <em style={{ color: '#adb5bd' }}>vuoto</em>
                        : String(value).length > 40
                          ? String(value).substring(0, 40) + '...'
                          : value;

                      return <td key={col}>{displayValue}</td>;
                    })}
                    {displayColumns.length > 5 && <td>...</td>}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Show validation errors for invalid rows */}
        {hasErrors && preview_data.some(r => r.validation_status === 'invalid') && (
          <div style={{ marginTop: 20 }}>
            <h4 style={{ color: '#dc3545', marginBottom: 10 }}>
              Errori di Validazione
            </h4>
            <div style={{ maxHeight: 200, overflowY: 'auto' }}>
              {preview_data
                .filter(r => r.validation_status === 'invalid')
                .slice(0, 10)
                .map((row, index) => (
                  <div key={index} style={{
                    padding: 12,
                    background: '#f8d7da',
                    borderRadius: 6,
                    marginBottom: 8,
                    borderLeft: '4px solid #dc3545'
                  }}>
                    <div style={{ fontWeight: 600, color: '#721c24', marginBottom: 6 }}>
                      Riga {row.row_number}
                    </div>
                    <div className="validation-errors">
                      {row.validation_errors.map((err, i) => (
                        <div key={i} className="validation-error">
                          {err}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              {preview_data.filter(r => r.validation_status === 'invalid').length > 10 && (
                <div style={{ textAlign: 'center', color: '#6c757d', fontStyle: 'italic', padding: 10 }}>
                  ... e altri {preview_data.filter(r => r.validation_status === 'invalid').length - 10} errori
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Warning if all rows are invalid */}
      {!canProceed && (
        <div className="error-message">
          <div className="error-message-icon">⚠️</div>
          <div>
            <strong>Attenzione:</strong> Nessuna riga valida da importare.
            Correggi gli errori nel file e riprova.
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="step-actions">
        <button
          className="btn-wizard btn-wizard-secondary"
          onClick={onBack}
        >
          ← {useTemplate ? 'Indietro' : 'Modifica Mappatura'}
        </button>
        <button
          className="btn-wizard btn-wizard-success"
          onClick={handleNext}
          disabled={!canProceed}
          title={!canProceed ? 'Nessuna riga valida da importare' : ''}
        >
          Importa {valid_rows} {valid_rows === 1 ? 'Riga' : 'Righe'} →
        </button>
      </div>
    </div>
  );
}

export default ImportPreviewStep;
