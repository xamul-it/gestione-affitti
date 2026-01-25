/**
 * useTableConfig - Table configuration management hook
 *
 * Fetches table definitions and user preferences from the backend.
 * Handles saving column visibility, order, and other preferences.
 *
 * @example
 * const { config, loading, updateColumns, resetConfig } = useTableConfig({
 *   moduleName: 'anagrafica_italiana',
 *   entityName: 'SoggettoAnagrafico'
 * });
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../../services/api';

const API_BASE = '/tables';

/**
 * Table configuration API
 */
export const tableConfigAPI = {
  // Get table definition and user config
  getConfig: (moduleName, entityName) =>
    api.get(`${API_BASE}/config/${moduleName}/${entityName}`),

  // Save full configuration
  saveConfig: (moduleName, entityName, config) =>
    api.put(`${API_BASE}/config/${moduleName}/${entityName}`, config),

  // Update only visible columns
  updateColumns: (moduleName, entityName, columns) =>
    api.post(`${API_BASE}/config/${moduleName}/${entityName}/columns`, columns),

  // Reset to defaults
  resetConfig: (moduleName, entityName) =>
    api.delete(`${API_BASE}/config/${moduleName}/${entityName}`),

  // Get table definition only
  getDefinition: (moduleName, entityName) =>
    api.get(`${API_BASE}/definitions/${moduleName}/${entityName}`),

  // List all definitions
  listDefinitions: (moduleName) =>
    api.get(`${API_BASE}/definitions`, { params: { module_name: moduleName } }),
};

/**
 * useTableConfig hook
 */
export function useTableConfig({ moduleName, entityName, autoFetch = true }) {
  const [definition, setDefinition] = useState(null);
  const [userConfig, setUserConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  /**
   * Fetch configuration from backend
   */
  const fetchConfig = useCallback(async () => {
    if (!moduleName || !entityName) return;

    setLoading(true);
    setError(null);

    try {
      const response = await tableConfigAPI.getConfig(moduleName, entityName);
      const data = response.data;

      setDefinition(data.definition);
      setUserConfig(data.user_config);
    } catch (err) {
      console.error('Error fetching table config:', err);
      setError(err.response?.data?.detail || 'Errore nel caricamento configurazione');
    } finally {
      setLoading(false);
    }
  }, [moduleName, entityName]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchConfig();
    }
  }, [autoFetch, fetchConfig]);

  /**
   * Get effective configuration (user config or defaults)
   */
  const effectiveConfig = useMemo(() => {
    if (!definition) return null;

    const userVisible = userConfig?.visible_columns;
    const defaultVisible = definition.default_visible?.length > 0
      ? definition.default_visible
      : definition.columns.filter(c => c.visible !== false).map(c => c.field);

    return {
      visibleColumns: userVisible || defaultVisible,
      columnWidths: userConfig?.column_widths || {},
      sortField: userConfig?.sort_field || definition.default_sort_field,
      sortOrder: userConfig?.sort_order || definition.default_sort_order || 'asc',
      pageSize: userConfig?.page_size || definition.default_page_size || 20,
      filters: userConfig?.filters || {},
    };
  }, [definition, userConfig]);

  /**
   * Get columns with visibility info
   */
  const columns = useMemo(() => {
    if (!definition || !effectiveConfig) return [];

    const visibleSet = new Set(effectiveConfig.visibleColumns);

    // Return columns in visibility order, preserving the order of visible columns
    const orderedVisible = effectiveConfig.visibleColumns
      .map(field => definition.columns.find(c => c.field === field))
      .filter(Boolean);

    const hiddenColumns = definition.columns.filter(
      c => !visibleSet.has(c.field)
    );

    return [...orderedVisible, ...hiddenColumns].map(col => ({
      ...col,
      visible: visibleSet.has(col.field),
      width: effectiveConfig.columnWidths[col.field] || col.width,
    }));
  }, [definition, effectiveConfig]);

  /**
   * Get visible columns only
   */
  const visibleColumns = useMemo(() => {
    return columns.filter(c => c.visible);
  }, [columns]);

  /**
   * Update visible columns
   */
  const updateColumns = useCallback(async (newVisibleColumns) => {
    if (!moduleName || !entityName) return;

    setSaving(true);
    try {
      await tableConfigAPI.updateColumns(moduleName, entityName, newVisibleColumns);

      // Update local state
      setUserConfig(prev => ({
        ...prev,
        visible_columns: newVisibleColumns,
      }));
    } catch (err) {
      console.error('Error saving column config:', err);
      throw err;
    } finally {
      setSaving(false);
    }
  }, [moduleName, entityName]);

  /**
   * Update full configuration
   */
  const updateConfig = useCallback(async (updates) => {
    if (!moduleName || !entityName) return;

    setSaving(true);
    try {
      const response = await tableConfigAPI.saveConfig(moduleName, entityName, {
        visible_columns: updates.visibleColumns || effectiveConfig?.visibleColumns,
        column_widths: updates.columnWidths || effectiveConfig?.columnWidths,
        sort_field: updates.sortField ?? effectiveConfig?.sortField,
        sort_order: updates.sortOrder ?? effectiveConfig?.sortOrder,
        page_size: updates.pageSize ?? effectiveConfig?.pageSize,
        filters: updates.filters ?? effectiveConfig?.filters,
      });

      setUserConfig(response.data);
    } catch (err) {
      console.error('Error saving table config:', err);
      throw err;
    } finally {
      setSaving(false);
    }
  }, [moduleName, entityName, effectiveConfig]);

  /**
   * Reset to default configuration
   */
  const resetConfig = useCallback(async () => {
    if (!moduleName || !entityName) return;

    setSaving(true);
    try {
      await tableConfigAPI.resetConfig(moduleName, entityName);
      setUserConfig(null);
    } catch (err) {
      console.error('Error resetting config:', err);
      throw err;
    } finally {
      setSaving(false);
    }
  }, [moduleName, entityName]);

  return {
    // Data
    definition,
    userConfig,
    effectiveConfig,
    columns,
    visibleColumns,

    // State
    loading,
    error,
    saving,

    // Actions
    fetchConfig,
    updateColumns,
    updateConfig,
    resetConfig,
  };
}

export default useTableConfig;
