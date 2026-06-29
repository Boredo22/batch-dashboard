<script>
  import { onMount, onDestroy } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Progress } from '$lib/components/ui/progress';
  import { Alert, AlertDescription } from '$lib/components/ui/alert';
  import { Separator } from '$lib/components/ui/separator';
  import ActivityLog from './ActivityLog.svelte';
  import StatusBar from './StatusBar.svelte';
  import TankStatusCard from './TankStatusCard.svelte';
  import NutrientPumpsCard from './NutrientPumpsCard.svelte';
  import RelayControlsCard from './RelayControlsCard.svelte';
  import FlowMonitorCard from './FlowMonitorCard.svelte';
  import SensorsCard from './SensorsCard.svelte';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';
  import { apiGet, apiPost } from '$lib/api.js';
  import { toast } from 'svelte-sonner';

  // Get reactive system status from SSE store
  const sseStatus = getSystemStatus();

  // State using Svelte 5 runes
  let relays = $state([
    { id: 1, name: 'Tank 1 Fill', status: 'off' },
    { id: 2, name: 'Tank 2 Fill', status: 'off' },
    { id: 3, name: 'Tank 3 Fill', status: 'off' },
    { id: 4, name: 'Tank 1 Mix Out', status: 'off' },
    { id: 5, name: 'Tank 2 Mix Out', status: 'off' },
    { id: 6, name: 'Tank 3 Mix Out', status: 'off' },
    { id: 7, name: 'Tank 1 Mix In', status: 'off' },
    { id: 8, name: 'Tank 2 Mix In', status: 'off' },
    { id: 9, name: 'Tank 3 Mix In', status: 'off' },
    { id: 10, name: 'Room 1', status: 'off' },
    { id: 11, name: 'Room 2', status: 'off' },
    { id: 12, name: 'Nursery', status: 'off' },
    { id: 13, name: 'Drain', status: 'off' }
  ]);

  let pumps = $state([]);
  let pumpConfig = $state({});

  let flowMeters = $state([
    { id: 1, name: 'Fill Flow', flow_rate: 0, total_gallons: 0, status: 'idle' },
    { id: 2, name: 'Send Flow', flow_rate: 0, total_gallons: 0, status: 'development' }
  ]);

  let tankStatus = $state({
    1: { volume: 0, status: 'idle', lastFilled: null },
    2: { volume: 0, status: 'idle', lastFilled: null },
    3: { volume: 0, status: 'idle', lastFilled: null }
  });

  let dosingAmount = $state(50);
  let logs = $state([]);
  let isProcessing = $state(false);

  // Derive system status from SSE connection
  let systemStatus = $derived(sseStatus.isConnected ? 'Connected' : 'Disconnected');

  // SSE unsubscribe function
  let unsubscribe = null;

  // Tank configuration
  const TANK_CONFIG = {
    1: { fillRelay: 1, mixRelays: [4, 7], sendRelay: 10, pumps: [1, 2, 3], color: 'blue' },
    2: { fillRelay: 2, mixRelays: [5, 8], sendRelay: 11, pumps: [4, 5, 6], color: 'green' },
    3: { fillRelay: 3, mixRelays: [6, 9], sendRelay: 12, pumps: [7, 8], color: 'yellow' }
  };

  // Derived values
  let activePumps = $derived(pumps.filter(pump => pump.status === 'dispensing'));
  let anyRelayActive = $derived(relays.some(relay => relay.status === 'on'));

  // Fetch pump configuration from backend
  async function fetchPumpConfig() {
    try {
      // Try to fetch pump config from dedicated endpoint
      let config = null;

      try {
        config = await apiGet('/api/config/pumps');
      } catch (primaryError) {
        // Fallback: try to get pump info from hardware status
        const pumpsData = await apiGet('/api/hardware/pumps');
        config = { pump_names: {} };
        // Extract names from pump data if available
        if (pumpsData.pumps) {
          pumpsData.pumps.forEach(pump => {
            if (pump.name) config.pump_names[pump.id] = pump.name;
          });
        }
      }

      if (config && config.pump_names) {
        pumpConfig = config;
        // Initialize pumps array with config names
        pumps = Object.entries(config.pump_names).map(([id, name]) => ({
          id: parseInt(id),
          name: name,
          status: 'idle',
          progress: 0,
          target_volume: 0
        }));
      } else {
        // Final fallback using the names from config.py
        pumps = [
          { id: 1, name: 'Veg A', status: 'idle', progress: 0, target_volume: 0 },
          { id: 2, name: 'Veg B', status: 'idle', progress: 0, target_volume: 0 },
          { id: 3, name: 'Bloom A', status: 'idle', progress: 0, target_volume: 0 },
          { id: 4, name: 'Bloom B', status: 'idle', progress: 0, target_volume: 0 },
          { id: 5, name: 'Cake', status: 'idle', progress: 0, target_volume: 0 },
          { id: 6, name: 'Runclean', status: 'idle', progress: 0, target_volume: 0 },
          { id: 7, name: 'PK Synergy', status: 'idle', progress: 0, target_volume: 0 },
          { id: 8, name: 'pH Down', status: 'idle', progress: 0, target_volume: 0 }
        ];
      }
    } catch (error) {
      toast.error(`Pump config: ${error.message}`);
      // Error fallback using config.py names
      pumps = [
        { id: 1, name: 'Veg A', status: 'idle', progress: 0, target_volume: 0 },
        { id: 2, name: 'Veg B', status: 'idle', progress: 0, target_volume: 0 },
        { id: 3, name: 'Bloom A', status: 'idle', progress: 0, target_volume: 0 },
        { id: 4, name: 'Bloom B', status: 'idle', progress: 0, target_volume: 0 },
        { id: 5, name: 'Cake', status: 'idle', progress: 0, target_volume: 0 },
        { id: 6, name: 'Runclean', status: 'idle', progress: 0, target_volume: 0 },
        { id: 7, name: 'PK Synergy', status: 'idle', progress: 0, target_volume: 0 },
        { id: 8, name: 'pH Down', status: 'idle', progress: 0, target_volume: 0 }
      ];
    }
  }

  // Track last processed timestamp to avoid reprocessing same data
  let lastProcessedTimestamp = '';

  // React to SSE status updates using $effect
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) return;

    // Skip if we've already processed this update (prevents infinite loops)
    if (data.timestamp === lastProcessedTimestamp) return;
    lastProcessedTimestamp = data.timestamp;

    // Update relays from SSE data
    if (data.relays) {
      relays = relays.map(relay => {
        const apiRelay = data.relays.find(r => r.id === relay.id);
        return apiRelay ? { ...relay, status: apiRelay.state ? 'on' : 'off' } : relay;
      });
    }

    // Update pumps from SSE data
    if (data.pumps && data.pumps.length > 0) {
      // If pumps haven't been initialized from config yet, initialize from SSE data
      if (pumps.length === 0) {
        pumps = data.pumps.map(pump => ({
          id: pump.id,
          name: pump.name || `Pump ${pump.id}`,
          status: pump.is_dispensing ? 'dispensing' : 'idle',
          progress: pump.current_volume && pump.target_volume
            ? Math.round((pump.current_volume / pump.target_volume) * 100)
            : 0,
          target_volume: pump.target_volume || 0
        }));
      } else {
        pumps = pumps.map(pump => {
          const apiPump = data.pumps.find(p => p.id === pump.id);
          if (apiPump) {
            return {
              ...pump,
              name: apiPump.name || pump.name,
              status: apiPump.is_dispensing ? 'dispensing' : 'idle',
              progress: apiPump.current_volume && apiPump.target_volume
                ? Math.round((apiPump.current_volume / apiPump.target_volume) * 100)
                : 0,
              target_volume: apiPump.target_volume || 0
            };
          }
          return pump;
        });
      }
    }
  });

  // Tank Operations
  async function fillTank(tankId) {
    if (isProcessing) return;
    isProcessing = true;

    try {
      const config = TANK_CONFIG[tankId];
      addLog(`Starting fill for Tank ${tankId}`);
      
      // Activate fill relay
      await controlRelay(config.fillRelay, 'on');
      
      // Start flow meter for 25 gallons (default)
      const result = await apiPost(`/api/flow/${flowMeters[0].id}/start`, { gallons: 25 });

      tankStatus[tankId] = { ...tankStatus[tankId], status: 'filling' };
      addLog(`Tank ${tankId} filling started - 25 gallons`);
    } catch (error) {
      addLog(`Error filling Tank ${tankId}: ${error.message}`);
      toast.error(`Fill Tank ${tankId}: ${error.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function mixTank(tankId) {
    if (isProcessing) return;
    
    const config = TANK_CONFIG[tankId];
    if (tankStatus[tankId].volume < 20) {
      addLog(`Tank ${tankId} needs at least 20 gallons before mixing`);
      return;
    }

    isProcessing = true;

    try {
      addLog(`Starting mix for Tank ${tankId}`);
      
      // Activate mix relays
      for (const relayId of config.mixRelays) {
        await controlRelay(relayId, 'on');
      }

      tankStatus[tankId] = { ...tankStatus[tankId], status: 'mixing' };
      addLog(`Tank ${tankId} mixing started - relays ${config.mixRelays.join(', ')} activated`);
      
      // Auto-stop mixing after 5 minutes
      setTimeout(async () => {
        for (const relayId of config.mixRelays) {
          await controlRelay(relayId, 'off');
        }
        tankStatus[tankId] = { ...tankStatus[tankId], status: 'ready' };
        addLog(`Tank ${tankId} mixing completed`);
      }, 300000); // 5 minutes

    } catch (error) {
      addLog(`Error mixing Tank ${tankId}: ${error.message}`);
    } finally {
      isProcessing = false;
    }
  }

  async function sendTank(tankId) {
    if (isProcessing) return;
    isProcessing = true;

    try {
      const config = TANK_CONFIG[tankId];
      addLog(`Starting send from Tank ${tankId} to Room`);
      
      // Activate tank relay and room relay
      await controlRelay(config.fillRelay, 'on'); // Tank valve
      await controlRelay(config.sendRelay, 'on'); // Room valve

      tankStatus[tankId] = { ...tankStatus[tankId], status: 'sending' };
      addLog(`Tank ${tankId} sending to room - monitor manually`);
      
    } catch (error) {
      addLog(`Error sending Tank ${tankId}: ${error.message}`);
    } finally {
      isProcessing = false;
    }
  }

  // Relay Control
  async function controlRelay(relayId, action) {
    try {
      const result = await apiPost(`/api/relay/${relayId}/${action}`);

      addLog(`Relay ${relayId} ${action.toUpperCase()}: ${result.message || 'Success'}`);

      // Update local state
      relays = relays.map(relay =>
        relay.id === relayId ? { ...relay, status: action } : relay
      );
    } catch (error) {
      addLog(`Relay ${relayId} error: ${error.message}`);
      toast.error(`Relay ${relayId}: ${error.message}`);
    }
  }

  async function toggleRelay(relayId) {
    const relay = relays.find(r => r.id === relayId);
    const newAction = relay.status === 'on' ? 'off' : 'on';
    await controlRelay(relayId, newAction);
  }

  // Pump Control
  async function dispensePump(pumpId, amount) {
    if (!amount || amount < 1) {
      addLog('Please set a dosing amount');
      return;
    }

    try {
      const result = await apiPost(`/api/pump/${pumpId}/dispense`, { amount: amount });

      addLog(`Dispensing ${amount}ml from ${pumps.find(p => p.id === pumpId)?.name}`);

      // Update pump status
      pumps = pumps.map(pump =>
        pump.id === pumpId
          ? { ...pump, status: 'dispensing', target_volume: amount, progress: 0 }
          : pump
      );
    } catch (error) {
      addLog(`Pump ${pumpId} error: ${error.message}`);
      toast.error(`Pump ${pumpId}: ${error.message}`);
    }
  }

  async function stopPump(pumpId) {
    try {
      const result = await apiPost(`/api/pump/${pumpId}/stop`);

      addLog(`Stopped pump ${pumpId}`);
      pumps = pumps.map(pump =>
        pump.id === pumpId
          ? { ...pump, status: 'idle', progress: 0, target_volume: 0 }
          : pump
      );
    } catch (error) {
      addLog(`Error stopping pump ${pumpId}: ${error.message}`);
      toast.error(`Stop pump ${pumpId}: ${error.message}`);
    }
  }

  // Emergency Stop
  async function emergencyStop() {
    try {
      const result = await apiPost('/api/relay/all/off');

      addLog('🛑 EMERGENCY STOP - All relays turned off');
      relays = relays.map(relay => ({ ...relay, status: 'off' }));

      // Reset tank statuses
      tankStatus[1].status = 'idle';
      tankStatus[2].status = 'idle';
      tankStatus[3].status = 'idle';
    } catch (error) {
      addLog(`Emergency stop error: ${error.message}`);
      toast.error(`Emergency stop: ${error.message}`);
    }
  }

  // Utility Functions
  function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    logs = [{ time: timestamp, message }, ...logs].slice(0, 50);
  }

  function clearLogs() {
    logs = [];
  }

  function setDosingPreset(amount) {
    dosingAmount = amount;
  }

  function handleSliderInput(event) {
    let value = parseInt(event.target.value);
    
    // Snap to appropriate increments based on value
    if (value <= 100) {
      // 1ml increments for 1-100
      dosingAmount = value;
    } else if (value <= 500) {
      // 5ml increments for 101-500
      dosingAmount = Math.round(value / 5) * 5;
    } else {
      // 25ml increments for 501-2000
      dosingAmount = Math.round(value / 25) * 25;
    }
  }

  function getNutrientClass(name) {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('veg')) return 'nutrient-veg';
    if (lowerName.includes('bloom')) return 'nutrient-bloom';
    if (lowerName.includes('pk synergy')) return 'nutrient-pk';
    if (lowerName.includes('runclean')) return 'nutrient-runclean';
    if (lowerName.includes('ph down')) return 'nutrient-ph';
    if (lowerName.includes('cake')) return 'nutrient-cake';
    return '';
  }

  function getTankIcon(tankId) {
    const icons = { 
      1: { icon: '🟦', color: 'var(--accent-blue)' }, 
      2: { icon: '🟩', color: 'var(--accent-green)' }, 
      3: { icon: '🟨', color: 'var(--accent-yellow)' } 
    };
    return icons[tankId] || { icon: '⚪', color: 'var(--text-muted)' };
  }

  function getTankStatusBadge(status) {
    const badges = {
      idle: { class: 'status-idle', text: 'Idle' },
      filling: { class: 'status-filling', text: 'Filling' },
      mixing: { class: 'status-mixing', text: 'Mixing' },
      sending: { class: 'status-sending', text: 'Sending' },
      ready: { class: 'status-ready', text: 'Ready' }
    };
    return badges[status] || badges.idle;
  }

  // Icons as SVG components
  function WaterDropIcon(props = {}) {
    return `<svg class="${props.class || ''}" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M7 16.5V19a3 3 0 0 0 3 3h4a3 3 0 0 0 3-3v-2.5"/>
      <path d="M8 8s0-2 2.5-4.5S15 1 15 1s3 2 3 7c0 1.657-.895 3-2 3s-2-1.343-2-3c0-2.5-1.5-4-2-4s-2 1.5-2 4"/>
    </svg>`;
  }

  // Lifecycle
  onMount(async () => {
    addLog('Growers dashboard started');

    // Subscribe to SSE updates
    unsubscribe = subscribe();

    // Fetch pump config (this is a one-time setup, not polling)
    await fetchPumpConfig();
  });

  onDestroy(() => {
    // Unsubscribe from SSE when component unmounts
    if (unsubscribe) {
      unsubscribe();
    }
  });
</script>

<!-- Compact System Status Bar -->
<div class="scaled-dashboard">
<StatusBar {relays} {activePumps} {flowMeters} onEmergencyStop={emergencyStop} />

<!-- Main Dashboard Grid -->
<div class="dashboard-grid">

  <!-- Top Row: Tank Status, Nute Pumps, Relay Controls -->
  <div class="top-controls-row">
    <TankStatusCard
      tankConfig={TANK_CONFIG}
      {tankStatus}
      {isProcessing}
      {getTankStatusBadge}
      onFill={fillTank}
      onMix={mixTank}
      onSend={sendTank}
    />

    <NutrientPumpsCard
      {pumps}
      {dosingAmount}
      onDispense={dispensePump}
      onSliderInput={handleSliderInput}
    />

    <RelayControlsCard {relays} onToggleRelay={toggleRelay} />
  </div>

  <!-- Monitoring Panel -->
  <div class="monitoring-panel">
    <FlowMonitorCard {flowMeters} />

    <SensorsCard />

    <!-- Activity Log -->
    <ActivityLog {logs} onClear={clearLogs} />
  </div>
</div>
</div>


<style>
  /* Design tokens are defined globally in src/app.css */

  /* Main Dashboard Layout - Optimized for 10" Tablet */
  .dashboard-grid {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    padding: 0 var(--space-md);
  }

  /* Top Controls Row - Tank Status, Pumps, Relays */
  .top-controls-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: var(--space-md);
  }

  /* Monitoring Panel */
  .monitoring-panel {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .dashboard-grid {
      grid-template-columns: 1fr 320px;
      gap: var(--space-lg);
    }

    .monitoring-panel {
      grid-column: 1 / -1;
      grid-row: 3;
    }
  }

  @media (max-width: 768px) {
    .dashboard-grid {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
      padding: 0 var(--space-md);
    }
  }

  /* Accessibility - High Contrast Mode */
  @media (prefers-contrast: high) {
    :root {
      --bg-primary: #000000;
      --bg-secondary: #1a1a1a;
      --bg-tertiary: #2d2d2d;
      --border-subtle: #4a5568;
      --border-emphasis: #64748b;
      --text-primary: #ffffff;
      --text-secondary: #f8fafc;
      --text-muted: #d1d5db;
    }
  }

  /* Accessibility - Reduced Motion */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation: none !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
