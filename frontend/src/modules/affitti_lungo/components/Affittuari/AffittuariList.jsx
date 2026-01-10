import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { affittuariAPI } from '../../services/affittiAPI';
import AffittuarioForm from './AffittuarioForm';
import './Affittuari.css';

function AffittuariList() {
  const [affittuari, setAffittuari] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAffittuario, setEditingAffittuario] = useState(null);

  useEffect(() => {
    fetchAffittuari();
  }, []);

  const fetchAffittuari = async () => {
    try {
      setLoading(true);
      const response = await affittuariAPI.getAll();
      setAffittuari(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento degli affittuari');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo affittuario?')) {
      try {
        await affittuariAPI.delete(id);
        fetchAffittuari();
      } catch (err) {
        setError('Errore nell\'eliminazione dell\'affittuario');
        console.error(err);
      }
    }
  };

  const handleEdit = (affittuario) => {
    setEditingAffittuario(affittuario);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingAffittuario(null);
    fetchAffittuari();
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="affittuari-container">
      <div className="header">
        <h1>Gestione Affittuari</h1>
        <button onClick={() => setShowForm(true)}>Nuovo Affittuario</button>
      </div>

      {showForm && (
        <AffittuarioForm
          affittuario={editingAffittuario}
          onClose={handleFormClose}
        />
      )}

      {affittuari.length === 0 ? (
        <div className="card">
          <p>Nessun affittuario presente. Clicca su "Nuovo Affittuario" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Cognome</th>
              <th>Codice Fiscale</th>
              <th>Email</th>
              <th>Telefono</th>
              <th>Città</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {affittuari.map((affittuario) => (
              <tr key={affittuario.id}>
                <td>{affittuario.nome}</td>
                <td>{affittuario.cognome}</td>
                <td>{affittuario.codice_fiscale}</td>
                <td>{affittuario.email || '-'}</td>
                <td>{affittuario.telefono || affittuario.cellulare || '-'}</td>
                <td>{affittuario.citta_residenza || '-'}</td>
                <td>
                  <div className="action-buttons">
                    <Link to={`/affittuari/${affittuario.id}`}>
                      <button className="primary">Dettagli</button>
                    </Link>
                    <button className="secondary" onClick={() => handleEdit(affittuario)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(affittuario.id)}>
                      Elimina
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default AffittuariList;
