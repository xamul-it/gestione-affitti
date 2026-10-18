import { useState, useEffect } from 'react';
import { caselleAPI, messaggiAPI } from '../services/pecAPI';

/**
 * PecSummaryWidget — widget dashboard PEC.
 *
 * Mostra per ogni casella il numero di messaggi non letti.
 * Si aggiorna ogni 60 secondi.
 */
export default function PecSummaryWidget() {
  const [caselle, setCaselle] = useState([]);
  const [conteggi, setConteggi] = useState({});
  const [loading, setLoading] = useState(true);
  const [errore, setErrore] = useState(null);

  const caricaDati = async () => {
    try {
      const res = await caselleAPI.getAll();
      const lista = res.data || [];
      setCaselle(lista);

      // Recupera conteggio non letti per ogni casella in parallelo
      const risultati = await Promise.allSettled(
        lista.map((c) =>
          messaggiAPI
            .getAll({ casella_id: c.id, solo_non_letti: true, page_size: 1 })
            .then((r) => ({ id: c.id, totale: r.data?.totale ?? 0 }))
        )
      );
      const nuoviConteggi = {};
      risultati.forEach((r) => {
        if (r.status === 'fulfilled') {
          nuoviConteggi[r.value.id] = r.value.totale;
        }
      });
      setConteggi(nuoviConteggi);
      setErrore(null);
    } catch (err) {
      setErrore('Impossibile caricare i dati PEC');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    caricaDati();
    const timer = setInterval(caricaDati, 60_000);
    return () => clearInterval(timer);
  }, []);

  const totalNonLetti = Object.values(conteggi).reduce((s, v) => s + v, 0);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.icon}>✉️</span>
          <span style={styles.title}>PEC</span>
        </div>
        <p style={styles.muted}>Caricamento...</p>
      </div>
    );
  }

  if (errore) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.icon}>✉️</span>
          <span style={styles.title}>PEC</span>
        </div>
        <p style={{ ...styles.muted, color: 'var(--color-error, #e53e3e)' }}>{errore}</p>
      </div>
    );
  }

  if (caselle.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.icon}>✉️</span>
          <span style={styles.title}>PEC</span>
        </div>
        <p style={styles.muted}>Nessuna casella configurata</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.icon}>✉️</span>
        <span style={styles.title}>PEC</span>
        {totalNonLetti > 0 && (
          <span style={styles.badge}>{totalNonLetti}</span>
        )}
      </div>

      <div style={styles.lista}>
        {caselle.map((c) => {
          const nonLetti = conteggi[c.id] ?? 0;
          return (
            <div key={c.id} style={styles.riga}>
              <div style={styles.rigaSx}>
                <span
                  style={{
                    ...styles.indicatore,
                    background: c.is_attiva
                      ? 'var(--color-success, #38a169)'
                      : 'var(--color-text-muted, #a0aec0)',
                  }}
                />
                <div>
                  <div style={styles.nomeCasella}>{c.nome_display}</div>
                  <div style={styles.indirizzo}>{c.indirizzo_pec}</div>
                </div>
              </div>
              {nonLetti > 0 ? (
                <span style={styles.badgeCasella}>{nonLetti} nuovi</span>
              ) : (
                <span style={styles.aggiornato}>✓</span>
              )}
            </div>
          );
        })}
      </div>

      <a href="/pec" style={styles.link}>
        Apri caselle PEC →
      </a>
    </div>
  );
}

const styles = {
  container: {
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    height: '100%',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  icon: {
    fontSize: '1.2rem',
  },
  title: {
    fontWeight: 600,
    fontSize: '1rem',
    color: 'var(--color-text, #2d3748)',
    flex: 1,
  },
  badge: {
    background: 'var(--color-error, #e53e3e)',
    color: '#fff',
    borderRadius: '12px',
    padding: '2px 8px',
    fontSize: '0.75rem',
    fontWeight: 700,
    minWidth: '20px',
    textAlign: 'center',
  },
  lista: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    flex: 1,
    overflowY: 'auto',
  },
  riga: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 10px',
    borderRadius: '6px',
    background: 'var(--color-surface-alt, #f7fafc)',
    border: '1px solid var(--color-border, #e2e8f0)',
  },
  rigaSx: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  indicatore: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  nomeCasella: {
    fontSize: '0.875rem',
    fontWeight: 500,
    color: 'var(--color-text, #2d3748)',
    lineHeight: 1.2,
  },
  indirizzo: {
    fontSize: '0.75rem',
    color: 'var(--color-text-muted, #718096)',
    lineHeight: 1.2,
  },
  badgeCasella: {
    background: 'var(--color-warning-bg, #fefcbf)',
    color: 'var(--color-warning, #744210)',
    border: '1px solid var(--color-warning-border, #f6e05e)',
    borderRadius: '10px',
    padding: '2px 8px',
    fontSize: '0.72rem',
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  aggiornato: {
    color: 'var(--color-success, #38a169)',
    fontSize: '0.875rem',
  },
  muted: {
    color: 'var(--color-text-muted, #718096)',
    fontSize: '0.875rem',
    margin: 0,
  },
  link: {
    fontSize: '0.8rem',
    color: 'var(--color-primary, #3182ce)',
    textDecoration: 'none',
    alignSelf: 'flex-end',
  },
};
