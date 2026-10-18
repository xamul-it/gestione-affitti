import { useRef, useEffect } from 'react';
import './Messaggi.css';

function formatData(dateString) {
  if (!dateString) return '';
  try {
    return new Date(dateString).toLocaleString('it-IT');
  } catch {
    return dateString;
  }
}

function formatDimensione(bytes) {
  if (!bytes || bytes === 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Blocca il caricamento di risorse remote (immagini/pixel di tracking,
// font, fogli di stile esterni) dal corpo HTML di un messaggio PEC non
// fidato. Lo sandbox dell'iframe blocca già JS/form; questo chiude il
// canale rimasto aperto (tracking via richieste di rete) senza dover
// aggiungere una dipendenza di sanitizzazione HTML.
//
// Usa DOMParser (lo stesso parser HTML del browser) invece di regex:
// un body malevolo può contenere testo simile a "<head>" dentro un
// commento o il valore di un attributo, che una regex individuerebbe
// ma che non è la vera testa del documento come la intende il
// renderer — la CSP finirebbe iniettata nel punto sbagliato (o resa
// inerte) mentre la vera <head> resta senza protezione.
const CSP_CONTENT =
  "default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline' data:;";

function withCspNoNetwork(html) {
  try {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const meta = doc.createElement('meta');
    meta.setAttribute('http-equiv', 'Content-Security-Policy');
    meta.setAttribute('content', CSP_CONTENT);
    doc.head.insertBefore(meta, doc.head.firstChild);
    return doc.documentElement.outerHTML;
  } catch {
    // Fallback: documento minimale interamente sotto il nostro controllo.
    return `<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="${CSP_CONTENT}"></head><body></body></html>`;
  }
}

/**
 * MessaggioDetail
 *
 * Props:
 *   messaggio      {object|null}  Messaggio completo da mostrare
 *   onRispondi     {function}     Callback per risposta (Fase 4)
 *   puoRispondere  {bool}         Abilita il pulsante Rispondi (Fase 4)
 */
export default function MessaggioDetail({ messaggio, onRispondi, puoRispondere = false }) {
  const iframeRef = useRef(null);

  // Regola l'altezza dell'iframe al contenuto dopo il caricamento
  const handleIframeLoad = () => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    try {
      const height = iframe.contentDocument?.body?.scrollHeight;
      if (height && height > 0) {
        iframe.style.height = `${height + 32}px`;
      }
    } catch {
      // Ignora errori cross-origin (non dovrebbe accadere con srcDoc)
    }
  };

  // Resetta l'altezza dell'iframe quando cambia il messaggio
  useEffect(() => {
    if (iframeRef.current) {
      iframeRef.current.style.height = '400px';
    }
  }, [messaggio?.id]);

  if (!messaggio) {
    return (
      <div className="messaggio-detail">
        <div className="messaggio-placeholder">
          <div className="messaggio-placeholder-icon">✉️</div>
          <span>Seleziona un messaggio per visualizzarlo</span>
        </div>
      </div>
    );
  }

  const allegati = messaggio.allegati_meta || [];

  return (
    <div className="messaggio-detail">
      {/* Intestazioni */}
      <div className="messaggio-header">
        <div className="messaggio-oggetto">{messaggio.oggetto || '(nessun oggetto)'}</div>

        <div className="messaggio-header-row">
          <span className="messaggio-header-label">Da:</span>
          <span className="messaggio-header-value">{messaggio.da}</span>
        </div>

        {messaggio.a && (
          <div className="messaggio-header-row">
            <span className="messaggio-header-label">A:</span>
            <span className="messaggio-header-value">{messaggio.a}</span>
          </div>
        )}

        {messaggio.cc && (
          <div className="messaggio-header-row">
            <span className="messaggio-header-label">CC:</span>
            <span className="messaggio-header-value">{messaggio.cc}</span>
          </div>
        )}

        <div className="messaggio-header-row">
          <span className="messaggio-header-label">Data:</span>
          <span className="messaggio-header-value">
            {formatData(messaggio.data_invio || messaggio.data_ricezione)}
          </span>
        </div>

        {allegati.length > 0 && (
          <div className="messaggio-header-row">
            <span className="messaggio-header-label">Allegati:</span>
            <span className="messaggio-header-value">📎 {allegati.length}</span>
          </div>
        )}
      </div>

      {/* Allegati */}
      {allegati.length > 0 && (
        <div className="messaggio-allegati-list">
          <h4>Allegati ({allegati.length})</h4>
          {allegati.map((allegato, idx) => (
            <div key={idx} className="messaggio-allegato-item">
              <span>📎</span>
              <span>{allegato.nome || allegato.filename || `Allegato ${idx + 1}`}</span>
              {allegato.dimensione_bytes != null && (
                <span className="messaggio-allegato-dim">
                  {formatDimensione(allegato.dimensione_bytes)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Corpo del messaggio */}
      <div className="messaggio-corpo">
        {messaggio.corpo_html ? (
          /*
           * RENDERING HTML SICURO: si usa sempre un iframe con sandbox.
           * sandbox="allow-same-origin" consente all'onLoad di leggere
           * scrollHeight, ma blocca JS e form.
           */
          <iframe
            ref={iframeRef}
            sandbox="allow-same-origin"
            srcDoc={withCspNoNetwork(messaggio.corpo_html)}
            className="messaggio-corpo-iframe"
            title="Corpo messaggio PEC"
            onLoad={handleIframeLoad}
          />
        ) : (
          <pre className="messaggio-corpo-testo">
            {messaggio.corpo_testo || '(nessun corpo)'}
          </pre>
        )}
      </div>

      {/* Pulsante Rispondi — attivo solo in Fase 4 */}
      {puoRispondere && (
        <div style={{ marginTop: '16px' }}>
          <button
            onClick={() => onRispondi && onRispondi(messaggio)}
            style={{
              padding: '8px 16px',
              background: 'var(--color-primary, #3182ce)',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            ↩ Rispondi
          </button>
        </div>
      )}
    </div>
  );
}
