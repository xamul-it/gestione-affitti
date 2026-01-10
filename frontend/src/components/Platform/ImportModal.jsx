import { useState, useRef } from 'react';
import { importExportAPI } from '../../services/api';
import { formatApiError } from '../../utils/errorHandling';
import './ImportModal.css';

/**
 * Import Modal Component
 *
 * Provides UI for importing data from CSV files.
 * Handles file selection, upload, progress tracking, and results display.
 */
function ImportModal({ moduleName, entityName, entityLabel, onClose, onComplete }) {
  const [file, setFile] = useState(null);
  const [skipErrors, setSkipErrors] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [downloadingTemplate, setDownloadingTemplate] = useState(false);

  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Per favore seleziona un file CSV');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile);
      setError(null);
      setResult(null);
    } else {
      setError('Per favore carica un file CSV');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleImport = async () => {
    if (!file) {
      setError('Seleziona un file da importare');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await importExportAPI.import(
        moduleName,
        entityName,
        file,
        skipErrors
      );

      setResult(response.data);

      // Auto-close on success after showing result
      if (response.data.success && response.data.errors === 0) {
        setTimeout(() => {
          if (onComplete) {
            onComplete(response.data);
          }
        }, 2000);
      }
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    setDownloadingTemplate(true);
    setError(null);

    try {
      const response = await importExportAPI.getTemplate(moduleName, entityName, true);

      // Create blob and download
      const blob = new Blob([response.data.content], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = response.data.filename || `${entityName}_template.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setDownloadingTemplate(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content import-modal">
        <div className="modal-header">
          <h2>📥 Importa {entityLabel}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Instructions */}
          <div className="import-instructions">
            <h3>Come funziona l'importazione</h3>
            <ol>
              <li>Scarica il <strong>template CSV</strong> con le colonne corrette</li>
              <li>Compila il file CSV con i tuoi dati</li>
              <li>Carica il file compilato qui sotto</li>
              <li>Verifica i risultati dell'importazione</li>
            </ol>
          </div>

          {/* Template Download */}
          <div className="template-section">
            <button
              className="btn-download-template"
              onClick={handleDownloadTemplate}
              disabled={downloadingTemplate}
            >
              {downloadingTemplate ? (
                <>⏳ Download...</>
              ) : (
                <>📄 Scarica Template CSV</>
              )}
            </button>
            <p className="template-help">
              Il template include tutte le colonne necessarie con un esempio di riga
            </p>
          </div>

          {/* File Upload Area */}
          {!result && (
            <div
              className={`upload-area ${file ? 'has-file' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />

              {file ? (
                <div className="file-selected">
                  <div className="file-icon">📄</div>
                  <div className="file-info">
                    <div className="file-name">{file.name}</div>
                    <div className="file-size">
                      {(file.size / 1024).toFixed(2)} KB
                    </div>
                  </div>
                  <button
                    className="btn-remove-file"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReset();
                    }}
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div className="upload-prompt">
                  <div className="upload-icon">📤</div>
                  <p className="upload-text">
                    <strong>Clicca per selezionare</strong> o trascina qui il file CSV
                  </p>
                  <p className="upload-hint">Solo file .csv</p>
                </div>
              )}
            </div>
          )}

          {/* Options */}
          {!result && (
            <div className="import-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={skipErrors}
                  onChange={(e) => setSkipErrors(e.target.checked)}
                />
                <span>Salta righe con errori e continua l'importazione</span>
              </label>
              <p className="option-help">
                Se disattivato, l'importazione si interrompe al primo errore
              </p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Import Results */}
          {result && (
            <div className="import-results">
              <div className={`result-summary ${result.success ? 'success' : 'error'}`}>
                <div className="result-icon">
                  {result.success ? '✅' : '⚠️'}
                </div>
                <div className="result-content">
                  <h3>
                    {result.success ? 'Importazione Completata' : 'Importazione Completata con Errori'}
                  </h3>
                  <div className="result-stats">
                    <div className="stat">
                      <span className="stat-value">{result.total_rows}</span>
                      <span className="stat-label">Righe Totali</span>
                    </div>
                    <div className="stat success">
                      <span className="stat-value">{result.imported}</span>
                      <span className="stat-label">Importate</span>
                    </div>
                    <div className="stat error">
                      <span className="stat-value">{result.errors}</span>
                      <span className="stat-label">Errori</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Error Details */}
              {result.error_details && result.error_details.length > 0 && (
                <div className="error-details">
                  <h4>Dettagli Errori</h4>
                  <div className="error-list">
                    {result.error_details.slice(0, 10).map((err, index) => (
                      <div key={index} className="error-item">
                        <div className="error-row">
                          <strong>Riga {err.row}:</strong>
                        </div>
                        <div className="error-message-detail">{err.error}</div>
                        {err.data && (
                          <div className="error-data">
                            {Object.entries(err.data).slice(0, 3).map(([key, value]) => (
                              <span key={key} className="data-field">
                                {key}: {value}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    {result.error_details.length > 10 && (
                      <div className="error-item more">
                        ... e altri {result.error_details.length - 10} errori
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Actions after import */}
              <div className="result-actions">
                <button className="btn-secondary" onClick={handleReset}>
                  Importa un altro file
                </button>
                {result.success && result.errors === 0 && (
                  <button
                    className="btn-primary"
                    onClick={() => onComplete && onComplete(result)}
                  >
                    Chiudi
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {!result && (
          <div className="modal-footer">
            <button className="btn-secondary" onClick={onClose}>
              Annulla
            </button>
            <button
              className="btn-primary"
              onClick={handleImport}
              disabled={!file || uploading}
            >
              {uploading ? (
                <>⏳ Importazione in corso...</>
              ) : (
                <>📥 Importa Dati</>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImportModal;
