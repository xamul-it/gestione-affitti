/**
 * ColumnSelector - Column visibility and order management
 *
 * Allows users to:
 * - Show/hide columns
 * - Reorder columns via drag-and-drop
 * - Reset to default configuration
 *
 * @example
 * <ColumnSelector
 *   columns={columns}
 *   visibleColumns={visibleColumns}
 *   onColumnsChange={handleColumnsChange}
 *   onReset={handleReset}
 * />
 */

import React, { useState, useCallback, useRef } from 'react';
import './ColumnSelector.css';

export function ColumnSelector({
  columns,
  visibleColumns,
  onColumnsChange,
  onReset,
  onClose,
}) {
  const [localVisible, setLocalVisible] = useState(() => new Set(visibleColumns));
  const [orderedColumns, setOrderedColumns] = useState(() => {
    // Start with visible columns in order, then add hidden ones
    const visible = columns.filter(c => visibleColumns.includes(c.field));
    const hidden = columns.filter(c => !visibleColumns.includes(c.field));
    return [...visible, ...hidden].map(c => c.field);
  });
  const [draggedItem, setDraggedItem] = useState(null);
  const [dragOverItem, setDragOverItem] = useState(null);

  const getColumn = useCallback((field) => {
    return columns.find(c => c.field === field);
  }, [columns]);

  /**
   * Toggle column visibility
   */
  const toggleColumn = useCallback((field) => {
    const column = getColumn(field);
    if (column?.required) return; // Can't hide required columns

    setLocalVisible(prev => {
      const newSet = new Set(prev);
      if (newSet.has(field)) {
        newSet.delete(field);
      } else {
        newSet.add(field);
      }
      return newSet;
    });
  }, [getColumn]);

  /**
   * Handle drag start
   */
  const handleDragStart = useCallback((e, field) => {
    setDraggedItem(field);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', field);
  }, []);

  /**
   * Handle drag over
   */
  const handleDragOver = useCallback((e, field) => {
    e.preventDefault();
    if (field !== draggedItem) {
      setDragOverItem(field);
    }
  }, [draggedItem]);

  /**
   * Handle drag end
   */
  const handleDragEnd = useCallback(() => {
    if (draggedItem && dragOverItem && draggedItem !== dragOverItem) {
      setOrderedColumns(prev => {
        const newOrder = [...prev];
        const draggedIdx = newOrder.indexOf(draggedItem);
        const dropIdx = newOrder.indexOf(dragOverItem);

        newOrder.splice(draggedIdx, 1);
        newOrder.splice(dropIdx, 0, draggedItem);

        return newOrder;
      });
    }
    setDraggedItem(null);
    setDragOverItem(null);
  }, [draggedItem, dragOverItem]);

  /**
   * Apply changes
   */
  const handleApply = useCallback(() => {
    // Return visible columns in current order
    const visibleInOrder = orderedColumns.filter(field => localVisible.has(field));
    onColumnsChange(visibleInOrder);
    onClose?.();
  }, [orderedColumns, localVisible, onColumnsChange, onClose]);

  /**
   * Reset to defaults
   */
  const handleReset = useCallback(() => {
    if (onReset) {
      onReset();
      onClose?.();
    }
  }, [onReset, onClose]);

  /**
   * Select all columns
   */
  const selectAll = useCallback(() => {
    setLocalVisible(new Set(columns.map(c => c.field)));
  }, [columns]);

  /**
   * Select only required columns
   */
  const selectMinimal = useCallback(() => {
    setLocalVisible(new Set(columns.filter(c => c.required).map(c => c.field)));
  }, [columns]);

  const visibleCount = localVisible.size;
  const totalCount = columns.length;

  return (
    <div className="column-selector">
      <div className="column-selector__header">
        <h3 className="column-selector__title">Gestione Colonne</h3>
        <button
          type="button"
          className="column-selector__close"
          onClick={onClose}
          title="Chiudi"
        >
          ×
        </button>
      </div>

      <div className="column-selector__info">
        <span>{visibleCount} di {totalCount} colonne visibili</span>
        <div className="column-selector__quick-actions">
          <button
            type="button"
            className="column-selector__quick-btn"
            onClick={selectAll}
          >
            Tutte
          </button>
          <button
            type="button"
            className="column-selector__quick-btn"
            onClick={selectMinimal}
          >
            Solo obbligatorie
          </button>
        </div>
      </div>

      <div className="column-selector__list">
        {orderedColumns.map((field) => {
          const column = getColumn(field);
          if (!column) return null;

          const isVisible = localVisible.has(field);
          const isRequired = column.required;
          const isDragging = draggedItem === field;
          const isDragOver = dragOverItem === field;

          return (
            <div
              key={field}
              className={`column-selector__item ${isVisible ? 'visible' : 'hidden'} ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''}`}
              draggable={!isRequired}
              onDragStart={(e) => handleDragStart(e, field)}
              onDragOver={(e) => handleDragOver(e, field)}
              onDragEnd={handleDragEnd}
            >
              <span className="column-selector__drag-handle" title="Trascina per riordinare">
                ⋮⋮
              </span>

              <label className="column-selector__checkbox">
                <input
                  type="checkbox"
                  checked={isVisible}
                  onChange={() => toggleColumn(field)}
                  disabled={isRequired}
                />
                <span className="column-selector__label">
                  {column.label}
                  {isRequired && <span className="column-selector__required" title="Colonna obbligatoria">*</span>}
                </span>
              </label>

              <span className="column-selector__type">
                {column.type || 'text'}
              </span>
            </div>
          );
        })}
      </div>

      <div className="column-selector__footer">
        <button
          type="button"
          className="column-selector__btn column-selector__btn--secondary"
          onClick={handleReset}
        >
          Ripristina default
        </button>
        <div className="column-selector__footer-right">
          <button
            type="button"
            className="column-selector__btn column-selector__btn--ghost"
            onClick={onClose}
          >
            Annulla
          </button>
          <button
            type="button"
            className="column-selector__btn column-selector__btn--primary"
            onClick={handleApply}
          >
            Applica
          </button>
        </div>
      </div>
    </div>
  );
}

export default ColumnSelector;
