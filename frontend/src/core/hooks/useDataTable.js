/**
 * useDataTable - Data table state management hook
 *
 * Provides comprehensive state management for data tables including
 * pagination, sorting, filtering, and row selection.
 *
 * @example
 * const table = useDataTable({
 *   endpoint: '/affittuari/',
 *   columns: [...],
 *   defaultSort: { field: 'cognome', order: 'asc' }
 * });
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useEntityCRUD } from './useEntityCRUD';
import { getNestedValue } from '../utils/formatters';

/**
 * useDataTable hook
 *
 * @param {Object} config - Table configuration
 * @param {string} config.endpoint - API endpoint
 * @param {Array} config.columns - Column definitions
 * @param {Object} config.defaultSort - Default sort { field, order }
 * @param {Array} config.defaultFilters - Default filter values
 * @param {number} config.pageSize - Items per page (default: 20)
 * @param {Object} options - Additional options
 * @returns {Object} Table state and handlers
 */
export function useDataTable(config, options = {}) {
  const {
    endpoint,
    columns = [],
    defaultSort = { field: null, order: 'asc' },
    defaultFilters = {},
    pageSize: defaultPageSize = 20,
    searchFields = [],
    localFiltering = true,
    localSorting = true,
    localPagination = true,
  } = config;

  const {
    autoFetch = true,
    onDataChange,
    onError,
  } = options;

  // CRUD operations
  const {
    data: rawData,
    loading,
    error,
    pagination: apiPagination,
    fetchAll,
    remove,
    bulkDelete,
    refresh,
    clearError,
  } = useEntityCRUD(endpoint, {
    autoFetch,
    onError,
  });

  // Local state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  const [sortField, setSortField] = useState(defaultSort.field);
  const [sortOrder, setSortOrder] = useState(defaultSort.order);
  const [filters, setFilters] = useState(defaultFilters);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [columnVisibility, setColumnVisibility] = useState(() => {
    const visibility = {};
    columns.forEach(col => {
      visibility[col.field] = col.visible !== false;
    });
    return visibility;
  });

  // Refs
  const prevDataRef = useRef(rawData);

  // Notify on data change
  useEffect(() => {
    if (rawData !== prevDataRef.current && onDataChange) {
      onDataChange(rawData);
    }
    prevDataRef.current = rawData;
  }, [rawData, onDataChange]);

  /**
   * Apply search filter
   */
  const applySearch = useCallback((data, term) => {
    if (!term || !localFiltering) return data;

    const searchLower = term.toLowerCase();
    const fieldsToSearch = searchFields.length > 0
      ? searchFields
      : columns.filter(c => c.filterable).map(c => c.field);

    return data.filter(item => {
      return fieldsToSearch.some(field => {
        const value = getNestedValue(item, field);
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(searchLower);
      });
    });
  }, [columns, searchFields, localFiltering]);

  /**
   * Apply column filters
   */
  const applyFilters = useCallback((data, filterValues) => {
    if (!localFiltering) return data;

    return data.filter(item => {
      return Object.entries(filterValues).every(([field, filterValue]) => {
        if (filterValue === null || filterValue === undefined || filterValue === '') {
          return true;
        }

        const itemValue = getNestedValue(item, field);

        // Handle different filter types
        if (Array.isArray(filterValue)) {
          // Multi-select filter
          return filterValue.length === 0 || filterValue.includes(itemValue);
        }

        if (typeof filterValue === 'object') {
          // Range filter { min, max }
          if (filterValue.min !== undefined && itemValue < filterValue.min) {
            return false;
          }
          if (filterValue.max !== undefined && itemValue > filterValue.max) {
            return false;
          }
          return true;
        }

        // Exact match or contains
        if (typeof itemValue === 'string') {
          return itemValue.toLowerCase().includes(String(filterValue).toLowerCase());
        }

        return itemValue === filterValue;
      });
    });
  }, [localFiltering]);

  /**
   * Apply sorting
   */
  const applySort = useCallback((data, field, order) => {
    if (!field || !localSorting) return data;

    return [...data].sort((a, b) => {
      const aValue = getNestedValue(a, field);
      const bValue = getNestedValue(b, field);

      // Handle null/undefined
      if (aValue === null || aValue === undefined) return order === 'asc' ? 1 : -1;
      if (bValue === null || bValue === undefined) return order === 'asc' ? -1 : 1;

      // Compare values
      let comparison = 0;
      if (typeof aValue === 'string') {
        comparison = aValue.localeCompare(bValue, 'it');
      } else if (aValue instanceof Date || !isNaN(Date.parse(aValue))) {
        comparison = new Date(aValue) - new Date(bValue);
      } else {
        comparison = aValue - bValue;
      }

      return order === 'asc' ? comparison : -comparison;
    });
  }, [localSorting]);

  /**
   * Apply pagination
   */
  const applyPagination = useCallback((data, currentPage, size) => {
    if (!localPagination) return data;

    const start = (currentPage - 1) * size;
    return data.slice(start, start + size);
  }, [localPagination]);

  /**
   * Process data through all transformations
   */
  const processedData = useMemo(() => {
    let result = [...rawData];

    // Apply search
    result = applySearch(result, searchTerm);

    // Apply filters
    result = applyFilters(result, filters);

    // Apply sorting
    result = applySort(result, sortField, sortOrder);

    return result;
  }, [rawData, searchTerm, filters, sortField, sortOrder, applySearch, applyFilters, applySort]);

  /**
   * Final paginated data
   */
  const data = useMemo(() => {
    return applyPagination(processedData, page, pageSize);
  }, [processedData, page, pageSize, applyPagination]);

  /**
   * Pagination info
   */
  const pagination = useMemo(() => {
    const total = localPagination ? processedData.length : apiPagination.total;
    return {
      page,
      pageSize,
      total,
      totalPages: Math.ceil(total / pageSize) || 1,
      hasNextPage: page < Math.ceil(total / pageSize),
      hasPrevPage: page > 1,
    };
  }, [page, pageSize, processedData.length, localPagination, apiPagination.total]);

  /**
   * Handle sort
   */
  const handleSort = useCallback((field) => {
    if (sortField === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
    setPage(1); // Reset to first page on sort change
  }, [sortField]);

  /**
   * Set filter value
   */
  const setFilter = useCallback((field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
    }));
    setPage(1); // Reset to first page on filter change
  }, []);

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    setFilters({});
    setSearchTerm('');
    setPage(1);
  }, []);

  /**
   * Handle search
   */
  const handleSearch = useCallback((term) => {
    setSearchTerm(term);
    setPage(1);
  }, []);

  /**
   * Toggle row selection
   */
  const toggleSelect = useCallback((id) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  /**
   * Select all visible rows
   */
  const selectAll = useCallback(() => {
    const allIds = data.map(item => item.id);
    const allSelected = allIds.every(id => selectedIds.has(id));

    if (allSelected) {
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        allIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    } else {
      setSelectedIds(prev => new Set([...prev, ...allIds]));
    }
  }, [data, selectedIds]);

  /**
   * Clear selection
   */
  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  /**
   * Check if all visible rows are selected
   */
  const isAllSelected = useMemo(() => {
    if (data.length === 0) return false;
    return data.every(item => selectedIds.has(item.id));
  }, [data, selectedIds]);

  /**
   * Check if some (but not all) visible rows are selected
   */
  const isSomeSelected = useMemo(() => {
    if (data.length === 0) return false;
    const selected = data.filter(item => selectedIds.has(item.id));
    return selected.length > 0 && selected.length < data.length;
  }, [data, selectedIds]);

  /**
   * Get selected items
   */
  const selectedItems = useMemo(() => {
    return rawData.filter(item => selectedIds.has(item.id));
  }, [rawData, selectedIds]);

  /**
   * Toggle column visibility
   */
  const toggleColumnVisibility = useCallback((field) => {
    setColumnVisibility(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  }, []);

  /**
   * Get visible columns
   */
  const visibleColumns = useMemo(() => {
    return columns.filter(col => columnVisibility[col.field] !== false);
  }, [columns, columnVisibility]);

  /**
   * Delete selected items
   */
  const deleteSelected = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;

    await bulkDelete(ids);
    clearSelection();
  }, [selectedIds, bulkDelete, clearSelection]);

  /**
   * Handle page change
   */
  const handlePageChange = useCallback((newPage) => {
    setPage(Math.max(1, Math.min(newPage, pagination.totalPages)));
  }, [pagination.totalPages]);

  /**
   * Handle page size change
   */
  const handlePageSizeChange = useCallback((newSize) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  // Reset page when data changes significantly
  useEffect(() => {
    if (page > pagination.totalPages && pagination.totalPages > 0) {
      setPage(pagination.totalPages);
    }
  }, [page, pagination.totalPages]);

  return {
    // Data
    data,
    rawData,
    processedData,
    loading,
    error,

    // Pagination
    page,
    pageSize,
    pagination,
    setPage: handlePageChange,
    setPageSize: handlePageSizeChange,

    // Sorting
    sortField,
    sortOrder,
    handleSort,

    // Filtering
    filters,
    searchTerm,
    setFilter,
    setSearchTerm: handleSearch,
    clearFilters,

    // Selection
    selectedIds,
    selectedItems,
    isAllSelected,
    isSomeSelected,
    toggleSelect,
    selectAll,
    clearSelection,
    deleteSelected,

    // Columns
    columns,
    visibleColumns,
    columnVisibility,
    toggleColumnVisibility,

    // CRUD operations
    remove,
    bulkDelete,
    refresh,
    clearError,
    fetchAll,
  };
}

export default useDataTable;
