/**
 * Centralized Token Refresh Service
 *
 * This service provides a single point for token refresh operations
 * to prevent race conditions when multiple components try to refresh
 * the token simultaneously.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Global lock for token refresh to prevent race conditions
let isRefreshingToken = false;
let refreshPromise = null;

/**
 * Safely refresh the access token, preventing concurrent refreshes.
 * If a refresh is already in progress, waits for it to complete.
 *
 * @returns {Promise<string|null>} The new access token, or null if refresh failed
 */
export async function refreshTokenSafe() {
  // If already refreshing, wait for the existing refresh to complete
  if (isRefreshingToken && refreshPromise) {
    console.log('[TokenService] Refresh already in progress, waiting...');
    return refreshPromise;
  }

  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    console.log('[TokenService] No refresh token available');
    return null;
  }

  // Debug: check if refresh token looks valid (has 3 parts)
  const parts = refreshToken.split('.');
  if (parts.length !== 3) {
    console.error('[TokenService] Invalid refresh token format, parts:', parts.length);
    return null;
  }
  console.log('[TokenService] Refresh token found, length:', refreshToken.length);

  isRefreshingToken = true;
  refreshPromise = (async () => {
    try {
      console.log('[TokenService] Starting token refresh...');
      const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken
      });
      const newAccessToken = refreshResponse.data?.access_token;
      const newRefreshToken = refreshResponse.data?.refresh_token;
      if (newAccessToken) {
        localStorage.setItem('access_token', newAccessToken);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }
        console.log('[TokenService] Token refresh successful');
        return newAccessToken;
      }
      console.log('[TokenService] No access token in response');
      return null;
    } catch (err) {
      console.error('[TokenService] Token refresh failed:', err);
      return null;
    } finally {
      isRefreshingToken = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/**
 * Get the current access token, refreshing if necessary.
 *
 * @returns {Promise<string|null>} The access token, or null if not available
 */
export async function getAccessToken() {
  let token = localStorage.getItem('access_token');
  if (!token) {
    token = await refreshTokenSafe();
  }
  return token;
}

/**
 * Clear all tokens (for logout)
 */
export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export default {
  refreshTokenSafe,
  getAccessToken,
  clearTokens
};
