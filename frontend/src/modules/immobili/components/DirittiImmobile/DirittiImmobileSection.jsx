import { useState, useEffect } from 'react';
import { dirittiImmobileAPI, proprietariAPI } from '../../services/immobiliAPI';
import { getSoggettoById } from '../../../anagrafica_italiana/services/anagraficaAPI';
import DirittoForm from './DirittoForm';
import './DirittiImmobile.css';

const TIPO_DIRITTO_LABELS = {
  PROPRIETARIO: 'Proprietario',
  COMPROPRIETARIO: 'Comproprietario',
  USUFRUTTUARIO: 'Usufruttuario',
  NUDA_PROPRIETA: 'Nuda Proprietà',
  ALTRO: 'Altro'
};

function DirittiImmobileSection({ immobileId }) {
  const [diritti, setDiritti] = useState([]);
  const [proprietari, setProprietari] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (immobileId) {
      fetchDiritti();
    }
  }, [immobileId]);

  const fetchDiritti = async () => {
    try {
      setLoading(true);
      const response = await dirittiImmobileAPI.getByImmobile(immobileId);
      setDiritti(response.data);

      // Carica i dati dei proprietari, risolvendo il nome tramite il soggetto anagrafico collegato
      const proprietariIds = [...new Set(response.data.map(d => d.proprietario_id))];
      const proprietariData = {};
      for (const id of proprietariIds) {
        let propResp;
        try {
          propResp = await proprietariAPI.getById(id);
        } catch (err) {
          console.error(`Errore caricamento proprietario ${id}:`, err);
          continue;
        }
        try {
          const soggetto = await getSoggettoById(propResp.data.soggetto_id);
          const nome = soggetto.ragione_sociale || [soggetto.nome, soggetto.cognome].filter(Boolean).join(' ');
          proprietariData[id] = {
            ...propResp.data,
            nomeVisualizzato: nome || `Soggetto #${propResp.data.soggetto_id}`,
            codiceFiscale: soggetto.codice_fiscale,
          };
        } catch (err) {
          console.error(`Errore caricamento soggetto ${propResp.data.soggetto_id} per proprietario ${id}:`, err);
          proprietariData[id] = { ...propResp.data, nomeVisualizzato: `Soggetto #${propResp.data.soggetto_id}`, codiceFiscale: null };
        }
      }
      setProprietari(proprietariData);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei diritti');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo diritto?')) {
      try {
        await dirittiImmobileAPI.delete(id);
        fetchDiritti();
      } catch (err) {
        alert('Errore nell\'eliminazione del diritto');
        console.error(err);
      }
    }
  };

  const handleFormComplete = () => {
    setShowForm(false);
    fetchDiritti();
  };

  if (!immobileId) {
    return (
      <div className="diritti-section">
        <p className="info-message">Salva prima l'immobile per poter gestire i diritti di proprietà</p>
      </div>
    );
  }

  return (
    <div className="diritti-section">
      <div className="diritti-header">
        <h3>Diritti di Proprietà</h3>
        <button onClick={() => setShowForm(true)} className="btn btn-sm btn-primary">
          + Aggiungi Diritto
        </button>
      </div>

      {showForm && (
        <DirittoForm
          immobileId={immobileId}
          onClose={() => setShowForm(false)}
          onComplete={handleFormComplete}
        />
      )}

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Caricamento...</div>
      ) : diritti.length === 0 ? (
        <p className="no-data">Nessun diritto registrato</p>
      ) : (
        <div className="diritti-list">
          {diritti.map((diritto) => {
            const proprietario = proprietari[diritto.proprietario_id];
            return (
              <div key={diritto.id} className="diritto-card">
                <div className="diritto-info">
                  <div className="diritto-nome">
                    {proprietario ? proprietario.nomeVisualizzato : 'Caricamento...'}
                    {proprietario && proprietario.codiceFiscale && (
                      <span className="diritto-cf"> - CF: {proprietario.codiceFiscale}</span>
                    )}
                  </div>
                  <div className="diritto-meta">
                    <span className="badge badge-info">
                      {TIPO_DIRITTO_LABELS[diritto.tipo_diritto] || diritto.tipo_diritto}
                    </span>
                    {diritto.quota_percentuale && (
                      <span className="diritto-quota">Quota: {diritto.quota_percentuale}%</span>
                    )}
                    {diritto.data_inizio && (
                      <span className="diritto-date">Dal: {new Date(diritto.data_inizio).toLocaleDateString('it-IT')}</span>
                    )}
                  </div>
                  {diritto.note && (
                    <div className="diritto-note">{diritto.note}</div>
                  )}
                </div>
                <div className="diritto-actions">
                  <button
                    onClick={() => handleDelete(diritto.id)}
                    className="btn btn-sm btn-danger"
                    title="Elimina"
                  >
                    🗑
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default DirittiImmobileSection;
