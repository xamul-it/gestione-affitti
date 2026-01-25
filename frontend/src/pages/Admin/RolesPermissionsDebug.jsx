import { useEffect, useState } from 'react';
import { ShieldCheck, RefreshCcw } from 'lucide-react';
import { rolesAPI } from '../../services/api';
import './RolesPermissionsDebug.css';

export default function RolesPermissionsDebug() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadRoles = async () => {
    try {
      setLoading(true);
      setError('');
      const token = localStorage.getItem('access_token');
      const response = await rolesAPI.getAllWithPermissions(token);
      setRoles(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoles();
  }, []);

  return (
    <div className="roles-debug">
      <div className="roles-debug-header">
        <div className="header-title">
          <ShieldCheck size={24} strokeWidth={1.7} />
          <h1>Debug Ruoli e Permessi</h1>
        </div>
        <button className="btn btn-secondary" onClick={loadRoles} disabled={loading}>
          <RefreshCcw size={16} strokeWidth={1.7} />
          Aggiorna
        </button>
      </div>

      {error && <div className="roles-debug-error">{error}</div>}
      {loading && <div className="roles-debug-loading">Caricamento...</div>}

      {!loading && !error && roles.length === 0 && (
        <div className="roles-debug-empty">Nessun ruolo trovato</div>
      )}

      {!loading && !error && roles.length > 0 && (
        <div className="roles-debug-list">
          {roles.map((role) => (
            <div key={role.id} className="roles-debug-card">
              <div className="roles-debug-card-header">
                <div>
                  <h2>{role.name}</h2>
                  {role.description && <p>{role.description}</p>}
                </div>
                {role.is_system && <span className="badge-system">Sistema</span>}
              </div>

              {role.permissions.length === 0 ? (
                <div className="roles-debug-empty-perms">Nessun permesso assegnato</div>
              ) : (
                <table className="roles-debug-table">
                  <thead>
                    <tr>
                      <th>Permesso</th>
                      <th>Resource</th>
                      <th>Action</th>
                      <th>Descrizione</th>
                    </tr>
                  </thead>
                  <tbody>
                    {role.permissions.map((perm) => (
                      <tr key={perm.id}>
                        <td>{perm.name}</td>
                        <td>{perm.resource}</td>
                        <td>{perm.action}</td>
                        <td>{perm.description || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
