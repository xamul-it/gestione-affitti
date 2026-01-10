/**
 * API service for RuoliAzienda (Person-Company role associations)
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const ruoliAziendaAPI = {
  /**
   * Get all ruoli azienda
   */
  getAll: (token) =>
    axios.get(`${API_BASE_URL}/anagrafica/ruoli-azienda/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }),

  /**
   * Get ruoli for a specific soggetto
   * @param {number} soggettoId - ID del soggetto
   * @param {boolean} attiviOnly - Se true, ritorna solo ruoli attivi
   */
  getBySoggetto: (soggettoId, attiviOnly = false, token) =>
    axios.get(`${API_BASE_URL}/anagrafica/ruoli-azienda/soggetto/${soggettoId}`, {
      params: { attivi_only: attiviOnly },
      headers: { 'Authorization': `Bearer ${token}` }
    }),

  /**
   * Get a specific ruolo azienda by ID
   */
  getById: (id, token) =>
    axios.get(`${API_BASE_URL}/anagrafica/ruoli-azienda/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }),

  /**
   * Create a new ruolo azienda
   */
  create: (data, token) =>
    axios.post(`${API_BASE_URL}/anagrafica/ruoli-azienda/`, data, {
      headers: { 'Authorization': `Bearer ${token}` }
    }),

  /**
   * Update an existing ruolo azienda
   */
  update: (id, data, token) =>
    axios.put(`${API_BASE_URL}/anagrafica/ruoli-azienda/${id}`, data, {
      headers: { 'Authorization': `Bearer ${token}` }
    }),

  /**
   * Delete a ruolo azienda
   */
  delete: (id, token) =>
    axios.delete(`${API_BASE_URL}/anagrafica/ruoli-azienda/${id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }),
};
