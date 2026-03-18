import { useEffect, useState } from 'react';
import { parsingServicesAPI } from '../../services/api';
import './ParsingServices.css';

const emptyForm = {
  service_key: '',
  transport_type: 'HTTP',
  endpoint_url: '',
  redis_queue: '',
  timeout_seconds: 300,
  enabled: true,
  notes: '',
};

export default function ParsingServices() {
  const [services, setServices] = useState([]);
  const [required, setRequired] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState(emptyForm);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [listResp, summaryResp] = await Promise.all([
        parsingServicesAPI.list(),
        parsingServicesAPI.summary(),
      ]);
      setServices(listResp.data || []);
      setRequired(summaryResp.data?.required_services || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleEdit = (service) => {
    setForm({
      service_key: service.service_key || '',
      transport_type: service.transport_type || 'HTTP',
      endpoint_url: service.endpoint_url || '',
      redis_queue: service.redis_queue || '',
      timeout_seconds: service.timeout_seconds || 300,
      enabled: service.enabled !== false,
      notes: service.notes || '',
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await parsingServicesAPI.upsert(form);
      setForm(emptyForm);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <div className="parsing-services">
      <h1>Servizi Parsing</h1>
      {error && <div className="parsing-services-error">{error}</div>}
      {loading && <div className="parsing-services-loading">Caricamento...</div>}

      {!loading && (
        <>
          <section className="parsing-services-section">
            <h2>Servizi richiesti dai moduli</h2>
            {required.length === 0 ? (
              <div className="parsing-services-empty">Nessun servizio richiesto</div>
            ) : (
              <table className="parsing-services-table">
                <thead>
                  <tr>
                    <th>Service Key</th>
                    <th>Configurato</th>
                    <th>Trasporto</th>
                    <th>Endpoint/Queue</th>
                  </tr>
                </thead>
                <tbody>
                  {required.map((item) => (
                    <tr key={item.service_key}>
                      <td>{item.service_key}</td>
                      <td>{item.configured ? 'Sì' : 'No'}</td>
                      <td>{item.config?.transport_type || '-'}</td>
                      <td>{item.config?.endpoint_url || item.config?.redis_queue || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="parsing-services-section">
            <h2>Configurazioni salvate</h2>
            {services.length === 0 ? (
              <div className="parsing-services-empty">Nessuna configurazione presente</div>
            ) : (
              <table className="parsing-services-table">
                <thead>
                  <tr>
                    <th>Service Key</th>
                    <th>Trasporto</th>
                    <th>Endpoint</th>
                    <th>Queue</th>
                    <th>Timeout</th>
                    <th>Abilitato</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {services.map((service) => (
                    <tr key={service.id}>
                      <td>{service.service_key}</td>
                      <td>{service.transport_type}</td>
                      <td>{service.endpoint_url || '-'}</td>
                      <td>{service.redis_queue || '-'}</td>
                      <td>{service.timeout_seconds || '-'}</td>
                      <td>{service.enabled ? 'Sì' : 'No'}</td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleEdit(service)}
                        >
                          Modifica
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="parsing-services-section">
            <h2>{form.service_key ? 'Modifica servizio' : 'Nuovo servizio'}</h2>
            <form className="parsing-services-form" onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder="service_key (es: mrz)"
                value={form.service_key}
                onChange={(e) => setForm((prev) => ({ ...prev, service_key: e.target.value }))}
                required
              />
              <select
                value={form.transport_type}
                onChange={(e) => setForm((prev) => ({ ...prev, transport_type: e.target.value }))}
              >
                <option value="HTTP">HTTP</option>
                <option value="REDIS">REDIS</option>
                <option value="WS">WS</option>
              </select>
              <input
                type="text"
                placeholder="endpoint_url (per HTTP/WS)"
                value={form.endpoint_url}
                onChange={(e) => setForm((prev) => ({ ...prev, endpoint_url: e.target.value }))}
              />
              <input
                type="text"
                placeholder="redis_queue (per REDIS)"
                value={form.redis_queue}
                onChange={(e) => setForm((prev) => ({ ...prev, redis_queue: e.target.value }))}
              />
              <input
                type="number"
                placeholder="timeout_seconds"
                value={form.timeout_seconds}
                onChange={(e) => setForm((prev) => ({ ...prev, timeout_seconds: Number(e.target.value) }))}
              />
              <label className="parsing-services-checkbox">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(e) => setForm((prev) => ({ ...prev, enabled: e.target.checked }))}
                />
                Abilitato
              </label>
              <textarea
                placeholder="note"
                value={form.notes}
                onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              />
              <button className="btn btn-primary" type="submit">
                Salva
              </button>
            </form>
          </section>
        </>
      )}
    </div>
  );
}
