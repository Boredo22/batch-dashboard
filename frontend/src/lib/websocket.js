/**
 * HTTP Polling manager for hardware status updates
 * Simplified version - no WebSocket, just REST API polling
 */

// Reactive state for connection status
let connectionStatus = 'disconnected';
let statusListeners = [];
let connectionListeners = [];
let pollingInterval = null;
let isPolling = false;

// Configure your Pi's IP here
const PI_ADDRESS = '192.168.1.243';

/**
 * Get the API base URL - exported for use by other modules
 */
export function getApiUrl() {
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    // Dev mode - direct to Pi (bypass slow Vite proxy)
    return `http://${PI_ADDRESS}:5000`;
  }
  // Production - same origin
  return '';
}

/**
 * Fetch status from the API
 */
async function fetchStatus() {
  try {
    const url = `${getApiUrl()}/api/status`;
    const response = await fetch(url);

    if (response.ok) {
      const data = await response.json();

      if (connectionStatus !== 'connected') {
        connectionStatus = 'connected';
        notifyConnectionListeners(connectionStatus);
      }

      notifyStatusListeners(data);
      return data;
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('[Polling] Error fetching status:', error.message);

    if (connectionStatus !== 'error') {
      connectionStatus = 'error';
      notifyConnectionListeners(connectionStatus);
    }

    return null;
  }
}

/**
 * Initialize polling (replaces WebSocket)
 * @param {number} intervalMs - Polling interval in milliseconds (default 2000)
 * @returns {Object} Polling controller
 */
export function initWebSocket(intervalMs = 2000) {
  if (isPolling) {
    console.log('[Polling] Already polling');
    return;
  }

  console.log('[Polling] Starting HTTP polling mode (no WebSocket)');
  isPolling = true;
  connectionStatus = 'connecting';
  notifyConnectionListeners(connectionStatus);

  // Initial fetch
  fetchStatus();

  // Start polling interval
  pollingInterval = setInterval(fetchStatus, intervalMs);

  return {
    stop: () => disconnectWebSocket()
  };
}

/**
 * Stop polling
 */
export function disconnectWebSocket() {
  if (pollingInterval) {
    console.log('[Polling] Stopping...');
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
  isPolling = false;
  connectionStatus = 'disconnected';
  notifyConnectionListeners(connectionStatus);
}

/**
 * Get current connection status
 * @returns {string} 'connected', 'disconnected', 'connecting', or 'error'
 */
export function getConnectionStatus() {
  return connectionStatus;
}

/**
 * Check if polling is active and connected
 * @returns {boolean}
 */
export function isConnected() {
  return isPolling && connectionStatus === 'connected';
}

/**
 * Request immediate status update
 */
export function requestStatusUpdate() {
  if (isPolling) {
    fetchStatus();
  }
}

/**
 * Subscribe to status updates
 * @param {Function} callback - Called with status data on each update
 * @returns {Function} Unsubscribe function
 */
export function onStatusUpdate(callback) {
  statusListeners.push(callback);

  // Return unsubscribe function
  return () => {
    statusListeners = statusListeners.filter(cb => cb !== callback);
  };
}

/**
 * Subscribe to connection status changes
 * @param {Function} callback - Called with status string on each change
 * @returns {Function} Unsubscribe function
 */
export function onConnectionChange(callback) {
  connectionListeners.push(callback);

  // Immediately notify with current status
  callback(connectionStatus);

  // Return unsubscribe function
  return () => {
    connectionListeners = connectionListeners.filter(cb => cb !== callback);
  };
}

/**
 * Notify all status listeners
 * @param {Object} data - Status update data
 */
function notifyStatusListeners(data) {
  statusListeners.forEach(callback => {
    try {
      callback(data);
    } catch (e) {
      console.error('[Polling] Error in status listener:', e);
    }
  });
}

/**
 * Notify all connection listeners
 * @param {string} status - Connection status
 */
function notifyConnectionListeners(status) {
  connectionListeners.forEach(callback => {
    try {
      callback(status);
    } catch (e) {
      console.error('[Polling] Error in connection listener:', e);
    }
  });
}

/**
 * Get the socket instance - returns null (no WebSocket)
 * @returns {null}
 */
export function getSocket() {
  return null;
}
