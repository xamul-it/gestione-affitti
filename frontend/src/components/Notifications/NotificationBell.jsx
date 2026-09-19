/**
 * NotificationBell - generic core notification bell.
 *
 * Separate from ScadenzaBadge/NotifichePanel (which already show live
 * scadenze in-app): this bell surfaces generic Notifica rows created by
 * NotificationService.notify() from any module. The scadenza reminder
 * job itself sends email-only (see docs/superpowers/plans/2026-09-18-notification-service.md
 * Global Constraints), so this bell stays quiet for scadenze today and
 * lights up once other modules start calling notify() with in-app content.
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotifiche } from './hooks/useNotifiche';
import { renderIcon } from '../Navigation/iconRegistry.jsx';
import './NotificationBell.css';

const NotificationBell = () => {
  const navigate = useNavigate();
  const { notifiche, badgeCount, loadNotifiche, loadBadge, segnaLetta, segnaTutteLette } = useNotifiche();
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    loadBadge();
    const interval = setInterval(loadBadge, 60 * 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (open) loadNotifiche(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleItemClick = async (notifica) => {
    if (!notifica.letta) await segnaLetta(notifica.id);
    setOpen(false);
    if (notifica.link_url) navigate(notifica.link_url);
  };

  return (
    <div className="notification-bell" ref={containerRef}>
      <button className="notification-bell__trigger" onClick={() => setOpen((v) => !v)} title="Notifiche">
        {renderIcon('bell', { size: 16 })}
        {badgeCount > 0 && <span className="notification-bell__count">{badgeCount}</span>}
      </button>

      {open && (
        <div className="notification-bell__panel">
          <div className="notification-bell__header">
            <span>Notifiche</span>
            {notifiche.some((n) => !n.letta) && (
              <button className="notification-bell__mark-all" onClick={segnaTutteLette}>
                Segna tutte lette
              </button>
            )}
          </div>
          <div className="notification-bell__body">
            {notifiche.length === 0 && <div className="notification-bell__empty">Nessuna notifica</div>}
            {notifiche.map((n) => (
              <div
                key={n.id}
                className={`notification-bell__item ${n.letta ? '' : 'notification-bell__item--unread'}`}
                onClick={() => handleItemClick(n)}
              >
                <div className="notification-bell__item-title">{n.titolo}</div>
                <div className="notification-bell__item-body">{n.corpo}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
