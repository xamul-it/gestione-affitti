import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSoggettiAnagrafici, deleteSoggetto } from '../../services/anagraficaAPI';
import './SoggettiAnagraficiList.css';

/**
 * SoggettiAnagraficiList - Lista principale delle anagrafiche
 *
 * Landing page del modulo Anagrafica Italiana
 * Mostra tabella con soggetti (persone fisiche e giuridiche)
 */
function SoggettiAnagraficiList() {
  const [soggetti, setSoggetti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attiviSolo, setAttiviSolo] = useState(false);

  useEffect(() => {
    loadSoggetti();
  }, [attiviSolo]);

  const loadSoggetti = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSoggettiAnagrafici({ attivi_solo: attiviSolo, limit: 1000 });
      setSoggetti(data);
    } catch (err) {
      console.error('Error loading soggetti:', err);
      setError('Errore nel caricamento delle anagrafiche');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Sei sicuro di voler eliminare questa anagrafica?')) {
      return;
    }

    try {
      await deleteSoggetto(id);
      loadSoggetti();
    } catch (err) {
      console.error('Error deleting soggetto:', err);
      alert('Errore nell\'eliminazione dell\'anagrafica');
    }
  };

  const getTipoLabel = (tipo) => {
    return tipo === 'PERSONA_FISICA' ? 'Persona Fisica' : 'Persona Giuridica';
  };

  const getTipoIcon = (tipo) => {
    return tipo === 'PERSONA_FISICA' ? '👤' : '🏢';
  };

  const getNomeCompleto = (soggetto) => {
    if (soggetto.tipo_soggetto === 'PERSONA_FISICA') {
      return `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim() || '(Non specificato)';
    }
    return soggetto.ragione_sociale || '(Non specificato)';
  };

  if (loading) {
    return (
      <div className="soggetti-list-container">
        <div className="loading">Caricamento anagrafiche...</div>
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
        <h1>Anagrafiche</h1>
        <div className="header-actions">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={attiviSolo}
              onChange={(e) => setAttiviSolo(e.target.checked)}
            />
            <span>Solo attivi</span>
          </label>
          <Link to="/anagrafiche/nuovo" className="btn btn-primary">
            + Nuova Anagrafica
          </Link>
        </div>
      </div>

      {soggetti.length === 0 ? (
        <div className="empty-state">
          <p>Nessuna anagrafica trovata</p>
          <Link to="/anagrafiche/nuovo" className="btn btn-primary">
            Crea la prima anagrafica
          </Link>
        </div>
      ) : (
        <div className="soggetti-table-wrapper">
          <table className="soggetti-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Nome / Ragione Sociale</th>
                <th>Codice Fiscale</th>
                <th>Partita IVA</th>
                <th>Email</th>
                <th>Telefono</th>
                <th>Citt�</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {soggetti.map((soggetto) => (
                <tr key={soggetto.id} className={!soggetto.attivo ? 'inactive' : ''}>
                  <td>
                    <span className="tipo-badge" title={getTipoLabel(soggetto.tipo_soggetto)}>
                      {getTipoIcon(soggetto.tipo_soggetto)}
                    </span>
                  </td>
                  <td>
                    <Link to={`/anagrafiche/${soggetto.id}`} className="soggetto-name">
                      {getNomeCompleto(soggetto)}
                    </Link>
                  </td>
                  <td>{soggetto.codice_fiscale || '-'}</td>
                  <td>{soggetto.partita_iva || '-'}</td>
                  <td>{soggetto.email || '-'}</td>
                  <td>{soggetto.telefono || soggetto.cellulare || '-'}</td>
                  <td>{soggetto.citta || '-'}</td>
                  <td>
                    <span className={`status-badge ${soggetto.attivo ? 'active' : 'inactive'}`}>
                      {soggetto.attivo ? 'Attivo' : 'Inattivo'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Link
                        to={`/anagrafiche/${soggetto.id}`}
                        className="btn btn-sm btn-secondary"
                        title="Visualizza"
                      >
                        👁️
                      </Link>
                      <Link
                        to={`/anagrafiche/${soggetto.id}/modifica`}
                        className="btn btn-sm btn-secondary"
                        title="Modifica"
                      >
                        ✏️
                      </Link>
                      <button
                        onClick={() => handleDelete(soggetto.id)}
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
        <p>Totale anagrafiche: {soggetti.length}</p>
      </div>
    </div>
  );
}

export default SoggettiAnagraficiList;
