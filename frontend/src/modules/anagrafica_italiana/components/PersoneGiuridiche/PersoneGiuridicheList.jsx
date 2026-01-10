import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSoggettiAnagrafici, deleteSoggetto } from '../../services/anagraficaAPI';
import '../SoggettiAnagrafici/SoggettiAnagraficiList.css';

/**
 * PersoneGiuridicheList - Lista persone giuridiche
 *
 * Vista ottimizzata per persone giuridiche (aziende, società)
 * Mostra campi specifici: Ragione Sociale, P.IVA, CF aziendale
 */
function PersoneGiuridicheList() {
  const [aziende, setAziende] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attiviSolo, setAttiviSolo] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadAziende();
  }, [attiviSolo]);

  const loadAziende = async () => {
    try {
      setLoading(true);
      setError(null);
      // Carica solo PERSONA_GIURIDICA
      const data = await getSoggettiAnagrafici({
        attivi_solo: attiviSolo,
        limit: 1000
      });
      // Filtra solo persone giuridiche
      const personeGiuridiche = data.filter(s => s.tipo_soggetto === 'PERSONA_GIURIDICA');
      setAziende(personeGiuridiche);
    } catch (err) {
      console.error('Error loading persone giuridiche:', err);
      setError('Errore nel caricamento delle persone giuridiche');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Sei sicuro di voler eliminare questa azienda/ente?')) {
      return;
    }

    try {
      await deleteSoggetto(id);
      loadAziende();
    } catch (err) {
      console.error('Error deleting azienda:', err);
      alert('Errore nell\'eliminazione dell\'azienda/ente');
    }
  };

  // Filtra per ricerca
  const filteredAziende = aziende.filter(azienda => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      (azienda.ragione_sociale || '').toLowerCase().includes(searchLower) ||
      (azienda.codice_fiscale || '').toLowerCase().includes(searchLower) ||
      (azienda.partita_iva || '').toLowerCase().includes(searchLower) ||
      (azienda.email || '').toLowerCase().includes(searchLower)
    );
  });

  if (loading) {
    return (
      <div className="soggetti-list-container">
        <div className="loading">Caricamento persone giuridiche...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="soggetti-list-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="soggetti-list-container">
      <div className="soggetti-list-header">
        <h1>🏢 Persone Giuridiche</h1>
        <div className="header-actions">
          <input
            type="text"
            placeholder="🔍 Cerca per ragione sociale, P.IVA, CF..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={attiviSolo}
              onChange={(e) => setAttiviSolo(e.target.checked)}
            />
            <span>Solo attivi</span>
          </label>
          <Link to="/anagrafiche/persone-giuridiche/nuovo" className="btn btn-primary">
            + Nuova Persona Giuridica
          </Link>
        </div>
      </div>

      {filteredAziende.length === 0 ? (
        <div className="empty-state">
          <p>{searchTerm ? 'Nessuna azienda/ente trovato con i criteri di ricerca' : 'Nessuna persona giuridica trovata'}</p>
          {!searchTerm && (
            <Link to="/anagrafiche/persone-giuridiche/nuovo" className="btn btn-primary">
              Crea la prima persona giuridica
            </Link>
          )}
        </div>
      ) : (
        <div className="soggetti-table-wrapper">
          <table className="soggetti-table">
            <thead>
              <tr>
                <th>Ragione Sociale</th>
                <th>Partita IVA</th>
                <th>Codice Fiscale</th>
                <th>Email</th>
                <th>Telefono</th>
                <th>Città</th>
                <th>PEC</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filteredAziende.map((azienda) => (
                <tr key={azienda.id} className={!azienda.attivo ? 'inactive' : ''}>
                  <td>
                    <Link to={`/anagrafiche/persone-giuridiche/${azienda.id}`} className="soggetto-name">
                      {azienda.ragione_sociale || '(Non specificato)'}
                    </Link>
                  </td>
                  <td>
                    <code className="piva-badge">{azienda.partita_iva || '-'}</code>
                  </td>
                  <td>
                    <code className="cf-badge">{azienda.codice_fiscale || '-'}</code>
                  </td>
                  <td>{azienda.email || '-'}</td>
                  <td>{azienda.telefono || azienda.cellulare || '-'}</td>
                  <td>{azienda.citta || '-'}</td>
                  <td>{azienda.pec || '-'}</td>
                  <td>
                    <span className={`status-badge ${azienda.attivo ? 'active' : 'inactive'}`}>
                      {azienda.attivo ? 'Attivo' : 'Inattivo'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Link
                        to={`/anagrafiche/persone-giuridiche/${azienda.id}`}
                        className="btn btn-sm btn-secondary"
                        title="Visualizza"
                      >
                        👁️
                      </Link>
                      <Link
                        to={`/anagrafiche/persone-giuridiche/${azienda.id}/modifica`}
                        className="btn btn-sm btn-secondary"
                        title="Modifica"
                      >
                        ✏️
                      </Link>
                      <button
                        onClick={() => handleDelete(azienda.id)}
                        className="btn btn-sm btn-danger"
                        title="Elimina"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="soggetti-list-footer">
        <p>
          Totale persone giuridiche: <strong>{filteredAziende.length}</strong>
          {searchTerm && aziende.length !== filteredAziende.length && (
            <span> (filtrate da {aziende.length})</span>
          )}
        </p>
        <div className="info-note">
          💡 <em>Le persone giuridiche (aziende, società) non possono avere account utente.
          Per accedere al sistema, crea un account per una persona fisica che rappresenta l'azienda.</em>
        </div>
      </div>
    </div>
  );
}

export default PersoneGiuridicheList;
