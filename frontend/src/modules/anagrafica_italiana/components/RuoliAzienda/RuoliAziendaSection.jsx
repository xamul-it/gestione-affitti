import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import { ruoliAziendaAPI } from '../../../../services/ruoliAziendaAPI';
import RuoloAziendaForm from './RuoloAziendaForm';
import './RuoliAziendaSection.css';

/**
 * Sezione per visualizzare e gestire i ruoli azienda di un soggetto
 * Usabile sia per persone fisiche (mostra aziende) che per persone giuridiche (mostra persone)
 */
export default function RuoliAziendaSection({ soggetto, onUpdate }) {
  const [ruoli, setRuoli] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingRuolo, setEditingRuolo] = useState(null);
  const [showAttiviOnly, setShowAttiviOnly] = useState(false);

  const token = localStorage.getItem('access_token');
  const isPersonaFisica = soggetto.tipo_soggetto === 'PERSONA_FISICA';

  useEffect(() => {
    loadRuoli();
  }, [soggetto.id, showAttiviOnly]);

  const loadRuoli = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await ruoliAziendaAPI.getBySoggetto(soggetto.id, showAttiviOnly, token);

      // L'endpoint restituisce {come_persona: [], come_azienda: []}
      // Se è persona fisica, mostra i ruoli come_persona (aziende dove lavora)
      // Se è persona giuridica, mostra i ruoli come_azienda (persone che lavorano qui)
      const data = response.data;
      const ruoliArray = isPersonaFisica ? data.come_persona : data.come_azienda;

      setRuoli(ruoliArray || []);
    } catch (err) {
      console.error('Error loading ruoli:', err);
      setError('Errore nel caricamento dei ruoli');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (data, id) => {
    if (id) {
      // Update
      await ruoliAziendaAPI.update(id, data, token);
    } else {
      // Create
      await ruoliAziendaAPI.create(data, token);
    }
    await loadRuoli();
    if (onUpdate) onUpdate();
  };

  const handleDelete = async (id) => {
    if (!confirm('Sei sicuro di voler eliminare questo ruolo?')) return;

    try {
      await ruoliAziendaAPI.delete(id, token);
      await loadRuoli();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error('Error deleting ruolo:', err);
      alert('Errore nell\'eliminazione del ruolo');
    }
  };

  const handleEdit = (ruolo) => {
    setEditingRuolo(ruolo);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingRuolo(null);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const isRuoloAttivo = (ruolo) => {
    if (!ruolo.data_fine) return true;
    const dataFine = new Date(ruolo.data_fine);
    return dataFine >= new Date();
  };

  return (
    <div className="ruoli-azienda-section">
      <div className="section-header">
        <div className="section-title">
          <h3>
            <span aria-hidden="true">{isPersonaFisica ? '🏢' : '👥'}</span>
            {isPersonaFisica ? 'Ruoli in Aziende' : 'Persone Associate'}
          </h3>
          <p className="section-subtitle">
            {isPersonaFisica
              ? 'Aziende in cui questa persona ha un ruolo'
              : 'Persone che hanno un ruolo in questa azienda'}
          </p>
        </div>
        <div className="section-actions">
          <label className="checkbox-filter">
            <input
              type="checkbox"
              checked={showAttiviOnly}
              onChange={(e) => setShowAttiviOnly(e.target.checked)}
            />
            Solo attivi
          </label>
          <button className="btn-add" onClick={() => setShowForm(true)}>
            ➕ Aggiungi Ruolo
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state">Caricamento ruoli...</div>
      ) : ruoli.length === 0 ? (
        <div className="empty-state">
          <p>
            {isPersonaFisica
              ? 'Nessun ruolo aziendale registrato per questa persona'
              : 'Nessuna persona associata a questa azienda'}
          </p>
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            Aggiungi primo ruolo
          </button>
        </div>
      ) : (
        <div className="ruoli-table-container">
          <table className="ruoli-table">
            <thead>
              <tr>
                <th>{isPersonaFisica ? 'Azienda' : 'Persona'}</th>
                <th>Ruolo</th>
                <th>Periodo</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {ruoli.map((ruolo) => {
                // Determina la controparte (azienda se persona fisica, persona se azienda)
                const controparte = isPersonaFisica ? ruolo.persona_giuridica : ruolo.persona_fisica;
                const controparteId = isPersonaFisica ? ruolo.persona_giuridica_id : ruolo.persona_fisica_id;
                const controparteNome = controparte
                  ? (isPersonaFisica ? controparte.ragione_sociale : controparte.nome_completo)
                  : 'Sconosciuto';

                return (
                  <tr key={ruolo.id} className={isRuoloAttivo(ruolo) ? '' : 'ruolo-scaduto'}>
                    <td>
                      <Link
                        to={`/anagrafiche/soggetto/${controparteId}`}
                        className="link-soggetto"
                      >
                        <strong>{controparteNome}</strong>
                      </Link>
                    </td>
                    <td>
                      <span className="ruolo-badge">
                        {ruolo.ruolo_tipo_nome || ruolo.ruolo || '(Non specificato)'}
                      </span>
                      {!ruolo.ruolo_tipo_id && ruolo.ruolo && (
                        <small className="text-warning" title="Ruolo personalizzato non collegato ai domini">
                          ⚠ Custom
                        </small>
                      )}
                    </td>
                  <td>
                    <div className="date-range">
                      {ruolo.data_inizio && (
                        <span className="date-start">
                          Dal {formatDate(ruolo.data_inizio)}
                        </span>
                      )}
                      {ruolo.data_fine && (
                        <span className="date-end">
                          Al {formatDate(ruolo.data_fine)}
                        </span>
                      )}
                      {!ruolo.data_inizio && !ruolo.data_fine && (
                        <span className="no-dates">Non specificato</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {isRuoloAttivo(ruolo) ? (
                      <span className="status-badge status-active">✓ Attivo</span>
                    ) : (
                      <span className="status-badge status-inactive">✗ Scaduto</span>
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn-icon btn-edit"
                        onClick={() => handleEdit(ruolo)}
                        title="Modifica"
                        aria-label="Modifica ruolo"
                      >
                        ✏️
                      </button>
                      <button
                        className="btn-icon btn-delete"
                        onClick={() => handleDelete(ruolo.id)}
                        title="Elimina"
                        aria-label="Elimina ruolo"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            </tbody>
          </table>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <RuoloAziendaForm
          soggettoCorrente={soggetto}
          ruoloToEdit={editingRuolo}
          onClose={handleCloseForm}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

RuoliAziendaSection.propTypes = {
  soggetto: PropTypes.object.isRequired,
  onUpdate: PropTypes.func
};
