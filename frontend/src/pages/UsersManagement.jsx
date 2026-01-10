import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI, rolesAPI } from '../services/api';
import './UsersManagement.css';

export default function UsersManagement() {
  console.log('🔥 UsersManagement component loaded - VERSION 2.0 UPDATED');

  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    phone: ''
  });

  const token = localStorage.getItem('access_token');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersRes, rolesRes] = await Promise.all([
        authAPI.getAllUsers(token),
        rolesAPI.getAll(token)
      ]);
      setUsers(usersRes.data);
      setRoles(rolesRes.data);
      setError('');
    } catch (err) {
      setError('Errore nel caricamento dei dati: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await authAPI.createUser(formData, token);
      setShowCreateForm(false);
      setFormData({ username: '', email: '', password: '', full_name: '', phone: '' });
      loadData();
    } catch (err) {
      setError('Errore nella creazione: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const { password, ...updateData } = formData;
      await authAPI.updateUser(editingUser.id, updateData, token);
      setEditingUser(null);
      setFormData({ username: '', email: '', password: '', full_name: '', phone: '' });
      loadData();
    } catch (err) {
      setError('Errore nell\'aggiornamento: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (userId) => {
    if (!confirm('Sei sicuro di voler eliminare questo utente?')) return;
    try {
      await authAPI.deleteUser(userId, token);
      loadData();
    } catch (err) {
      setError('Errore nell\'eliminazione: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAssignRole = async (userId, roleId) => {
    try {
      await authAPI.assignRole(userId, roleId, token);
      loadData();
    } catch (err) {
      setError('Errore nell\'assegnazione ruolo: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRemoveRole = async (userId, roleId) => {
    try {
      await authAPI.removeRole(userId, roleId, token);
      loadData();
    } catch (err) {
      setError('Errore nella rimozione ruolo: ' + (err.response?.data?.detail || err.message));
    }
  };

  const startEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      full_name: user.full_name || '',
      phone: user.phone || ''
    });
    setShowCreateForm(false);
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setFormData({ username: '', email: '', password: '', full_name: '', phone: '' });
  };

  // Loading state
  if (loading) {
    return <div className="users-management"><p>Caricamento...</p></div>;
  }

  return (
    <div className="users-management">
      <div className="users-header">
        <h1>👥 Gestione Utenti e Ruoli</h1>
        <button className="btn-create" onClick={() => {
          setShowCreateForm(true);
          setEditingUser(null);
          setFormData({ username: '', email: '', password: '', full_name: '', phone: '' });
        }}>
          ➕ Nuovo Utente
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError('')}>✖</button>
        </div>
      )}

      {(showCreateForm || editingUser) && (
        <div className="user-form-card">
          <h2>
            <span aria-hidden="true">{editingUser ? '✏️' : '➕'}</span>
            {editingUser ? 'Modifica Utente' : 'Crea Nuovo Utente'}
          </h2>
          <form onSubmit={editingUser ? handleUpdate : handleCreate} aria-label={editingUser ? 'Modifica utente' : 'Crea nuovo utente'}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="username">Username *</label>
                <input
                  id="username"
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                  aria-required="true"
                />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  aria-required="true"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="full_name">Nome Completo</label>
                <input
                  id="full_name"
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label htmlFor="phone">Telefono</label>
                <input
                  id="phone"
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                />
              </div>
            </div>

            {!editingUser && (
              <div className="form-group">
                <label htmlFor="password">Password *</label>
                <input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  minLength={8}
                  aria-required="true"
                  aria-describedby="password-help"
                />
                <small id="password-help">Minimo 8 caratteri</small>
              </div>
            )}

            <div className="form-actions">
              <button type="submit" className="btn-submit" aria-label={editingUser ? 'Aggiorna utente' : 'Crea utente'}>
                {editingUser ? 'Aggiorna' : 'Crea'}
              </button>
              <button
                type="button"
                className="btn-cancel"
                onClick={() => {
                  setShowCreateForm(false);
                  cancelEdit();
                }}
                aria-label="Annulla operazione"
              >
                Annulla
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="users-table-container">
        {users.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            <p>Nessun utente presente nel sistema</p>
            <p style={{ fontSize: '14px', marginTop: '10px' }}>
              Clicca su "Nuovo Utente" per creare il primo utente
            </p>
          </div>
        ) : (
          <table className="users-table" role="table" aria-label="Tabella utenti">
            <thead>
              <tr>
                <th scope="col">Username</th>
                <th scope="col">Email</th>
                <th scope="col">Nome Completo</th>
                <th scope="col">Ruoli</th>
                <th scope="col">Stato</th>
                <th scope="col">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <strong>{user.username}</strong>
                    {user.is_superuser && <span className="badge-superuser" aria-label="Superutente">Superuser</span>}
                  </td>
                  <td>{user.email}</td>
                  <td>{user.full_name || '-'}</td>
                  <td>
                    <div className="roles-cell">
                      {user.roles.map((role) => (
                        <span key={role.id} className="role-badge" role="group" aria-label={`Ruolo: ${role.name}`}>
                          {role.name}
                          {!role.is_system && user.id !== currentUser?.id && (
                            <button
                              className="role-remove"
                              onClick={() => handleRemoveRole(user.id, role.id)}
                              aria-label={`Rimuovi ruolo ${role.name} da ${user.username}`}
                            >
                              <span aria-hidden="true">✖</span>
                            </button>
                          )}
                        </span>
                      ))}
                      {user.id !== currentUser?.id && (
                        <select
                          className="role-select"
                          value=""
                          onChange={(e) => handleAssignRole(user.id, parseInt(e.target.value))}
                          aria-label={`Aggiungi ruolo a ${user.username}`}
                        >
                          <option value="">+ Aggiungi ruolo</option>
                          {roles.filter(r => !user.roles.find(ur => ur.id === r.id)).map(role => (
                            <option key={role.id} value={role.id}>{role.name}</option>
                          ))}
                        </select>
                      )}
                    </div>
                  </td>
                  <td>
                    <span
                      className={`status-badge ${user.is_active ? 'status-active' : 'status-inactive'}`}
                      aria-label={user.is_active ? 'Utente attivo' : 'Utente inattivo'}
                    >
                      <span aria-hidden="true">{user.is_active ? '✓' : '✗'}</span>
                      {user.is_active ? ' Attivo' : ' Inattivo'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      {user.id !== currentUser?.id && (
                        <>
                          <button
                            className="btn-edit"
                            onClick={() => startEdit(user)}
                            aria-label={`Modifica utente ${user.username}`}
                          >
                            <span aria-hidden="true">✏️</span>
                          </button>
                          <button
                            className="btn-delete"
                            onClick={() => handleDelete(user.id)}
                            aria-label={`Elimina utente ${user.username}`}
                          >
                            <span aria-hidden="true">🗑️</span>
                          </button>
                        </>
                      )}
                      {user.id === currentUser?.id && (
                        <span className="text-muted" aria-label="Sei tu stesso">Tu stesso</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="roles-info">
        <h3>
          <span aria-hidden="true">📋</span>
          Ruoli Disponibili
        </h3>
        {roles.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            Nessun ruolo disponibile
          </p>
        ) : (
          <div className="roles-grid">
            {roles.map(role => (
              <div key={role.id} className="role-card" role="article" aria-label={`Ruolo ${role.name}`}>
                <h4>{role.name}</h4>
                <p>{role.description}</p>
                {role.is_system && <span className="badge-system" aria-label="Ruolo di sistema">Sistema</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
