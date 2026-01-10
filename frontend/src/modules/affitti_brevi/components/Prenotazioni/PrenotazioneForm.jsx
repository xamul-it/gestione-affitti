import { useState, useEffect } from 'react';
import { prenotazioniAPI } from '../../services/affittiBreviAPI';

function PrenotazioneForm({ prenotazione, onClose }) {
  const [formData, setFormData] = useState({
    codice_prenotazione: '',
    unita_immobiliare_id: '',
    portale_origine: 'DIRETTA',
    data_checkin: '',
    data_checkout: '',
    numero_ospiti: 1,
    prezzo_totale: '',
    stato: 'CONFERMATA',
    note: ''
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (prenotazione) {
      setFormData({
        ...formData,
        ...prenotazione,
        data_checkin: prenotazione.data_checkin || '',
        data_checkout: prenotazione.data_checkout || '',
      });
    }
  }, [prenotazione]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (prenotazione) {
        await prenotazioniAPI.update(prenotazione.id, formData);
      } else {
        await prenotazioniAPI.create(formData);
      }
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel salvataggio della prenotazione');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{prenotazione ? 'Modifica Prenotazione' : 'Nuova Prenotazione'}</h2>
          <button onClick={onClose} className="btn-close">&times;</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-danger">{error}</div>}

          <div className="form-group">
            <label htmlFor="codice_prenotazione">Codice Prenotazione *</label>
            <input
              type="text"
              id="codice_prenotazione"
              name="codice_prenotazione"
              value={formData.codice_prenotazione}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="unita_immobiliare_id">ID Immobile *</label>
            <input
              type="number"
              id="unita_immobiliare_id"
              name="unita_immobiliare_id"
              value={formData.unita_immobiliare_id}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="portale_origine">Portale Origine</label>
            <select
              id="portale_origine"
              name="portale_origine"
              value={formData.portale_origine}
              onChange={handleChange}
              required
            >
              <option value="DIRETTA">Diretta</option>
              <option value="BOOKING_COM">Booking.com</option>
              <option value="AIRBNB">Airbnb</option>
              <option value="VRBO">Vrbo</option>
              <option value="ALTRO">Altro</option>
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="data_checkin">Check-in *</label>
              <input
                type="date"
                id="data_checkin"
                name="data_checkin"
                value={formData.data_checkin}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="data_checkout">Check-out *</label>
              <input
                type="date"
                id="data_checkout"
                name="data_checkout"
                value={formData.data_checkout}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="numero_ospiti">Numero Ospiti</label>
              <input
                type="number"
                id="numero_ospiti"
                name="numero_ospiti"
                value={formData.numero_ospiti}
                onChange={handleChange}
                min="1"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="prezzo_totale">Prezzo Totale (€)</label>
              <input
                type="number"
                id="prezzo_totale"
                name="prezzo_totale"
                value={formData.prezzo_totale}
                onChange={handleChange}
                step="0.01"
                min="0"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="stato">Stato</label>
            <select
              id="stato"
              name="stato"
              value={formData.stato}
              onChange={handleChange}
            >
              <option value="CONFERMATA">Confermata</option>
              <option value="IN_ATTESA">In Attesa</option>
              <option value="CANCELLATA">Cancellata</option>
              <option value="CHECK_IN_EFFETTUATO">Check-in Effettuato</option>
              <option value="CHECK_OUT_EFFETTUATO">Check-out Effettuato</option>
              <option value="NO_SHOW">No Show</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="note">Note</label>
            <textarea
              id="note"
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="3"
            />
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Annulla
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PrenotazioneForm;
