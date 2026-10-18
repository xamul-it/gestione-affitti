import { useState, useEffect, useCallback } from 'react';
import { caselleAPI, messaggiAPI } from '../services/pecAPI';
import MessaggiList from '../components/Messaggi/MessaggiList';
import MessaggioDetail from '../components/Messaggi/MessaggioDetail';
import RispostaModal from '../components/Risposta/RispostaModal';
import '../components/Messaggi/Messaggi.css';

const POLLING_INTERVAL_MS = 60_000; // 60 secondi

/**
 * PecInboxPage — pagina principale inbox PEC.
 *
 * Layout a due pannelli: lista messaggi a sinistra, dettaglio a destra.
 * Polling automatico ogni 60 secondi per aggiornare la lista.
 */
export default function PecInboxPage() {
  const [caselle, setCaselle] = useState([]);
  const [casellaSelezionata, setCasellaSelezionata] = useState(null);
  const [messaggioDettaglio, setMessaggioDettaglio] = useState(null);
  const [caricandoCaselle, setCaricandoCaselle] = useState(true);
  const [erroreCaselle, setErroreCaselle] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [rispostaAperta, setRispostaAperta] = useState(false);
  const [toastMessaggio, setToastMessaggio] = useState(null);

  // Carica le caselle all'avvio
  useEffect(() => {
    setCaricandoCaselle(true);
    caselleAPI
      .getAll()
      .then((res) => {
        const lista = res.data || [];
        setCaselle(lista);
        // Seleziona automaticamente la prima casella se disponibile
        if (lista.length > 0 && !casellaSelezionata) {
          setCasellaSelezionata(lista[0].id);
        }
      })
      .catch((err) => {
        setErroreCaselle(err.response?.data?.detail || 'Errore nel caricamento delle caselle');
      })
      .finally(() => setCaricandoCaselle(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Polling ogni 60 secondi
  useEffect(() => {
    if (!casellaSelezionata) return;
    const interval = setInterval(() => {
      setRefreshTrigger((t) => t + 1);
    }, POLLING_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [casellaSelezionata]);

  const handleCambioUCasella = (nuovaId) => {
    setCasellaSelezionata(Number(nuovaId));
    setMessaggioDettaglio(null);
    setRefreshTrigger((t) => t + 1);
  };

  const handleSelectMessaggio = useCallback(async (msgRiepilogo) => {
    // Se il messaggio selezionato è già quello aperto, non fare nulla
    if (messaggioDettaglio?.id === msgRiepilogo.id) return;
    try {
      const res = await messaggiAPI.getById(msgRiepilogo.id);
      setMessaggioDettaglio(res.data);
      // Aggiorna la lista per riflettere il flag is_letto
      setRefreshTrigger((t) => t + 1);
    } catch {
      // In caso di errore mostra comunque i dati di riepilogo
      setMessaggioDettaglio(msgRiepilogo);
    }
  }, [messaggioDettaglio?.id]);

  const handleAggiorna = () => {
    setRefreshTrigger((t) => t + 1);
  };

  const handleRispondi = () => {
    setRispostaAperta(true);
  };

  const handleChiudiRisposta = () => {
    setRispostaAperta(false);
  };

  const handleRispostaInviata = (smtpStatus) => {
    setRispostaAperta(false);
    if (smtpStatus === 'SENT') {
      setToastMessaggio('Risposta inviata con successo.');
      // Aggiorna is_risposto nel dettaglio ricaricando il messaggio
      if (messaggioDettaglio) {
        setMessaggioDettaglio((prev) => prev ? { ...prev, is_risposto: true } : prev);
      }
    } else {
      setToastMessaggio('Invio non riuscito (SMTP). La risposta e stata registrata nel log di audit.');
    }
    setRefreshTrigger((t) => t + 1);
    // Nascondi il toast dopo 5 secondi
    setTimeout(() => setToastMessaggio(null), 5000);
  };

  const casellaCorrente = caselle.find((c) => c.id === casellaSelezionata);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 16px',
          borderBottom: '1px solid var(--color-border, #e2e8f0)',
          background: 'var(--color-surface, #fff)',
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: '1rem' }}>Caselle PEC</span>

        {caricandoCaselle ? (
          <span style={{ color: 'var(--color-text-muted, #718096)', fontSize: '0.875rem' }}>
            Caricamento caselle...
          </span>
        ) : erroreCaselle ? (
          <span style={{ color: 'var(--color-error, #e53e3e)', fontSize: '0.875rem' }}>
            {erroreCaselle}
          </span>
        ) : caselle.length === 0 ? (
          <span style={{ color: 'var(--color-text-muted, #718096)', fontSize: '0.875rem' }}>
            Nessuna casella disponibile
          </span>
        ) : (
          <select
            value={casellaSelezionata ?? ''}
            onChange={(e) => handleCambioUCasella(e.target.value)}
            style={{
              padding: '6px 10px',
              border: '1px solid var(--color-border, #e2e8f0)',
              borderRadius: '4px',
              fontSize: '0.875rem',
              minWidth: '220px',
            }}
            aria-label="Seleziona casella PEC"
          >
            {caselle.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome || c.indirizzo_pec}
              </option>
            ))}
          </select>
        )}

        <button
          onClick={handleAggiorna}
          disabled={!casellaSelezionata}
          style={{
            padding: '6px 12px',
            border: '1px solid var(--color-border, #e2e8f0)',
            borderRadius: '4px',
            background: 'transparent',
            cursor: casellaSelezionata ? 'pointer' : 'not-allowed',
            fontSize: '0.875rem',
          }}
          aria-label="Aggiorna messaggi"
        >
          🔄 Aggiorna
        </button>

        {casellaCorrente && (
          <span
            style={{
              marginLeft: 'auto',
              fontSize: '0.8rem',
              color: 'var(--color-text-muted, #718096)',
            }}
          >
            {casellaCorrente.indirizzo_pec}
          </span>
        )}
      </div>

      {/* Toast notifica risposta */}
      {toastMessaggio && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            background: 'var(--color-surface, #fff)',
            border: '1px solid var(--color-border, #e2e8f0)',
            borderRadius: '6px',
            padding: '12px 18px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.14)',
            zIndex: 1100,
            fontSize: '0.9rem',
            color: 'var(--color-text, #1a202c)',
            maxWidth: '360px',
          }}
        >
          {toastMessaggio}
        </div>
      )}

      {/* Pannelli principali */}
      <div className="messaggi-container">
        <MessaggiList
          casellaId={casellaSelezionata}
          onSelectMessaggio={handleSelectMessaggio}
          messaggioSelezionatoId={messaggioDettaglio?.id ?? null}
          refreshTrigger={refreshTrigger}
        />
        <MessaggioDetail
          messaggio={messaggioDettaglio}
          puoRispondere={!!messaggioDettaglio}
          onRispondi={handleRispondi}
        />
      </div>

      {/* Modale risposta */}
      {rispostaAperta && messaggioDettaglio && (
        <RispostaModal
          messaggio={messaggioDettaglio}
          casella={casellaCorrente}
          onClose={handleChiudiRisposta}
          onRispostaInviata={handleRispostaInviata}
        />
      )}
    </div>
  );
}
