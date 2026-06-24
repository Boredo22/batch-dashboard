// Centralized fetch wrapper for the Flask backend.
//
// Replaces the ~40 copies of the try / response.ok / response.json() / catch
// pattern that were scattered across the pages. Call sites become:
//
//   try {
//     const result = await apiPost(`/api/relay/${id}/on`);
//     addLog(result.message);
//   } catch (e) {
//     addLog(`Error: ${e.message}`);
//   }
//
// On a non-2xx response (or a thrown network error) `request` raises an
// ApiError whose `.message` is the backend's `error`/`message` field, so a
// single catch handles both transport and application failures.

import { toast } from 'svelte-sonner';

export class ApiError extends Error {
  constructor(message, payload, status) {
    super(message);
    this.name = 'ApiError';
    this.payload = payload;   // full parsed JSON body, if any
    this.status = status;     // HTTP status (0 for network failure)
  }
}

// Default per-request timeout. The backend drives hardware and can briefly
// block; this just prevents a hung request from leaving the UI waiting forever
// (replaces the old per-call fetchWithTimeout in Settings.svelte).
const DEFAULT_TIMEOUT_MS = 15000;

async function request(path, { method = 'GET', body, timeout = DEFAULT_TIMEOUT_MS } = {}) {
  let res;
  try {
    res = await fetch(path, {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(timeout),
    });
  } catch (e) {
    // Timeout (AbortError) or network/CORS/server-down: normalize to ApiError
    // so callers need only one catch.
    const message = e.name === 'TimeoutError' || e.name === 'AbortError'
      ? `Request timed out after ${timeout}ms`
      : (e.message || 'Network error');
    throw new ApiError(message, null, 0);
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(data.error || data.message || res.statusText, data, res.status);
  }
  return data;
}

export const apiGet = (path) => request(path, { method: 'GET' });
export const apiPost = (path, body) => request(path, { method: 'POST', body });

// Optional convenience for the common "fire a command, toast on failure" case.
// Returns the result on success (and toasts `success` if provided), or null on
// failure (toasting the error). Use the raw apiPost+try/catch when a call site
// needs to also update local UI state or log to a panel.
export async function apiPostToast(path, body, { success } = {}) {
  try {
    const result = await apiPost(path, body);
    if (success) toast.success(typeof success === 'function' ? success(result) : success);
    return result;
  } catch (e) {
    toast.error(e.message);
    return null;
  }
}
