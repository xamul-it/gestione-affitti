/**
 * useScadenze Hook - State management for Scadenze (Deadlines/Reminders)
 *
 * Provides CRUD operations, state transitions, and badge info for scadenze.
 * Automatically handles loading states, errors, and cache invalidation.
 */
import { useState, useCallback, useEffect } from 'react';
import { scadenzeAPI } from '../../../../services/api';

export const useScadenze = (options = {}) => {
  const {
    autoLoad = false,
    filters = {},
    entity = null, // { modulo, entityType, entityId }
  } = options;

  const [scadenze, setScadenze] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [badgeInfo, setBadgeInfo] = useState(null);

  /**
   * Load scadenze with filters
   */
  const loadScadenze = useCallback(async (customFilters = {}) => {
    setLoading(true);
    setError(null);

    try {
      const mergedFilters = { ...filters, ...customFilters };
      const response = await scadenzeAPI.list(mergedFilters);
      setScadenze(response.data);
      return response.data;
    } catch (err) {
      console.error('Error loading scadenze:', err);
      setError(err.response?.data?.detail || 'Errore nel caricamento scadenze');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [filters]);

  /**
   * Load scadenze for a specific entity
   */
  const loadScadenzeByEntity = useCallback(async (modulo, entityType, entityId, includeCompleted = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.getByEntity(modulo, entityType, entityId, includeCompleted);
      setScadenze(response.data);
      return response.data;
    } catch (err) {
      console.error('Error loading scadenze by entity:', err);
      setError(err.response?.data?.detail || 'Errore nel caricamento scadenze');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Load my scadenze (created by me or I'm recipient)
   */
  const loadMyScadenze = useCallback(async (includeCompleted = false, onlyOverdue = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.getMyScadenze(includeCompleted, onlyOverdue);
      setScadenze(response.data);
      return response.data;
    } catch (err) {
      console.error('Error loading my scadenze:', err);
      setError(err.response?.data?.detail || 'Errore nel caricamento scadenze');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Load badge info
   */
  const loadBadgeInfo = useCallback(async () => {
    try {
      const response = await scadenzeAPI.getBadgeInfo();
      setBadgeInfo(response.data);
      return response.data;
    } catch (err) {
      console.error('Error loading badge info:', err);
      return null;
    }
  }, []);

  /**
   * Create a new scadenza
   */
  const createScadenza = useCallback(async (data) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.create(data);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
      return response.data;
    } catch (err) {
      console.error('Error creating scadenza:', err);
      setError(err.response?.data?.detail || 'Errore nella creazione scadenza');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Create a standalone TODO
   */
  const createTodo = useCallback(async (data) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.createTodo(data);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
      return response.data;
    } catch (err) {
      console.error('Error creating TODO:', err);
      setError(err.response?.data?.detail || 'Errore nella creazione TODO');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Update a scadenza
   */
  const updateScadenza = useCallback(async (id, data) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.update(id, data);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
      return response.data;
    } catch (err) {
      console.error('Error updating scadenza:', err);
      setError(err.response?.data?.detail || 'Errore nell\'aggiornamento scadenza');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Delete a scadenza (soft delete)
   */
  const deleteScadenza = useCallback(async (id) => {
    setLoading(true);
    setError(null);

    try {
      await scadenzeAPI.delete(id);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
    } catch (err) {
      console.error('Error deleting scadenza:', err);
      setError(err.response?.data?.detail || 'Errore nella cancellazione scadenza');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Complete a scadenza
   */
  const completaScadenza = useCallback(async (id, note = null) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.completa(id, note);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
      return response.data;
    } catch (err) {
      console.error('Error completing scadenza:', err);
      setError(err.response?.data?.detail || 'Errore nel completamento scadenza');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Postpone a scadenza to a new date
   */
  const posticipaScadenza = useCallback(async (id, nuovaData, note = null) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.posticipa(id, nuovaData, note);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
      return response.data;
    } catch (err) {
      console.error('Error postponing scadenza:', err);
      setError(err.response?.data?.detail || 'Errore nel posticipo scadenza');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Reactivate a completed/cancelled scadenza
   */
  const riattivaScadenza = useCallback(async (id) => {
    setLoading(true);
    setError(null);

    try {
      const response = await scadenzeAPI.riattiva(id);
      // Refresh list and badge
      await Promise.all([
        loadScadenze(),
        loadBadgeInfo()
      ]);
      return response.data;
    } catch (err) {
      console.error('Error reactivating scadenza:', err);
      setError(err.response?.data?.detail || 'Errore nella riattivazione scadenza');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadScadenze, loadBadgeInfo]);

  /**
   * Get audit logs for a scadenza
   */
  const loadLogs = useCallback(async (id) => {
    try {
      const response = await scadenzeAPI.getLogs(id);
      return response.data;
    } catch (err) {
      console.error('Error loading logs:', err);
      throw err;
    }
  }, []);

  // Auto-load on mount if enabled
  useEffect(() => {
    if (autoLoad) {
      if (entity) {
        loadScadenzeByEntity(entity.modulo, entity.entityType, entity.entityId);
      } else {
        loadScadenze();
      }
      loadBadgeInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoad, entity?.modulo, entity?.entityType, entity?.entityId]);

  return {
    // State
    scadenze,
    loading,
    error,
    badgeInfo,

    // Load operations
    loadScadenze,
    loadScadenzeByEntity,
    loadMyScadenze,
    loadBadgeInfo,

    // CRUD operations
    createScadenza,
    createTodo,
    updateScadenza,
    deleteScadenza,

    // State transitions
    completaScadenza,
    posticipaScadenza,
    riattivaScadenza,

    // Audit
    loadLogs,

    // Utilities
    refresh: () => Promise.all([loadScadenze(), loadBadgeInfo()]),
  };
};

export default useScadenze;
