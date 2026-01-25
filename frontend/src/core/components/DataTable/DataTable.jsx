/**
 * DataTable - Configurable data table component
 *
 * A fully featured data table with sorting, filtering, pagination,
 * row selection, and bulk actions.
 *
 * @example
 * <DataTable
 *   config={{
 *     endpoint: '/affittuari/',
 *     title: 'Gestione Affittuari',
 *     columns: [...],
 *     rowActions: [...]
 *   }}
 *   onAdd={() => setShowForm(true)}
 * />
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useDataTable, useDebounce, useToast, tableConfigAPI } from '../../hooks';
import { formatValue, getNestedValue } from '../../utils/formatters';
import { LoadingSpinner, EmptyState, ErrorMessage, ConfirmDialog, Badge, StatusBadge } from '../common';
import { ColumnSelector } from './ColumnSelector';
import './DataTable.css';

/**
 * DataTable component
 */
export function DataTable({
  config,
  FormComponent,
  onAdd,
  onEdit,
  onView,
  onDelete,
  onRowClick,
  customActions,
  toolbarContent,
  addDisabled = false,
  hideAddButton = false,
  tableOptions = {},
  onTableReady,
  options = {},
}) {
  const {
    endpoint,
    title,
    columns = [],
    rowActions = [],
    bulkActions = [],
    defaultSort,
    defaultFilters,
    defaultParams,
    searchPlaceholder = 'Cerca...',
    emptyTitle = 'Nessun dato trovato',
    emptyMessage,
    addButtonLabel = 'Nuovo',
  } = config;

  const {
    selectable = false,
    showSearch = true,
    showPagination = true,
    showColumnSelector = false,
    pageSize = 20,
    exportable = false,
  } = options;

  // Table state from hook
  const table = useDataTable({
    endpoint,
    columns,
    defaultSort,
    defaultFilters,
    defaultParams,
    pageSize,
  }, tableOptions);

  // Local UI state
  const [showForm, setShowForm] = useState(false);
  const [editingEntity, setEditingEntity] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [bulkDeleteTarget, setBulkDeleteTarget] = useState([]);
  const [columnSelectorOpen, setColumnSelectorOpen] = useState(false);

  // Toast notifications
  const toast = useToast();

  React.useEffect(() => {
    if (onTableReady) {
      onTableReady(table);
    }
  }, [onTableReady, table]);

  // Search with debounce
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebounce(searchInput, 300);

  // Apply debounced search to table
  React.useEffect(() => {
    table.setSearchTerm(debouncedSearch);
  }, [debouncedSearch]);

  /**
   * Handle add new entity
   */
  const handleAdd = useCallback(() => {
    if (onAdd) {
      onAdd();
    } else {
      setEditingEntity(null);
      setShowForm(true);
    }
  }, [onAdd]);

  /**
   * Handle edit entity
   */
  const handleEdit = useCallback((entity) => {
    if (onEdit) {
      onEdit(entity);
    } else {
      setEditingEntity(entity);
      setShowForm(true);
    }
  }, [onEdit]);

  /**
   * Handle view entity
   */
  const handleView = useCallback((entity) => {
    if (onView) {
      onView(entity);
    }
  }, [onView]);

  /**
   * Handle delete request
   */
  const handleDeleteRequest = useCallback((entity) => {
    setDeleteTarget(entity);
    setShowDeleteConfirm(true);
  }, []);

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    try {
      if (onDelete) {
        await onDelete(deleteTarget);
      } else {
        await table.remove(deleteTarget.id);
      }
      toast.success('Elemento eliminato con successo');
      setShowDeleteConfirm(false);
      setDeleteTarget(null);
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Errore durante l\'eliminazione');
    } finally {
      setIsDeleting(false);
    }
  }, [deleteTarget, onDelete, table, toast]);

  /**
   * Handle form close
   */
  const handleFormClose = useCallback(() => {
    setShowForm(false);
    setEditingEntity(null);
    table.refresh();
  }, [table]);

  /**
   * Handle bulk delete request
   */
  const handleBulkDeleteRequest = useCallback(() => {
    if (table.selectedIds.size === 0) return;
    setBulkDeleteTarget(Array.from(table.selectedIds));
    setShowBulkDeleteConfirm(true);
  }, [table]);

  /**
   * Confirm bulk delete
   */
  const handleBulkDeleteConfirm = useCallback(async () => {
    setIsDeleting(true);
    try {
      await table.deleteSelected();
      toast.success(`${bulkDeleteTarget.length} elementi eliminati con successo`);
      setShowBulkDeleteConfirm(false);
      setBulkDeleteTarget([]);
    } catch (err) {
      console.error('Bulk delete failed:', err);
      toast.error('Errore durante l\'eliminazione multipla');
    } finally {
      setIsDeleting(false);
    }
  }, [table, bulkDeleteTarget, toast]);

  /**
   * Render cell value based on column type
   */
  const renderCellValue = useCallback((column, row) => {
    const value = getNestedValue(row, column.field);

    // Custom render function
    if (column.render) {
      const rendered = column.render(value, row);
      // If render returns a badge config object, render it as badge
      if (rendered && typeof rendered === 'object' && rendered.type === 'badge') {
        return (
          <span className={`badge badge-${rendered.variant}`}>
            {rendered.label}
          </span>
        );
      }
      return rendered;
    }

    // Link type
    if (column.type === 'link' && column.linkTo) {
      const linkPath = column.linkTo.replace(':id', row.id);
      return (
        <Link to={linkPath} className="core-datatable__link">
          {formatValue(value, 'text')}
        </Link>
      );
    }

    // Badge type
    if (column.type === 'badge') {
      return <StatusBadge status={value} statusMap={column.badgeMap} />;
    }

    // Boolean type
    if (column.type === 'boolean') {
      return <StatusBadge status={value} />;
    }

    // Default formatting
    return formatValue(value, column.type || 'text', column);
  }, []);

  /**
   * Render row actions
   */
  const renderRowActions = useCallback((row) => {
    return (
      <div className="core-datatable__actions">
        {rowActions.map((action) => {
          if (action.visible && !action.visible(row)) {
            return null;
          }

          const actionLabel = typeof action.label === 'function' ? action.label(row) : action.label;
          const actionVariant = typeof action.variant === 'function' ? action.variant(row) : action.variant;
          const actionIcon = typeof action.icon === 'function' ? action.icon(row) : action.icon;

          // Built-in actions
          if (action.action === 'view' || action.id === 'view') {
            if (action.to) {
              const linkPath = action.to.replace(':id', row.id);
              return (
                <Link
                  key={action.id}
                  to={linkPath}
                  className="core-datatable__action-btn core-datatable__action-btn--primary"
                  title={actionLabel || 'Dettagli'}
                >
                  {actionIcon || 'Dettagli'}
                </Link>
              );
            }
            return (
              <button
                key={action.id}
                type="button"
                className="core-datatable__action-btn core-datatable__action-btn--primary"
                onClick={() => handleView(row)}
                title={actionLabel || 'Dettagli'}
              >
                {actionIcon || 'Dettagli'}
              </button>
            );
          }

          if (action.action === 'edit' || action.id === 'edit') {
            return (
              <button
                key={action.id}
                type="button"
                className="core-datatable__action-btn core-datatable__action-btn--secondary"
                onClick={() => handleEdit(row)}
                title={actionLabel || 'Modifica'}
              >
                {actionIcon || 'Modifica'}
              </button>
            );
          }

          if (action.action === 'delete' || action.id === 'delete') {
            return (
              <button
                key={action.id}
                type="button"
                className="core-datatable__action-btn core-datatable__action-btn--danger"
                onClick={() => handleDeleteRequest(row)}
                title={actionLabel || 'Elimina'}
              >
                {actionIcon || 'Elimina'}
              </button>
            );
          }

          // Custom action
          if (action.onClick) {
            return (
              <button
                key={action.id}
                type="button"
                className={`core-datatable__action-btn core-datatable__action-btn--${actionVariant || 'default'}`}
                onClick={() => action.onClick(row, table)}
                title={actionLabel}
              >
                {actionIcon || actionLabel}
              </button>
            );
          }

          return null;
        })}
      </div>
    );
  }, [rowActions, handleView, handleEdit, handleDeleteRequest]);

  /**
   * Get sort indicator
   */
  const getSortIndicator = useCallback((field) => {
    if (table.sortField !== field) return null;
    return table.sortOrder === 'asc' ? ' ▲' : ' ▼';
  }, [table.sortField, table.sortOrder]);

  // Visible columns with actions
  const visibleColumns = useMemo(() => {
    return table.visibleColumns;
  }, [table.visibleColumns]);

  return (
    <div className="core-datatable">
      {/* Header */}
      <div className="core-datatable__header">
        <h1 className="core-datatable__title">{title}</h1>
        <div className="core-datatable__header-actions">
          {typeof customActions === 'function' ? customActions({ table }) : customActions}
          {!hideAddButton && (
            <button
              type="button"
              className="core-datatable__add-btn"
              onClick={handleAdd}
              disabled={addDisabled}
            >
              + {addButtonLabel}
            </button>
          )}
        </div>
      </div>

      {/* Toolbar */}
      <div className="core-datatable__toolbar">
        {/* Search */}
        {showSearch && (
          <div className="core-datatable__search">
            <input
              type="text"
              placeholder={searchPlaceholder}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="core-datatable__search-input"
            />
            {(searchInput || table.searchTerm) && (
              <button
                type="button"
                className="core-datatable__search-clear"
                onClick={() => {
                  setSearchInput('');
                  table.setSearchTerm('');
                }}
                title="Cancella ricerca"
              >
                ×
              </button>
            )}
            {searchInput !== debouncedSearch && (
              <span className="core-datatable__search-loading" title="Ricerca in corso...">
                ⟳
              </span>
            )}
          </div>
        )}

        {toolbarContent && (
          <div className="core-datatable__toolbar-extra">
            {typeof toolbarContent === 'function' ? toolbarContent({ table }) : toolbarContent}
          </div>
        )}

        {/* Bulk Actions */}
        {selectable && table.selectedIds.size > 0 && (
          <div className="core-datatable__bulk-actions">
            <span className="core-datatable__selected-count">
              {table.selectedIds.size} selezionati
            </span>
            {bulkActions.map((action) => {
              if (action.action === 'bulkDelete') {
                return (
                  <button
                    key={action.id}
                    type="button"
                    className="core-datatable__bulk-btn core-datatable__bulk-btn--danger"
                    onClick={handleBulkDeleteRequest}
                  >
                    {action.label || 'Elimina selezionati'}
                  </button>
                );
              }
              return (
                <button
                  key={action.id}
                  type="button"
                  className={`core-datatable__bulk-btn core-datatable__bulk-btn--${action.variant || 'default'}`}
                  onClick={() => action.onClick?.(table.selectedItems)}
                >
                  {action.label}
                </button>
              );
            })}
            <button
              type="button"
              className="core-datatable__bulk-btn"
              onClick={table.clearSelection}
            >
              Annulla selezione
            </button>
          </div>
        )}

        {/* Filters info */}
        {Object.keys(table.filters).length > 0 && (
          <button
            type="button"
            className="core-datatable__clear-filters"
            onClick={table.clearFilters}
          >
            Rimuovi filtri
          </button>
        )}

        {/* Column Selector Toggle */}
        {showColumnSelector !== undefined && (
          <div className="core-datatable__column-selector-wrapper">
            <button
              type="button"
              className="core-datatable__columns-btn"
              onClick={() => setColumnSelectorOpen(!columnSelectorOpen)}
              title="Gestisci colonne"
            >
              <span className="core-datatable__columns-icon">☰</span>
              Colonne
            </button>

            {columnSelectorOpen && (
              <>
                <div
                  className="core-datatable__column-selector-overlay"
                  onClick={() => setColumnSelectorOpen(false)}
                />
                <ColumnSelector
                  columns={columns}
                  visibleColumns={visibleColumns.map(c => c.field)}
                  onColumnsChange={(newColumns) => {
                    // Update local state
                    newColumns.forEach(field => {
                      if (!table.columnVisibility[field]) {
                        table.toggleColumnVisibility(field);
                      }
                    });
                    Object.keys(table.columnVisibility).forEach(field => {
                      if (table.columnVisibility[field] && !newColumns.includes(field)) {
                        table.toggleColumnVisibility(field);
                      }
                    });

                    // Persist to backend if module/entity configured
                    if (config.moduleName && config.entityName) {
                      tableConfigAPI.updateColumns(
                        config.moduleName,
                        config.entityName,
                        newColumns
                      ).catch(err => {
                        console.warn('Could not persist column config:', err);
                      });
                    }
                  }}
                  onReset={() => {
                    // Reset all columns to visible
                    columns.forEach(col => {
                      if (!table.columnVisibility[col.field]) {
                        table.toggleColumnVisibility(col.field);
                      }
                    });

                    // Reset backend config
                    if (config.moduleName && config.entityName) {
                      tableConfigAPI.resetConfig(
                        config.moduleName,
                        config.entityName
                      ).catch(err => {
                        console.warn('Could not reset column config:', err);
                      });
                    }
                  }}
                  onClose={() => setShowColumnSelector(false)}
                />
              </>
            )}
          </div>
        )}
      </div>

      {/* Error */}
      {table.error && (
        <ErrorMessage
          message={table.error}
          onRetry={table.refresh}
          onDismiss={table.clearError}
        />
      )}

      {/* Table */}
      <div className="core-datatable__wrapper">
        {table.loading && <LoadingSpinner overlay />}

        {!table.loading && table.data.length === 0 ? (
          <EmptyState
            icon="📋"
            title={emptyTitle}
            message={emptyMessage || `Nessun risultato trovato${table.searchTerm ? ' per la ricerca' : ''}.`}
            action={
              <button
                type="button"
                className="core-datatable__add-btn"
                onClick={handleAdd}
              >
                + {addButtonLabel}
              </button>
            }
          />
        ) : (
          <table className="core-datatable__table">
            <thead>
              <tr>
                {/* Select all checkbox */}
                {selectable && (
                  <th className="core-datatable__th core-datatable__th--select">
                    <input
                      type="checkbox"
                      checked={table.isAllSelected}
                      ref={(el) => {
                        if (el) el.indeterminate = table.isSomeSelected;
                      }}
                      onChange={table.selectAll}
                    />
                  </th>
                )}

                {/* Column headers */}
                {visibleColumns.map((column) => (
                  <th
                    key={column.field}
                    className={`core-datatable__th ${column.sortable ? 'core-datatable__th--sortable' : ''}`}
                    style={{
                      width: column.width,
                      textAlign: column.align || 'left',
                    }}
                    onClick={() => column.sortable && table.handleSort(column.field)}
                  >
                    {column.label}
                    {column.sortable && getSortIndicator(column.field)}
                  </th>
                ))}

                {/* Actions header */}
                {rowActions.length > 0 && (
                  <th className="core-datatable__th core-datatable__th--actions">
                    Azioni
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {table.data.map((row) => (
                <tr
                  key={row.id}
                  className={`core-datatable__tr ${table.selectedIds.has(row.id) ? 'core-datatable__tr--selected' : ''}`}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {/* Row checkbox */}
                  {selectable && (
                    <td className="core-datatable__td core-datatable__td--select">
                      <input
                        type="checkbox"
                        checked={table.selectedIds.has(row.id)}
                        onChange={() => table.toggleSelect(row.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                  )}

                  {/* Data cells */}
                  {visibleColumns.map((column) => (
                    <td
                      key={column.field}
                      className="core-datatable__td"
                      style={{ textAlign: column.align || 'left' }}
                    >
                      {renderCellValue(column, row)}
                    </td>
                  ))}

                  {/* Action cells */}
                  {rowActions.length > 0 && (
                    <td
                      className="core-datatable__td core-datatable__td--actions"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {renderRowActions(row)}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {showPagination && table.pagination.totalPages > 1 && (
        <div className="core-datatable__pagination">
          <div className="core-datatable__pagination-info">
            Mostrando {((table.page - 1) * table.pageSize) + 1} -{' '}
            {Math.min(table.page * table.pageSize, table.pagination.total)} di{' '}
            {table.pagination.total} risultati
          </div>
          <div className="core-datatable__pagination-controls">
            <button
              type="button"
              className="core-datatable__page-btn"
              disabled={!table.pagination.hasPrevPage}
              onClick={() => table.setPage(1)}
            >
              ««
            </button>
            <button
              type="button"
              className="core-datatable__page-btn"
              disabled={!table.pagination.hasPrevPage}
              onClick={() => table.setPage(table.page - 1)}
            >
              «
            </button>
            <span className="core-datatable__page-info">
              Pagina {table.page} di {table.pagination.totalPages}
            </span>
            <button
              type="button"
              className="core-datatable__page-btn"
              disabled={!table.pagination.hasNextPage}
              onClick={() => table.setPage(table.page + 1)}
            >
              »
            </button>
            <button
              type="button"
              className="core-datatable__page-btn"
              disabled={!table.pagination.hasNextPage}
              onClick={() => table.setPage(table.pagination.totalPages)}
            >
              »»
            </button>
          </div>
          <div className="core-datatable__page-size">
            <select
              value={table.pageSize}
              onChange={(e) => table.setPageSize(Number(e.target.value))}
            >
              <option value={10}>10 per pagina</option>
              <option value={20}>20 per pagina</option>
              <option value={50}>50 per pagina</option>
              <option value={100}>100 per pagina</option>
            </select>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showForm && FormComponent && (
        <FormComponent
          entity={editingEntity}
          onClose={handleFormClose}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Conferma eliminazione"
        message={`Sei sicuro di voler eliminare questo elemento? Questa azione non puo essere annullata.`}
        confirmLabel="Elimina"
        cancelLabel="Annulla"
        variant="danger"
        loading={isDeleting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => {
          setShowDeleteConfirm(false);
          setDeleteTarget(null);
        }}
      />

      {/* Bulk Delete Confirmation */}
      <ConfirmDialog
        isOpen={showBulkDeleteConfirm}
        title="Conferma eliminazione multipla"
        message={`Sei sicuro di voler eliminare ${bulkDeleteTarget.length} elementi? Questa azione non puo essere annullata.`}
        confirmLabel={`Elimina ${bulkDeleteTarget.length} elementi`}
        cancelLabel="Annulla"
        variant="danger"
        loading={isDeleting}
        onConfirm={handleBulkDeleteConfirm}
        onCancel={() => {
          setShowBulkDeleteConfirm(false);
          setBulkDeleteTarget([]);
        }}
      />
    </div>
  );
}

export default DataTable;
