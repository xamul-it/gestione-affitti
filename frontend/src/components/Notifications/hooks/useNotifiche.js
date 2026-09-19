/**
 * useNotifiche Hook - State management for generic core Notifiche.
 */
import { useState, useCallback } from 'react';
import { notificheAPI } from '../../../services/api';

export const useNotifiche = () => {
  const [notifiche, setNotifiche] = useState([]);
  const [badgeCount, setBadgeCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadNotifiche = useCallback(async (soloNonLette = false) => {
    setLoading(true);
    try {
      const response = await notificheAPI.list({ solo_non_lette: soloNonLette });
      setNotifiche(response.data);
      return response.data;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBadge = useCallback(async () => {
    const response = await notificheAPI.getBadge();
    setBadgeCount(response.data.count_non_lette);
    return response.data.count_non_lette;
  }, []);

  const segnaLetta = useCallback(async (id) => {
    await notificheAPI.segnaLetta(id);
    setNotifiche((prev) => prev.map((n) => (n.id === id ? { ...n, letta: true } : n)));
    setBadgeCount((prev) => Math.max(0, prev - 1));
  }, []);

  const segnaTutteLette = useCallback(async () => {
    await notificheAPI.segnaTutteLette();
    setNotifiche((prev) => prev.map((n) => ({ ...n, letta: true })));
    setBadgeCount(0);
  }, []);

  return { notifiche, badgeCount, loading, loadNotifiche, loadBadge, segnaLetta, segnaTutteLette };
};
