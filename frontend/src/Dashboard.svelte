<script>
  import { onMount, onDestroy } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { logger } from '$lib/utils';
  import { initWebSocket, disconnectWebSocket, onStatusUpdate, onConnectionChange, isConnected } from '$lib/websocket';
  import { Card, CardContent, CardHeader } from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import RelayControlCard from '$lib/components/hardware/relay-control-card.svelte';
  import PumpControlCard from '$lib/components/hardware/pump-control-card.svelte';
  import PumpCalibrationWizard from '$lib/components/hardware/pump-calibration-wizard.svelte';
  import FlowMeterCard from '$lib/components/hardware/flow-meter-card.svelte';
  import ECPHMonitorCard from '$lib/components/hardware/ecph-monitor-card.svelte';
  import SystemLogCard from '$lib/components/hardware/system-log-card.svelte';

  // State variables using Svelte 5 runes
  let logs = $state([]);
  let systemStatus = $state('Disconnected');
  let errorMessage = $state('');

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
  let lastProgressReported = $state(new Map());

  // Collapsible section states
  let expandedSections = $state({
    relays: true,
    pumps: true,
    flow: true,
    ecph: true
  });

  // Calibration wizard state
  let showCalibrationWizard = $state(false);

  // Derived values
  let activeRelayCount = $derived(relays.filter(r => r.status === 'on').length);
  let activePumpCount = $derived(pumps.filter(p => p.status === 'dispensing').length);

  let statusInterval;
  let unsubscribeStatus;
  let unsubscribeConnection;
  let useWebSocket = $state(true); // Toggle between WebSocket and polling

  // WebSocket status handler
  function handleWebSocketStatus(data) {
    logger.debug('WebSocket', 'Received status update', data);

    // Update relays
    if (data.relays && data.relays.length > 0) {
      relays = data.relays.map(relay => ({
        ...relay,
        status: relay.state ? 'on' : 'off'
      }));
    }

    // Update pumps
    if (data.pumps && data.pumps.length > 0) {
      pumps = data.pumps.map(pump => {
        // Track dispensing progress
        if (pump.is_dispensing && pump.current_volume > 0 && pump.target_volume > 0) {
          const currentPercent = Math.floor((pump.current_volume / pump.target_volume) * 100 / 10) * 10;
          const lastPercent = lastProgressReported.get(pump.id) || -10;

          if (currentPercent > lastPercent && currentPercent >= 10) {
            const progressMsg = `Pump ${pump.id} (${pump.name}): ${pump.current_volume.toFixed(1)}ml / ${pump.target_volume.toFixed(1)}ml (${currentPercent}% complete)`;
            addLog(progressMsg);
            lastProgressReported.set(pump.id, currentPercent);
          }
        }

        // Check for completion
        const oldPump = pumps.find(p => p.id === pump.id);
        if (oldPump && oldPump.is_dispensing && !pump.is_dispensing) {
          const completionMsg = `Pump ${pump.id} (${pump.name}) completed dispensing`;
          addLog(completionMsg);
          lastProgressReported.delete(pump.id);
        }

        return {
          ...pump,
          status: pump.is_dispensing ? 'dispensing' : 'idle'
        };
      });
    }

    // Update flow meters
    if (data.flow_meters && data.flow_meters.length > 0) {
      flowMeters = data.flow_meters.map(fm => ({
        ...fm,
        status: fm.status === 'running' ? 'flowing' : 'idle'
      }));
    }

    // Update EC/pH
    ecValue = data.ec_value || 0;
    phValue = data.ph_value || 0;
    ecPhMonitoring = data.ec_ph_monitoring || false;
  }

  // Connection status handler
  function handleConnectionChange(status) {
    logger.info('WebSocket', 'Connection status changed', { status });
    if (status === 'connected') {
      systemStatus = 'Connected';
      errorMessage = '';
    } else if (status === 'reconnecting') {
      systemStatus = 'Reconnecting';
    } else if (status === 'error') {
      systemStatus = 'Error';
    } else {
      systemStatus = 'Disconnected';
    }
  }

  // API functions
  async function fetchHardwareData() {
    try {
      const response = await fetch('/api/hardware/status');
      if (response.ok) {
        const data = await response.json();
        if (data.relays && data.relays.length > 0) {
          relays = data.relays.map(relay => ({
            ...relay,
            status: relay.state ? 'on' : 'off'
          }));
        }
        if (data.pumps && data.pumps.length > 0) {
          pumps = data.pumps.map(pump => ({
            ...pump,
            status: pump.status === 'running' ? 'dispensing' : 'idle'
          }));
        }
        if (data.flow_meters && data.flow_meters.length > 0) {
          flowMeters = data.flow_meters.map(flowMeter => ({
            ...flowMeter,
            status: flowMeter.status === 'running' ? 'flowing' : 'idle'
          }));
        }
        systemStatus = 'Connected';
        errorMessage = '';
      } else {
        throw new Error('Failed to fetch hardware data');
      }
    } catch (error) {
      console.error('Error fetching hardware data:', error);
      systemStatus = 'Disconnected';
      errorMessage = error.message;
    }
  }

  async function fetchSystemStatus() {
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const data = await response.json();
        ecValue = data.ec_value || 0;
        phValue = data.ph_value || 0;
        ecPhMonitoring = data.ec_ph_monitoring || false;

        if (data.pumps) {
          pumps = pumps.map(pump => {
            const statusInfo = data.pumps[pump.id];
            if (statusInfo) {
              if (statusInfo.is_dispensing && statusInfo.current_volume > 0 && statusInfo.target_volume > 0) {
                const currentPercent = Math.floor((statusInfo.current_volume / statusInfo.target_volume) * 100 / 10) * 10;
                const lastPercent = lastProgressReported.get(pump.id) || -10;

                if (currentPercent > lastPercent && currentPercent >= 10) {
                  const progressMsg = `Pump ${pump.id} (${pump.name}): ${statusInfo.current_volume.toFixed(1)}ml / ${statusInfo.target_volume.toFixed(1)}ml (${currentPercent}% complete)`;
                  addLog(progressMsg);
                  lastProgressReported.set(pump.id, currentPercent);
                }
              }

              if (!statusInfo.is_dispensing && pump.is_dispensing) {
                const completionMsg = `Pump ${pump.id} (${pump.name}) completed dispensing: ${statusInfo.current_volume?.toFixed(1) || 0}ml dispensed`;
                addLog(completionMsg);
                lastProgressReported.delete(pump.id);
              }

              return {
                ...pump,
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
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  }

  async function controlRelay(relayId, action) {
    if (relayId === 0 && action === 'off') {
      await allRelaysOff();
      return;
    }

    logger.debug('Hardware', `Controlling relay ${relayId}`, { relayId, action });

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
        toast.success(`Relay ${relayId} turned ${action.toUpperCase()}`);
        logger.info('Hardware', `Relay ${relayId} ${action}`, { relayId, action, result });

        relays = relays.map(relay =>
          relay.id === relayId ? { ...relay, status: action } : relay
        );
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to control relay: ${error.error || 'Unknown error'}`);
        logger.error('Hardware', `Relay control failed`, { relayId, action, error });
      }
    } catch (error) {
      console.error('Error controlling relay:', error);
      addLog(`Error controlling relay: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
      logger.error('API', `Network error controlling relay`, { relayId, action, error: error.message });
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
        toast.success('All relays turned OFF');

        relays = relays.map(relay => ({ ...relay, status: 'off' }));
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to turn off relays: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error turning off all relays:', error);
      addLog(`Error turning off all relays: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
    }
  }

  function handleComboControl(comboName, action, result) {
    // Update relay states based on combo activation
    if (result && result.success && result.relays) {
      const newState = action === 'on' ? 'on' : 'off';
      relays = relays.map(relay =>
        result.relays.includes(relay.id) ? { ...relay, status: newState } : relay
      );

      addLog(`${comboName} turned ${action.toUpperCase()}`);
      toast.success(`${comboName} ${action.toUpperCase()}`);
      logger.info('Hardware', `Combo activated: ${comboName}`, { comboName, action, relays: result.relays });
    }
  }

  async function dispensePump(pumpId, amount) {
    if (!pumpId || !amount) {
      addLog('Please select a pump and amount');
      toast.warning('Please select a pump and enter an amount');
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
        toast.success(`Dispensing ${amount}ml from pump ${pumpId}`);

        lastProgressReported.set(parseInt(pumpId), -10);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to dispense: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error dispensing pump:', error);
      addLog(`Error dispensing pump: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
    }
  }

  async function stopPump(pumpId) {
    if (!pumpId) {
      addLog('Please select a pump');
      toast.warning('Please select a pump to stop');
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
        toast.success(`Pump ${pumpId} stopped`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to stop pump: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error stopping pump:', error);
      addLog(`Error stopping pump: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
    }
  }

  async function startFlow(flowMeterId, gallons) {
    if (!flowMeterId || !gallons) {
      addLog('Please select a flow meter and gallons');
      toast.warning('Please select a flow meter and enter gallons');
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
        toast.success(`Flow meter ${flowMeterId} started for ${gallons} gallons`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to start flow meter: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error starting flow meter:', error);
      addLog(`Error starting flow meter: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
    }
  }

  async function stopFlow(flowMeterId) {
    if (!flowMeterId) {
      addLog('Please select a flow meter');
      toast.warning('Please select a flow meter to stop');
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
        toast.success(`Flow meter ${flowMeterId} stopped`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to stop flow meter: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error stopping flow meter:', error);
      addLog(`Error stopping flow meter: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
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
        toast.success('EC/pH monitoring started');
        ecPhMonitoring = true;
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to start monitoring: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error starting EC/pH monitoring:', error);
      addLog(`Error starting EC/pH monitoring: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
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
        toast.success('EC/pH monitoring stopped');
        ecPhMonitoring = false;
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
        addLog(`Raw Error: ${JSON.stringify(error)}`);
        toast.error(`Failed to stop monitoring: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error stopping EC/pH monitoring:', error);
      addLog(`Error stopping EC/pH monitoring: ${error.message}`);
      toast.error(`Network error: ${error.message}`);
    }
  }

  function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    logs = [{ time: timestamp, message }, ...logs].slice(0, 100);
  }

  function clearLogs() {
    logs = [];
  }

  function toggleSection(section) {
    expandedSections[section] = !expandedSections[section];
  }

  onMount(async () => {
    addLog('Hardware testing page started');

    // Try WebSocket first, fall back to polling if unavailable
    if (useWebSocket) {
      try {
        initWebSocket();
        unsubscribeStatus = onStatusUpdate(handleWebSocketStatus);
        unsubscribeConnection = onConnectionChange(handleConnectionChange);
        addLog('WebSocket connection initialized');
        logger.info('System', 'WebSocket mode enabled');
      } catch (e) {
        logger.error('WebSocket', 'Failed to initialize, falling back to polling', { error: e.message });
        useWebSocket = false;
      }
    }

    // Initial data fetch (for both modes)
    await fetchHardwareData();

    // Polling fallback if WebSocket fails or is disabled
    if (!useWebSocket) {
      await fetchSystemStatus();
      statusInterval = setInterval(async () => {
        await fetchSystemStatus();
      }, 2000);
      addLog('Using HTTP polling mode');
    }

    if (pumps.length > 0) selectedPump = pumps[0].id;
    if (flowMeters.length > 0) selectedFlowMeter = flowMeters[0].id;
  });

  onDestroy(() => {
    // Cleanup WebSocket subscriptions
    if (unsubscribeStatus) unsubscribeStatus();
    if (unsubscribeConnection) unsubscribeConnection();
    disconnectWebSocket();

    // Cleanup polling interval
    if (statusInterval) {
      clearInterval(statusInterval);
    }
  });
</script>

<div class="dashboard-container">
  <!-- Page Header -->
  <div class="page-header">
    <div class="header-content">
      <div class="header-text">
        <h1 class="page-title">Hardware Testing</h1>
        <p class="page-subtitle">Stage 1: Individual Component Testing</p>
      </div>

      <div class="header-status">
        <div class="status-group">
          <div class="status-label">SYSTEM STATUS</div>
          <div class="flex items-center gap-2">
            <div class="status-dot {systemStatus.toLowerCase().startsWith('connected') ? 'bg-green-500' : systemStatus.toLowerCase() === 'reconnecting' ? 'bg-yellow-500' : 'bg-red-500'}"></div>
            <span class="text-sm font-medium text-slate-200">{systemStatus}</span>
          </div>
        </div>

        <div class="status-divider"></div>

        <div class="status-group">
          <div class="status-label">ACTIVE COMPONENTS</div>
          <div class="flex gap-4">
            <div class="flex items-baseline gap-1">
              <span class="text-xs text-slate-400">Relays:</span>
              <span class="text-sm font-bold text-purple-400">{activeRelayCount}</span>
            </div>
            <div class="flex items-baseline gap-1">
              <span class="text-xs text-slate-400">Pumps:</span>
              <span class="text-sm font-bold text-green-400">{activePumpCount}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    {#if errorMessage}
      <div class="error-banner">
        <svg class="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>{errorMessage}</span>
      </div>
    {/if}
  </div>

  <!-- Main Grid Layout -->
  <div class="main-grid">
    <!-- Left Column -->
    <div class="grid-column">
      <!-- Relay Control Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('relays')}
              aria-expanded={expandedSections.relays}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">Relay Control</span>
                <Badge variant="secondary" class="section-count-badge">{activeRelayCount} / 13</Badge>
              </div>
              <svg
                class="chevron-icon {expandedSections.relays ? 'chevron-expanded' : ''}"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
          </div>
        </CardHeader>
        {#if expandedSections.relays}
        <CardContent>
          <RelayControlCard {relays} onRelayControl={controlRelay} onComboControl={handleComboControl} />
        </CardContent>
        {/if}
      </Card>

      <!-- Pump Control Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('pumps')}
              aria-expanded={expandedSections.pumps}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">Pump Testing</span>
                <Badge variant="secondary" class="section-count-badge">{activePumpCount} / 8</Badge>
              </div>
              <svg
                class="chevron-icon {expandedSections.pumps ? 'chevron-expanded' : ''}"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
            <Button
              variant="outline"
              size="sm"
              onclick={() => showCalibrationWizard = true}
              class="calibrate-btn"
            >
              Calibrate
            </Button>
          </div>
        </CardHeader>
        {#if expandedSections.pumps}
        <CardContent>
          <PumpControlCard
            {pumps}
            bind:selectedPump
            bind:pumpAmount
            onDispensePump={dispensePump}
            onStopPump={stopPump}
          />
        </CardContent>
        {/if}
      </Card>
    </div>

    <!-- Right Column -->
    <div class="grid-column">
      <!-- Flow Meter Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('flow')}
              aria-expanded={expandedSections.flow}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">Flow Meter Testing</span>
                <Badge variant="secondary" class="section-count-badge">2 Meters</Badge>
              </div>
              <svg
                class="chevron-icon {expandedSections.flow ? 'chevron-expanded' : ''}"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
          </div>
        </CardHeader>
        {#if expandedSections.flow}
        <CardContent>
          <FlowMeterCard
            flowMeters={flowMeters}
            bind:selectedFlowMeter
            bind:flowGallons
            onStartFlow={startFlow}
            onStopFlow={stopFlow}
          />
        </CardContent>
        {/if}
      </Card>

      <!-- EC/pH Monitor Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('ecph')}
              aria-expanded={expandedSections.ecph}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">EC/pH Sensor Monitoring</span>
                {#if ecPhMonitoring}
                  <Badge variant="outline" class="monitoring-badge bg-green-500/10 text-green-400 border-green-500/30">LIVE</Badge>
                {:else}
                  <Badge variant="outline" class="monitoring-badge">STANDBY</Badge>
                {/if}
              </div>
              <svg
                class="chevron-icon {expandedSections.ecph ? 'chevron-expanded' : ''}"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
          </div>
        </CardHeader>
        {#if expandedSections.ecph}
        <CardContent>
          <ECPHMonitorCard
            {ecValue}
            {phValue}
            {ecPhMonitoring}
            onStartMonitoring={startEcPhMonitoring}
            onStopMonitoring={stopEcPhMonitoring}
          />
        </CardContent>
        {/if}
      </Card>

      <!-- System Log Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="flex justify-between items-center w-full">
            <div class="flex items-center gap-2">
              <span class="section-title-text">System Activity Log</span>
            </div>
            <Button variant="ghost" size="sm" class="h-6 text-xs text-slate-500" onclick={clearLogs}>Clear</Button>
          </div>
        </CardHeader>
        <CardContent>
          <SystemLogCard {logs} onClearLogs={clearLogs} />
        </CardContent>
      </Card>
    </div>
  </div>
</div>

<!-- Pump Calibration Wizard Modal -->
{#if showCalibrationWizard}
  <PumpCalibrationWizard
    {pumps}
    onClose={() => showCalibrationWizard = false}
  />
{/if}

<style>
  :global(body) {
    background-color: #0a0f1e;
    color: #e2e8f0;
  }

  .dashboard-container {
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    box-sizing: border-box;
    min-height: 100vh;
  }

  /* Page Header - Enhanced with gradient and better spacing */
  .page-header {
    width: 100%;
    background: linear-gradient(135deg, #1a1f35 0%, #151929 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 0.75rem;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-shadow:
      0 4px 16px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(139, 92, 246, 0.1) inset;
    box-sizing: border-box;
    backdrop-filter: blur(10px);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .header-text {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .page-title {
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: #f1f5f9;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: linear-gradient(135deg, #f1f5f9 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .page-subtitle {
    font-size: 0.875rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .header-status {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .status-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .status-label {
    font-size: 0.625rem;
    font-weight: 800;
    color: #8b5cf6;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }

  .status-dot {
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 9999px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .status-divider {
    width: 1px;
    height: 2.5rem;
    background: linear-gradient(to bottom, transparent, rgba(139, 92, 246, 0.3), transparent);
  }

  .error-banner {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 0.5rem;
    color: #fca5a5;
    font-size: 0.875rem;
    font-weight: 500;
  }

  /* Main Grid */
  .main-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.25rem;
    width: 100%;
  }

  @media (min-width: 768px) {
    .main-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  .grid-column {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  /* Cards - Enhanced with better shadows and borders */
  :global(.dashboard-card) {
    background: linear-gradient(135deg, #1a1f35 0%, #151929 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.15) !important;
    box-shadow:
      0 8px 24px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(139, 92, 246, 0.08) inset !important;
    border-radius: 0.75rem !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  }

  :global(.dashboard-card:hover) {
    border-color: rgba(139, 92, 246, 0.25) !important;
    box-shadow:
      0 12px 32px rgba(0, 0, 0, 0.5),
      0 0 0 1px rgba(139, 92, 246, 0.12) inset !important;
  }

  /* Section Headers - Collapsible */
  .section-header-collapsible {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .section-toggle-btn {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: none;
    border: none;
    color: #f1f5f9;
    cursor: pointer;
    padding: 0;
    transition: all 0.2s;
  }

  .section-toggle-btn:hover .section-title-text {
    color: #a78bfa;
  }

  .section-title-text {
    font-size: 1.125rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    transition: color 0.2s;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }

  .chevron-icon {
    color: #6b7280;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .chevron-expanded {
    transform: rotate(180deg);
    color: #8b5cf6;
  }

  /* Badge styling overrides */
  :global(.section-count-badge) {
    background: rgba(139, 92, 246, 0.15) !important;
    color: #a78bfa !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
  }

  :global(.monitoring-badge) {
    font-size: 0.625rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.05em !important;
    padding: 0.125rem 0.5rem !important;
  }

  /* Responsive Design */
  @media (max-width: 767px) {
    .dashboard-container {
      padding: 0.75rem;
      gap: 1rem;
    }

    .page-header {
      padding: 1rem;
    }

    .header-content {
      flex-direction: column;
      align-items: flex-start;
    }

    .page-title {
      font-size: 1.5rem;
    }

    .header-status {
      flex-wrap: wrap;
      width: 100%;
    }

    .section-title-text {
      font-size: 1rem;
    }
  }

  @media (max-width: 480px) {
    .page-title {
      font-size: 1.25rem;
    }

    .page-subtitle {
      font-size: 0.75rem;
    }
  }
</style>
