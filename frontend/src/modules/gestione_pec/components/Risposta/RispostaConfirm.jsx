/**
 * RispostaConfirm
 *
 * Pagina di riepilogo/conferma prima dell'invio della risposta PEC.
 *
 * Props:
 *   casella       {object}   Casella PEC mittente (per mostrare indirizzo)
 *   destinatari   {string}   Destinatari (già formattati come stringa)
 *   oggetto       {string}   Oggetto della risposta
 *   corpo         {string}   Testo della risposta
 *   onConferma    {function} Callback di invio effettivo
 *   onIndietro    {function} Callback per tornare al form di composizione
 *   loading       {bool}     Indica invio in corso (disabilita pulsante)
 */
export default function RispostaConfirm({
  casella,
  destinatari,
  oggetto,
  corpo,
  onConferma,
  onIndietro,
  loading,
}) {
  const MAX_ANTEPRIMA = 300;
  const anteprimaCorpo =
    corpo.length > MAX_ANTEPRIMA ? corpo.slice(0, MAX_ANTEPRIMA) + '…' : corpo;

  const indirizzoMittente = casella?.indirizzo_pec || '(casella non disponibile)';

  return (
    <div className="risposta-confirm">
      <div className="risposta-confirm-warning">
        Stai per inviare una risposta PEC a nome di{' '}
        <strong>{indirizzoMittente}</strong>
      </div>

      <div className="risposta-confirm-dettagli">
        <div className="risposta-confirm-riga">
          <span className="risposta-confirm-riga-label">A:</span>
          <span>{destinatari}</span>
        </div>
        <div className="risposta-confirm-riga">
          <span className="risposta-confirm-riga-label">Oggetto:</span>
          <span>{oggetto}</span>
        </div>
      </div>

      <pre className="risposta-confirm-anteprima">{anteprimaCorpo}</pre>

      <p className="risposta-confirm-audit-note">
        Questa operazione verra registrata nel log di audit.
      </p>

      <div className="risposta-actions">
        <button
          type="button"
          className="risposta-btn risposta-btn-secondary"
          onClick={onIndietro}
          disabled={loading}
        >
          Modifica
        </button>
        <button
          type="button"
          className="risposta-btn risposta-btn-primary"
          onClick={onConferma}
          disabled={loading}
        >
          {loading && <span className="risposta-spinner" aria-hidden="true" />}
          {loading ? 'Invio in corso...' : 'Invia risposta'}
        </button>
      </div>
    </div>
  );
}
