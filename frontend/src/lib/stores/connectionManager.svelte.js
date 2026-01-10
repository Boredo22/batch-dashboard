/**
 * Connection Manager for Hardware Control System
 *
 * Unified connection management with:
 * - WebSocket as primary transport (infinite reconnection)
 * - HTTP polling as fallback when WebSocket fails
 * - Automatic switching between transports
 * - Connection health monitoring
 */

import { io } from 'socket.io-client';
import { updateFromBackend, setConnectionStatus } from './systemStore.svelte.js';

// ============================================================================
// STATE
// ============================================================================

let socket = null;
let pollingInterval = null;
let pollingFetchInProgress = false;
let initialized = false;

// Configuration
const POLLING_INTERVAL_MS = 2000;
const FETCH_TIMEOUT_MS = 5000;

// ============================================================================
// URL HELPERS
// ============================================================================

/**
 * Get the WebSocket server URL based on environment
 */
function getSocketUrl() {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    // In dev mode (Vite), connect directly to Flask backend
    if (window.location.port === '5173') {
      return 'http://localhost:5000';
    }
    // In production, same origin on port 5000
    return `${window.location.protocol}//${host}:5000`;
  }
  return 'http://localhost:5000';
}

// ============================================================================
// WEBSOCKET CONNECTION
// ============================================================================

/**
 * Initialize WebSocket connection with infinite reconnection
 */
function initWebSocket() {
  if (socket && socket.connected) {
    console.log('[ConnectionManager] WebSocket already connected');
    return socket;
  }

  const url = getSocketUrl();
  console.log('[ConnectionManager] Connecting WebSocket to:', url);

  socket = io(url, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: Infinity,  // Never give up
    reconnectionDelay: 1000,
    reconnectionDelayMax: 30000,     // Cap at 30 seconds
    randomizationFactor: 0.5,
    timeout: 20000
  });

  // Connection established
  socket.on('connect', () => {
    console.log('[ConnectionManager] WebSocket connected');
    setConnectionStatus('connected', { wsConnected: true });

    // Stop polling when WebSocket connects
    stopPolling();

    // Subscribe to status updates
    socket.emit('subscribe_status');
  });

  // Connection lost
  socket.on('disconnect', (reason) => {
    console.log('[ConnectionManager] WebSocket disconnected:', reason);
    setConnectionStatus('disconnected', { wsConnected: false });

    // Start polling fallback
    startPolling();
  });

  // Connection error
  socket.on('connect_error', (error) => {
    console.error('[ConnectionManager] WebSocket error:', error.message);
    setConnectionStatus('error', { wsConnected: false });

    // Ensure polling is running
    startPolling();
  });

  // Reconnecting
  socket.on('reconnecting', (attemptNumber) => {
    console.log('[ConnectionManager] Reconnecting, attempt:', attemptNumber);
    setConnectionStatus('reconnecting', { wsConnected: false });
  });

  // Reconnected
  socket.on('reconnect', (attemptNumber) => {
    console.log('[ConnectionManager] Reconnected after', attemptNumber, 'attempts');
    setConnectionStatus('connected', { wsConnected: true });

    // Stop polling on successful reconnection
    stopPolling();

    socket.emit('subscribe_status');
  });

  // Status update from server
  socket.on('status_update', (data) => {
    updateFromBackend(data);
  });

  // Server confirmed subscription
  socket.on('subscribed', (data) => {
    console.log('[ConnectionManager] Subscribed to:', data.channel);
  });

  return socket;
}

// ============================================================================
// HTTP POLLING FALLBACK
// ============================================================================

/**
 * Start HTTP polling fallback
 */
function startPolling() {
  if (pollingInterval) {
    return; // Already polling
  }

  console.log('[ConnectionManager] Starting HTTP polling fallback');
  setConnectionStatus(undefined, { pollingActive: true });

  pollingInterval = setInterval(async () => {
    await pollStatus();
  }, POLLING_INTERVAL_MS);

  // Immediate first poll
  pollStatus();
}

/**
 * Stop HTTP polling
 */
function stopPolling() {
  if (pollingInterval) {
    console.log('[ConnectionManager] Stopping HTTP polling');
    clearInterval(pollingInterval);
    pollingInterval = null;
    pollingFetchInProgress = false;
    setConnectionStatus(undefined, { pollingActive: false });
  }
}

/**
 * Perform a single poll request
 */
async function pollStatus() {
  // Prevent overlapping requests
  if (pollingFetchInProgress) {
    return;
  }

  pollingFetchInProgress = true;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch('/api/system/status', {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      updateFromBackend(data);

      // If we got data, we're at least partially connected
      setConnectionStatus('connected', { pollingActive: true });
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      console.warn('[ConnectionManager] Poll request timed out');
    } else {
      console.error('[ConnectionManager] Poll error:', error.message);
    }
  } finally {
    pollingFetchInProgress = false;
  }
}

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * Initialize the connection manager.
 * Call this once on app startup.
 */
export function initConnection() {
  if (initialized) {
    console.log('[ConnectionManager] Already initialized');
    return;
  }

  initialized = true;
  console.log('[ConnectionManager] Initializing...');

  // Start with WebSocket
  initWebSocket();

  // Also start polling initially until WebSocket connects
  startPolling();
}

/**
 * Disconnect and clean up all connections
 */
export function disconnect() {
  console.log('[ConnectionManager] Disconnecting...');

  stopPolling();

  if (socket) {
    socket.disconnect();
    socket = null;
  }

  initialized = false;
  setConnectionStatus('disconnected', { wsConnected: false, pollingActive: false });
}

/**
 * Force a status refresh
 */
export async function refreshStatus() {
  if (socket && socket.connected) {
    socket.emit('request_status');
  } else {
    await pollStatus();
  }
}

/**
 * Check if WebSocket is connected
 */
export function isWebSocketConnected() {
  return socket && socket.connected;
}

/**
 * Get the socket instance for direct access (advanced usage)
 */
export function getSocket() {
  return socket;
}
