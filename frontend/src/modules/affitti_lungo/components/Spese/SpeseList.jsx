import { useState, useEffect } from 'react';
import { speseAPI } from '../../services/affittiAPI';
import { unitaImmobiliariAPI } from '../../../../services/api';
import SpesaForm from './SpesaForm';
import './Spese.css';

function SpeseList() {
  const [spese, setSpese] = useState([]);
  const [immobili, setImmobili] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingSpesa, setEditingSpesa] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [speseRes, immobiliRes] = await Promise.all([
        speseAPI.getAll(),
        unitaImmobiliariAPI.getAll(),
      ]);
      setSpese(speseRes.data);
      setImmobili(immobiliRes.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei dati');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa spesa?')) {
      try {
        await speseAPI.delete(id);
        fetchData();
      } catch (err) {
        setError('Errore nell\'eliminazione della spesa');
        console.error(err);
      }
    }
  };

  const handleEdit = (spesa) => {
    setEditingSpesa(spesa);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingSpesa(null);
    fetchData();
  };

  const getImmobileNome = (id) => {
    const immobile = immobili.find(i => i.id === id);
    return immobile ? `${immobile.codice} - ${immobile.indirizzo}` : '-';
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="spese-container">
      <div className="header">
        <h1>Gestione Spese</h1>
        <button onClick={() => setShowForm(true)}>Nuova Spesa</button>
      </div>

      {showForm && (
        <SpesaForm
          spesa={editingSpesa}
          immobili={immobili}
          onClose={handleFormClose}
        />
      )}

      {spese.length === 0 ? (
        <div className="card">
          <p>Nessuna spesa presente. Clicca su "Nuova Spesa" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Immobile</th>
              <th>Categoria</th>
              <th>Descrizione</th>
              <th>Importo</th>
              <th>Pagata</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {spese.map((spesa) => (
              <tr key={spesa.id}>
                <td>{new Date(spesa.data).toLocaleDateString('it-IT')}</td>
                <td>{getImmobileNome(spesa.immobile_id)}</td>
                <td>
                  <span className={`badge badge-${spesa.categoria}`}>
                    {spesa.categoria}
                  </span>
                </td>
                <td>{spesa.descrizione}</td>
                <td>€ {spesa.importo}</td>
                <td>
                  <span className={`status ${spesa.pagata ? 'pagata' : 'non-pagata'}`}>
                    {spesa.pagata ? 'Sì' : 'No'}
                  </span>
                </td>
                <td>
                  <div className="action-buttons">
                    <button className="secondary" onClick={() => handleEdit(spesa)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(spesa.id)}>
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

export default SpeseList;
