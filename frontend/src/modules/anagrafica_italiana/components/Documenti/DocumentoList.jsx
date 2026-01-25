/**
 * DocumentoList Component
 *
 * Display list of documents for a soggetto anagrafico with deadline tracking.
 * Shows expired, expiring soon, and upcoming documents with visual indicators.
 */
import React, { useState, useEffect, useMemo, useRef } from 'react';
import axios from 'axios';
import { DataTable } from '../../../../core/components';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './DocumentoList.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const DocumentoList = ({ soggettoId, onDocumentDeleted, refreshTrigger }) => {
  const [scadenzario, setScadenzario] = useState(null);
  const [view, setView] = useState('all'); // 'all', 'expired', 'expiring', 'upcoming'
  const tableRef = useRef(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadScadenzario();
  }, [soggettoId, refreshTrigger]);

  const loadScadenzario = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/anagrafica/documenti/scadenzario/soggetto/${soggettoId}`,
        { headers: getAuthHeader() }
      );
      setScadenzario(response.data);
    } catch (err) {
      console.error('Errore caricamento scadenzario:', err);
    }
  };

  const handleDownload = async (documentoId, nomeFile) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/anagrafica/documenti/${documentoId}/download`,
        {
          headers: getAuthHeader(),
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', nomeFile);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Errore download documento:', err);
      alert('Errore durante il download del documento');
    }
  };

  const handleDelete = async (documentoId) => {
    await axios.delete(
      `${API_BASE_URL}/anagrafica/documenti/${documentoId}`,
      { headers: getAuthHeader() }
    );

    if (tableRef) {
      tableRef.refresh();
    }
    await loadScadenzario();

    if (onDocumentDeleted) {
      onDocumentDeleted(documentoId);
    }
  };

  const getScadenzaStatus = (doc) => {
    if (!doc.data_scadenza) return 'none';
    if (doc.is_scaduto) return 'expired';
    if (doc.days_to_expiry !== null && doc.days_to_expiry <= 30) return 'expiring';
    return 'upcoming';
  };

  const getScadenzaBadge = (doc) => {
    if (!doc.data_scadenza) return null;

    const status = getScadenzaStatus(doc);
    const daysText = doc.days_to_expiry !== null
      ? Math.abs(doc.days_to_expiry) === 1
        ? '1 giorno'
        : `${Math.abs(doc.days_to_expiry)} giorni`
      : '';

    const badges = {
      expired: (
        <span className="badge badge-expired">
          Scaduto ({daysText} fa)
        </span>
      ),
      expiring: (
        <span className="badge badge-expiring">
          Scade tra {daysText}
        </span>
      ),
      upcoming: (
        <span className="badge badge-upcoming">
          Scade tra {daysText}
        </span>
      )
    };

    return badges[status];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const applyViewFilter = (table, currentView) => {
    if (!table) return;
    if (currentView === 'all') {
      table.setFilter('scadenza_status', '');
      return;
    }
    table.setFilter('scadenza_status', (_, row) => {
      if (currentView === 'upcoming') {
        return getScadenzaStatus(row) === 'upcoming';
      }
      return getScadenzaStatus(row) === currentView;
    });
  };

  useEffect(() => {
    applyViewFilter(tableRef.current, view);
  }, [view]);

  useEffect(() => {
    if (tableRef.current) {
      tableRef.current.refresh();
    }
  }, [refreshTrigger, soggettoId]);

  const columns = useMemo(() => ([
    {
      field: 'tipo_documento.nome',
      label: 'Tipo Documento',
      sortable: true,
      render: (_, row) => (
        row.tipo_documento ? (
          <div className="tipo-info">
            <span className="tipo-nome">{row.tipo_documento.nome}</span>
            {row.tipo_documento.categoria && (
              <span className="tipo-categoria">{row.tipo_documento.categoria}</span>
            )}
          </div>
        ) : (
          <span className="tipo-unknown">-</span>
        )
      ),
    },
    {
      field: 'nome_file',
      label: 'Nome File',
      sortable: true,
      visible: false,
      render: (value, row) => (
        <div className="file-info">
          <span className="file-name">{value || '-'}</span>
          {row.note && <div className="file-note">{row.note}</div>}
        </div>
      ),
    },
    {
      field: 'data_scadenza',
      label: 'Data Scadenza',
      sortable: true,
      visible: false,
      render: (value) => formatDate(value),
    },
    {
      field: 'scadenza_status',
      label: 'Stato',
      render: (_, row) => getScadenzaBadge(row),
    },
    {
      field: 'dimensione',
      label: 'Dimensione',
      sortable: true,
      visible: false,
      render: (value) => value ? `${(value / 1024).toFixed(1)} KB` : '-',
    },
    {
      field: 'created_at',
      label: 'Caricato il',
      sortable: true,
      visible: false,
      render: (value) => formatDate(value),
    },
  ]), []);

  const tableConfig = {
    endpoint: `/anagrafica/documenti/soggetto/${soggettoId}`,
    title: '',
    emptyTitle: 'Nessun documento caricato',
    emptyMessage: 'Carica il primo documento per questo soggetto.',
    columns,
    rowActions: [
      {
        id: 'download',
        label: 'Download',
        variant: 'primary',
        onClick: (row) => handleDownload(row.id, row.nome_file),
        icon: renderIcon('download', { size: 14, className: 'doc-action-icon', fallbackClassName: 'doc-action-icon' }),
      },
      { id: 'delete', label: 'Elimina', action: 'delete', variant: 'danger', icon: renderIcon('trash', { size: 14, className: 'doc-action-icon', fallbackClassName: 'doc-action-icon' }) },
    ],
    moduleName: 'anagrafica_italiana',
    entityName: 'DocumentiSoggetto',
  };

  return (
    <div className="documento-list">
      {/* Scadenzario Summary */}
      {scadenzario && (
        <div className="scadenzario-summary">
          <h4>Riepilogo Scadenze</h4>
          <div className="summary-cards" aria-label="Riepilogo scadenze">
            <div
              className={`summary-card expired ${view === 'expired' ? 'active' : ''}`}
              onClick={() => setView('expired')}
            >
              <div className="card-value">{scadenzario.expired.length}</div>
              <div className="card-label">Scaduti</div>
            </div>
            <div
              className={`summary-card expiring ${view === 'expiring' ? 'active' : ''}`}
              onClick={() => setView('expiring')}
            >
              <div className="card-value">{scadenzario.expiring_soon.length}</div>
              <div className="card-label">In scadenza</div>
            </div>
            <div
              className={`summary-card upcoming ${view === 'upcoming' ? 'active' : ''}`}
              onClick={() => setView('upcoming')}
            >
              <div className="card-value">{scadenzario.upcoming.length}</div>
              <div className="card-label">Futuri</div>
            </div>
            <div
              className={`summary-card all ${view === 'all' ? 'active' : ''}`}
              onClick={() => setView('all')}
            >
              <div className="card-value">{totalCount}</div>
              <div className="card-label">Totali</div>
            </div>
          </div>
        </div>
      )}

      <DataTable
        config={tableConfig}
        hideAddButton
        onTableReady={(table) => {
          tableRef.current = table;
          applyViewFilter(table, view);
        }}
        onDelete={async (row) => handleDelete(row.id)}
        tableOptions={{
          onDataChange: (data) => setTotalCount(data?.length ?? 0),
        }}
        options={{
          showSearch: true,
          showPagination: true,
          showColumnSelector: true,
          pageSize: 20,
        }}
      />
    </div>
  );
};

export default DocumentoList;
