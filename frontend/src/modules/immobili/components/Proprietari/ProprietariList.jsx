import { useState, useEffect } from 'react';
import { proprietariAPI } from '../../services/immobiliAPI';
import ProprietarioForm from './ProprietarioForm';
import './Proprietari.css';

function ProprietariList() {
  const [proprietari, setProprietari] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProprietario, setSelectedProprietario] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [showOnlyActive, setShowOnlyActive] = useState(false);

  useEffect(() => {
    fetchProprietari();
  }, [showOnlyActive]);

  const fetchProprietari = async () => {
    try {
      setLoading(true);
      const response = await proprietariAPI.getAll(showOnlyActive);
      setProprietari(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei proprietari');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (proprietario) => {
    setSelectedProprietario(proprietario);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler disattivare questo proprietario?')) {
      try {
        await proprietariAPI.delete(id);
        fetchProprietari();
      } catch (err) {
        alert('Errore nella disattivazione del proprietario');
        console.error(err);
      }
    }
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setSelectedProprietario(null);
    fetchProprietari();
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>Proprietari</h1>
        <button onClick={() => setShowForm(true)} className="btn btn-primary">
          + Nuovo Proprietario
        </button>
      </div>

      <div className="filters">
        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={showOnlyActive}
            onChange={(e) => setShowOnlyActive(e.target.checked)}
          />
          Mostra solo attivi
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
                <th>Nome</th>
                <th>Cognome</th>
                <th>Codice Fiscale</th>
                <th>Email</th>
                <th>Telefono</th>
                <th>Città</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {proprietari.length === 0 ? (
                <tr>
                  <td colSpan="8" className="no-data">
                    Nessun proprietario trovato
                  </td>
                </tr>
              ) : (
                proprietari.map((proprietario) => (
                  <tr key={proprietario.id}>
                    <td>{proprietario.nome}</td>
                    <td>{proprietario.cognome}</td>
                    <td>{proprietario.codice_fiscale}</td>
                    <td>{proprietario.email || '-'}</td>
                    <td>{proprietario.telefono || proprietario.cellulare || '-'}</td>
                    <td>{proprietario.citta || '-'}</td>
                    <td>
                      <span className={`status-badge ${proprietario.attivo ? 'active' : 'inactive'}`}>
                        {proprietario.attivo ? 'Attivo' : 'Inattivo'}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          onClick={() => handleEdit(proprietario)}
                          className="btn btn-sm btn-secondary"
                          title="Modifica"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDelete(proprietario.id)}
                          className="btn btn-sm btn-danger"
                          title="Disattiva"
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
        <ProprietarioForm
          proprietario={selectedProprietario}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
}

export default ProprietariList;
