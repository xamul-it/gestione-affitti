import { useState, useEffect } from 'react';
import {
  getRuoliAziendaBySoggetto,
  deleteRuoloAzienda,
  getSoggettiAnagrafici,
  createRuoloAzienda,
  updateRuoloAzienda
} from '../../services/anagraficaAPI';
import RuoloAziendaForm from './RuoloAziendaForm';
import './RuoliAzienda.css';

/**
 * Lista centralizzata di tutte le associazioni ruolo persona-azienda
 */
export default function RuoliAziendaList() {
  const [ruoli, setRuoli] = useState([]);
  const [soggetti, setSoggetti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [filterPersona, setFilterPersona] = useState('');
  const [filterAzienda, setFilterAzienda] = useState('');
  const [filterRuolo, setFilterRuolo] = useState('');
  const [filterAttiviOnly, setFilterAttiviOnly] = useState(true);

  // Edit modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [ruoloToEdit, setRuoloToEdit] = useState(null);
  const [soggettoCorrente, setSoggettoCorrente] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      // Carica tutti i soggetti per dropdown filtri
      const soggettiData = await getSoggettiAnagrafici();
      setSoggetti(soggettiData);

      // Carica tutti i ruoli
      // Nota: questo è un workaround - l'endpoint ottimale sarebbe GET /api/v1/anagrafica/ruoli-azienda/
      // Per ora carichiamo ruoli per ogni soggetto (non ottimale ma funziona)
      await loadAllRuoli(soggettiData);

    } catch (err) {
      console.error('Error loading data:', err);
      setError('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const loadAllRuoli = async (soggettiList) => {
    try {
      // Carica ruoli per ogni soggetto e unisci i risultati
      const allRuoli = [];
      const seenIds = new Set();

      for (const soggetto of soggettiList) {
        try {
          const data = await getRuoliAziendaBySoggetto(soggetto.id, { attivi_only: false });

          // Aggiungi ruoli come persona (con persona_fisica_id)
          if (data.come_persona) {
            data.come_persona.forEach(ruolo => {
              if (!seenIds.has(ruolo.id)) {
                allRuoli.push({
                  ...ruolo,
                  persona_fisica: soggetto,
                  tipo: 'come_persona'
                });
                seenIds.add(ruolo.id);
              }
            });
          }

          // Aggiungi ruoli come azienda (con persona_giuridica_id)
          if (data.come_azienda) {
            data.come_azienda.forEach(ruolo => {
              if (!seenIds.has(ruolo.id)) {
                allRuoli.push({
                  ...ruolo,
                  persona_giuridica: soggetto,
                  tipo: 'come_azienda'
                });
                seenIds.add(ruolo.id);
              }
            });
          }
        } catch (err) {
          // Skip soggetti senza ruoli
          console.debug(`Soggetto ${soggetto.id} has no roles`);
        }
      }

      setRuoli(allRuoli);
    } catch (err) {
      console.error('Error loading all ruoli:', err);
    }
  };

  const handleDelete = async (ruoloId) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo ruolo?')) {
      return;
    }

    try {
      await deleteRuoloAzienda(ruoloId);
      setRuoli(prev => prev.filter(r => r.id !== ruoloId));
    } catch (err) {
      console.error('Error deleting ruolo:', err);
      alert('Errore nell\'eliminazione del ruolo');
    }
  };

  const handleEdit = (ruolo) => {
    // Prepara dati per modal edit
    const soggetto = ruolo.tipo === 'come_persona' ? ruolo.persona_fisica : ruolo.persona_giuridica;
    setSoggettoCorrente(soggetto);
    setRuoloToEdit(ruolo);
    setShowEditModal(true);
  };

  const handleSaveRuolo = async (dataToSave, ruoloId) => {
    try {
      if (ruoloId) {
        // Update existing
        await updateRuoloAzienda(ruoloId, dataToSave);
      } else {
        // Create new
        await createRuoloAzienda(dataToSave);
      }

      setShowEditModal(false);
      setRuoloToEdit(null);
      await loadData();
    } catch (err) {
      console.error('Error saving ruolo:', err);
      throw err; // Re-throw per far gestire l'errore al form
    }
  };

  // Computed: persone fisiche e giuridiche separate per filtri
  const personeFisiche = soggetti.filter(s => s.tipo_soggetto === 'PERSONA_FISICA');
  const personeGiuridiche = soggetti.filter(s => s.tipo_soggetto === 'PERSONA_GIURIDICA');

  // Filter ruoli in base ai criteri
  const ruoliFiltrati = ruoli.filter(ruolo => {
    // Filtro persona
    if (filterPersona && ruolo.persona_fisica_id !== parseInt(filterPersona)) {
      return false;
    }

    // Filtro azienda
    if (filterAzienda && ruolo.persona_giuridica_id !== parseInt(filterAzienda)) {
      return false;
    }

    // Filtro ruolo (nome) - cerca sia in ruolo_tipo_nome che in ruolo
    if (filterRuolo) {
      const ruoloDisplayName = ruolo.ruolo_tipo_nome || ruolo.ruolo || '';
      if (!ruoloDisplayName.toLowerCase().includes(filterRuolo.toLowerCase())) {
        return false;
      }
    }

    // Filtro attivi
    if (filterAttiviOnly) {
      const oggi = new Date().toISOString().split('T')[0];
      if (ruolo.data_fine && ruolo.data_fine < oggi) {
        return false;
      }
    }

    return true;
  });

  const getSoggettoNome = (soggetto) => {
    if (!soggetto) return '(Sconosciuto)';
    if (soggetto.tipo_soggetto === 'PERSONA_FISICA') {
      return `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim();
    }
    return soggetto.ragione_sociale || '';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  const isAttivo = (ruolo) => {
    if (!ruolo.data_fine) return true;
    const oggi = new Date().toISOString().split('T')[0];
    return ruolo.data_fine >= oggi;
  };

  if (loading) {
    return (
      <div className="ruoli-azienda-container">
        <div className="loading">Caricamento...</div>
      </div>
    );
  }

  return (
    <div className="ruoli-azienda-container">
      <div className="page-header">
        <h1>Ruoli Azienda</h1>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => loadData()}>
            🔄 Ricarica
          </button>
        </div>
      </div>

      {error && (
        <div className="error">{error}</div>
      )}

      {/* Filtri */}
      <div className="filters">
        <div className="filter-group">
          <label htmlFor="filterPersona">Persona:</label>
          <select
            id="filterPersona"
            value={filterPersona}
            onChange={(e) => setFilterPersona(e.target.value)}
            className="form-control"
          >
            <option value="">-- Tutte --</option>
            {personeFisiche.map(p => (
              <option key={p.id} value={p.id}>{getSoggettoNome(p)}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filterAzienda">Azienda:</label>
          <select
            id="filterAzienda"
            value={filterAzienda}
            onChange={(e) => setFilterAzienda(e.target.value)}
            className="form-control"
          >
            <option value="">-- Tutte --</option>
            {personeGiuridiche.map(p => (
              <option key={p.id} value={p.id}>{getSoggettoNome(p)}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filterRuolo">Ruolo:</label>
          <input
            id="filterRuolo"
            type="text"
            value={filterRuolo}
            onChange={(e) => setFilterRuolo(e.target.value)}
            placeholder="Cerca ruolo..."
            className="form-control"
          />
        </div>

        <div className="filter-checkbox">
          <input
            type="checkbox"
            id="filterAttivi"
            checked={filterAttiviOnly}
            onChange={(e) => setFilterAttiviOnly(e.target.checked)}
          />
          <label htmlFor="filterAttivi">Solo attivi</label>
        </div>

        {(filterPersona || filterAzienda || filterRuolo) && (
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              setFilterPersona('');
              setFilterAzienda('');
              setFilterRuolo('');
            }}
          >
            ✖ Pulisci Filtri
          </button>
        )}
      </div>

      {/* Statistiche */}
      <div className="stats-bar">
        <span>Totale: {ruoliFiltrati.length} ruoli</span>
        <span>•</span>
        <span>Attivi: {ruoliFiltrati.filter(r => isAttivo(r)).length}</span>
        <span>•</span>
        <span>Cessati: {ruoliFiltrati.filter(r => !isAttivo(r)).length}</span>
      </div>

      {/* Tabella */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Persona</th>
              <th>Azienda</th>
              <th>Ruolo</th>
              <th>Data Inizio</th>
              <th>Data Fine</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {ruoliFiltrati.length === 0 ? (
              <tr>
                <td colSpan="7" className="no-data">
                  Nessun ruolo trovato
                </td>
              </tr>
            ) : (
              ruoliFiltrati.map(ruolo => (
                <tr key={ruolo.id}>
                  <td>
                    {getSoggettoNome(ruolo.persona_fisica)}
                    {ruolo.persona_fisica?.codice_fiscale && (
                      <div className="text-muted">{ruolo.persona_fisica.codice_fiscale}</div>
                    )}
                  </td>
                  <td>
                    {getSoggettoNome(ruolo.persona_giuridica)}
                    {ruolo.persona_giuridica?.codice_fiscale && (
                      <div className="text-muted">{ruolo.persona_giuridica.codice_fiscale}</div>
                    )}
                  </td>
                  <td>
                    <span className="ruolo-badge">
                      <strong>{ruolo.ruolo_tipo_nome || ruolo.ruolo || '(Non specificato)'}</strong>
                    </span>
                    {!ruolo.ruolo_tipo_id && ruolo.ruolo && (
                      <small className="text-warning" title="Ruolo personalizzato non collegato ai domini">
                        {' '}⚠ Custom
                      </small>
                    )}
                  </td>
                  <td>{formatDate(ruolo.data_inizio)}</td>
                  <td>{formatDate(ruolo.data_fine)}</td>
                  <td>
                    {isAttivo(ruolo) ? (
                      <span className="badge badge-success">Attivo</span>
                    ) : (
                      <span className="badge badge-secondary">Cessato</span>
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleEdit(ruolo)}
                        title="Modifica"
                      >
                        ✏️
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(ruolo.id)}
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

      {/* Modal Edit */}
      {showEditModal && soggettoCorrente && (
        <RuoloAziendaForm
          soggettoCorrente={soggettoCorrente}
          ruoloToEdit={ruoloToEdit}
          onClose={() => {
            setShowEditModal(false);
            setRuoloToEdit(null);
          }}
          onSave={handleSaveRuolo}
        />
      )}
    </div>
  );
}
