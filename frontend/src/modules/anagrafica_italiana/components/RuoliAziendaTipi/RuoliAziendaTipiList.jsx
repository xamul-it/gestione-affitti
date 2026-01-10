import { useState, useEffect } from 'react';
import {
  getRuoliAziendaTipi,
  deleteRuoloAziendaTipo,
  mergeRuoliAziendaTipi
} from '../../services/anagraficaAPI';
import RuoloAziendaTipoForm from './RuoloAziendaTipoForm';
import './RuoliAziendaTipi.css';

function RuoliAziendaTipiList() {
  const [ruoli, setRuoli] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedRuolo, setSelectedRuolo] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [showOnlyActive, setShowOnlyActive] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Merge state
  const [showMerge, setShowMerge] = useState(false);
  const [mergeSource, setMergeSource] = useState('');
  const [mergeTarget, setMergeTarget] = useState('');

  useEffect(() => {
    fetchRuoli();
  }, [showOnlyActive, searchTerm]);

  const fetchRuoli = async () => {
    try {
      setLoading(true);
      const params = {
        attivi_solo: showOnlyActive,
        search: searchTerm || null
      };
      const data = await getRuoliAziendaTipi(params);
      setRuoli(data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei ruoli azienda');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (ruolo) => {
    setSelectedRuolo(ruolo);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    const ruolo = ruoli.find(r => r.id === id);
    if (window.confirm(`Sei sicuro di voler eliminare il ruolo "${ruolo.nome}"?\n\nATTENZIONE: Non è possibile eliminare un ruolo se è utilizzato in associazioni esistenti. Usa la funzione di merge per unificare ruoli simili prima di eliminare.`)) {
      try {
        await deleteRuoloAziendaTipo(id);
        fetchRuoli();
      } catch (err) {
        if (err.response && err.response.data && err.response.data.detail) {
          alert(err.response.data.detail);
        } else {
          alert('Errore nell\'eliminazione del ruolo');
        }
        console.error(err);
      }
    }
  };

  const handleMerge = async () => {
    if (!mergeSource || !mergeTarget) {
      alert('Seleziona sia il ruolo di origine che quello di destinazione');
      return;
    }

    if (mergeSource === mergeTarget) {
      alert('I ruoli devono essere diversi');
      return;
    }

    const sourceRuolo = ruoli.find(r => r.id === parseInt(mergeSource));
    const targetRuolo = ruoli.find(r => r.id === parseInt(mergeTarget));

    if (window.confirm(
      `Vuoi unificare "${sourceRuolo.nome}" in "${targetRuolo.nome}"?\n\n` +
      `Tutte le associazioni che usano "${sourceRuolo.nome}" verranno spostate su "${targetRuolo.nome}", ` +
      `poi "${sourceRuolo.nome}" verrà eliminato.\n\n` +
      `Questa operazione non può essere annullata.`
    )) {
      try {
        const result = await mergeRuoliAziendaTipi(parseInt(mergeSource), parseInt(mergeTarget));
        alert(
          `Merge completato con successo!\n\n` +
          `"${result.source_nome}" è stato unificato in "${result.target_nome}".\n` +
          `Associazioni aggiornate: ${result.associazioni_aggiornate}`
        );
        setShowMerge(false);
        setMergeSource('');
        setMergeTarget('');
        fetchRuoli();
      } catch (err) {
        if (err.response && err.response.data && err.response.data.detail) {
          alert(`Errore nel merge: ${err.response.data.detail}`);
        } else {
          alert('Errore nel merge dei ruoli');
        }
        console.error(err);
      }
    }
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setSelectedRuolo(null);
    fetchRuoli();
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>Ruoli Azienda</h1>
        <div className="header-actions">
          <button onClick={() => setShowMerge(!showMerge)} className="btn btn-secondary">
            {showMerge ? 'Annulla Merge' : 'Unifica Ruoli'}
          </button>
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            + Nuovo Ruolo
          </button>
        </div>
      </div>

      <div className="filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Cerca per nome..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-control"
          />
        </div>
        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={showOnlyActive}
            onChange={(e) => setShowOnlyActive(e.target.checked)}
          />
          Mostra solo attivi
        </label>
      </div>

      {showMerge && (
        <div className="merge-panel">
          <h3>Unifica Ruoli Duplicati</h3>
          <p>Seleziona due ruoli per unificarli. Il ruolo di origine verrà eliminato e tutte le sue associazioni verranno spostate sul ruolo di destinazione.</p>
          <div className="merge-selects">
            <div className="form-group">
              <label>Ruolo di Origine (verrà eliminato):</label>
              <select
                value={mergeSource}
                onChange={(e) => setMergeSource(e.target.value)}
                className="form-control"
              >
                <option value="">-- Seleziona --</option>
                {ruoli.map(ruolo => (
                  <option key={ruolo.id} value={ruolo.id}>
                    {ruolo.nome} {!ruolo.attivo && '(inattivo)'}
                  </option>
                ))}
              </select>
            </div>
            <div className="merge-arrow">→</div>
            <div className="form-group">
              <label>Ruolo di Destinazione (sarà mantenuto):</label>
              <select
                value={mergeTarget}
                onChange={(e) => setMergeTarget(e.target.value)}
                className="form-control"
              >
                <option value="">-- Seleziona --</option>
                {ruoli.map(ruolo => (
                  <option key={ruolo.id} value={ruolo.id}>
                    {ruolo.nome} {!ruolo.attivo && '(inattivo)'}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={handleMerge}
            className="btn btn-primary"
            disabled={!mergeSource || !mergeTarget}
          >
            Unifica Ruoli
          </button>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="loading">Caricamento...</div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Descrizione</th>
                <th>Attivo</th>
                <th>Creato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {ruoli.length === 0 ? (
                <tr>
                  <td colSpan="5" className="no-data">
                    Nessun ruolo trovato
                  </td>
                </tr>
              ) : (
                ruoli.map((ruolo) => (
                  <tr key={ruolo.id}>
                    <td><strong>{ruolo.nome}</strong></td>
                    <td>{ruolo.descrizione || '-'}</td>
                    <td>
                      <span className={`badge ${ruolo.attivo ? 'badge-success' : 'badge-secondary'}`}>
                        {ruolo.attivo ? 'Sì' : 'No'}
                      </span>
                    </td>
                    <td>
                      {new Date(ruolo.created_at).toLocaleDateString('it-IT')}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          onClick={() => handleEdit(ruolo)}
                          className="btn btn-sm btn-secondary"
                          title="Modifica"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDelete(ruolo.id)}
                          className="btn btn-sm btn-danger"
                          title="Elimina"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <RuoloAziendaTipoForm
          ruolo={selectedRuolo}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
}

export default RuoliAziendaTipiList;
