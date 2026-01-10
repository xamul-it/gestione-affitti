import { useState, useEffect } from 'react';
import { categorieCatastaliAPI } from '../../services/immobiliAPI';
import CategoriaCatastaleForm from './CategoriaCatastaleForm';
import './CategorieCatastali.css';

function CategorieCatastaliList() {
  const [categorie, setCategorie] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategoria, setSelectedCategoria] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [showOnlyActive, setShowOnlyActive] = useState(false);

  useEffect(() => {
    fetchCategorie();
  }, [showOnlyActive]);

  const fetchCategorie = async () => {
    try {
      setLoading(true);
      const response = await categorieCatastaliAPI.getAll(showOnlyActive);
      // Sort by ordinamento and then by codice
      const sortedData = response.data.sort((a, b) => {
        if (a.ordinamento !== b.ordinamento) {
          return (a.ordinamento || 999) - (b.ordinamento || 999);
        }
        return (a.codice || '').localeCompare(b.codice || '');
      });
      setCategorie(sortedData);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle categorie catastali');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (categoria) => {
    setSelectedCategoria(categoria);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa categoria catastale?')) {
      try {
        await categorieCatastaliAPI.delete(id);
        fetchCategorie();
      } catch (err) {
        alert('Errore nell\'eliminazione della categoria catastale');
        console.error(err);
      }
    }
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setSelectedCategoria(null);
    fetchCategorie();
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>Categorie Catastali</h1>
        <button onClick={() => setShowForm(true)} className="btn btn-primary">
          + Nuova Categoria
        </button>
      </div>

      <div className="filters">
        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={showOnlyActive}
            onChange={(e) => setShowOnlyActive(e.target.checked)}
          />
          Mostra solo attive
        </label>
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="loading">Caricamento...</div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Codice</th>
                <th>Nome</th>
                <th>Gruppo</th>
                <th>Descrizione</th>
                <th>Ordinamento</th>
                <th>Attiva</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {categorie.length === 0 ? (
                <tr>
                  <td colSpan="7" className="no-data">
                    Nessuna categoria catastale trovata
                  </td>
                </tr>
              ) : (
                categorie.map((categoria) => (
                  <tr key={categoria.id}>
                    <td><strong>{categoria.codice}</strong></td>
                    <td>{categoria.nome}</td>
                    <td>{categoria.gruppo || '-'}</td>
                    <td className="truncate-text">{categoria.descrizione || '-'}</td>
                    <td>{categoria.ordinamento || '-'}</td>
                    <td>
                      <span className={`status-badge ${categoria.attiva ? 'active' : 'inactive'}`}>
                        {categoria.attiva ? '✓' : '✗'}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          onClick={() => handleEdit(categoria)}
                          className="btn btn-sm btn-secondary"
                          title="Modifica"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDelete(categoria.id)}
                          className="btn btn-sm btn-danger"
                          title="Elimina"
                        >
                          🗑
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
        <CategoriaCatastaleForm
          categoria={selectedCategoria}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
}

export default CategorieCatastaliList;
