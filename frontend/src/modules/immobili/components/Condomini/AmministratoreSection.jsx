import { useCallback, useEffect, useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { getSoggettoById } from '../../../anagrafica_italiana/services/anagraficaAPI';
import SoggettoPicker from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettoPicker';
import { nomeSoggetto } from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable';
import { ConfirmDialog } from '../../../../core/components/common';
import { formatApiError } from '../../../../utils/errorHandling';
import './AmministratoreSection.css';

const TIPO = 'amministratore_condominio';

const formatData = (iso) => {
  if (!iso) return '—';
  const [y, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${y}`;
};

const oggiIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

/**
 * Administrator of a condominium as a linked anagrafica (core relation
 * amministratore_condominio): one-year mandate, renewed for the same period
 * (art. 1129 c.c.), with its expiry in the scadenziario.
 */
function AmministratoreSection({ condominioId, legacy = {} }) {
  const dataId = useId();
  const [corrente, setCorrente] = useState(undefined);
  const [soggetto, setSoggetto] = useState(null);
  const [scelto, setScelto] = useState(null);
  const [dal, setDal] = useState(oggiIso());
  const [errore, setErrore] = useState(null);
  const [lavoro, setLavoro] = useState(false);
  const [chiudere, setChiudere] = useState(false);

  const carica = useCallback(async () => {
    try {
      const res = await relazioniAPI.list({
        tipo: TIPO, entity_type: 'CONDOMINIO', entity_id: condominioId, solo_correnti: true,
      });
      const rel = (res.data || [])[0] || null;
      setCorrente(rel);
      setSoggetto(rel ? await getSoggettoById(rel.soggetto_id).catch(() => null) : null);
    } catch (err) {
      setCorrente(null);
      setErrore(formatApiError(err));
    }
  }, [condominioId]);

  useEffect(() => { carica(); }, [carica]);

  const esegui = async (fn) => {
    setLavoro(true);
    setErrore(null);
    try {
      await fn();
      await carica();
    } catch (err) {
      setErrore(formatApiError(err));
    } finally {
      setLavoro(false);
    }
  };

  const collega = () => esegui(async () => {
    await relazioniAPI.create({
      tipo: TIPO, entity_type: 'CONDOMINIO', entity_id: condominioId, soggetto_id: scelto.id, data_inizio: dal,
    });
    setScelto(null);
  });

  const legacyTesto = [legacy.amministratore_nome, legacy.amministratore_telefono, legacy.amministratore_email]
    .filter(Boolean).join(', ');

  if (corrente === undefined) return <p className="amministratore__info">Caricamento amministratore…</p>;

  return (
    <div className="amministratore">
      {errore && <div className="error-message" role="alert">{errore}</div>}

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
            <div><dt>In carica dal</dt><dd>{formatData(corrente.data_inizio)}</dd></div>
            <div><dt>Scadenza mandato</dt><dd>{formatData(corrente.data_scadenza)}</dd></div>
          </dl>
          <div className="amministratore__azioni">
            <button type="button" className="btn btn-secondary" disabled={lavoro}
              onClick={() => esegui(() => relazioniAPI.rinnova(corrente.relazione_id))}>
              Rinnova mandato
            </button>
            <button type="button" className="btn btn-danger" disabled={lavoro} onClick={() => setChiudere(true)}>
              Chiudi incarico
            </button>
          </div>
          <ConfirmDialog
            isOpen={chiudere}
            title="Chiudi incarico"
            message="Chiudere l'incarico dell'amministratore con data di oggi? La scadenza del mandato verrà segnata come completata."
            confirmLabel="Chiudi"
            cancelLabel="Annulla"
            variant="danger"
            loading={lavoro}
            onConfirm={() => { setChiudere(false); esegui(() => relazioniAPI.update(corrente.relazione_id, { data_fine: oggiIso() })); }}
            onCancel={() => setChiudere(false)}
          />
        </>
      ) : (
        <>
          {legacyTesto && !errore && (
            <p className="amministratore__info">Dati precedenti: {legacyTesto}</p>
          )}
          <div className="amministratore__nuovo">
            <SoggettoPicker label="Amministratore" value={scelto} onSelect={setScelto} />
            <div className="amministratore__data">
              <label htmlFor={dataId}>In carica dal</label>
              <input id={dataId} type="date" value={dal} onChange={(e) => setDal(e.target.value)} />
            </div>
            <p className="amministratore__info">
              Il mandato dura un anno e si rinnova per un altro anno (art. 1129 c.c.): la scadenza va nello scadenziario.
            </p>
            <button type="button" className="btn btn-primary" disabled={!scelto || !dal || lavoro} onClick={collega}>
              Collega amministratore
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default AmministratoreSection;
