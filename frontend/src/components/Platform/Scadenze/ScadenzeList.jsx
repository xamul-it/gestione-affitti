/**
 * ScadenzeList Component - Advanced Scadenze List with Filters
 *
 * Features:
 * - Advanced filters (stato, priorità, date range, module, entity)
 * - Sorting (data_scadenza, priorità, created_at)
 * - View modes (grid, list, compact)
 * - Quick actions (completa, posticipa, delete)
 * - Batch actions for multiple selection
 * - Pagination support
 */
import React, { useState, useMemo } from 'react';
import { useScadenze } from './hooks/useScadenze';
import { useNavigate } from 'react-router-dom';
import './ScadenzeList.css';

const ScadenzeList = ({
  filters: externalFilters = {},
  onScadenzaClick = null,
  onScadenzaUpdated = null,
  showFilters = true,
  viewMode: initialViewMode = 'grid',
  pageSize = 20,
  enableBatchActions = true,
}) => {
  const navigate = useNavigate();
  const {
    scadenze,
    loading,
    error,
    completaScadenza,
    posticipаScadenza,
    deleteScadenza,
    loadScadenze,
  } = useScadenze({ autoLoad: true, filters: externalFilters });

  // View state
  const [viewMode, setViewMode] = useState(initialViewMode);
  const [selectedIds, setSelectedIds] = useState([]);

  // Filter state
  const [localFilters, setLocalFilters] = useState({
    stato: '',
    priorita: '',
    modulo: '',
    entity_type: '',
    is_scaduta: '',
    is_todo: '',
    search: '',
    data_da: '',
    data_a: '',
  });

  // Sorting state
  const [sortBy, setSortBy] = useState('data_scadenza');
  const [sortOrder, setSortOrder] = useState('asc'); // asc or desc

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // Apply filters and sorting
  const filteredAndSortedScadenze = useMemo(() => {
    let result = [...scadenze];

    // Apply local filters
    if (localFilters.stato) {
      result = result.filter(s => s.stato === localFilters.stato);
    }
    if (localFilters.priorita) {
      result = result.filter(s => s.priorita === localFilters.priorita);
    }
    if (localFilters.modulo) {
      result = result.filter(s => s.modulo === localFilters.modulo);
    }
    if (localFilters.entity_type) {
      result = result.filter(s => s.entity_type === localFilters.entity_type);
    }
    if (localFilters.is_scaduta !== '') {
      const isScadutaBool = localFilters.is_scaduta === 'true';
      result = result.filter(s => s.is_scaduta === isScadutaBool);
    }
    if (localFilters.is_todo !== '') {
      const isTodoBool = localFilters.is_todo === 'true';
      result = result.filter(s => s.is_todo === isTodoBool);
    }
    if (localFilters.search) {
      const searchLower = localFilters.search.toLowerCase();
      result = result.filter(s =>
        s.titolo.toLowerCase().includes(searchLower) ||
        (s.descrizione && s.descrizione.toLowerCase().includes(searchLower))
      );
    }
    if (localFilters.data_da) {
      result = result.filter(s => s.data_scadenza >= localFilters.data_da);
    }
    if (localFilters.data_a) {
      result = result.filter(s => s.data_scadenza <= localFilters.data_a);
    }

    // Apply sorting
    result.sort((a, b) => {
      let compareA, compareB;

      switch (sortBy) {
        case 'data_scadenza':
          compareA = new Date(a.data_scadenza);
          compareB = new Date(b.data_scadenza);
          break;
        case 'priorita':
          const priorityOrder = { ALTA: 1, MEDIA: 2, BASSA: 3 };
          compareA = priorityOrder[a.priorita] || 99;
          compareB = priorityOrder[b.priorita] || 99;
          break;
        case 'created_at':
          compareA = new Date(a.created_at);
          compareB = new Date(b.created_at);
          break;
        case 'titolo':
          compareA = a.titolo.toLowerCase();
          compareB = b.titolo.toLowerCase();
          break;
        default:
          return 0;
      }

      if (compareA < compareB) return sortOrder === 'asc' ? -1 : 1;
      if (compareA > compareB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [scadenze, localFilters, sortBy, sortOrder]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedScadenze.length / pageSize);
  const paginatedScadenze = filteredAndSortedScadenze.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // Handlers
  const handleFilterChange = (key, value) => {
    setLocalFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page
  };

  const handleResetFilters = () => {
    setLocalFilters({
      stato: '',
      priorita: '',
      modulo: '',
      entity_type: '',
      is_scaduta: '',
      is_todo: '',
      search: '',
      data_da: '',
      data_a: '',
    });
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const toggleSelection = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    setSelectedIds(paginatedScadenze.map(s => s.id));
  };

  const deselectAll = () => {
    setSelectedIds([]);
  };

  const handleCompleta = async (id) => {
    if (window.confirm('Vuoi completare questa scadenza?')) {
      try {
        await completaScadenza(id, 'Completato da lista scadenze');
        if (onScadenzaUpdated) onScadenzaUpdated();
      } catch (err) {
        console.error('Error completing scadenza:', err);
      }
    }
  };

  const handlePosticipa = async (id) => {
    const nuovaData = prompt('Nuova data (YYYY-MM-DD):');
    if (nuovaData) {
      try {
        await posticipаScadenza(id, nuovaData, 'Posticipato da lista scadenze');
        if (onScadenzaUpdated) onScadenzaUpdated();
      } catch (err) {
        console.error('Error postponing scadenza:', err);
      }
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Vuoi cancellare questa scadenza?')) {
      try {
        await deleteScadenza(id);
        if (onScadenzaUpdated) onScadenzaUpdated();
      } catch (err) {
        console.error('Error deleting scadenza:', err);
      }
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) return;
    if (window.confirm(`Vuoi cancellare ${selectedIds.length} scadenze?`)) {
      try {
        await Promise.all(selectedIds.map(id => deleteScadenza(id)));
        setSelectedIds([]);
        if (onScadenzaUpdated) onScadenzaUpdated();
      } catch (err) {
        console.error('Error batch deleting:', err);
      }
    }
  };

  // Rendering helpers
  const getStatoColor = (stato) => {
    switch (stato) {
      case 'ATTIVA': return 'green';
      case 'SCADUTA': return 'red';
      case 'COMPLETATA': return 'gray';
      case 'POSTICIPATA': return 'orange';
      case 'CANCELLATA': return 'darkgray';
      default: return 'black';
    }
  };

  const getPrioritaIcon = (priorita) => {
    switch (priorita) {
      case 'ALTA': return '🔴';
      case 'MEDIA': return '🟡';
      case 'BASSA': return '🟢';
      default: return '⚪';
    }
  };

  const getEntityLink = (scadenza) => {
    if (!scadenza?.modulo || !scadenza?.entity_type || !scadenza?.entity_id) return null;
    const params = new URLSearchParams({
      modulo: scadenza.modulo,
      entity_type: scadenza.entity_type,
      entity_id: String(scadenza.entity_id),
      scadenza_id: String(scadenza.id),
    });
    return `/scadenze/resolve?${params.toString()}`;
  };

  // Get unique values for filter dropdowns
  const uniqueModuli = [...new Set(scadenze.map(s => s.modulo).filter(Boolean))];
  const uniqueEntityTypes = [...new Set(scadenze.map(s => s.entity_type).filter(Boolean))];

  return (
    <div className="scadenze-list">
      {/* Header with view controls */}
      <div className="scadenze-list__header">
        <div className="scadenze-list__title">
          <h2>📋 Scadenze ({filteredAndSortedScadenze.length})</h2>
        </div>

        <div className="scadenze-list__view-controls">
          <button
            className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
            title="Vista Griglia"
          >
            ◫
          </button>
          <button
            className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
            title="Vista Lista"
          >
            ☰
          </button>
          <button
            className={`view-btn ${viewMode === 'compact' ? 'active' : ''}`}
            onClick={() => setViewMode('compact')}
            title="Vista Compatta"
          >
            ≡
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="scadenze-list__filters">
          <div className="filters-row">
            <input
              type="text"
              placeholder="🔍 Cerca titolo o descrizione..."
              value={localFilters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="filter-input filter-search"
            />

            <select
              value={localFilters.stato}
              onChange={(e) => handleFilterChange('stato', e.target.value)}
              className="filter-select"
            >
              <option value="">Tutti gli stati</option>
              <option value="ATTIVA">Attiva</option>
              <option value="SCADUTA">Scaduta</option>
              <option value="COMPLETATA">Completata</option>
              <option value="POSTICIPATA">Posticipata</option>
              <option value="CANCELLATA">Cancellata</option>
            </select>

            <select
              value={localFilters.priorita}
              onChange={(e) => handleFilterChange('priorita', e.target.value)}
              className="filter-select"
            >
              <option value="">Tutte le priorità</option>
              <option value="ALTA">🔴 Alta</option>
              <option value="MEDIA">🟡 Media</option>
              <option value="BASSA">🟢 Bassa</option>
            </select>

            <select
              value={localFilters.is_todo}
              onChange={(e) => handleFilterChange('is_todo', e.target.value)}
              className="filter-select"
            >
              <option value="">Tutti i tipi</option>
              <option value="true">Solo TODO</option>
              <option value="false">Solo Entity-Linked</option>
            </select>

            {uniqueModuli.length > 0 && (
              <select
                value={localFilters.modulo}
                onChange={(e) => handleFilterChange('modulo', e.target.value)}
                className="filter-select"
              >
                <option value="">Tutti i moduli</option>
                {uniqueModuli.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            )}

            <input
              type="date"
              placeholder="Data da"
              value={localFilters.data_da}
              onChange={(e) => handleFilterChange('data_da', e.target.value)}
              className="filter-input filter-date"
            />

            <input
              type="date"
              placeholder="Data a"
              value={localFilters.data_a}
              onChange={(e) => handleFilterChange('data_a', e.target.value)}
              className="filter-input filter-date"
            />

            <button
              onClick={handleResetFilters}
              className="btn-filter-reset"
              title="Reset filtri"
            >
              ✖
            </button>
          </div>

          {/* Sort controls */}
          <div className="filters-row filters-row--secondary">
            <span className="sort-label">Ordina per:</span>
            <button
              className={`btn-sort ${sortBy === 'data_scadenza' ? 'active' : ''}`}
              onClick={() => handleSort('data_scadenza')}
            >
              Data {sortBy === 'data_scadenza' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button
              className={`btn-sort ${sortBy === 'priorita' ? 'active' : ''}`}
              onClick={() => handleSort('priorita')}
            >
              Priorità {sortBy === 'priorita' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button
              className={`btn-sort ${sortBy === 'titolo' ? 'active' : ''}`}
              onClick={() => handleSort('titolo')}
            >
              Titolo {sortBy === 'titolo' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button
              className={`btn-sort ${sortBy === 'created_at' ? 'active' : ''}`}
              onClick={() => handleSort('created_at')}
            >
              Creazione {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
          </div>
        </div>
      )}

      {/* Batch actions */}
      {enableBatchActions && selectedIds.length > 0 && (
        <div className="scadenze-list__batch-actions">
          <span className="batch-count">{selectedIds.length} selezionate</span>
          <button onClick={deselectAll} className="btn-batch">Deseleziona tutto</button>
          <button onClick={handleBatchDelete} className="btn-batch btn-batch--danger">
            🗑️ Cancella selezionate
          </button>
        </div>
      )}

      {/* Loading / Error */}
      {loading && <div className="scadenze-list__loading">⏳ Caricamento...</div>}
      {error && <div className="scadenze-list__error">❌ {error}</div>}

      {/* Empty state */}
      {!loading && paginatedScadenze.length === 0 && (
        <div className="scadenze-list__empty">
          Nessuna scadenza trovata con i filtri selezionati.
        </div>
      )}

      {/* Scadenze list */}
      {!loading && paginatedScadenze.length > 0 && (
        <div className={`scadenze-list__items scadenze-list__items--${viewMode}`}>
          {paginatedScadenze.map((scadenza) => (
            <div
              key={scadenza.id}
              className={`scadenza-item scadenza-item--${viewMode} ${
                scadenza.is_scaduta ? 'scadenza-item--overdue' : ''
              } ${selectedIds.includes(scadenza.id) ? 'scadenza-item--selected' : ''}`}
              onClick={() => onScadenzaClick && onScadenzaClick(scadenza)}
            >
              {enableBatchActions && (
                <div className="scadenza-item__checkbox" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(scadenza.id)}
                    onChange={() => toggleSelection(scadenza.id)}
                  />
                </div>
              )}

              <div className="scadenza-item__content">
                <div className="scadenza-item__header">
                  <span className="scadenza-item__priority">{getPrioritaIcon(scadenza.priorita)}</span>
                  <span
                    className="scadenza-item__stato"
                    style={{ color: getStatoColor(scadenza.stato) }}
                  >
                    {scadenza.stato}
                  </span>
                  {scadenza.is_todo && <span className="scadenza-item__badge">TODO</span>}
                </div>

                <h3 className="scadenza-item__title">{scadenza.titolo}</h3>

                {scadenza.descrizione && viewMode !== 'compact' && (
                  <p className="scadenza-item__description">{scadenza.descrizione}</p>
                )}

                <div className="scadenza-item__meta">
                  <div className="scadenza-item__date">📅 {scadenza.data_scadenza}</div>
                  {!scadenza.is_todo && viewMode !== 'compact' && (
                    <div className="scadenza-item__entity">
                      {scadenza.modulo}/{scadenza.entity_type}#{scadenza.entity_id}
                      {getEntityLink(scadenza) && (
                        <button
                          className="btn-action btn-action--link"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(getEntityLink(scadenza));
                          }}
                          title="Apri scheda"
                          type="button"
                        >
                          🔗
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {scadenza.stato !== 'COMPLETATA' && scadenza.stato !== 'CANCELLATA' && (
                  <div className="scadenza-item__actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="btn-action btn-action--success"
                      onClick={() => handleCompleta(scadenza.id)}
                      title="Completa"
                    >
                      ✅
                    </button>
                    <button
                      className="btn-action btn-action--warning"
                      onClick={() => handlePosticipa(scadenza.id)}
                      title="Posticipa"
                    >
                      ⏭️
                    </button>
                    <button
                      className="btn-action btn-action--danger"
                      onClick={() => handleDelete(scadenza.id)}
                      title="Cancella"
                    >
                      🗑️
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="scadenze-list__pagination">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="btn-pagination"
          >
            ← Precedente
          </button>

          <span className="pagination-info">
            Pagina {currentPage} di {totalPages}
          </span>

          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="btn-pagination"
          >
            Successiva →
          </button>
        </div>
      )}
    </div>
  );
};

export default ScadenzeList;
