import { useState, useEffect } from 'react';
import { scadenzeAPI } from '../../services/affittiBreviAPI';
import ScadenzaDetail from './ScadenzaDetail';
import './Scadenze.css';

function ScadenzeList() {
  const [scadenze, setScadenze] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedScadenza, setSelectedScadenza] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  // Filters
  const [filterTipo, setFilterTipo] = useState('all');
  const [filterStato, setFilterStato] = useState('all');
  const [filterView, setFilterView] = useState('all'); // all, upcoming, overdue

  useEffect(() => {
    fetchScadenze();
  }, [filterView]);

  const fetchScadenze = async () => {
    try {
      setLoading(true);
      let response;

      if (filterView === 'upcoming') {
        response = await scadenzeAPI.getUpcoming(7); // Next 7 days
      } else if (filterView === 'overdue') {
        response = await scadenzeAPI.getOverdue();
      } else {
        response = await scadenzeAPI.getAll();
      }

      setScadenze(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle scadenze');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (id, note = null) => {
    try {
      await scadenzeAPI.markCompleted(id, note);
      fetchScadenze();
    } catch (err) {
      setError('Errore nel completamento della scadenza');
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa scadenza?')) {
      try {
        await scadenzeAPI.delete(id);
        fetchScadenze();
      } catch (err) {
        setError('Errore nell\'eliminazione della scadenza');
        console.error(err);
      }
    }
  };

  const handleViewDetail = (scadenza) => {
    setSelectedScadenza(scadenza);
    setShowDetail(true);
  };

  const handleCloseDetail = () => {
    setShowDetail(false);
    setSelectedScadenza(null);
    fetchScadenze();
  };

  const getTipoLabel = (tipo) => {
    const labels = {
      COMUNICAZIONE_POLIZIA: 'Comunicazione Polizia',
      REPORT_ISTAT: 'Report ISTAT',
      ALTRO: 'Altro'
    };
    return labels[tipo] || tipo;
  };

  const getStatoLabel = (scadenza) => {
    if (scadenza.completata) return 'Completata';

    const dataScadenza = new Date(scadenza.data_scadenza);
    const oggi = new Date();
    const setteDa = new Date();
    setteDa.setDate(oggi.getDate() + 7);

    if (dataScadenza < oggi) return 'Scaduta';
    if (dataScadenza <= setteDa) return 'In Scadenza';
    return 'Da Fare';
  };

  const getStatoBadgeClass = (scadenza) => {
    if (scadenza.completata) return 'badge-success';

    const stato = getStatoLabel(scadenza);
    const classes = {
      'Scaduta': 'badge-danger',
      'In Scadenza': 'badge-warning',
      'Da Fare': 'badge-info'
    };
    return classes[stato] || 'badge-secondary';
  };

  const getTipoBadgeClass = (tipo) => {
    const classes = {
      COMUNICAZIONE_POLIZIA: 'tipo-badge-polizia',
      REPORT_ISTAT: 'tipo-badge-istat',
      ALTRO: 'tipo-badge-altro'
    };
    return classes[tipo] || 'tipo-badge-altro';
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredScadenze = scadenze.filter(scadenza => {
    if (filterTipo !== 'all' && scadenza.tipo_scadenza !== filterTipo) return false;
    if (filterStato === 'completata' && !scadenza.completata) return false;
    if (filterStato === 'attiva' && scadenza.completata) return false;
    return true;
  });

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="scadenze-container">
      <div className="header">
        <h1>Scadenze</h1>
        <div className="header-actions">
          <button onClick={fetchScadenze} className="btn btn-secondary">
            🔄 Aggiorna
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-group">
          <label>Vista:</label>
          <select value={filterView} onChange={(e) => setFilterView(e.target.value)}>
            <option value="all">Tutte</option>
            <option value="upcoming">In Scadenza (7 giorni)</option>
            <option value="overdue">Scadute</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Tipo:</label>
          <select value={filterTipo} onChange={(e) => setFilterTipo(e.target.value)}>
            <option value="all">Tutti</option>
            <option value="COMUNICAZIONE_POLIZIA">Comunicazione Polizia</option>
            <option value="REPORT_ISTAT">Report ISTAT</option>
            <option value="ALTRO">Altro</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Stato:</label>
          <select value={filterStato} onChange={(e) => setFilterStato(e.target.value)}>
            <option value="all">Tutti</option>
            <option value="attiva">Attive</option>
            <option value="completata">Completate</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card card-danger">
          <div className="card-number">{scadenze.filter(s => !s.completata && new Date(s.data_scadenza) < new Date()).length}</div>
          <div className="card-label">Scadute</div>
        </div>
        <div className="summary-card card-warning">
          <div className="card-number">
            {scadenze.filter(s => {
              if (s.completata) return false;
              const dataScadenza = new Date(s.data_scadenza);
              const oggi = new Date();
              const setteDa = new Date();
              setteDa.setDate(oggi.getDate() + 7);
              return dataScadenza >= oggi && dataScadenza <= setteDa;
            }).length}
          </div>
          <div className="card-label">In Scadenza (7 giorni)</div>
        </div>
        <div className="summary-card card-success">
          <div className="card-number">{scadenze.filter(s => s.completata).length}</div>
          <div className="card-label">Completate</div>
        </div>
      </div>

      {/* Detail Modal */}
      {showDetail && selectedScadenza && (
        <ScadenzaDetail
          scadenza={selectedScadenza}
          onClose={handleCloseDetail}
          onComplete={handleComplete}
        />
      )}

      {/* Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Titolo</th>
              <th>Data Scadenza</th>
              <th>Stato</th>
              <th>Prenotazione</th>
              <th>Ricorrente</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {filteredScadenze.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center">Nessuna scadenza trovata</td>
              </tr>
            ) : (
              filteredScadenze.map((scadenza) => (
                <tr key={scadenza.id} className={scadenza.completata ? 'row-completed' : ''}>
                  <td>
                    <span className={`tipo-badge ${getTipoBadgeClass(scadenza.tipo_scadenza)}`}>
                      {getTipoLabel(scadenza.tipo_scadenza)}
                    </span>
                  </td>
                  <td>
                    <strong>{scadenza.titolo}</strong>
                    {scadenza.descrizione && (
                      <div className="descrizione-preview">{scadenza.descrizione.substring(0, 50)}...</div>
                    )}
                  </td>
                  <td>
                    {formatDateTime(scadenza.data_scadenza)}
                  </td>
                  <td>
                    <span className={`badge ${getStatoBadgeClass(scadenza)}`}>
                      {getStatoLabel(scadenza)}
                    </span>
                  </td>
                  <td>
                    {scadenza.prenotazione_id ? (
                      <a href={`#/prenotazioni/${scadenza.prenotazione_id}`}>
                        #{scadenza.prenotazione_id}
                      </a>
                    ) : '-'}
                  </td>
                  <td>
                    {scadenza.ricorrente ? '🔁 Sì' : '-'}
                  </td>
                  <td>
                    <button
                      onClick={() => handleViewDetail(scadenza)}
                      className="btn btn-sm btn-info"
                      title="Dettagli"
                    >
                      👁️ Dettagli
                    </button>
                    {!scadenza.completata && (
                      <>
                        <button
                          onClick={() => handleComplete(scadenza.id)}
                          className="btn btn-sm btn-success"
                          title="Completa"
                        >
                          ✓
                        </button>
                        <button
                          onClick={() => handleDelete(scadenza.id)}
                          className="btn btn-sm btn-danger"
                          title="Elimina"
                        >
                          🗑️
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <p>Totale: {filteredScadenze.length} scadenze</p>
      </div>
    </div>
  );
}

export default ScadenzeList;
