<script>
  import { onMount, onDestroy } from 'svelte';
  import RelayControlCard from '$lib/components/hardware/relay-control-card.svelte';
  import PumpControlCard from '$lib/components/hardware/pump-control-card.svelte';
  import FlowMeterCard from '$lib/components/hardware/flow-meter-card.svelte';
  import ECPHMonitorCard from '$lib/components/hardware/ecph-monitor-card.svelte';
  import SystemLogCard from '$lib/components/hardware/system-log-card.svelte';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';

  // Get reactive system status from SSE store
  const sseStatus = getSystemStatus();

  // State variables using Svelte 5 runes
  let logs = $state([]);
  let errorMessage = $state('');

  // Derive system status from SSE connection
  let systemStatus = $derived(sseStatus.isConnected ? 'Connected' : 'Disconnected');

  // Hardware data with defaults to show all hardware
  let relays = $state([
    { id: 1, name: 'Relay 1', status: 'off' },
    { id: 2, name: 'Relay 2', status: 'off' },
    { id: 3, name: 'Relay 3', status: 'off' },
    { id: 4, name: 'Relay 4', status: 'off' },
    { id: 5, name: 'Relay 5', status: 'off' },
    { id: 6, name: 'Relay 6', status: 'off' },
    { id: 7, name: 'Relay 7', status: 'off' },
    { id: 8, name: 'Relay 8', status: 'off' },
    { id: 9, name: 'Relay 9', status: 'off' },
    { id: 10, name: 'Relay 10', status: 'off' },
    { id: 11, name: 'Relay 11', status: 'off' },
    { id: 12, name: 'Relay 12', status: 'off' },
    { id: 13, name: 'Relay 13', status: 'off' }
  ]);
  let pumps = $state([
    { id: 1, name: 'Pump 1', status: 'idle' },
    { id: 2, name: 'Pump 2', status: 'idle' },
    { id: 3, name: 'Pump 3', status: 'idle' },
    { id: 4, name: 'Pump 4', status: 'idle' },
    { id: 5, name: 'Pump 5', status: 'idle' },
    { id: 6, name: 'Pump 6', status: 'idle' },
    { id: 7, name: 'Pump 7', status: 'idle' },
    { id: 8, name: 'Pump 8', status: 'idle' }
  ]);
  let flowMeters = $state([
    { id: 1, name: 'Flow Meter 1', status: 'idle', flow_rate: 0, total_gallons: 0 },
    { id: 2, name: 'Flow Meter 2', status: 'idle', flow_rate: 0, total_gallons: 0 }
  ]);
  let ecPhMonitoring = $state(false);
  let ecValue = $state(0);
  let phValue = $state(0);

  // Form inputs
  let selectedPump = $state("");
  let pumpAmount = $state(10);
  let selectedFlowMeter = $state("");
  let flowGallons = $state(1);

  // Progress tracking for log messages
  let lastProgressReported = $state(new Map()); // pump_id -> last_percentage

  // SSE unsubscribe function
  let unsubscribe = null;

  // React to SSE status updates using $effect
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) return;

    // Update error message from SSE
    errorMessage = sseStatus.lastError;

    // Update EC/pH values
    ecValue = data.ec_value || 0;
    phValue = data.ph_value || 0;
    ecPhMonitoring = data.ec_ph_monitoring || false;

    // Update relays from SSE data
    if (data.relays && data.relays.length > 0) {
      relays = data.relays.map(relay => ({
        ...relay,
        status: relay.state ? 'on' : 'off'
      }));
    }

    // Update flow meters from SSE data
    if (data.flow_meters && data.flow_meters.length > 0) {
      flowMeters = data.flow_meters.map(flowMeter => ({
        ...flowMeter,
        status: flowMeter.status === 'running' ? 'flowing' : 'idle'
      }));
    }

    // Update pumps with progress tracking
    if (data.pumps && data.pumps.length > 0) {
      pumps = pumps.map(pump => {
        const statusInfo = data.pumps.find(p => p.id === pump.id);
        if (statusInfo) {
          // Add progress log message for dispensing pumps (every 10% progress)
          if (statusInfo.is_dispensing && statusInfo.current_volume > 0 && statusInfo.target_volume > 0) {
            const currentPercent = Math.floor((statusInfo.current_volume / statusInfo.target_volume) * 100 / 10) * 10;
            const lastPercent = lastProgressReported.get(pump.id) || -10;

            if (currentPercent > lastPercent && currentPercent >= 10) {
              const progressMsg = `Pump ${pump.id} (${statusInfo.name}): ${statusInfo.current_volume.toFixed(1)}ml / ${statusInfo.target_volume.toFixed(1)}ml (${currentPercent}% complete)`;
              addLog(progressMsg);
              lastProgressReported.set(pump.id, currentPercent);
            }
          }

          // Check if pump just finished dispensing
          if (!statusInfo.is_dispensing && pump.is_dispensing) {
            const completionMsg = `Pump ${pump.id} (${statusInfo.name}) completed dispensing: ${statusInfo.current_volume?.toFixed(1) || 0}ml dispensed`;
            addLog(completionMsg);
            lastProgressReported.delete(pump.id);
          }

          return {
            ...pump,
            name: statusInfo.name || pump.name,
            status: statusInfo.is_dispensing ? 'dispensing' : 'idle',
            voltage: statusInfo.voltage || 0,
            is_dispensing: statusInfo.is_dispensing || false,
            current_volume: statusInfo.current_volume || 0,
            target_volume: statusInfo.target_volume || 0
          };
        }
        return pump;
      });
    }
  });

  async function controlRelay(relayId, action) {
    // Handle ALL OFF special case
    if (relayId === 0 && action === 'off') {
      await allRelaysOff();
      return;
    }

    try {
      const response = await fetch(`/api/relay/${relayId}/${action}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || `Relay ${relayId} ${action.toUpperCase()}`;
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);

        // Update local state for responsive UI
        relays = relays.map(relay =>
          relay.id === relayId ? { ...relay, status: action } : relay
        );
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error controlling relay:', error);
      addLog(`Error controlling relay: ${error.message}`);
    }
  }

  async function allRelaysOff() {
    try {
      const response = await fetch('/api/relay/all/off', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || 'All relays turned off';
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);

        // Update local state to turn all relays off
        relays = relays.map(relay => ({ ...relay, status: 'off' }));
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error turning off all relays:', error);
      addLog(`Error turning off all relays: ${error.message}`);
    }
  }

  async function dispensePump(pumpId, amount) {
    if (!pumpId || !amount) {
      addLog('Please select a pump and amount');
      return;
    }

    try {
      const response = await fetch(`/api/pump/${pumpId}/dispense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount })
      });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || `Dispensing ${amount}ml from pump ${pumpId}`;
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);

        // Reset progress tracking for this pump
        lastProgressReported.set(parseInt(pumpId), -10);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error dispensing pump:', error);
      addLog(`Error dispensing pump: ${error.message}`);
    }
  }

  async function stopPump(pumpId) {
    if (!pumpId) {
      addLog('Please select a pump');
      return;
    }

    try {
      const response = await fetch(`/api/pump/${pumpId}/stop`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || `Stopped pump ${pumpId}`;
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error stopping pump:', error);
      addLog(`Error stopping pump: ${error.message}`);
    }
  }

  async function startFlow(flowMeterId, gallons) {
    if (!flowMeterId || !gallons) {
      addLog('Please select a flow meter and gallons');
      return;
    }

    try {
      const response = await fetch(`/api/flow/${flowMeterId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gallons: gallons })
      });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || `Started flow meter ${flowMeterId} for ${gallons} gallons`;
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error starting flow meter:', error);
      addLog(`Error starting flow meter: ${error.message}`);
    }
  }

  async function stopFlow(flowMeterId) {
    if (!flowMeterId) {
      addLog('Please select a flow meter');
      return;
    }

    try {
      const response = await fetch(`/api/flow/${flowMeterId}/stop`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || `Stopped flow meter ${flowMeterId}`;
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error stopping flow meter:', error);
      addLog(`Error stopping flow meter: ${error.message}`);
    }
  }

  async function startEcPhMonitoring() {
    try {
      const response = await fetch('/api/ecph/start', { method: 'POST' });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || 'Started EC/pH monitoring';
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);
        ecPhMonitoring = true;
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error starting EC/pH monitoring:', error);
      addLog(`Error starting EC/pH monitoring: ${error.message}`);
    }
  }

  async function stopEcPhMonitoring() {
    try {
      const response = await fetch('/api/ecph/stop', { method: 'POST' });

      if (response.ok) {
        const result = await response.json();
        const userMessage = result.message || 'Stopped EC/pH monitoring';
        const rawMessage = `Raw: ${JSON.stringify(result)}`;

        addLog(userMessage);
        addLog(rawMessage);
        ecPhMonitoring = false;
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
      }
    } catch (error) {
      console.error('Error stopping EC/pH monitoring:', error);
      addLog(`Error stopping EC/pH monitoring: ${error.message}`);
    }
  }

  function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    logs = [{ time: timestamp, message }, ...logs].slice(0, 100); // Keep last 100 logs
  }

  function clearLogs() {
    logs = [];
  }

  onMount(async () => {
    addLog('System starting...');

    // Subscribe to SSE updates
    unsubscribe = subscribe();

    // Set default selections after a short delay to allow SSE data to arrive
    setTimeout(() => {
      if (pumps.length > 0 && !selectedPump) selectedPump = pumps[0].id;
      if (flowMeters.length > 0 && !selectedFlowMeter) selectedFlowMeter = flowMeters[0].id;
    }, 500);
  });

  onDestroy(() => {
    // Unsubscribe from SSE when component unmounts
    if (unsubscribe) {
      unsubscribe();
    }
  });
</script>

<div class="dashboard">
  <!-- Status Banner -->
  <div class="status-banner">
    <div class="status-left">
      <div class="connection-status">
        <div class="status-indicator status-{systemStatus.toLowerCase()}"></div>
        <span class="status-text">{systemStatus}</span>
      </div>
      {#if ecPhMonitoring}
        <div class="quick-metrics">
          EC: {ecValue.toFixed(2)} | pH: {phValue.toFixed(2)}
        </div>
      {/if}
    </div>
    {#if errorMessage}
      <span class="error-message">{errorMessage}</span>
    {/if}
  </div>

  <!-- Hardware Control Cards - Grid Layout -->
  <div class="cards-container">
    <!-- Left Column - Hardware Controls -->
    <div class="controls-column">
      <RelayControlCard {relays} onRelayControl={controlRelay} />

      <PumpControlCard
        {pumps}
        bind:selectedPump
        bind:pumpAmount
        onDispensePump={dispensePump}
        onStopPump={stopPump}
      />
    </div>

    <!-- Middle Column - Sensors -->
    <div class="sensors-column">
      <FlowMeterCard
        flowMeters={flowMeters}
        bind:selectedFlowMeter
        bind:flowGallons
        onStartFlow={startFlow}
        onStopFlow={stopFlow}
      />

      <ECPHMonitorCard
        {ecValue}
        {phValue}
        {ecPhMonitoring}
        onStartMonitoring={startEcPhMonitoring}
        onStopMonitoring={stopEcPhMonitoring}
      />
    </div>

    <!-- Right Column - System Log -->
    <div class="log-column">
      <SystemLogCard {logs} onClearLogs={clearLogs} />
    </div>
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;

    --accent-steel: #64748b;

    --status-success: #059669;
    --status-error: #dc2626;

    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;

    --border-subtle: #334155;

    --space-sm: 0.5rem;
    --space-md: 0.75rem;

    --text-xs: 0.6875rem;
    --text-sm: 0.8125rem;
  }

  :global(body) {
    background: var(--bg-primary);
    color: var(--text-primary);
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
    max-width: 100%;
    margin: 0 auto;
  }

  .status-banner {
    position: sticky;
    top: 0;
    z-index: 10;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--border-subtle);
    padding: var(--space-sm) var(--space-md) var(--space-md);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .status-left {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .status-indicator {
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 50%;
  }

  .status-indicator.status-connected {
    background: var(--status-success);
  }

  .status-indicator.status-disconnected {
    background: var(--status-error);
  }

  .status-text {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-primary);
  }

  .quick-metrics {
    font-size: var(--text-xs);
    color: var(--text-muted);
    padding: 0.25rem 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
  }

  .error-message {
    font-size: var(--text-xs);
    color: var(--status-error);
  }

  .cards-container {
    display: grid;
    grid-template-columns: 1fr 1fr 320px;
    gap: var(--space-md);
    padding: 0 var(--space-md) var(--space-md);
    max-width: 100%;
    margin: 0 auto;
  }

  .controls-column,
  .sensors-column {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .log-column {
    display: flex;
    flex-direction: column;
    position: sticky;
    top: 4rem;
    height: calc(100vh - 5rem);
    align-self: start;
  }

  /* Responsive Design for Tablet */
  @media (max-width: 1400px) {
    .cards-container {
      grid-template-columns: 1fr 1fr 300px;
    }
  }

  @media (max-width: 1200px) {
    .cards-container {
      grid-template-columns: 1fr 1fr 280px;
      gap: var(--space-sm);
    }
  }

  @media (max-width: 768px) {
    .cards-container {
      grid-template-columns: 1fr;
      gap: var(--space-md);
    }

    .log-column {
      position: relative;
      height: auto;
      top: 0;
    }
  }
</style>
