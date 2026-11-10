import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { OggettoRelazione } from '../../../../core/components/Relazioni/RelazioniSection';
import SoggettiTable, { nomeSoggetto } from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable';
import { ConfirmDialog } from '../../../../core/components/common';
import { useToast } from '../../../../core/hooks';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './RuoloSoggettiPage.css';

const MAX_OGGETTI = 3;

/**
 * The anagrafiche of one module role (proprietario, conduttore): the shared
 * SoggettiTable prefiltered on the role, plus the objects of each relation,
 * the notes of the module record, and actions on that record only (the
 * anagrafica itself is never deleted from here).
 */
function RuoloSoggettiPage({
  ruolo, title, colonnaOggetti, recordsAPI, noteField, FormComponent, formProp,
  testi, addButtonLabel,
}) {
  const navigate = useNavigate();
  const toast = useToast();
  const [records, setRecords] = useState({});
  const [oggetti, setOggetti] = useState({});
  const [refreshKey, setRefreshKey] = useState(0);
  const [form, setForm] = useState(null);
  const [daTogliere, setDaTogliere] = useState(null);
  const [togliendo, setTogliendo] = useState(false);

  const carica = useCallback(async () => {
    const avvisa = (testo) => () => {
      toast.error(testo);
      return { data: [] };
    };
    const [rec, rel] = await Promise.all([
      recordsAPI.getAll().catch(avvisa('Impossibile caricare le note: riprova più tardi')),
      relazioniAPI.list({ tipo: ruolo }).catch(avvisa(`Impossibile caricare la colonna ${colonnaOggetti}`)),
    ]);
    setRecords(Object.fromEntries((rec.data || []).map((r) => [r.soggetto_id, r])));
    const perSoggetto = {};
    (rel.data || []).forEach((r) => {
      if (!r.descrizione) return;
      (perSoggetto[r.soggetto_id] ||= []).push(r);
    });
    setOggetti(perSoggetto);
  }, [recordsAPI, ruolo, colonnaOggetti]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { carica(); }, [carica, refreshKey]);

  const aggiorna = () => setRefreshKey((k) => k + 1);

  const extraColumns = useMemo(() => [
    {
      field: `oggetti_${ruolo}`,
      label: colonnaOggetti,
      render: (_, row) => {
        const lista = oggetti[row.id] || [];
        if (!lista.length) return '-';
        const visibili = lista.slice(0, MAX_OGGETTI);
        return (
          <ul className="ruolo-oggetti">
            {visibili.map((r, i) => (
              <li key={i} className={r.corrente ? undefined : 'ruolo-oggetti--cessato'}>
                <OggettoRelazione r={r} />{r.corrente ? '' : ' (cessato)'}
              </li>
            ))}
            {lista.length > MAX_OGGETTI && (
              <li><Link to={`/anagrafiche/${row.id}`}>+{lista.length - MAX_OGGETTI} altri</Link></li>
            )}
          </ul>
        );
      },
    },
    { field: `note_${ruolo}`, label: 'Note', render: (_, row) => records[row.id]?.[noteField] || '-' },
  ], [ruolo, colonnaOggetti, oggetti, records, noteField]);

  const rowActions = useMemo(() => [
    { id: 'apri', label: 'Apri anagrafica', variant: 'secondary', icon: renderIcon('external-link', { size: 14 }),
      onClick: (row) => navigate(`/anagrafiche/${row.id}`) },
    { id: 'note', label: 'Modifica note', variant: 'secondary', icon: renderIcon('pencil', { size: 14 }),
      onClick: (row) => setForm({ record: records[row.id] || { soggetto_id: row.id } }) },
    { id: 'togli', label: testi.azione, variant: 'danger', icon: renderIcon('user-minus', { size: 14 }),
      onClick: (row) => setDaTogliere(row) },
  ], [navigate, records, testi.azione]);

  const conferma = async () => {
    const record = records[daTogliere.id];
    if (!record) {
      toast.warning('Record non trovato: ricarica la pagina e riprova');
      setDaTogliere(null);
      return;
    }
    setTogliendo(true);
    try {
      await recordsAPI.delete(record.id);
      toast.success(testi.fatto);
      setDaTogliere(null);
      aggiorna();
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setTogliendo(false);
    }
  };

  return (
    <>
      <SoggettiTable
        ruolo={ruolo}
        title={title}
        showRuoli={false}
        extraColumns={extraColumns}
        rowActions={rowActions}
        addButtonLabel={addButtonLabel}
        onAdd={() => setForm({ record: null })}
        emptyMessage={testi.vuoto}
        refreshKey={refreshKey}
      />
      {form && (
        <FormComponent
          {...{ [formProp]: form.record }}
          onClose={() => { setForm(null); aggiorna(); }}
        />
      )}
      <ConfirmDialog
        isOpen={Boolean(daTogliere)}
        title={testi.azione}
        message={daTogliere ? testi.conferma(nomeSoggetto(daTogliere)) : ''}
        confirmLabel={testi.azione}
        cancelLabel="Annulla"
        variant="danger"
        loading={togliendo}
        onConfirm={conferma}
        onCancel={() => setDaTogliere(null)}
      />
    </>
  );
}

export default RuoloSoggettiPage;
