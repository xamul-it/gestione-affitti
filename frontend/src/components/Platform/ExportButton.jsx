import { useState } from 'react';
import { importExportAPI } from '../../services/api';
import { renderIcon } from '../Navigation/iconRegistry.jsx';
import './ExportButton.css';

/**
 * Reusable Export Button Component
 *
 * Platform-level component that can be used in any entity list
 * to enable data export functionality in CSV or Excel format.
 *
 * Features:
 * - Export to CSV or Excel
 * - Optional field selection
 * - Download template for import
 * - Tenant-aware (uses JWT token with tenant context)
 *
 * Usage:
 *   <ExportButton
 *     moduleName="immobili"
 *     entityName="UnitaImmobiliare"
 *     entityLabel="Unita Immobiliari"
 *   />
 */
function ExportButton({ moduleName, entityName, entityLabel, fields = null }) {
  const [showMenu, setShowMenu] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async (format) => {
    setLoading(true);
    setError(null);
    setShowMenu(false);

    try {
      const response = await importExportAPI.downloadExport(
        moduleName,
        entityName,
        format,
        fields
      );

      // Get filename from Content-Disposition header or generate one
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${entityName}_export.${format === 'excel' ? 'xlsx' : 'csv'}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      // Trigger browser download
      importExportAPI.triggerDownload(response.data, filename);
    } catch (err) {
      console.error('Export error:', err);
      setError(err.response?.data?.detail || 'Errore durante l\'export');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTemplate = async (includeSample = false) => {
    setLoading(true);
    setError(null);
    setShowMenu(false);

    try {
      const response = await importExportAPI.downloadTemplate(
        moduleName,
        entityName,
        includeSample
      );

      const filename = `${entityName}_import_template.csv`;
      importExportAPI.triggerDownload(response.data, filename);
    } catch (err) {
      console.error('Template download error:', err);
      setError(err.response?.data?.detail || 'Errore durante il download del template');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="export-button-container">
      <button
        className="btn-export"
        onClick={() => setShowMenu(!showMenu)}
        disabled={loading}
        title={`Esporta ${entityLabel || entityName}`}
      >
        {loading ? (
          <>
            <span className="export-spinner"></span>
            Esportazione...
          </>
        ) : (
          <>
            <span className="export-icon" aria-hidden="true">
              {renderIcon('download', { size: 16, className: 'export-icon-svg', fallbackClassName: 'export-icon-svg' })}
            </span>
            Esporta
          </>
        )}
      </button>

      {showMenu && !loading && (
        <>
          <div className="export-menu-overlay" onClick={() => setShowMenu(false)} />
          <div className="export-menu">
            <div className="export-menu-header">
              Esporta {entityLabel || entityName}
            </div>

            <div className="export-menu-section">
              <div className="export-menu-section-title">Formato Export</div>
              <button
                className="export-menu-item"
                onClick={() => handleExport('csv')}
              >
                <span className="export-menu-icon" aria-hidden="true">
                  {renderIcon('file-text', { size: 16, className: 'export-menu-icon-svg', fallbackClassName: 'export-menu-icon-svg' })}
                </span>
                <div className="export-menu-item-content">
                  <div className="export-menu-item-title">CSV</div>
                  <div className="export-menu-item-desc">Formato testo, apribile con Excel</div>
                </div>
              </button>
              <button
                className="export-menu-item"
                onClick={() => handleExport('excel')}
              >
                <span className="export-menu-icon" aria-hidden="true">
                  {renderIcon('chart-line', { size: 16, className: 'export-menu-icon-svg', fallbackClassName: 'export-menu-icon-svg' })}
                </span>
                <div className="export-menu-item-content">
                  <div className="export-menu-item-title">Excel (XLSX)</div>
                  <div className="export-menu-item-desc">Formato nativo Microsoft Excel</div>
                </div>
              </button>
            </div>

            <div className="export-menu-divider" />

            <div className="export-menu-section">
              <div className="export-menu-section-title">Template Import</div>
              <button
                className="export-menu-item"
                onClick={() => handleDownloadTemplate(false)}
              >
                <span className="export-menu-icon" aria-hidden="true">
                  {renderIcon('file-signature', { size: 16, className: 'export-menu-icon-svg', fallbackClassName: 'export-menu-icon-svg' })}
                </span>
                <div className="export-menu-item-content">
                  <div className="export-menu-item-title">Template Vuoto</div>
                  <div className="export-menu-item-desc">Solo intestazioni colonne</div>
                </div>
              </button>
              <button
                className="export-menu-item"
                onClick={() => handleDownloadTemplate(true)}
              >
                <span className="export-menu-icon" aria-hidden="true">
                  {renderIcon('list', { size: 16, className: 'export-menu-icon-svg', fallbackClassName: 'export-menu-icon-svg' })}
                </span>
                <div className="export-menu-item-content">
                  <div className="export-menu-item-title">Template con Esempio</div>
                  <div className="export-menu-item-desc">Include riga di esempio</div>
                </div>
              </button>
            </div>
          </div>
        </>
      )}

      {error && (
        <div className="export-error-toast">
          <span className="export-error-icon" aria-hidden="true">
            {renderIcon('alert-triangle', { size: 16, className: 'export-error-icon-svg', fallbackClassName: 'export-error-icon-svg' })}
          </span>
          {error}
          <button className="export-error-close" onClick={() => setError(null)}>×</button>
        </div>
      )}
    </div>
  );
}

export default ExportButton;
