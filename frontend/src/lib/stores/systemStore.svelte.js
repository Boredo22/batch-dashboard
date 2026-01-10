/**
 * Centralized System State Store using Svelte 5 Runes
 *
 * Provides a single source of truth for all hardware state:
 * - Relay states
 * - Pump states and progress
 * - Flow meter states
 * - EC/pH sensor values
 * - Connection status
 *
 * Features:
 * - Optimistic updates with rollback on failure
 * - State synchronization from backend
 * - Derived values for active component counts
 */

// ============================================================================
// RELAY STATE
// ============================================================================

// Relay states: Map of relay_id -> { id, name, status }
let relayStates = $state({});

// Pending optimistic updates for rollback
let pendingRelayUpdates = $state(new Map());

/**
 * Get all relay states as an array
 */
export function getRelays() {
  return Object.values(relayStates).sort((a, b) => a.id - b.id);
}

/**
 * Get a specific relay state
 */
export function getRelay(id) {
  return relayStates[id] ?? { id, name: `Relay ${id}`, status: 'off' };
}

/**
 * Update relay state optimistically (before API call completes)
 * Stores the original state for rollback if API fails.
 */
export function setRelayOptimistic(id, newStatus) {
  const original = relayStates[id] ? { ...relayStates[id] } : null;
  pendingRelayUpdates.set(id, { original, timestamp: Date.now() });

  relayStates[id] = {
    ...relayStates[id],
    id,
    status: newStatus
  };
}

/**
 * Confirm relay state after successful API call
 */
export function confirmRelayState(id, confirmedState) {
  pendingRelayUpdates.delete(id);
  relayStates[id] = {
    ...relayStates[id],
    ...confirmedState,
    id
  };
}

/**
 * Rollback relay state after failed API call
 */
export function rollbackRelayState(id) {
  const pending = pendingRelayUpdates.get(id);
  if (pending && pending.original) {
    relayStates[id] = pending.original;
  }
  pendingRelayUpdates.delete(id);
}

/**
 * Get count of active relays
 */
export function getActiveRelayCount() {
  return Object.values(relayStates).filter(r => r.status === 'on').length;
}

// ============================================================================
// PUMP STATE
// ============================================================================

// Pump states: Map of pump_id -> { id, name, status, is_dispensing, current_volume, target_volume, voltage }
let pumpStates = $state({});

/**
 * Get all pump states as an array
 */
export function getPumps() {
  return Object.values(pumpStates).sort((a, b) => a.id - b.id);
}

/**
 * Get a specific pump state
 */
export function getPump(id) {
  return pumpStates[id] ?? { id, name: `Pump ${id}`, status: 'idle', is_dispensing: false };
}

/**
 * Get count of active (dispensing) pumps
 */
export function getActivePumpCount() {
  return Object.values(pumpStates).filter(p => p.is_dispensing || p.status === 'dispensing').length;
}

// ============================================================================
// FLOW METER STATE
// ============================================================================

// Flow meter states: Map of meter_id -> { id, name, status, flow_rate, total_gallons }
let flowMeterStates = $state({});

/**
 * Get all flow meter states as an array
 */
export function getFlowMeters() {
  return Object.values(flowMeterStates).sort((a, b) => a.id - b.id);
}

/**
 * Get a specific flow meter state
 */
export function getFlowMeter(id) {
  return flowMeterStates[id] ?? { id, name: `Flow Meter ${id}`, status: 'idle', flow_rate: 0, total_gallons: 0 };
}

// ============================================================================
// EC/pH SENSOR STATE
// ============================================================================

let ecPhState = $state({
  ec: 0,
  ph: 0,
  monitoring: false,
  lastUpdate: null
});

/**
 * Get EC/pH sensor state
 */
export function getEcPhState() {
  return ecPhState;
}

// ============================================================================
// CONNECTION STATE
// ============================================================================

let connectionState = $state({
  status: 'disconnected',  // 'connected', 'disconnected', 'reconnecting', 'error'
  lastUpdate: null,
  wsConnected: false,
  pollingActive: false
});

/**
 * Get connection state
 */
