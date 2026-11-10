import { useState, useCallback, useEffect, useId, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { DataTable } from '../../../../core/components';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import './SoggettiAnagraficiList.css';
import './SoggettiTable.css';

export const nomeSoggetto = (s) => (s.tipo_soggetto === 'PERSONA_FISICA'
  ? `${s.nome || ''} ${s.cognome || ''}`.trim() || '(Non specificato)'
  : s.ragione_sociale || '(Non specificato)');

export const linkSoggetto = (s) => (s.tipo_soggetto === 'PERSONA_FISICA'
  ? `/anagrafiche/persone-fisiche/${s.id}`
  : `/anagrafiche/persone-giuridiche/${s.id}`);

const dash = (value) => value || '-';

function RuoliBadges({ ruoli = [] }) {
  if (!ruoli.length) return '-';
  return (
    <span className="soggetti-ruoli">
      {ruoli.map((r) => (
        <span
          key={r.codice}
          className={`soggetti-ruolo${r.n > 0 ? '' : ' soggetti-ruolo--cessato'}`}
          title={r.n > 0 ? `${r.n} in corso` : 'Solo relazioni cessate'}
        >
          {r.nome}
        </span>
      ))}
    </span>
  );
}

/**
 * The anagrafiche list, reusable by any module: optional role prefilter
 * (`ruolo`, a relation type code), module columns (`extraColumns`) and
 * actions. Without handlers the rows open the anagrafica pages.
 */
function SoggettiTable({
  ruolo,
  title = 'Anagrafiche',
  extraColumns = [],
  rowActions,
  onAdd,
  onView,
  onEdit,
  onDelete,
  customActions,
  addButtonLabel = 'Nuova Anagrafica',
  emptyMessage,
  showRuoli = true,
  showFiltroRuolo = false,
  toolbarExtra,
  hideAddButton = false,
  refreshKey = 0,
}) {
  const [attiviSolo, setAttiviSolo] = useState(false);
  const [ancheCessati, setAncheCessati] = useState(false);
  const [ruoloScelto, setRuoloScelto] = useState('');
  const [tipi, setTipi] = useState([]);
  const filtroId = useId();
  const ruoloAttivo = ruolo || ruoloScelto || undefined;

  useEffect(() => {
    if (!showFiltroRuolo) return;
    relazioniAPI.getTipi().then((res) => setTipi(res.data || [])).catch(() => setTipi([]));
  }, [showFiltroRuolo]);

  const params = useMemo(() => {
    const p = { limit: 1000 };
    if (ruoloAttivo) p.ruolo = ruoloAttivo;
    if (ruoloAttivo && ancheCessati) p.ruolo_anche_cessati = true;
    return p;
  }, [ruoloAttivo, ancheCessati]);

  const columns = useMemo(() => [
    {
      field: 'tipo_soggetto',
      label: 'Tipo',
      render: (value) => (
        <span className="tipo-badge" title={value === 'PERSONA_FISICA' ? 'Persona fisica' : 'Persona giuridica'}>
          {renderIcon(value === 'PERSONA_FISICA' ? 'user' : 'building', { size: 14 })}
        </span>
      ),
    },
    {
      field: 'nome_completo',
      label: 'Nome / Ragione Sociale',
      sortable: true,
      render: (_, row) => <Link to={linkSoggetto(row)} className="table-link">{nomeSoggetto(row)}</Link>,
    },
    ...(showRuoli ? [{ field: 'ruoli', label: 'Ruoli', render: (value) => <RuoliBadges ruoli={value} /> }] : []),
    ...extraColumns,
    { field: 'partita_iva', label: 'Partita IVA', filterable: true, render: dash },
    { field: 'email', label: 'Email', filterable: true, render: dash },
    { field: 'telefono', label: 'Telefono', filterable: true, render: (value, row) => value || row.cellulare || '-' },
    { field: 'codice_fiscale', label: 'Codice Fiscale', filterable: true, visible: false, render: dash },
    { field: 'citta', label: 'Città', filterable: true, visible: false, render: dash },
    {
      field: 'attivo',
      label: 'Stato',
      visible: false,
      render: (value) => (
        <span className={`status-badge ${value ? 'active' : 'inactive'}`}>{value ? 'Attivo' : 'Inattivo'}</span>
      ),
    },
    { field: 'nome', label: 'Nome', filterable: true, visible: false },
    { field: 'cognome', label: 'Cognome', filterable: true, visible: false },
    { field: 'ragione_sociale', label: 'Ragione Sociale', filterable: true, visible: false },
  ], [extraColumns, showRuoli]);

  const renderToolbar = useCallback(({ table }) => (
    <div className="soggetti-toolbar">
      <label className="filter-checkbox">
        <input
          type="checkbox"
          checked={attiviSolo}
          onChange={(e) => {
            setAttiviSolo(e.target.checked);
            table.setFilter('attivo', e.target.checked ? true : '');
          }}
        />
        <span>Solo attivi</span>
      </label>
      {ruoloAttivo && (
        <label className="filter-checkbox">
          <input type="checkbox" checked={ancheCessati} onChange={(e) => setAncheCessati(e.target.checked)} />
          <span>Anche cessati</span>
        </label>
      )}
      {showFiltroRuolo && (
        <span className="filter-checkbox">
          <label htmlFor={filtroId}>Ruolo</label>
          <select id={filtroId} value={ruoloScelto} onChange={(e) => setRuoloScelto(e.target.value)}>
            <option value="">Tutti</option>
            {tipi.map((t) => <option key={t.codice} value={t.codice}>{t.nome}</option>)}
          </select>
        </span>
      )}
      {typeof toolbarExtra === 'function' ? toolbarExtra({ table }) : toolbarExtra}
    </div>
  ), [attiviSolo, ancheCessati, ruoloAttivo, showFiltroRuolo, ruoloScelto, tipi, filtroId, toolbarExtra]);

  const config = {
    endpoint: '/anagrafica/soggetti-v2/',
    title,
    searchPlaceholder: 'Cerca per nome, ragione sociale, CF o email...',
    emptyTitle: 'Nessuna anagrafica trovata',
    emptyMessage: emptyMessage || 'Non ci sono anagrafiche registrate.',
    addButtonLabel,
    defaultParams: params,
    columns,
    defaultSort: { field: 'nome', order: 'asc' },
    rowActions: rowActions || [
      { id: 'view', label: 'Dettagli', action: 'view', variant: 'secondary', icon: renderIcon('info', { size: 14 }) },
      { id: 'edit', label: 'Modifica', action: 'edit', variant: 'secondary', icon: renderIcon('pencil', { size: 14 }) },
      { id: 'delete', label: 'Elimina', action: 'delete', variant: 'danger', icon: renderIcon('trash', { size: 14 }) },
    ],
  };

  return (
    <div className="soggetti-list-container">
      <DataTable
        // The table fetches on mount: remount when the server-side prefilter changes.
        key={`${JSON.stringify(params)}:${refreshKey}`}
        config={config}
        toolbarContent={renderToolbar}
        onAdd={onAdd}
        onView={onView}
        onEdit={onEdit}
        onDelete={onDelete}
        customActions={customActions}
        hideAddButton={hideAddButton}
        options={{ selectable: false, showSearch: true, showPagination: true, pageSize: 50 }}
      />
    </div>
  );
}

export default SoggettiTable;
