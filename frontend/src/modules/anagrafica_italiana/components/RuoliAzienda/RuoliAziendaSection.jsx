import { useState, useMemo, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import { ruoliAziendaAPI } from '../../../../services/ruoliAziendaAPI';
import RuoloAziendaForm from './RuoloAziendaForm';
import { DataTable } from '../../../../core/components';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './RuoliAziendaSection.css';

/**
 * Sezione per visualizzare e gestire i ruoli azienda di un soggetto
 * Usabile sia per persone fisiche (mostra aziende) che per persone giuridiche (mostra persone)
 */
export default function RuoliAziendaSection({ soggetto, onUpdate }) {
  const [showForm, setShowForm] = useState(false);
  const [editingRuolo, setEditingRuolo] = useState(null);
  const [showAttiviOnly, setShowAttiviOnly] = useState(false);
  const tableRef = useRef(null);

  const token = localStorage.getItem('access_token');
  const isPersonaFisica = soggetto.tipo_soggetto === 'PERSONA_FISICA';

  const handleSave = async (data, id) => {
    if (id) {
      // Update
      await ruoliAziendaAPI.update(id, data, token);
    } else {
      // Create
      await ruoliAziendaAPI.create(data, token);
    }
    if (onUpdate) onUpdate();
    if (tableRef.current) {
      tableRef.current.refresh();
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Sei sicuro di voler eliminare questo ruolo?')) return;

    try {
      await ruoliAziendaAPI.delete(id, token);
      if (onUpdate) onUpdate();
      if (tableRef.current) {
        tableRef.current.refresh();
      }
    } catch (err) {
      console.error('Error deleting ruolo:', err);
      alert('Errore nell\'eliminazione del ruolo');
    }
  };

  const handleEdit = (ruolo) => {
    setEditingRuolo(ruolo);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingRuolo(null);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const isRuoloAttivo = (ruolo) => {
    if (!ruolo.data_fine) return true;
    const dataFine = new Date(ruolo.data_fine);
    return dataFine >= new Date();
  };

  const getControparteInfo = useCallback((ruolo) => {
    const controparte = isPersonaFisica ? ruolo.persona_giuridica : ruolo.persona_fisica;
    const controparteId = isPersonaFisica ? ruolo.persona_giuridica_id : ruolo.persona_fisica_id;
    let nome = 'Sconosciuto';
    if (controparte) {
      if (isPersonaFisica) {
        nome = controparte.ragione_sociale || controparte.partita_iva || 'Sconosciuto';
      } else {
        const parts = [controparte.nome, controparte.cognome].filter(Boolean);
        nome = parts.join(' ').trim() || controparte.codice_fiscale || 'Sconosciuto';
      }
    }
    const path = isPersonaFisica
      ? `/anagrafiche/persone-giuridiche/${controparteId}`
      : `/anagrafiche/persone-fisiche/${controparteId}`;
    return { controparteId, nome, path };
  }, [isPersonaFisica]);

  const tableConfig = useMemo(() => ({
    endpoint: '/anagrafica/ruoli-azienda/',
    title: isPersonaFisica ? 'Ruoli in Aziende' : 'Persone Associate',
    searchPlaceholder: 'Cerca...',
    emptyTitle: isPersonaFisica ? 'Nessun ruolo aziendale' : 'Nessuna persona associata',
    emptyMessage: isPersonaFisica
      ? 'Nessun ruolo aziendale registrato per questa persona.'
      : 'Nessuna persona associata a questa azienda.',
    addButtonLabel: 'Aggiungi Ruolo',
    defaultParams: { limit: 1000 },
    defaultFilters: {
      [isPersonaFisica ? 'persona_fisica_id' : 'persona_giuridica_id']: (value) => value === soggetto.id,
    },
    columns: [
      {
        field: isPersonaFisica ? 'persona_giuridica.ragione_sociale' : 'persona_fisica.nome',
        label: isPersonaFisica ? 'Azienda' : 'Persona',
        filterable: true,
        sortable: true,
        render: (value, row) => {
          const info = getControparteInfo(row);
          return info.controparteId ? (
            <Link to={info.path} className="table-link">
              <strong>{info.nome}</strong>
            </Link>
          ) : (
            <strong>{info.nome}</strong>
          );
        },
      },
      {
        field: 'ruolo_tipo_nome',
        label: 'Ruolo',
        filterable: true,
        render: (value, row) => (
          <div className="ruolo-cell">
            <span className="ruolo-badge">
              {value || row.ruolo || '(Non specificato)'}
            </span>
            {!row.ruolo_tipo_id && row.ruolo && (
              <span className="ruolo-custom" title="Ruolo personalizzato non collegato ai domini">
                {renderIcon('alert-triangle', { size: 12, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
                Custom
              </span>
            )}
          </div>
        ),
      },
      {
        field: 'data_inizio',
        label: 'Periodo',
        render: (value, row) => (
          <div className="date-range">
            {row.data_inizio && (
              <span className="date-start">Dal {formatDate(row.data_inizio)}</span>
            )}
            {row.data_fine && (
              <span className="date-end">Al {formatDate(row.data_fine)}</span>
            )}
            {!row.data_inizio && !row.data_fine && (
              <span className="no-dates">Non specificato</span>
            )}
          </div>
        ),
      },
      {
        field: 'stato_ruolo',
        label: 'Stato',
        render: (value, row) => (
          isRuoloAttivo(row) ? (
            <span className="status-badge status-active">Attivo</span>
          ) : (
            <span className="status-badge status-inactive">Scaduto</span>
          )
        ),
      },
    ],
    rowActions: [
      {
        id: 'edit',
        label: 'Modifica',
        action: 'edit',
        variant: 'secondary',
        icon: renderIcon('pencil', { size: 14 }),
      },
      {
        id: 'delete',
        label: 'Elimina',
        action: 'delete',
        variant: 'danger',
        icon: renderIcon('trash', { size: 14 }),
      },
    ],
  }), [getControparteInfo, isPersonaFisica, soggetto.id]);

  const renderToolbar = useCallback(({ table }) => (
    <label className="checkbox-filter">
      <input
        type="checkbox"
        checked={showAttiviOnly}
        onChange={(e) => {
          const checked = e.target.checked;
          setShowAttiviOnly(checked);
          table.setFilter('ruolo_attivo', checked
            ? (value, row) => !row.data_fine || new Date(row.data_fine) >= new Date()
            : ''
          );
        }}
      />
      Solo attivi
    </label>
  ), [showAttiviOnly]);

  return (
    <div className="ruoli-azienda-section">
      <div className="section-header">
        <div className="section-title">
          <h3>
            <span className="inline-icon" aria-hidden="true">
              {renderIcon(isPersonaFisica ? 'building' : 'users', { size: 18, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
            </span>
            {isPersonaFisica ? 'Ruoli in Aziende' : 'Persone Associate'}
          </h3>
          <p className="section-subtitle">
            {isPersonaFisica
              ? 'Aziende in cui questa persona ha un ruolo'
              : 'Persone che hanno un ruolo in questa azienda'}
          </p>
        </div>
        <div className="section-actions">
          <button className="btn-add" onClick={() => setShowForm(true)}>
            <span className="button-icon">
              {renderIcon('plus', { size: 16, className: 'detail-icon', fallbackClassName: 'nav-emoji-icon' })}
            </span>
            Aggiungi Ruolo
          </button>
        </div>
      </div>

      <DataTable
        config={tableConfig}
        hideAddButton
        onTableReady={(table) => { tableRef.current = table; }}
        onEdit={(row) => handleEdit(row)}
        onDelete={async (row) => handleDelete(row.id)}
        toolbarContent={renderToolbar}
        options={{
          selectable: false,
          showSearch: true,
          showPagination: true,
          showColumnSelector: true,
          pageSize: 20,
        }}
      />

      {/* Form Modal */}
      {showForm && (
        <RuoloAziendaForm
          soggettoCorrente={soggetto}
          ruoloToEdit={editingRuolo}
          onClose={handleCloseForm}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

RuoliAziendaSection.propTypes = {
  soggetto: PropTypes.object.isRequired,
  onUpdate: PropTypes.func
};
