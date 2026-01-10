/**
 * API Service for Anagrafica Italiana (Italian Registry) Module
 *
 * Provides methods to interact with the anagrafica backend API:
 * - Soggetti Anagrafici (persons and companies)
 * - Domini (reference data: comuni, tipi documento)
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Helper to get auth token
const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ============================================================================
// SOGGETTI ANAGRAFICI
// ============================================================================

/**
 * Get list of soggetti anagrafici
 */
export const getSoggettiAnagrafici = async (params = {}) => {
  const { skip = 0, limit = 100, attivi_solo = false } = params;

  const response = await axios.get(`${API_BASE_URL}/anagrafica/soggetti`, {
    headers: getAuthHeader(),
    params: { skip, limit, attivi_solo }
  });

  return response.data;
};

/**
 * Get a single soggetto by ID
 */
export const getSoggettoById = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/anagrafica/soggetti/${id}`, {
    headers: getAuthHeader()
  });

  return response.data;
};

/**
 * Create a new soggetto anagrafico
 */
export const createSoggetto = async (soggettoData) => {
  const response = await axios.post(
    `${API_BASE_URL}/anagrafica/soggetti`,
    soggettoData,
    { headers: getAuthHeader() }
  );

  return response.data;
};

/**
 * Update an existing soggetto
 */
export const updateSoggetto = async (id, soggettoData) => {
  const response = await axios.put(
    `${API_BASE_URL}/anagrafica/soggetti/${id}`,
    soggettoData,
    { headers: getAuthHeader() }
  );

  return response.data;
};

/**
 * Delete a soggetto
 */
export const deleteSoggetto = async (id) => {
  await axios.delete(`${API_BASE_URL}/anagrafica/soggetti/${id}`, {
    headers: getAuthHeader()
  });
};

/**
 * Get ruoli for a soggetto
 */
export const getSoggettoRuoli = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/anagrafica/soggetti/${id}/ruoli`, {
    headers: getAuthHeader()
  });

  return response.data;
};

// ============================================================================
// COMUNI ITALIA
// ============================================================================

/**
 * Get list of Italian municipalities (comuni)
 */
export const getComuni = async (params = {}) => {
  const { skip = 0, limit = 100, provincia = null, search = null } = params;

  const response = await axios.get(`${API_BASE_URL}/anagrafica/domini/comuni`, {
    headers: getAuthHeader(),
    params: { skip, limit, provincia, search }
  });

  return response.data;
};

/**
 * Get a single comune by ID
 */
export const getComuneById = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/anagrafica/domini/comuni/${id}`, {
    headers: getAuthHeader()
  });

  return response.data;
};

/**
 * Search comuni by postal code (CAP)
 */
export const searchComuniByCAP = async (cap) => {
  const response = await axios.get(
    `${API_BASE_URL}/anagrafica/domini/comuni/search/cap/${cap}`,
    { headers: getAuthHeader() }
  );

  return response.data;
};

// ============================================================================
// TIPI DOCUMENTO
// ============================================================================

/**
 * Get list of document types
 */
export const getTipiDocumento = async (params = {}) => {
  const { skip = 0, limit = 100, categoria = null, attivi_solo = true } = params;

  const response = await axios.get(`${API_BASE_URL}/anagrafica/domini/tipi-documento`, {
    headers: getAuthHeader(),
    params: { skip, limit, categoria, attivi_solo }
  });

  return response.data;
};

/**
 * Get a single tipo documento by ID
 */
export const getTipoDocumentoById = async (id) => {
  const response = await axios.get(
    `${API_BASE_URL}/anagrafica/domini/tipi-documento/${id}`,
    { headers: getAuthHeader() }
  );

  return response.data;
};

/**
 * Get document categories with counts
 */
export const getCategorieDocumento = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/anagrafica/domini/categorie-documento`,
    { headers: getAuthHeader() }
  );

  return response.data;
};

// ============================================================================
// RUOLI AZIENDA TIPI
// ============================================================================

/**
 * Get list of ruoli azienda tipi (company role types)
 */
