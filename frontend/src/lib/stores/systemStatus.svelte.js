/**
 * System Status Store using Server-Sent Events (SSE)
 *
 * This store manages a single SSE connection that all components share,
 * eliminating redundant polling requests.
 *
 * Features:
 * - Single SSE connection shared across all components
 * - Automatic reconnection on disconnect
 * - Fallback to polling if SSE fails
 * - Svelte 5 runes for reactive state
 */

// Connection state
let eventSource = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY_MS = 3000;
const FALLBACK_POLL_INTERVAL_MS = 2000;

// Fallback polling interval reference
let fallbackInterval = null;

// Reactive state using Svelte 5 runes
let connectionStatus = $state('disconnected'); // 'connected', 'connecting', 'disconnected', 'error'
let lastError = $state('');
let usingFallback = $state(false);

// System status data - mirrors the structure from /api/system/status
let systemData = $state({
  success: false,
  status: {},
  hardware: {},
  timestamp: '',
  relays: [],
  pumps: [],
  flow_meters: [],
  ec_value: 0,
  ph_value: 0,
  ec_ph_monitoring: false
});

// Subscriber count to manage connection lifecycle
let subscriberCount = 0;

/**
 * Initialize SSE connection
 */
function connect() {
  if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
    return; // Already connected or connecting
  }

  connectionStatus = 'connecting';
  lastError = '';

  try {
    eventSource = new EventSource('/api/system/status/stream');

    eventSource.onopen = () => {
      connectionStatus = 'connected';
      reconnectAttempts = 0;
      usingFallback = false;

      // Clear fallback polling if it was active
      if (fallbackInterval) {
        clearInterval(fallbackInterval);
        fallbackInterval = null;
      }

      console.log('[SSE] Connected to status stream');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        systemData = data;

        if (!data.success) {
          lastError = data.error || 'Unknown error';
        } else {
          lastError = '';
        }
      } catch (e) {
        console.error('[SSE] Error parsing message:', e);
        lastError = 'Failed to parse status data';
      }
    };

    eventSource.onerror = (error) => {
      console.error('[SSE] Connection error:', error);
      connectionStatus = 'error';
      lastError = 'Connection lost';

      // Close the current connection
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }

      // Attempt reconnection
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && subscriberCount > 0) {
        reconnectAttempts++;
        console.log(`[SSE] Reconnecting... Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);

        setTimeout(() => {
          if (subscriberCount > 0) {
            connect();
          }
        }, RECONNECT_DELAY_MS);
      } else if (subscriberCount > 0) {
        // Fall back to polling
        console.log('[SSE] Max reconnection attempts reached, falling back to polling');
        startFallbackPolling();
      }
    };

  } catch (e) {
    console.error('[SSE] Failed to create EventSource:', e);
    connectionStatus = 'error';
    lastError = e.message;
    startFallbackPolling();
  }
}

/**
 * Disconnect SSE connection
 */
function disconnect() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }

  if (fallbackInterval) {
    clearInterval(fallbackInterval);
    fallbackInterval = null;
  }

  connectionStatus = 'disconnected';
  console.log('[SSE] Disconnected');
}

/**
 * Start fallback polling when SSE is unavailable
 */
function startFallbackPolling() {
  if (fallbackInterval) return; // Already polling

  usingFallback = true;
  connectionStatus = 'connected'; // Still "connected" via polling
  console.log('[SSE] Starting fallback polling');

  // Initial fetch
  fetchStatus();

  // Set up interval
  fallbackInterval = setInterval(fetchStatus, FALLBACK_POLL_INTERVAL_MS);
}

/**
 * Fetch status via REST API (fallback)
 */
async function fetchStatus() {
  try {
    const response = await fetch('/api/system/status');
    if (response.ok) {
      const data = await response.json();
      systemData = data;
      lastError = '';
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (e) {
    console.error('[SSE Fallback] Fetch error:', e);
    lastError = e.message;
  }
}

/**
 * Subscribe to status updates
 * Call this when a component mounts to ensure connection is active
 * Returns an unsubscribe function to call on unmount
 */
export function subscribe() {
  subscriberCount++;

  // Connect if this is the first subscriber
  if (subscriberCount === 1) {
    connect();
  }

  // Return unsubscribe function
  return () => {
    subscriberCount--;

    // Disconnect if no more subscribers
    if (subscriberCount === 0) {
      disconnect();
    }
  };
}

/**
 * Force reconnect (useful after network recovery)
 */
export function reconnect() {
  reconnectAttempts = 0;
  disconnect();
  if (subscriberCount > 0) {
    connect();
  }
}

/**
 * Get reactive references to the store state
 * Use these in components with $derived or direct access
 */
export function getSystemStatus() {
  return {
    get data() { return systemData; },
    get connectionStatus() { return connectionStatus; },
    get lastError() { return lastError; },
    get usingFallback() { return usingFallback; },

    // Convenience accessors for common data
    get relays() { return systemData.relays || []; },
    get pumps() { return systemData.pumps || []; },
    get flowMeters() { return systemData.flow_meters || []; },
    get ecValue() { return systemData.ec_value || 0; },
    get phValue() { return systemData.ph_value || 0; },
    get ecPhMonitoring() { return systemData.ec_ph_monitoring || false; },
    get timestamp() { return systemData.timestamp || ''; },
    get hardware() { return systemData.hardware || {}; },
    get isConnected() { return connectionStatus === 'connected'; }
  };
}
