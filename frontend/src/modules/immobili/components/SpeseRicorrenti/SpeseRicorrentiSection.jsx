import { useState, useEffect } from 'react';
import { speseRicorrentiAPI } from '../../services/immobiliAPI';
import SpesaRicorrenteForm from './SpesaRicorrenteForm';
import DuplicaSpesaModal from './DuplicaSpesaModal';
import './SpeseRicorrenti.css';

const RESPONSABILE_LABELS = {
  PROPRIETARIO: 'Proprietario',
  CONDUTTORE: 'Conduttore',
};

function formatImporto(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString('it-IT', { style: 'currency', currency: 'EUR' }) : value;
}

function formatData(value) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('it-IT');
}

/**
 * Embeddable section for recurring property expenses (IMU, TARI, utility
 * bills, ...). Pass exactly one of unitaImmobiliareId / condominioId,
 * matching the backend's own exactly-one-of-two constraint.
 */
function SpeseRicorrentiSection({ unitaImmobiliareId, condominioId }) {
  const [spese, setSpese] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [duplicandoSpesa, setDuplicandoSpesa] = useState(null);

  const targetId = unitaImmobiliareId || condominioId;

  useEffect(() => {
    if (targetId) {
      fetchSpese();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetId]);

  const fetchSpese = async () => {
    try {
      setLoading(true);
      const response = await speseRicorrentiAPI.getAll(unitaImmobiliareId || null, condominioId || null);
      setSpese(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle spese ricorrenti');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSegnaPagato = async (spesa) => {
    if (!window.confirm(`Segnare "${spesa.tipo_spesa} ${spesa.periodo}" come pagata oggi?`)) return;
    try {
      await speseRicorrentiAPI.segnaPagato(spesa.id, {});
      fetchSpese();
    } catch (err) {
      alert('Errore nel segnare la spesa come pagata');
      console.error(err);
    }
  };

  const handleDelete = async (spesa) => {
    if (!window.confirm(`Eliminare la spesa "${spesa.tipo_spesa} ${spesa.periodo}"?`)) return;
    try {
      await speseRicorrentiAPI.delete(spesa.id);
      fetchSpese();
    } catch (err) {
      alert('Errore nell\'eliminazione della spesa');
      console.error(err);
    }
  };

  const handleFormClose = (saved) => {
    setShowForm(false);
    if (saved) fetchSpese();
  };

  const handleDuplicaClose = (saved) => {
    setDuplicandoSpesa(null);
    if (saved) fetchSpese();
  };

  if (!targetId) {
    return (
      <div className="spese-ricorrenti-section">
        <p className="info-message">Salva prima l'entità per poter gestire le spese ricorrenti</p>
      </div>
    );
  }

  return (
    <div className="spese-ricorrenti-section">
      <div className="spese-ricorrenti-header">
        <h3>Spese Ricorrenti (IMU, TARI, utenze)</h3>
        <button type="button" onClick={() => setShowForm(true)} className="btn btn-sm btn-primary">
          + Nuova Spesa
        </button>
      </div>

      {showForm && (
        <SpesaRicorrenteForm
          unitaImmobiliareId={unitaImmobiliareId}
          condominioId={condominioId}
          onClose={handleFormClose}
        />
      )}
      {duplicandoSpesa && (
        <DuplicaSpesaModal spesa={duplicandoSpesa} onClose={handleDuplicaClose} />
      )}

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Caricamento...</div>
      ) : spese.length === 0 ? (
        <p className="no-data">Nessuna spesa ricorrente registrata</p>
      ) : (
        <div className="spese-ricorrenti-list">
          {spese.map((spesa) => (
            <div key={spesa.id} className={`spesa-ricorrente-card ${spesa.pagato ? 'pagato' : ''}`}>
              <div className="spesa-ricorrente-info">
                <div className="spesa-ricorrente-titolo">
                  {spesa.tipo_spesa} {spesa.periodo} {spesa.rata ? `(${spesa.rata})` : ''}
                </div>
                <div className="spesa-ricorrente-meta">
                  <span className="badge badge-info">{RESPONSABILE_LABELS[spesa.responsabile] || spesa.responsabile}</span>
                  <span className="spesa-ricorrente-importo">{formatImporto(spesa.importo)}</span>
                  <span className="spesa-ricorrente-scadenza">Scadenza: {formatData(spesa.data_scadenza)}</span>
                  {spesa.pagato ? (
                    <span className="badge badge-success">Pagato il {formatData(spesa.data_pagamento)}</span>
                  ) : (
                    <span className="badge badge-warning">Da pagare</span>
                  )}
                </div>
                {spesa.note && <div className="spesa-ricorrente-note">{spesa.note}</div>}
              </div>
              <div className="spesa-ricorrente-actions">
                {!spesa.pagato && (
                  <button onClick={() => handleSegnaPagato(spesa)} className="btn btn-sm btn-secondary" title="Segna come pagato">
                    ✓ Pagato
                  </button>
                )}
                <button onClick={() => setDuplicandoSpesa(spesa)} className="btn btn-sm btn-secondary" title="Duplica per periodo successivo">
                  ⧉ Duplica
                </button>
                <button onClick={() => handleDelete(spesa)} className="btn btn-sm btn-danger" title="Elimina">
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SpeseRicorrentiSection;
