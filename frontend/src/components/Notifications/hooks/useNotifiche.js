/**
 * useNotifiche Hook - State management for generic core Notifiche.
 */
import { useState, useCallback } from 'react';
import { notificheAPI } from '../../../services/api';

export const useNotifiche = () => {
  const [notifiche, setNotifiche] = useState([]);
  const [badgeCount, setBadgeCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadNotifiche = useCallback(async (soloNonLette = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await notificheAPI.list({ solo_non_lette: soloNonLette });
      setNotifiche(response.data);
      return response.data;
    } catch (err) {
      console.error('Error loading notifiche:', err);
      setError(err.response?.data?.detail || 'Errore nel caricamento notifiche');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBadge = useCallback(async () => {
    try {
      const response = await notificheAPI.getBadge();
      setBadgeCount(response.data.count_non_lette);
      return response.data.count_non_lette;
    } catch (err) {
      console.error('Error loading notifiche badge:', err);
      return null;
    }
  }, []);

  const segnaLetta = useCallback(async (id) => {
    try {
      await notificheAPI.segnaLetta(id);
      setNotifiche((prev) => prev.map((n) => (n.id === id ? { ...n, letta: true } : n)));
      setBadgeCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error marking notifica as read:', err);
      setError(err.response?.data?.detail || 'Errore nella lettura notifica');
      throw err;
    }
  }, []);

  const segnaTutteLette = useCallback(async () => {
    try {
      await notificheAPI.segnaTutteLette();
      setNotifiche((prev) => prev.map((n) => ({ ...n, letta: true })));
      setBadgeCount(0);
    } catch (err) {
      console.error('Error marking all notifiche as read:', err);
      setError(err.response?.data?.detail || 'Errore nella lettura di tutte le notifiche');
      throw err;
    }
  }, []);

  return { notifiche, badgeCount, loading, error, loadNotifiche, loadBadge, segnaLetta, segnaTutteLette };
};