export function getConnectionState() {
  return connectionState;
}

/**
 * Update connection status
 */
export function setConnectionStatus(status, options = {}) {
  connectionState = {
    ...connectionState,
    status,
    ...options,
    lastUpdate: Date.now()
  };
}

// ============================================================================
// BULK STATE UPDATES FROM BACKEND
// ============================================================================

/**
 * Update all state from backend data.
 * This is called by the connection manager when new data arrives.
 *
 * @param {Object} data - Backend status data
 */
export function updateFromBackend(data) {
  // Update relay states
  if (data.relays && Array.isArray(data.relays)) {
    for (const relay of data.relays) {
      // Only update if no pending optimistic update
      if (!pendingRelayUpdates.has(relay.id)) {
        relayStates[relay.id] = {
          id: relay.id,
          name: relay.name || `Relay ${relay.id}`,
          status: relay.state ? 'on' : 'off',
          gpio_pin: relay.gpio_pin
        };
      }
    }
  }

  // Update pump states
  if (data.pumps) {
    // Handle both array and object formats
    const pumps = Array.isArray(data.pumps) ? data.pumps : Object.entries(data.pumps).map(([id, p]) => ({ id: parseInt(id), ...p }));
    for (const pump of pumps) {
      const id = pump.id || pump.pump_id;
      if (id) {
        pumpStates[id] = {
          id,
          name: pump.name || `Pump ${id}`,
          status: pump.is_dispensing ? 'dispensing' : 'idle',
          is_dispensing: pump.is_dispensing || false,
          current_volume: pump.current_volume || 0,
          target_volume: pump.target_volume || 0,
          voltage: pump.voltage || 0,
          connected: pump.connected ?? true,
          calibrated: pump.calibrated ?? false
        };
      }
    }
  }

  // Update flow meter states
  if (data.flow_meters && Array.isArray(data.flow_meters)) {
    for (const meter of data.flow_meters) {
      flowMeterStates[meter.id] = {
        id: meter.id,
        name: meter.name || `Flow Meter ${meter.id}`,
        status: meter.status === 'running' ? 'flowing' : 'idle',
        flow_rate: meter.flow_rate || 0,
        total_gallons: meter.total_gallons || meter.current_gallons || 0,
        target_gallons: meter.target_gallons || 0
      };
    }
  }

  // Update EC/pH values
  if (data.ec_value !== undefined || data.ph_value !== undefined || data.ec !== undefined || data.ph !== undefined) {
    ecPhState = {
      ec: data.ec_value ?? data.ec ?? ecPhState.ec,
      ph: data.ph_value ?? data.ph ?? ecPhState.ph,
      monitoring: data.ec_ph_monitoring ?? data.ecph_monitoring ?? ecPhState.monitoring,
      lastUpdate: Date.now()
    };
  }

  // Update connection state
  connectionState = {
    ...connectionState,
    lastUpdate: Date.now()
  };
}

/**
 * Initialize state with default values
 * Called on app startup before first backend data arrives
 */
export function initializeDefaultState(config) {
  // Initialize relays from config
  if (config.relays) {
    for (const relay of config.relays) {
      relayStates[relay.id] = {
        id: relay.id,
        name: relay.name || `Relay ${relay.id}`,
        status: 'off'
      };
    }
  }

  // Initialize pumps from config
  if (config.pumps) {
    for (const pump of config.pumps) {
      pumpStates[pump.id] = {
        id: pump.id,
        name: pump.name || `Pump ${pump.id}`,
        status: 'idle',
        is_dispensing: false
      };
    }
  }

  // Initialize flow meters from config
  if (config.flowMeters) {
    for (const meter of config.flowMeters) {
      flowMeterStates[meter.id] = {
        id: meter.id,
        name: meter.name || `Flow Meter ${meter.id}`,
        status: 'idle',
        flow_rate: 0,
        total_gallons: 0
      };
    }
  }
}

// ============================================================================
// EXPORTS FOR REACTIVE ACCESS
// ============================================================================

// Export state objects for reactive access in components
export { relayStates, pumpStates, flowMeterStates, ecPhState, connectionState };