export const getRuoliAziendaTipi = async (params = {}) => {
  const { skip = 0, limit = 100, attivi_solo = false, search = null } = params;

  const response = await axios.get(`${API_BASE_URL}/anagrafica/domini/ruoli-azienda-tipi/`, {
    headers: getAuthHeader(),
    params: { skip, limit, attivi_solo, search }
  });

  return response.data;
};

/**
 * Get a single ruolo azienda tipo by ID
 */
export const getRuoloAziendaTipoById = async (id) => {
  const response = await axios.get(
    `${API_BASE_URL}/anagrafica/domini/ruoli-azienda-tipi/${id}`,
    { headers: getAuthHeader() }
  );

  return response.data;
};

/**
 * Create a new ruolo azienda tipo
 */
export const createRuoloAziendaTipo = async (ruoloData) => {
  const response = await axios.post(
    `${API_BASE_URL}/anagrafica/domini/ruoli-azienda-tipi/`,
    ruoloData,
    { headers: getAuthHeader() }
  );

  return response.data;
};

/**
 * Update an existing ruolo azienda tipo
 */
export const updateRuoloAziendaTipo = async (id, ruoloData) => {
  const response = await axios.put(
    `${API_BASE_URL}/anagrafica/domini/ruoli-azienda-tipi/${id}`,
    ruoloData,
    { headers: getAuthHeader() }
  );

  return response.data;
};

/**
 * Delete a ruolo azienda tipo
 */
export const deleteRuoloAziendaTipo = async (id) => {
  await axios.delete(
    `${API_BASE_URL}/anagrafica/domini/ruoli-azienda-tipi/${id}`,
    { headers: getAuthHeader() }
  );
};

/**
 * Merge two ruoli azienda tipi (consolidate duplicates)
 */
export const mergeRuoliAziendaTipi = async (sourceId, targetId) => {
  const response = await axios.post(
    `${API_BASE_URL}/anagrafica/domini/ruoli-azienda-tipi/merge`,
    { source_id: sourceId, target_id: targetId },
    { headers: getAuthHeader() }
  );

  return response.data;
};

// ============================================
// RUOLI AZIENDA (Associazioni Persona-Azienda)
// ============================================

/**
 * Get all ruoli for a soggetto (both as persona and as azienda)
 */
export const getRuoliAziendaBySoggetto = async (soggettoId, params = {}) => {
  const { attivi_only = false } = params;
  const response = await axios.get(
    `${API_BASE_URL}/anagrafica/ruoli-azienda/soggetto/${soggettoId}`,
    {
      headers: getAuthHeader(),
      params: { attivi_only }
    }
  );
  return response.data;
};

/**
 * Create a new ruolo azienda association
 */
export const createRuoloAzienda = async (ruoloData) => {
  const response = await axios.post(
    `${API_BASE_URL}/anagrafica/ruoli-azienda/`,
    ruoloData,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Update an existing ruolo azienda association
 */
export const updateRuoloAzienda = async (id, ruoloData) => {
  const response = await axios.put(
    `${API_BASE_URL}/anagrafica/ruoli-azienda/${id}`,
    ruoloData,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Delete a ruolo azienda association
 */
export const deleteRuoloAzienda = async (id) => {
  const response = await axios.delete(
    `${API_BASE_URL}/anagrafica/ruoli-azienda/${id}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

// Export all API functions
export default {
  // Soggetti
  getSoggettiAnagrafici,
  getSoggettoById,
  createSoggetto,
  updateSoggetto,
  deleteSoggetto,
  getSoggettoRuoli,

  // Comuni
  getComuni,
  getComuneById,
  searchComuniByCAP,

  // Tipi Documento
  getTipiDocumento,
  getTipoDocumentoById,
  getCategorieDocumento,

  // Ruoli Azienda Tipi
  getRuoliAziendaTipi,
  getRuoloAziendaTipoById,
  createRuoloAziendaTipo,
  updateRuoloAziendaTipo,
  deleteRuoloAziendaTipo,
  mergeRuoliAziendaTipi,

  // Ruoli Azienda (Associazioni)
  getRuoliAziendaBySoggetto,
  createRuoloAzienda,
  updateRuoloAzienda,
  deleteRuoloAzienda,
};
