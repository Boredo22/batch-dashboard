/**
 * WebSocket connection manager for real-time hardware status updates
 * Uses Socket.IO client to connect to Flask-SocketIO backend
 *
 * Features:
 * - Infinite reconnection with exponential backoff
 * - Automatic polling fallback when WebSocket is unavailable
 * - Connection health monitoring
 */
import { io } from 'socket.io-client';

// Reactive state for connection status
let socket = null;
let connectionStatus = 'disconnected';
let statusListeners = [];
let connectionListeners = [];

// Polling fallback state
let pollingInterval = null;
let pollingFetchInProgress = false;
const POLLING_INTERVAL_MS = 2000;

/**
 * Get the WebSocket server URL based on environment
 */
function getSocketUrl() {
  // In development, Vite proxies to localhost:5000
  // In production, connect to same host
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // In dev mode (Vite), connect directly to Flask backend
    if (window.location.port === '5173') {
      return 'http://localhost:5000';
    }
    // In production, same origin
    return `${window.location.protocol}//${host}:5000`;
  }
  return 'http://localhost:5000';
}

/**
 * Initialize WebSocket connection with infinite reconnection
 * @returns {Socket} Socket.IO client instance
 */
export function initWebSocket() {
  if (socket && socket.connected) {
    console.log('[WebSocket] Already connected');
    return socket;
  }

  const url = getSocketUrl();
  console.log('[WebSocket] Connecting to:', url);

  socket = io(url, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: Infinity,  // Never give up reconnecting
    reconnectionDelay: 1000,
    reconnectionDelayMax: 30000,     // Cap at 30 seconds between attempts
    randomizationFactor: 0.5,        // Add jitter to prevent thundering herd
    timeout: 20000
  });

  // Connection events
  socket.on('connect', () => {
    console.log('[WebSocket] Connected, sid:', socket.id);
    connectionStatus = 'connected';
    notifyConnectionListeners(connectionStatus);

    // Stop polling fallback when WebSocket connects
    stopPollingFallback();

    // Subscribe to status updates
    socket.emit('subscribe_status');
  });

  socket.on('disconnect', (reason) => {
    console.log('[WebSocket] Disconnected:', reason);
    connectionStatus = 'disconnected';
    notifyConnectionListeners(connectionStatus);

    // Start polling fallback when WebSocket disconnects
    startPollingFallback();
  });

  socket.on('connect_error', (error) => {
    console.error('[WebSocket] Connection error:', error.message);
    connectionStatus = 'error';
    notifyConnectionListeners(connectionStatus);

    // Ensure polling fallback is running on connection errors
    startPollingFallback();
  });

  socket.on('reconnecting', (attemptNumber) => {
    console.log('[WebSocket] Reconnecting, attempt:', attemptNumber);
    connectionStatus = 'reconnecting';
    notifyConnectionListeners(connectionStatus);
  });

  socket.on('reconnect', (attemptNumber) => {
    console.log('[WebSocket] Reconnected after', attemptNumber, 'attempts');
    connectionStatus = 'connected';
    notifyConnectionListeners(connectionStatus);

    // Stop polling fallback on successful reconnection
    stopPollingFallback();

    socket.emit('subscribe_status');
  });

  // Handle case where reconnection gives up (shouldn't happen with Infinity, but safety)
  socket.on('reconnect_failed', () => {
    console.warn('[WebSocket] Reconnection failed, attempting manual reconnect in 5s...');
    connectionStatus = 'error';
    notifyConnectionListeners(connectionStatus);

    // Manual reconnect attempt after delay
    setTimeout(() => {
      if (!socket.connected) {
        console.log('[WebSocket] Manual reconnection attempt...');
        socket.connect();
      }
    }, 5000);
  });

  // Server events
  socket.on('connected', (data) => {
    console.log('[WebSocket] Server confirmed connection:', data.message);
  });

  socket.on('subscribed', (data) => {
    console.log('[WebSocket] Subscribed to:', data.channel);
  });

  socket.on('status_update', (data) => {
    notifyStatusListeners(data);
  });

  socket.on('error', (data) => {
    console.error('[WebSocket] Server error:', data.message);
  });

  return socket;
}

/**
 * Start HTTP polling fallback when WebSocket is unavailable
 */
function startPollingFallback() {
  if (pollingInterval) {
    return; // Already polling
  }

  console.log('[WebSocket] Starting HTTP polling fallback');

  pollingInterval = setInterval(async () => {
    // Prevent overlapping requests
    if (pollingFetchInProgress) {
      return;
    }

    pollingFetchInProgress = true;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch('/api/system/status', {
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        notifyStatusListeners(data);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.warn('[WebSocket] Polling request timed out');
      } else {
        console.error('[WebSocket] Polling error:', error.message);
      }
    } finally {
      pollingFetchInProgress = false;
    }
  }, POLLING_INTERVAL_MS);
}

/**
 * Stop HTTP polling fallback
 */
function stopPollingFallback() {
  if (pollingInterval) {
    console.log('[WebSocket] Stopping HTTP polling fallback');
    clearInterval(pollingInterval);
    pollingInterval = null;
    pollingFetchInProgress = false;
  }
}

/**
 * Disconnect WebSocket and clean up all resources
 */
export function disconnectWebSocket() {
  // Stop polling fallback
  stopPollingFallback();

  if (socket) {
    console.log('[WebSocket] Disconnecting...');
    socket.disconnect();
    socket = null;
    connectionStatus = 'disconnected';
    notifyConnectionListeners(connectionStatus);
  }
}

/**
 * Get current connection status
 * @returns {string} 'connected', 'disconnected', 'reconnecting', or 'error'
 */
export function getConnectionStatus() {
  return connectionStatus;
}

/**
 * Check if WebSocket is connected
 * @returns {boolean}
 */
export function isConnected() {
  return socket && socket.connected;
}

/**
 * Request immediate status update from server
 */
export function requestStatusUpdate() {
  if (socket && socket.connected) {
    socket.emit('request_status');
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
      console.error('[WebSocket] Error in status listener:', e);
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
      console.error('[WebSocket] Error in connection listener:', e);
    }
  });
}

/**
 * Get the socket instance (for advanced usage)
 * @returns {Socket|null}
 */
export function getSocket() {
  return socket;
}
