import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSoggettiAnagrafici, deleteSoggetto } from '../../services/anagraficaAPI';
import '../SoggettiAnagrafici/SoggettiAnagraficiList.css';

/**
 * PersoneFisicheList - Lista persone fisiche
 *
 * Vista ottimizzata per persone fisiche (individui con CF)
 * Mostra campi specifici: Nome, Cognome, Data Nascita, CF
 */
function PersoneFisicheList() {
  const [persone, setPersone] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attiviSolo, setAttiviSolo] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadPersone();
  }, [attiviSolo]);

  const loadPersone = async () => {
    try {
      setLoading(true);
      setError(null);
      // Carica solo PERSONA_FISICA
      const data = await getSoggettiAnagrafici({
        attivi_solo: attiviSolo,
        limit: 1000
      });
      // Filtra solo persone fisiche
      const personeFisiche = data.filter(s => s.tipo_soggetto === 'PERSONA_FISICA');
      setPersone(personeFisiche);
    } catch (err) {
      console.error('Error loading persone fisiche:', err);
      setError('Errore nel caricamento delle persone fisiche');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Sei sicuro di voler eliminare questa persona?')) {
      return;
    }

    try {
      await deleteSoggetto(id);
      loadPersone();
    } catch (err) {
      console.error('Error deleting persona:', err);
      alert('Errore nell\'eliminazione della persona');
    }
  };

  const getNomeCompleto = (persona) => {
    return `${persona.nome || ''} ${persona.cognome || ''}`.trim() || '(Non specificato)';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
  };

  // Filtra per ricerca
  const filteredPersone = persone.filter(persona => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      getNomeCompleto(persona).toLowerCase().includes(searchLower) ||
      (persona.codice_fiscale || '').toLowerCase().includes(searchLower) ||
      (persona.email || '').toLowerCase().includes(searchLower) ||
      (persona.telefono || '').toLowerCase().includes(searchLower)
    );
  });

  if (loading) {
    return (
      <div className="soggetti-list-container">
        <div className="loading">Caricamento persone fisiche...</div>
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
        <h1>👤 Persone Fisiche</h1>
        <div className="header-actions">
          <input
            type="text"
            placeholder="🔍 Cerca per nome, CF, email..."
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
          <Link to="/anagrafiche/persone-fisiche/nuovo" className="btn btn-primary">
            + Nuova Persona Fisica
          </Link>
        </div>
      </div>

      {filteredPersone.length === 0 ? (
        <div className="empty-state">
          <p>{searchTerm ? 'Nessuna persona trovata con i criteri di ricerca' : 'Nessuna persona fisica trovata'}</p>
          {!searchTerm && (
            <Link to="/anagrafiche/persone-fisiche/nuovo" className="btn btn-primary">
              Crea la prima persona fisica
            </Link>
          )}
        </div>
      ) : (
        <div className="soggetti-table-wrapper">
          <table className="soggetti-table">
            <thead>
              <tr>
                <th>Nome Completo</th>
                <th>Codice Fiscale</th>
                <th>Data Nascita</th>
                <th>Luogo Nascita</th>
                <th>Email</th>
                <th>Telefono</th>
                <th>Città</th>
                <th>P.IVA</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filteredPersone.map((persona) => (
                <tr key={persona.id} className={!persona.attivo ? 'inactive' : ''}>
                  <td>
                    <Link to={`/anagrafiche/persone-fisiche/${persona.id}`} className="soggetto-name">
                      {getNomeCompleto(persona)}
                    </Link>
                  </td>
                  <td>
                    <code className="cf-badge">{persona.codice_fiscale || '-'}</code>
                  </td>
                  <td>{formatDate(persona.data_nascita)}</td>
                  <td>{persona.luogo_nascita || '-'}</td>
                  <td>{persona.email || '-'}</td>
                  <td>{persona.telefono || persona.cellulare || '-'}</td>
                  <td>{persona.citta || '-'}</td>
                  <td>{persona.partita_iva ? <code className="piva-badge">{persona.partita_iva}</code> : '-'}</td>
                  <td>
                    <span className={`status-badge ${persona.attivo ? 'active' : 'inactive'}`}>
                      {persona.attivo ? 'Attivo' : 'Inattivo'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Link
                        to={`/anagrafiche/persone-fisiche/${persona.id}`}
                        className="btn btn-sm btn-secondary"
                        title="Visualizza"
                      >
                        👁️
                      </Link>
                      <Link
                        to={`/anagrafiche/persone-fisiche/${persona.id}/modifica`}
                        className="btn btn-sm btn-secondary"
                        title="Modifica"
                      >
                        ✏️
                      </Link>
                      <button
                        onClick={() => handleDelete(persona.id)}
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
          Totale persone fisiche: <strong>{filteredPersone.length}</strong>
          {searchTerm && persone.length !== filteredPersone.length && (
            <span> (filtrate da {persone.length})</span>
          )}
        </p>
      </div>
    </div>
  );
}

export default PersoneFisicheList;
