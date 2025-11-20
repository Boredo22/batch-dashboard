/**
 * Frontend configuration
 * Uses environment variables for flexible deployment
 */

// API Base URL - configured via environment variable
// Defaults to localhost:5000 if not set
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Log the configured API URL in development
if (import.meta.env.DEV) {
  console.log('[Config] API Base URL:', API_BASE_URL);
}
