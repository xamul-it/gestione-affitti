import { useState, useEffect, useCallback } from 'react';
import { caselleAPI, schedulerAPI, auditAPI } from '../services/pecAPI';

const TABS = [
  { id: 'caselle', label: 'Caselle' },
  { id: 'scheduler', label: 'Scheduler' },
  { id: 'utenti', label: 'Utenti' },
  { id: 'audit', label: 'Audit' },
];

// ---------------------------------------------------------------------------
// Tab Caselle
// ---------------------------------------------------------------------------
function TabCaselle() {
  const [caselle, setCaselle] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errore, setErrore] = useState(null);
  const [testingId, setTestingId] = useState(null);
  const [testResults, setTestResults] = useState({});

  const carica = useCallback(() => {
    setLoading(true);
    caselleAPI
      .getAll()
      .then((r) => setCaselle(r.data || []))
      .catch(() => setErrore('Impossibile caricare le caselle'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { carica(); }, [carica]);

  const testConnessione = async (id) => {
    setTestingId(id);
    try {
      const res = await caselleAPI.testConnessione(id);
      setTestResults((prev) => ({ ...prev, [id]: res.data }));
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [id]: { successo: false, messaggio: err.response?.data?.detail || 'Errore di connessione' },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const toggleAttiva = async (casella) => {
    try {
      await caselleAPI.update(casella.id, { is_attiva: !casella.is_attiva });
      carica();
    } catch {
      // silenzioso — UI aggiornata al prossimo reload
    }
  };

  if (loading) return <p style={s.muted}>Caricamento...</p>;
  if (errore) return <p style={{ color: 'var(--color-error, #e53e3e)' }}>{errore}</p>;
  if (caselle.length === 0) {
    return <p style={s.muted}>Nessuna casella configurata. Usa l'API o il pannello di gestione per aggiungerne una.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {caselle.map((c) => {
        const result = testResults[c.id];
        return (
          <div key={c.id} style={s.card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <strong style={{ fontSize: '0.95rem' }}>{c.nome_display}</strong>
                <div style={s.muted}>{c.indirizzo_pec}</div>
                <div style={{ ...s.muted, fontSize: '0.75rem', marginTop: '4px' }}>
                  IMAP: {c.imap_host}:{c.imap_port} · Polling: ogni {c.polling_intervallo_minuti} min
                  {c.errori_consecutivi > 0 && (
                    <span style={{ color: 'var(--color-error, #e53e3e)', marginLeft: '8px' }}>
                      ⚠ {c.errori_consecutivi} errori consecutivi
                    </span>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span
                  style={{
                    ...s.badge,
                    background: c.is_attiva ? 'var(--color-success-bg, #f0fff4)' : 'var(--color-surface-alt, #f7fafc)',
                    color: c.is_attiva ? 'var(--color-success, #276749)' : s.muted.color,
                    border: `1px solid ${c.is_attiva ? 'var(--color-success, #68d391)' : 'var(--color-border, #e2e8f0)'}`,
                  }}
                >
                  {c.is_attiva ? 'Attiva' : 'Inattiva'}
                </span>
                <button style={s.btnSm} onClick={() => toggleAttiva(c)}>
                  {c.is_attiva ? 'Disattiva' : 'Attiva'}
                </button>
                <button
                  style={{ ...s.btnSm, opacity: testingId === c.id ? 0.6 : 1 }}
                  onClick={() => testConnessione(c.id)}
                  disabled={testingId === c.id}
                >
                  {testingId === c.id ? 'Test...' : 'Test IMAP'}
                </button>
              </div>
            </div>

            {result && (
              <div
                style={{
                  marginTop: '8px',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  fontSize: '0.82rem',
                  background: result.successo ? 'var(--color-success-bg, #f0fff4)' : 'var(--color-error-bg, #fff5f5)',
                  color: result.successo ? 'var(--color-success, #276749)' : 'var(--color-error, #c53030)',
                  border: `1px solid ${result.successo ? 'var(--color-success, #68d391)' : 'var(--color-error, #fc8181)'}`,
                }}
              >
                {result.successo ? '✓' : '✗'} {result.messaggio}
                {result.num_messaggi !== undefined && ` (${result.num_messaggi} messaggi)`}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab Scheduler
// ---------------------------------------------------------------------------
function TabScheduler() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errore, setErrore] = useState(null);
  const [triggeringAll, setTriggeringAll] = useState(false);

  const caricaStatus = useCallback(() => {
    setLoading(true);
    setErrore(null);
    schedulerAPI
      .getStatus()
      .then((r) => setStatus(r.data))
      .catch(() => setErrore('Errore nel caricamento dello stato scheduler'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { caricaStatus(); }, [caricaStatus]);

  const triggerAll = async () => {
    setTriggeringAll(true);
    try {
      await schedulerAPI.triggerAll();
      setTimeout(caricaStatus, 1500);
    } finally {
      setTriggeringAll(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button style={s.btnSm} onClick={caricaStatus} disabled={loading}>
          {loading ? 'Caricamento...' : '🔄 Aggiorna'}
        </button>
        <button style={s.btnSm} onClick={triggerAll} disabled={triggeringAll}>
          {triggeringAll ? 'Avvio...' : '▶ Poll tutti ora'}
        </button>
      </div>

      {errore && <p style={{ color: 'var(--color-error, #e53e3e)' }}>{errore}</p>}

      {status && (
        <>
          <p style={{ margin: '0 0 12px', fontSize: '0.875rem' }}>
            Stato: <strong>{status.running ? '🟢 In esecuzione' : '🔴 Fermo'}</strong>
            &nbsp;·&nbsp; Job attivi: <strong>{status.jobs?.length ?? 0}</strong>
          </p>
          {status.jobs?.length > 0 && (
            <table style={s.table}>
              <thead>
                <tr>
                  <th style={s.th}>Job ID</th>
                  <th style={s.th}>Nome</th>
                  <th style={s.th}>Prossima esecuzione</th>
                </tr>
              </thead>
              <tbody>
                {status.jobs.map((j) => (
                  <tr key={j.id}>
                    <td style={s.td}><code style={{ fontSize: '0.75rem' }}>{j.id}</code></td>
                    <td style={s.td}>{j.name}</td>
                    <td style={s.td}>{j.next_run ? new Date(j.next_run).toLocaleString('it-IT') : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab Utenti
// ---------------------------------------------------------------------------
function TabUtenti() {
  const [caselle, setCaselle] = useState([]);
  const [casellaSelezionata, setCasellaSelezionata] = useState(null);
  const [utenti, setUtenti] = useState([]);
  const [loadingCaselle, setLoadingCaselle] = useState(true);
  const [loadingUtenti, setLoadingUtenti] = useState(false);

  useEffect(() => {
    caselleAPI
      .getAll()
      .then((r) => {
        const lista = r.data || [];
        setCaselle(lista);
        if (lista.length > 0) setCasellaSelezionata(lista[0].id);
      })
      .finally(() => setLoadingCaselle(false));
  }, []);

  useEffect(() => {
    if (!casellaSelezionata) return;
    setLoadingUtenti(true);
    caselleAPI
      .getUtenti(casellaSelezionata)
      .then((r) => setUtenti(r.data || []))
      .catch(() => setUtenti([]))
      .finally(() => setLoadingUtenti(false));
  }, [casellaSelezionata]);

  const rimuovi = async (userId) => {
    await caselleAPI.removeUtente(casellaSelezionata, userId);
    setUtenti((prev) => prev.filter((u) => u.user_id !== userId));
  };

  if (loadingCaselle) return <p style={s.muted}>Caricamento...</p>;
  if (caselle.length === 0) return <p style={s.muted}>Nessuna casella configurata.</p>;

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <label style={{ ...s.muted, fontSize: '0.8rem', display: 'block', marginBottom: '4px' }}>
          Casella:
        </label>
        <select
          value={casellaSelezionata ?? ''}
          onChange={(e) => setCasellaSelezionata(Number(e.target.value))}
          style={s.select}
        >
          {caselle.map((c) => (
            <option key={c.id} value={c.id}>{c.nome_display} — {c.indirizzo_pec}</option>
          ))}
        </select>
      </div>

      {loadingUtenti && <p style={s.muted}>Caricamento utenti...</p>}

      {!loadingUtenti && utenti.length === 0 && (
        <p style={s.muted}>Nessun utente abilitato per questa casella.</p>
      )}

      {!loadingUtenti && utenti.length > 0 && (
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>User ID</th>
              <th style={s.th}>Può rispondere</th>
              <th style={s.th}>Notifica email</th>
              <th style={s.th}></th>
            </tr>
          </thead>
          <tbody>
            {utenti.map((u) => (
              <tr key={u.user_id}>
                <td style={s.td}>{u.user_id}</td>
                <td style={s.td}>{u.puo_rispondere ? '✓' : '—'}</td>
                <td style={s.td}>{u.notifica_email ? '✓' : '—'}</td>
                <td style={s.td}>
                  <button
                    style={{ ...s.btnSm, color: 'var(--color-error, #e53e3e)' }}
                    onClick={() => rimuovi(u.user_id)}
                  >
                    Rimuovi
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab Audit
// ---------------------------------------------------------------------------
function TabAudit() {
  const [tipoAudit, setTipoAudit] = useState('accessi');
  const [righe, setRighe] = useState([]);
  const [loading, setLoading] = useState(false);
  const [casellaId, setCasellaId] = useState('');
  const [caselle, setCaselle] = useState([]);

  useEffect(() => {
    caselleAPI.getAll().then((r) => setCaselle(r.data || []));
  }, []);

  const caricaAudit = useCallback(() => {
    setLoading(true);
    const params = { limit: 100 };
    if (casellaId) params.casella_id = Number(casellaId);

    const fn = tipoAudit === 'accessi' ? auditAPI.getAccessi : auditAPI.getRisposte;
    fn(params)
      .then((r) => setRighe(r.data || []))
      .catch(() => setRighe([]))
      .finally(() => setLoading(false));
  }, [tipoAudit, casellaId]);

  useEffect(() => { caricaAudit(); }, [caricaAudit]);

  const fmtDate = (v) => v ? new Date(v).toLocaleString('it-IT') : '—';

  return (
    <div>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div>
          <label style={{ ...s.muted, fontSize: '0.8rem', display: 'block', marginBottom: '4px' }}>Tipo:</label>
          <select value={tipoAudit} onChange={(e) => setTipoAudit(e.target.value)} style={s.select}>
            <option value="accessi">Accessi</option>
            <option value="risposte">Risposte inviate</option>
          </select>
        </div>
        <div>
          <label style={{ ...s.muted, fontSize: '0.8rem', display: 'block', marginBottom: '4px' }}>Casella:</label>
          <select value={casellaId} onChange={(e) => setCasellaId(e.target.value)} style={s.select}>
            <option value="">Tutte</option>
            {caselle.map((c) => (
              <option key={c.id} value={c.id}>{c.nome_display}</option>
            ))}
          </select>
        </div>
        <div style={{ alignSelf: 'flex-end' }}>
          <button style={s.btnSm} onClick={caricaAudit} disabled={loading}>
            {loading ? 'Caricamento...' : '🔄 Aggiorna'}
          </button>
        </div>
      </div>

      {!loading && righe.length === 0 && (
        <p style={s.muted}>Nessun record di audit trovato.</p>
      )}

      {!loading && righe.length > 0 && tipoAudit === 'accessi' && (
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Timestamp</th>
              <th style={s.th}>User ID</th>
              <th style={s.th}>Azione</th>
              <th style={s.th}>IP</th>
              <th style={s.th}>Msg ID</th>
            </tr>
          </thead>
          <tbody>
            {righe.map((r) => (
              <tr key={r.id}>
                <td style={s.td}>{fmtDate(r.timestamp)}</td>
                <td style={s.td}>{r.user_id}</td>
                <td style={s.td}><code style={{ fontSize: '0.75rem' }}>{r.azione}</code></td>
                <td style={s.td}>{r.ip_address || '—'}</td>
                <td style={s.td}>{r.messaggio_id ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && righe.length > 0 && tipoAudit === 'risposte' && (
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Data invio</th>
              <th style={s.th}>User ID</th>
              <th style={s.th}>Destinatari</th>
              <th style={s.th}>Oggetto</th>
              <th style={s.th}>SMTP</th>
              <th style={s.th}>Hash</th>
            </tr>
          </thead>
          <tbody>
            {righe.map((r) => (
              <tr key={r.id}>
                <td style={s.td}>{fmtDate(r.inviato_at || r.created_at)}</td>
                <td style={s.td}>{r.user_id}</td>
                <td style={s.td} title={r.destinatari}>
                  {r.destinatari ? r.destinatari.slice(0, 30) + (r.destinatari.length > 30 ? '…' : '') : '—'}
                </td>
                <td style={s.td} title={r.oggetto_risposta}>
                  {r.oggetto_risposta ? r.oggetto_risposta.slice(0, 40) + (r.oggetto_risposta.length > 40 ? '…' : '') : '—'}
                </td>
                <td style={{
                  ...s.td,
                  color: r.smtp_status === 'SENT'
                    ? 'var(--color-success, #276749)'
                    : r.smtp_status === 'FAILED'
                      ? 'var(--color-error, #c53030)'
                      : undefined,
                }}>
                  {r.smtp_status || '—'}
                </td>
                <td style={s.td} title={r.hash_integrita}>
                  <code style={{ fontSize: '0.68rem' }}>
                    {r.hash_integrita ? r.hash_integrita.slice(0, 12) + '…' : '—'}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina principale
// ---------------------------------------------------------------------------
export default function PecAdminPage() {
  const [tabAttiva, setTabAttiva] = useState('caselle');

  const tabContent = {
    caselle: <TabCaselle />,
    scheduler: <TabScheduler />,
    utenti: <TabUtenti />,
    audit: <TabAudit />,
  };

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ marginTop: 0, marginBottom: '20px' }}>Configurazione PEC</h2>

      <div style={{ display: 'flex', borderBottom: '2px solid var(--color-border, #e2e8f0)', marginBottom: '24px' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setTabAttiva(tab.id)}
            style={{
              padding: '8px 20px',
              border: 'none',
              borderBottom: tabAttiva === tab.id
                ? '2px solid var(--color-primary, #3182ce)'
                : '2px solid transparent',
              marginBottom: '-2px',
              background: 'transparent',
              cursor: 'pointer',
              fontWeight: tabAttiva === tab.id ? 600 : 400,
              color: tabAttiva === tab.id
                ? 'var(--color-primary, #3182ce)'
                : 'var(--color-text, #2d3748)',
              fontSize: '0.9rem',
              transition: 'color 0.15s, border-color 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabContent[tabAttiva]}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stili condivisi
// ---------------------------------------------------------------------------
const s = {
  muted: {
    color: 'var(--color-text-muted, #718096)',
    fontSize: '0.875rem',
    margin: 0,
  },
  card: {
    padding: '12px 16px',
    borderRadius: '8px',
    border: '1px solid var(--color-border, #e2e8f0)',
    background: 'var(--color-surface, #fff)',
  },
  badge: {
    borderRadius: '10px',
    padding: '2px 10px',
    fontSize: '0.78rem',
    fontWeight: 600,
  },
  btnSm: {
    padding: '5px 12px',
    border: '1px solid var(--color-border, #e2e8f0)',
    borderRadius: '4px',
    background: 'transparent',
    cursor: 'pointer',
    fontSize: '0.82rem',
    whiteSpace: 'nowrap',
  },
  select: {
    padding: '5px 8px',
    border: '1px solid var(--color-border, #e2e8f0)',
    borderRadius: '4px',
    fontSize: '0.875rem',
    background: 'var(--color-surface, #fff)',
    color: 'var(--color-text, #2d3748)',
    cursor: 'pointer',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.825rem',
  },
  th: {
    textAlign: 'left',
    padding: '8px 12px',
    borderBottom: '1px solid var(--color-border, #e2e8f0)',
    color: 'var(--color-text-muted, #718096)',
    fontWeight: 600,
    fontSize: '0.78rem',
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '8px 12px',
    borderBottom: '1px solid var(--color-border, #e2e8f0)',
    verticalAlign: 'top',
  },
};
