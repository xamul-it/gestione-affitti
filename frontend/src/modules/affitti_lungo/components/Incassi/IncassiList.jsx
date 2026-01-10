import { useState, useEffect } from 'react';
import { incassiAPI, contrattiAPI } from '../../services/affittiAPI';
import IncassoForm from './IncassoForm';
import './Incassi.css';

function IncassiList() {
  const [incassi, setIncassi] = useState([]);
  const [contratti, setContratti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingIncasso, setEditingIncasso] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [incassiRes, contrattiRes] = await Promise.all([
        incassiAPI.getAll(),
        contrattiAPI.getAll(),
      ]);
      setIncassi(incassiRes.data);
      setContratti(contrattiRes.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei dati');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questo incasso?')) {
      try {
        await incassiAPI.delete(id);
        fetchData();
      } catch (err) {
        setError('Errore nell\'eliminazione dell\'incasso');
        console.error(err);
      }
    }
  };

  const handleEdit = (incasso) => {
    setEditingIncasso(incasso);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingIncasso(null);
    fetchData();
  };

  const getContrattoInfo = (id) => {
    const contratto = contratti.find(c => c.id === id);
    return contratto ? contratto.numero_contratto : '-';
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="incassi-container">
      <div className="header">
        <h1>Gestione Incassi</h1>
        <button onClick={() => setShowForm(true)}>Nuovo Incasso</button>
      </div>

      {showForm && (
        <IncassoForm
          incasso={editingIncasso}
          contratti={contratti}
          onClose={handleFormClose}
        />
      )}

      {incassi.length === 0 ? (
        <div className="card">
          <p>Nessun incasso presente. Clicca su "Nuovo Incasso" per iniziare.</p>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Data Incasso</th>
              <th>Contratto</th>
              <th>Mese Rif.</th>
              <th>Importo</th>
              <th>Metodo</th>
              <th>Ricevuta</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {incassi.map((incasso) => (
              <tr key={incasso.id}>
                <td>{new Date(incasso.data_incasso).toLocaleDateString('it-IT')}</td>
                <td>{getContrattoInfo(incasso.contratto_id)}</td>
                <td>{incasso.mese_riferimento}</td>
                <td>€ {incasso.importo}</td>
                <td>{incasso.metodo_pagamento || '-'}</td>
                <td>{incasso.numero_ricevuta || '-'}</td>
                <td>
                  <div className="action-buttons">
                    <button className="secondary" onClick={() => handleEdit(incasso)}>
                      Modifica
                    </button>
                    <button className="danger" onClick={() => handleDelete(incasso.id)}>
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

export default IncassiList;
