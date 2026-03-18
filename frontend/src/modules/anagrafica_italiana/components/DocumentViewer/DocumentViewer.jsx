import React, { useState, useEffect } from 'react';
import './DocumentViewer.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * DocumentViewer Component
 *
 * Multi-page document viewer with navigation, zoom, rotation, and metadata overlay.
 * Supports both legacy single-file and new multi-file documents.
 *
 * Props:
 * - documentoId: ID of the Documento to view
 * - onClose: Callback when user closes the viewer
 *
 * Features:
 * - Multi-page navigation (prev/next, keyboard shortcuts)
 * - Thumbnail sidebar for quick navigation
 * - Zoom controls (fit, 50%, 100%, 150%, 200%)
 * - Rotate controls (90° increments)
 * - Download original file
 * - Metadata overlay (toggleable)
 * - Responsive design
 */
const DocumentViewer = ({ documentoId, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [documento, setDocumento] = useState(null);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [zoom, setZoom] = useState('fit'); // 'fit', 50, 100, 150, 200
  const [rotation, setRotation] = useState(0); // 0, 90, 180, 270
  const [showMetadata, setShowMetadata] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(true);

  // Load document data
  useEffect(() => {
    loadDocument();
  }, [documentoId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!documento) return;

      switch (e.key) {
        case 'ArrowLeft':
          prevPage();
          break;
        case 'ArrowRight':
          nextPage();
          break;
        case 'Escape':
          onClose();
          break;
        case '+':
        case '=':
          zoomIn();
          break;
        case '-':
          zoomOut();
          break;
        case 'r':
        case 'R':
          rotateRight();
          break;
        case 'm':
        case 'M':
          toggleMetadata();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [documento, currentPageIndex, zoom, rotation]);

  const loadDocument = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/anagrafica/documenti/${documentoId}/view`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Errore nel caricamento del documento');
      }

      const data = await response.json();
      setDocumento(data);
      setCurrentPageIndex(0);
    } catch (err) {
      console.error('[DocumentViewer] Load error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const nextPage = () => {
    if (!documento || !documento.files) return;
    if (currentPageIndex < documento.files.length - 1) {
      setCurrentPageIndex(currentPageIndex + 1);
    }
  };

  const prevPage = () => {
    if (currentPageIndex > 0) {
      setCurrentPageIndex(currentPageIndex - 1);
    }
  };

  const goToPage = (index) => {
    setCurrentPageIndex(index);
  };

  const zoomIn = () => {
    const zoomLevels = ['fit', 50, 100, 150, 200];
    const currentIndex = zoomLevels.indexOf(zoom);
    if (currentIndex < zoomLevels.length - 1) {
      setZoom(zoomLevels[currentIndex + 1]);
    }
  };

  const zoomOut = () => {
    const zoomLevels = ['fit', 50, 100, 150, 200];
    const currentIndex = zoomLevels.indexOf(zoom);
    if (currentIndex > 0) {
      setZoom(zoomLevels[currentIndex - 1]);
    }
  };

  const rotateRight = () => {
    setRotation((rotation + 90) % 360);
  };

  const rotateLeft = () => {
    setRotation((rotation - 90 + 360) % 360);
  };

  const toggleMetadata = () => {
    setShowMetadata(!showMetadata);
  };

  const downloadOriginal = async () => {
    if (!documento || !documento.files || !documento.files[currentPageIndex]) return;

    const currentFile = documento.files[currentPageIndex];
    const fileId = currentFile.id || currentFile._legacy_id;

    if (!fileId) {
      // Legacy single-file: use old download endpoint
      window.open(`${API_BASE_URL}/anagrafica/documenti/${documentoId}/download`, '_blank');
      return;
    }

    // Multi-file: download specific file
    const token = localStorage.getItem('token');
    window.open(
      `${API_BASE_URL}/anagrafica/documenti/file/${fileId}/download-original?token=${token}`,
      '_blank'
    );
  };

  const getCurrentFileUrl = () => {
    if (!documento || !documento.files || !documento.files[currentPageIndex]) {
      return null;
    }

    const currentFile = documento.files[currentPageIndex];

    if (currentFile._legacy) {
      // Legacy single-file
      return `${API_BASE_URL}/anagrafica/documenti/${documentoId}/download`;
    }

    // Multi-file: use normalized view
    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/anagrafica/documenti/file/${currentFile.id}/view-normalized?token=${token}`;
  };

  const getThumbnailUrl = (file, index) => {
    if (file._legacy) {
      return `${API_BASE_URL}/anagrafica/documenti/${documentoId}/download`;
    }

    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/anagrafica/documenti/file/${file.id}/thumbnail?size=160&token=${token}`;
  };

  if (loading) {
    return (
      <div className="document-viewer-overlay">
        <div className="document-viewer-loading">
          <div className="spinner"></div>
          <p>Caricamento documento...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-viewer-overlay">
        <div className="document-viewer-error">
          <h3>Errore</h3>
          <p>{error}</p>
          <button onClick={onClose}>Chiudi</button>
        </div>
      </div>
    );
  }

  if (!documento) {
    return null;
  }

  const currentFile = documento.files[currentPageIndex];
  const totalPages = documento.files.length;

  return (
    <div className="document-viewer-overlay">
      <div className="document-viewer">
        {/* Header */}
        <div className="viewer-header">
          <div className="header-left">
            <h2>{documento.tipo_documento?.nome || 'Documento'}</h2>
            {currentFile && (
              <span className="file-name">{currentFile.nome_file}</span>
            )}
          </div>

          <div className="header-controls">
            {/* Zoom controls */}
            <div className="control-group">
              <button onClick={zoomOut} disabled={zoom === 'fit'} title="Zoom out (-)">
                🔍-
              </button>
              <select value={zoom} onChange={(e) => setZoom(e.target.value)}>
                <option value="fit">Adatta</option>
                <option value={50}>50%</option>
                <option value={100}>100%</option>
                <option value={150}>150%</option>
                <option value={200}>200%</option>
              </select>
              <button onClick={zoomIn} disabled={zoom === 200} title="Zoom in (+)">
                🔍+
              </button>
            </div>

            {/* Rotation controls */}
            <div className="control-group">
              <button onClick={rotateLeft} title="Ruota sinistra">
                ↶
              </button>
              <button onClick={rotateRight} title="Ruota destra (R)">
                ↷
              </button>
            </div>

            {/* Actions */}
            <div className="control-group">
              <button onClick={downloadOriginal} title="Scarica originale">
                ⬇ Download
              </button>
              <button
                onClick={toggleMetadata}
                className={showMetadata ? 'active' : ''}
                title="Mostra metadata (M)"
              >
                ℹ Info
              </button>
              <button
                onClick={() => setShowThumbnails(!showThumbnails)}
                className={showThumbnails ? 'active' : ''}
                title="Mostra miniature"
              >
                ☰ Pagine
              </button>
            </div>

            <button onClick={onClose} className="close-button" title="Chiudi (ESC)">
              ✕
            </button>
          </div>
        </div>

        {/* Main content */}
        <div className="viewer-content">
          {/* Thumbnail sidebar */}
          {showThumbnails && totalPages > 1 && (
            <div className="thumbnails-sidebar">
              <div className="thumbnails-list">
                {documento.files.map((file, index) => (
                  <div
                    key={index}
                    className={`thumbnail-item ${index === currentPageIndex ? 'active' : ''}`}
                    onClick={() => goToPage(index)}
                  >
                    <img
                      src={getThumbnailUrl(file, index)}
                      alt={`Pagina ${index + 1}`}
                    />
                    <div className="thumbnail-label">
                      <span className="page-number">{index + 1}</span>
                      {file.tipo_pagina && (
                        <span className="page-type">{file.tipo_pagina}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Main viewer */}
          <div className="viewer-main">
            <div className="image-container">
              <img
                src={getCurrentFileUrl()}
                alt={`Pagina ${currentPageIndex + 1}`}
                className={`document-image zoom-${zoom}`}
                style={{
                  transform: `rotate(${rotation}deg)`,
                }}
              />

              {/* Navigation arrows */}
              {totalPages > 1 && (
                <>
                  <button
                    className="nav-arrow nav-prev"
                    onClick={prevPage}
                    disabled={currentPageIndex === 0}
                    title="Pagina precedente (←)"
                  >
                    ‹
                  </button>
                  <button
                    className="nav-arrow nav-next"
                    onClick={nextPage}
                    disabled={currentPageIndex === totalPages - 1}
                    title="Pagina successiva (→)"
                  >
                    ›
                  </button>
                </>
              )}

              {/* Page indicator */}
              {totalPages > 1 && (
                <div className="page-indicator">
                  Pagina {currentPageIndex + 1} di {totalPages}
                </div>
              )}
            </div>

            {/* Metadata overlay */}
            {showMetadata && (
              <div className="metadata-overlay">
                <h3>Metadata Documento</h3>

                <div className="metadata-section">
                  <h4>Informazioni Generali</h4>
                  <div className="metadata-row">
                    <span className="label">Tipo:</span>
                    <span className="value">{documento.tipo_documento?.nome}</span>
                  </div>
                  {documento.descrizione && (
                    <div className="metadata-row">
                      <span className="label">Descrizione:</span>
                      <span className="value">{documento.descrizione}</span>
                    </div>
                  )}
                  {documento.data_scadenza && (
                    <div className="metadata-row">
                      <span className="label">Scadenza:</span>
                      <span className="value">{documento.data_scadenza}</span>
                    </div>
                  )}
                  {documento.note && (
                    <div className="metadata-row">
                      <span className="label">Note:</span>
                      <span className="value">{documento.note}</span>
                    </div>
                  )}
                </div>

                {currentFile && currentFile.is_parsed && (
                  <div className="metadata-section">
                    <h4>Dati Parsati (Pagina Corrente)</h4>
                    {currentFile.confidence_score && (
                      <div className="metadata-row">
                        <span className="label">Confidence:</span>
                        <span className="value">{currentFile.confidence_score}%</span>
                      </div>
                    )}
                    {currentFile.parsing_result && (
                      <pre className="parsing-result">
                        {JSON.stringify(currentFile.parsing_result, null, 2)}
                      </pre>
                    )}
                  </div>
                )}

                {documento.metadata_parsato && (
                  <div className="metadata-section">
                    <h4>Metadata Aggregato</h4>
                    {documento.confidence_score && (
                      <div className="metadata-row">
                        <span className="label">Confidence Media:</span>
                        <span className="value">{documento.confidence_score}%</span>
                      </div>
                    )}
                    <pre className="parsing-result">
                      {JSON.stringify(documento.metadata_parsato, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer with keyboard shortcuts help */}
        <div className="viewer-footer">
          <div className="shortcuts-help">
            <span>⌨ Shortcuts:</span>
            <span>← → Naviga</span>
            <span>+ - Zoom</span>
            <span>R Ruota</span>
            <span>M Metadata</span>
            <span>ESC Chiudi</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
