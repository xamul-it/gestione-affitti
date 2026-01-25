/**
 * Esempio Componenti Module - API Service
 *
 * API endpoints for the example module demonstrating cross-cutting components.
 */
import api from '../../../services/api';

const ESEMPIO_API_PREFIX = '/esempio';

// ============================================================================
// ELEMENTI (Tenant Data - Full CRUD)
// ============================================================================

/**
 * List elementi with filtering, sorting, and pagination
 */
export const getElementi = async (params = {}) => {
  const response = await api.get(`${ESEMPIO_API_PREFIX}/elementi/`, { params });
  return response.data;
};

/**
 * Get single elemento by ID
 */
export const getElemento = async (id) => {
  const response = await api.get(`${ESEMPIO_API_PREFIX}/elementi/${id}`);
  return response.data;
};

/**
 * Create new elemento
 */
export const createElemento = async (data) => {
  const response = await api.post(`${ESEMPIO_API_PREFIX}/elementi/`, data);
  return response.data;
};

/**
 * Update existing elemento
 */
export const updateElemento = async (id, data) => {
  const response = await api.put(`${ESEMPIO_API_PREFIX}/elementi/${id}`, data);
  return response.data;
};

/**
 * Delete elemento
 */
export const deleteElemento = async (id) => {
  const response = await api.delete(`${ESEMPIO_API_PREFIX}/elementi/${id}`);
  return response.data;
};

/**
 * Bulk delete elementi
 */
export const bulkDeleteElementi = async (ids) => {
  const response = await api.delete(`${ESEMPIO_API_PREFIX}/elementi/`, { params: { ids } });
  return response.data;
};

// ============================================================================
// CATEGORIE (Domain Data - Read Only)
// ============================================================================

/**
 * List all categories (domain data)
 */
export const getCategorie = async (soloAttive = true) => {
  const response = await api.get(`${ESEMPIO_API_PREFIX}/categorie/`, {
    params: { solo_attive: soloAttive }
  });
  return response.data;
};

/**
 * Get single categoria by ID
 */
export const getCategoria = async (id) => {
  const response = await api.get(`${ESEMPIO_API_PREFIX}/categorie/${id}`);
  return response.data;
};

// ============================================================================
// PRIORITÀ (Domain Data - Read Only)
// ============================================================================

/**
 * List all priorities (domain data)
 */
export const getPriorita = async (soloAttive = true) => {
  const response = await api.get(`${ESEMPIO_API_PREFIX}/priorita/`, {
    params: { solo_attive: soloAttive }
  });
  return response.data;
};

/**
 * Get single priorità by ID
 */
export const getPrioritaSingle = async (id) => {
  const response = await api.get(`${ESEMPIO_API_PREFIX}/priorita/${id}`);
  return response.data;
};

// ============================================================================
// EXPORT DEFAULT
// ============================================================================

const esempioAPI = {
  // Elementi
  getElementi,
  getElemento,
  createElemento,
  updateElemento,
  deleteElemento,
  bulkDeleteElementi,
  // Categorie
  getCategorie,
  getCategoria,
  // Priorità
  getPriorita,
  getPrioritaSingle,
};

export default esempioAPI;
