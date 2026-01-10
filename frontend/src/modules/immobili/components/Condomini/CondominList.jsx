import { useState, useEffect } from 'react';
import { condominAPI } from '../../services/immobiliAPI';
import CondominioForm from './CondominioForm';
import './Condomini.css';

function CondominList() {
  const [condomini, setCondomini] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCondominio, setEditingCondominio] = useState(null);

  useEffect(() => {
    fetchCondomini();
  }, []);

  const fetchCondomini = async () => {
    try {
      setLoading(true);
      const response = await condominAPI.getAll();
      setCondomini(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei condomini');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo condominio?')) {
      try {
        await condominAPI.delete(id);
        fetchCondomini();
      } catch (err) {
        setError('Errore nell\'eliminazione del condominio');
        console.error(err);
      }
    }
  };

  const handleEdit = (condominio) => {
    setEditingCondominio(condominio);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingCondominio(null);
    fetchCondomini();
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="condomini-container">
      <div className="header">
        <h1>Gestione Condomini</h1>
        <button onClick={() => setShowForm(true)}>Nuovo Condominio</button>
      </div>

      {showForm && (
        <CondominioForm
          condominio={editingCondominio}
          onClose={handleFormClose}
        />
      )}

      {condomini.length === 0 ? (
        <div className="card">
          <p>Nessun condominio presente. Clicca su "Nuovo Condominio" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Codice</th>
              <th>Nome</th>
              <th>Indirizzo</th>
              <th>Città</th>
              <th>Amministratore</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {condomini.map((condominio) => (
              <tr key={condominio.id}>
                <td>{condominio.codice}</td>
                <td>{condominio.nome}</td>
                <td>{condominio.indirizzo}</td>
                <td>{condominio.citta}</td>
                <td>{condominio.amministratore_nome || '-'}</td>
                <td>
                  <span className={`badge ${condominio.attivo ? 'success' : 'inactive'}`}>
                    {condominio.attivo ? 'Attivo' : 'Non attivo'}
                  </span>
                </td>
                <td>
                  <div className="action-buttons">
                    <button className="secondary" onClick={() => handleEdit(condominio)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(condominio.id)}>
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

export default CondominList;
