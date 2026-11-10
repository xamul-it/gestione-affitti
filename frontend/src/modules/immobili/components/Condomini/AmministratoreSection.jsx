import { useCallback, useEffect, useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { getSoggettoById } from '../../../anagrafica_italiana/services/anagraficaAPI';
import SoggettoPicker from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettoPicker';
import { nomeSoggetto } from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable';
import { ConfirmDialog, ErrorMessage, LoadingSpinner } from '../../../../core/components/common';
import { useToast } from '../../../../core/hooks';
import { formatDate } from '../../../../core/utils/formatters';
import Button from '../../../../components/UI/Button';
import { formatApiError } from '../../../../utils/errorHandling';
import './AmministratoreSection.css';

const TIPO = 'amministratore_condominio';

const oggiIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

/**
 * Administrator of a condominium as a linked anagrafica (core relation
 * amministratore_condominio): one-year mandate, renewed for the same period,
 * with its expiry in the scadenziario.
 */
function AmministratoreSection({ condominioId, legacy = {} }) {
  const dataId = useId();
  const toast = useToast();
  const [corrente, setCorrente] = useState(undefined);
  const [soggetto, setSoggetto] = useState(null);
  const [erroreCarico, setErroreCarico] = useState(null);
  const [scelto, setScelto] = useState(null);
  const [dal, setDal] = useState(oggiIso());
  const [errore, setErrore] = useState(null);
  const [lavoro, setLavoro] = useState(false);
  const [conferma, setConferma] = useState(null); // 'rinnova' | 'chiudi'

  const carica = useCallback(async () => {
    setErroreCarico(null);
    try {
      const res = await relazioniAPI.list({
        tipo: TIPO, entity_type: 'CONDOMINIO', entity_id: condominioId, solo_correnti: true,
      });
      const rel = (res.data || [])[0] || null;
      setSoggetto(rel ? await getSoggettoById(rel.soggetto_id).catch(() => null) : null);
      setCorrente(rel);
    } catch (err) {
      setErroreCarico(formatApiError(err));
      setCorrente(null);
    }
  }, [condominioId]);

  useEffect(() => { carica(); }, [carica]);

  const esegui = async (fn, messaggio) => {
    setLavoro(true);
    setErrore(null);
    try {
      const res = await fn();
      toast.success(typeof messaggio === 'function' ? messaggio(res) : messaggio);
      await carica();
    } catch (err) {
      setErrore(formatApiError(err));
    } finally {
      setLavoro(false);
      setConferma(null);
    }
  };

  const collega = () => esegui(async () => {
    await relazioniAPI.create({
      tipo: TIPO, entity_type: 'CONDOMINIO', entity_id: condominioId, soggetto_id: scelto.id, data_inizio: dal,
    });
    setScelto(null);
  }, 'Amministratore collegato');

  const legacyTesto = [legacy.amministratore_nome, legacy.amministratore_telefono, legacy.amministratore_email]
    .filter(Boolean).join(', ');

  if (erroreCarico) return <ErrorMessage message={erroreCarico} onRetry={carica} />;
  if (corrente === undefined) return <LoadingSpinner size="small" message="Caricamento amministratore..." />;

  return (
    <div className="amministratore">
      {errore && (
        <div role="alert"><ErrorMessage message={errore} onDismiss={() => setErrore(null)} /></div>
      )}

      {corrente ? (
        <>
          <dl className="amministratore__dati">
            <div>
              <dt>Amministratore</dt>
              <dd>
                <Link to={`/anagrafiche/${corrente.soggetto_id}`}>
                  {soggetto ? nomeSoggetto(soggetto) : `Anagrafica ${corrente.soggetto_id}`}
                </Link>
              </dd>
            </div>
            <div><dt>In carica dal</dt><dd>{corrente.data_inizio ? formatDate(corrente.data_inizio) : '—'}</dd></div>
            <div><dt>Scadenza mandato</dt><dd>{corrente.data_scadenza ? formatDate(corrente.data_scadenza) : '—'}</dd></div>
          </dl>
          <div className="amministratore__azioni">
            <Button type="button" variant="secondary" disabled={lavoro} onClick={() => setConferma('rinnova')}>
              Rinnova mandato
            </Button>
            <Button type="button" variant="danger" disabled={lavoro} onClick={() => setConferma('chiudi')}>
              Chiudi incarico
            </Button>
          </div>
          <ConfirmDialog
            isOpen={conferma === 'rinnova'}
            title="Rinnova mandato"
            message="Rinnovare il mandato per un altro anno? La scadenza nello scadenziario si sposta di conseguenza."
            confirmLabel="Rinnova"
            cancelLabel="Annulla"
            loading={lavoro}
            onConfirm={() => esegui(
              () => relazioniAPI.rinnova(corrente.relazione_id),
              (res) => `Mandato rinnovato fino al ${res?.data?.data_scadenza ? formatDate(res.data.data_scadenza) : 'nuova scadenza'}`,
            )}
            onCancel={() => setConferma(null)}
          />
          <ConfirmDialog
            isOpen={conferma === 'chiudi'}
            title="Chiudi incarico"
            message="Chiudere l'incarico dell'amministratore con data di oggi? La scadenza del mandato verrà segnata come completata."
            confirmLabel="Chiudi"
            cancelLabel="Annulla"
            variant="danger"
            loading={lavoro}
            onConfirm={() => esegui(() => relazioniAPI.update(corrente.relazione_id, { data_fine: oggiIso() }), 'Incarico chiuso')}
            onCancel={() => setConferma(null)}
          />
        </>
      ) : (
        <>
          {legacyTesto && (
            <p className="amministratore__info">Dati precedenti: {legacyTesto}</p>
          )}
          <div className="amministratore__nuovo">
            <SoggettoPicker label="Amministratore" value={scelto} onSelect={setScelto} />
            <div className="amministratore__data">
              <label htmlFor={dataId}>In carica dal</label>
              <input id={dataId} type="date" value={dal} onChange={(e) => setDal(e.target.value)} />
            </div>
            <p className="amministratore__info">
              Il mandato dura un anno e si rinnova per un altro anno. La scadenza compare nello scadenziario.
            </p>
            <Button type="button" variant="primary" disabled={!scelto || !dal} loading={lavoro} onClick={collega}>
              Collega amministratore
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export default AmministratoreSection;
