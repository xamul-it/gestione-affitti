import React, { useState } from 'react';
import './SimilarityMatchDialog.css';

/**
 * SimilarityMatchDialog Component
 *
 * Shows list of similar anagrafiche when creating from document.
 * User can choose to:
 * - Add document to existing anagrafica
 * - Create new anagrafica
 *
 * Props:
 * - parsedData: Object with codice_fiscale, nome, cognome, data_nascita
 * - candidates: Array of {soggetto_id, similarity_score, match_reason, soggetto}
 * - onSelectExisting: (soggetto_id) => void
 * - onCreateNew: () => void
 * - onClose: () => void
 */
const SimilarityMatchDialog = ({
  parsedData,
  candidates = [],
  onSelectExisting,
  onCreateNew,
  onClose
}) => {
  const [selectedId, setSelectedId] = useState(null);

  const getScoreColor = (score) => {
    if (score >= 1.0) return '#10b981'; // green-500
    if (score >= 0.85) return '#22c55e'; // green-400
    if (score >= 0.70) return '#f59e0b'; // amber-500
    return '#f97316'; // orange-500
  };

  const getScoreBadge = (score) => {
    if (score >= 1.0) return 'Identico';
    if (score >= 0.85) return 'Molto Simile';
    if (score >= 0.70) return 'Simile';
    return 'Possibile';
  };

  const handleConfirm = () => {
    if (selectedId) {
      onSelectExisting(selectedId);
    }
  };

  if (candidates.length === 0) {
    return null;
  }

  return (
    <div className="similarity-match-overlay">
      <div className="similarity-match-dialog">
        {/* Header */}
        <div className="dialog-header">
          <h2>Anagrafica Esistente Rilevata</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        {/* Content */}
        <div className="dialog-content">
          <div className="info-section">
            <p className="info-message">
              Abbiamo trovato <strong>{candidates.length}</strong> anagrafica{candidates.length > 1 ? 'he' : ''} simile{candidates.length > 1 ? 'i' : ''} ai dati del documento:
            </p>
            <div className="parsed-data-preview">
              <div className="data-row">
                <span className="label">Nome:</span>
                <span className="value">{parsedData.nome} {parsedData.cognome}</span>
              </div>
              {parsedData.codice_fiscale && (
                <div className="data-row">
                  <span className="label">CF:</span>
                  <span className="value">{parsedData.codice_fiscale}</span>
                </div>
              )}
              {parsedData.data_nascita && (
                <div className="data-row">
                  <span className="label">Data di nascita:</span>
                  <span className="value">{parsedData.data_nascita}</span>
                </div>
              )}
            </div>
          </div>

          {/* Candidates List */}
          <div className="candidates-section">
            <h3>Seleziona l'anagrafica corrispondente:</h3>
            <div className="candidates-list">
              {candidates.map((candidate) => (
                <div
                  key={candidate.soggetto_id}
                  className={`candidate-card ${selectedId === candidate.soggetto_id ? 'selected' : ''}`}
                  onClick={() => setSelectedId(candidate.soggetto_id)}
                >
                  {/* Score Badge */}
                  <div className="score-section">
                    <div
                      className="score-circle"
                      style={{ backgroundColor: getScoreColor(candidate.similarity_score) }}
                    >
                      <span className="score-value">
                        {Math.round(candidate.similarity_score * 100)}%
                      </span>
                    </div>
                    <span className="score-badge">
                      {getScoreBadge(candidate.similarity_score)}
                    </span>
                  </div>

                  {/* Soggetto Info */}
                  <div className="soggetto-info">
                    <h4 className="soggetto-name">
                      {candidate.soggetto.nome} {candidate.soggetto.cognome}
                      {candidate.soggetto.ragione_sociale && ` - ${candidate.soggetto.ragione_sociale}`}
                    </h4>

                    <div className="soggetto-details">
                      {candidate.soggetto.codice_fiscale && (
                        <div className="detail-row">
                          <span className="detail-label">CF:</span>
                          <span className="detail-value">{candidate.soggetto.codice_fiscale}</span>
                        </div>
                      )}
                      {candidate.soggetto.email && (
                        <div className="detail-row">
                          <span className="detail-label">Email:</span>
                          <span className="detail-value">{candidate.soggetto.email}</span>
                        </div>
                      )}
                      {candidate.soggetto.telefono && (
                        <div className="detail-row">
                          <span className="detail-label">Tel:</span>
                          <span className="detail-value">{candidate.soggetto.telefono}</span>
                        </div>
                      )}
                      {candidate.soggetto.data_nascita && (
                        <div className="detail-row">
                          <span className="detail-label">Nato il:</span>
                          <span className="detail-value">{candidate.soggetto.data_nascita}</span>
                        </div>
                      )}
                    </div>

                    <p className="match-reason">{candidate.match_reason}</p>
                  </div>

                  {/* Selection Indicator */}
                  <div className="selection-indicator">
                    {selectedId === candidate.soggetto_id && (
                      <span className="checkmark">✓</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="dialog-footer">
          <button
            className="btn-secondary"
            onClick={onCreateNew}
          >
            No, Crea Nuova Anagrafica
          </button>
          <button
            className="btn-primary"
            onClick={handleConfirm}
            disabled={!selectedId}
          >
            {selectedId
              ? 'Aggiungi Documento a Questa Anagrafica'
              : 'Seleziona un\'anagrafica'
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimilarityMatchDialog;
