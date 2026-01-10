import { useState, useEffect } from 'react';
import { calendariAPI } from '../../services/affittiBreviAPI';

function CalendarioForm({ calendario, onClose }) {
  const [formData, setFormData] = useState({
    unita_immobiliare_id: '',
    portale: 'BOOKING_COM',
    url_ical: '',
    url_dashboard_portale: '',
    attivo: true,
    note: ''
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (calendario) {
      setFormData({
        ...formData,
        ...calendario
      });
    }
  }, [calendario]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      if (calendario) {
        await calendariAPI.update(calendario.id, formData);
      } else {
        await calendariAPI.create(formData);
      }
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel salvataggio del calendario');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{calendario ? 'Modifica Calendario iCal' : 'Nuovo Calendario iCal'}</h2>
          <button onClick={onClose} className="btn-close">&times;</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-danger">{error}</div>}

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
            <label htmlFor="portale">Portale *</label>
            <select
              id="portale"
              name="portale"
              value={formData.portale}
              onChange={handleChange}
              required
            >
              <option value="BOOKING_COM">Booking.com</option>
              <option value="AIRBNB">Airbnb</option>
              <option value="VRBO">Vrbo</option>
              <option value="ALTRO">Altro</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="url_ical">URL iCal *</label>
            <input
              type="url"
              id="url_ical"
              name="url_ical"
              value={formData.url_ical}
              onChange={handleChange}
              placeholder="https://..."
              required
            />
            <small className="form-text">
              URL del calendario iCal fornito dalla piattaforma di prenotazione
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="url_dashboard_portale">URL Dashboard Portale</label>
            <input
              type="url"
              id="url_dashboard_portale"
              name="url_dashboard_portale"
              value={formData.url_dashboard_portale}
              onChange={handleChange}
              placeholder="https://..."
            />
            <small className="form-text">
              Link diretto alla dashboard del portale (opzionale)
            </small>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="attivo"
                checked={formData.attivo}
                onChange={handleChange}
              />
              <span>Calendario attivo (sincronizzazione automatica)</span>
            </label>
          </div>

          <div className="form-group">
            <label htmlFor="note">Note</label>
            <textarea
              id="note"
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="3"
              placeholder="Note aggiuntive sulla configurazione..."
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

export default CalendarioForm;
