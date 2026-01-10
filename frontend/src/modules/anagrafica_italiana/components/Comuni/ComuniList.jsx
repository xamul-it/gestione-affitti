import { useState, useEffect } from 'react';
import { getComuni, searchComuniByCAP } from '../../services/anagraficaAPI';
import './ComuniList.css';

/**
 * ComuniList - Lista comuni italiani
 *
 * Dati di riferimento: comuni italiani con CAP, provincia, regione
 * Ricerca avanzata per nome, provincia, CAP
 */
function ComuniList() {
  const [comuni, setComuni] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [searchProvincia, setSearchProvincia] = useState('');
  const [searchCAP, setSearchCAP] = useState('');
  const [searchMode, setSearchMode] = useState('nome'); // 'nome', 'provincia', 'cap'

  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
    total: 0
  });

  useEffect(() => {
    loadComuni();
  }, [pagination.skip, searchMode, searchProvincia]);

  const loadComuni = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      if (searchMode === 'cap' && searchCAP) {
        // Ricerca per CAP
        data = await searchComuniByCAP(searchCAP);
      } else {
        // Ricerca standard
        data = await getComuni({
          skip: pagination.skip,
          limit: pagination.limit,
          provincia: searchProvincia || null,
          search: searchTerm || null
        });
      }

      setComuni(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading comuni:', err);
      setError('Errore nel caricamento dei comuni');
      setComuni([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, skip: 0 }));
    loadComuni();
  };

  const handleReset = () => {
    setSearchTerm('');
    setSearchProvincia('');
    setSearchCAP('');
    setSearchMode('nome');
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const handleNextPage = () => {
    setPagination(prev => ({
      ...prev,
      skip: prev.skip + prev.limit
    }));
  };

  const handlePrevPage = () => {
    setPagination(prev => ({
      ...prev,
      skip: Math.max(0, prev.skip - prev.limit)
    }));
  };

  if (loading && comuni.length === 0) {
    return (
      <div className="comuni-list-container">
        <div className="loading">Caricamento comuni...</div>
      </div>
    );
  }

  return (
    <div className="comuni-list-container">
      <div className="comuni-list-header">
        <h1>🏛️ Comuni Italiani</h1>
        <div className="info-badge">
          <span>Dati di Riferimento</span>
        </div>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-mode-selector">
          <label>
            <input
              type="radio"
              name="searchMode"
              value="nome"
              checked={searchMode === 'nome'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            <span>Cerca per Nome</span>
          </label>
          <label>
            <input
              type="radio"
              name="searchMode"
              value="provincia"
              checked={searchMode === 'provincia'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            <span>Cerca per Provincia</span>
          </label>
          <label>
            <input
              type="radio"
              name="searchMode"
              value="cap"
              checked={searchMode === 'cap'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            <span>Cerca per CAP</span>
          </label>
        </div>

        <div className="search-inputs">
          {searchMode === 'nome' && (
            <input
              type="text"
              placeholder="🔍 Cerca per nome comune (es. Milano, Roma...)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          )}

          {searchMode === 'provincia' && (
            <input
              type="text"
              placeholder="🔍 Sigla provincia (es. MI, RM, TO...)"
              value={searchProvincia}
              onChange={(e) => setSearchProvincia(e.target.value.toUpperCase())}
              maxLength="2"
              className="search-input provincia-input"
              style={{ textTransform: 'uppercase' }}
            />
          )}

          {searchMode === 'cap' && (
            <input
              type="text"
              placeholder="🔍 CAP (es. 20100, 00100...)"
              value={searchCAP}
              onChange={(e) => setSearchCAP(e.target.value)}
              maxLength="5"
              className="search-input cap-input"
            />
          )}

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Ricerca...' : 'Cerca'}
          </button>
          <button type="button" onClick={handleReset} className="btn btn-secondary">
            Reset
          </button>
        </div>
      </form>

      {error && (
        <div className="alert alert-error">
          <strong>Errore:</strong> {error}
        </div>
      )}

      {comuni.length === 0 && !loading ? (
        <div className="empty-state">
          <div className="empty-icon">🏛️</div>
          <p>Nessun comune trovato</p>
          <p className="empty-hint">
            Prova a modificare i criteri di ricerca
          </p>
        </div>
      ) : (
        <>
          <div className="comuni-table-wrapper">
            <table className="comuni-table">
              <thead>
                <tr>
                  <th>Comune</th>
                  <th>Provincia</th>
                  <th>Regione</th>
                  <th>CAP</th>
                  <th>Codice Catastale</th>
                  <th>Codice ISTAT</th>
                </tr>
              </thead>
              <tbody>
                {comuni.map((comune) => (
                  <tr key={comune.id}>
                    <td className="comune-name">
                      <strong>{comune.nome}</strong>
                    </td>
                    <td>
                      <span className="provincia-badge">{comune.provincia}</span>
                    </td>
                    <td>{comune.regione || '-'}</td>
                    <td>
                      <code className="cap-badge">{comune.cap || '-'}</code>
                    </td>
                    <td>
                      <code className="codice-badge">{comune.codice_catastale || '-'}</code>
                    </td>
                    <td>
                      <code className="codice-badge">{comune.codice_istat || '-'}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button
              onClick={handlePrevPage}
              disabled={pagination.skip === 0 || loading}
              className="btn btn-secondary btn-sm"
            >
              ← Precedente
            </button>
            <span className="pagination-info">
              Visualizzando {pagination.skip + 1} - {pagination.skip + comuni.length}
            </span>
            <button
              onClick={handleNextPage}
              disabled={comuni.length < pagination.limit || loading}
              className="btn btn-secondary btn-sm"
            >
              Successiva →
            </button>
          </div>
        </>
      )}

      <div className="comuni-list-footer">
        <p>
          Totale comuni visualizzati: <strong>{comuni.length}</strong>
        </p>
        <div className="info-note">
          💡 <em>Database completo dei comuni italiani con codici catastali, ISTAT e CAP.
          Utilizza la ricerca per trovare rapidamente un comune specifico.</em>
        </div>
      </div>
    </div>
  );
}

export default ComuniList;
