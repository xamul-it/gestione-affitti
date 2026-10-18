import { useState, useEffect, useCallback, useRef } from 'react';
import { messaggiAPI } from '../../services/pecAPI';
import './Messaggi.css';

/**
 * Debounce hook — ritarda l'aggiornamento di un valore.
 */
function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function formatData(dateString) {
  if (!dateString) return '';
  try {
    return new Date(dateString).toLocaleString('it-IT');
  } catch {
    return dateString;
  }
}

/**
 * MessaggiList
 *
 * Props:
 *   casellaId            {number}    ID della casella PEC corrente
 *   onSelectMessaggio    {function}  Chiamata con l'oggetto messaggio al click
 *   messaggioSelezionatoId {number|null} ID del messaggio attualmente aperto
 *   refreshTrigger       {number}    Incrementa per forzare il refresh
 */
export default function MessaggiList({
  casellaId,
  onSelectMessaggio,
  messaggioSelezionatoId,
  refreshTrigger,
}) {
  const [messaggi, setMessaggi] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filtroNonLetti, setFiltroNonLetti] = useState(false);
  const [ricerca, setRicerca] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);

  const debouncedRicerca = useDebounce(ricerca, 400);

  // Quando cambia la casella, azzeramento filtri e pagina
  useEffect(() => {
    setPage(1);
    setRicerca('');
    setFiltroNonLetti(false);
  }, [casellaId]);

  // Reset pagina quando cambiano i filtri
  useEffect(() => {
    setPage(1);
  }, [debouncedRicerca, filtroNonLetti]);

  const carica = useCallback(async () => {
    if (!casellaId) return;
    setLoading(true);
    setError(null);
    try {
      const params = {
        casella_id: casellaId,
        page,
        page_size: 50,
        solo_non_letti: filtroNonLetti || undefined,
        q: debouncedRicerca || undefined,
      };
      const res = await messaggiAPI.getAll(params);
      setMessaggi(res.data.items || []);
      setTotal(res.data.total ?? 0);
      setPages(res.data.pages ?? 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel caricamento dei messaggi');
      setMessaggi([]);
    } finally {
      setLoading(false);
    }
  }, [casellaId, page, filtroNonLetti, debouncedRicerca]);

  // Ricarica al cambio di dipendenze o al trigger esterno
  useEffect(() => {
    carica();
  }, [carica, refreshTrigger]);

  if (!casellaId) {
    return (
      <div className="messaggi-list">
        <div className="messaggio-placeholder" style={{ padding: '40px 16px' }}>
          Seleziona una casella PEC
        </div>
      </div>
    );
  }

  return (
    <div className="messaggi-list">
      {/* Header con ricerca e filtro */}
      <div className="messaggi-list-header">
        <input
          type="text"
          placeholder="Cerca..."
          value={ricerca}
          onChange={(e) => setRicerca(e.target.value)}
          aria-label="Cerca messaggi"
        />
        <label>
          <input
            type="checkbox"
            checked={filtroNonLetti}
            onChange={(e) => setFiltroNonLetti(e.target.checked)}
          />
          Solo non letti
        </label>
      </div>

      {/* Contenuto lista */}
      {loading && (
        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--color-text-muted, #718096)', fontSize: '0.875rem' }}>
          Caricamento...
        </div>
      )}

      {error && (
        <div style={{ padding: '12px', color: 'var(--color-error, #e53e3e)', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {!loading && !error && messaggi.length === 0 && (
        <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--color-text-muted, #718096)', fontSize: '0.875rem' }}>
          Nessun messaggio trovato
        </div>
      )}

      {messaggi.map((msg) => (
        <div
          key={msg.id}
          className={[
            'messaggio-item',
            !msg.is_letto ? 'non-letto' : '',
            msg.id === messaggioSelezionatoId ? 'selezionato' : '',
          ]
            .filter(Boolean)
            .join(' ')}
          onClick={() => onSelectMessaggio(msg)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onSelectMessaggio(msg)}
          aria-pressed={msg.id === messaggioSelezionatoId}
        >
          <div className="messaggio-item-mittente">{msg.da}</div>
          <div className="messaggio-item-oggetto">{msg.oggetto || '(nessun oggetto)'}</div>
          <div className="messaggio-item-footer">
            <span>{formatData(msg.data_ricezione)}</span>
            {msg.allegati_meta && msg.allegati_meta.length > 0 && (
              <span className="messaggio-item-allegati" aria-label={`${msg.allegati_meta.length} allegati`}>
                📎 {msg.allegati_meta.length}
              </span>
            )}
          </div>
        </div>
      ))}

      {/* Paginazione */}
      {pages > 1 && (
        <div className="messaggi-list-pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            aria-label="Pagina precedente"
          >
            ←
          </button>
          <span>
            {page} / {pages} ({total})
          </span>
          <button
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page >= pages}
            aria-label="Pagina successiva"
          >
            →
          </button>
        </div>
      )}
    </div>
  );
}
