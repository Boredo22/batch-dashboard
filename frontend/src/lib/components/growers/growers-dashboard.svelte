<script>
  import { onMount, onDestroy } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Progress } from '$lib/components/ui/progress';
  import { Alert, AlertDescription } from '$lib/components/ui/alert';
  import { Separator } from '$lib/components/ui/separator';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';

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
      let response = await fetch('/api/config/pumps');
      let config = null;
      
      if (response.ok) {
        config = await response.json();
      } else {
        // Fallback: try to get pump info from hardware status
        response = await fetch('/api/hardware/pumps');
        if (response.ok) {
          const pumpsData = await response.json();
          config = { pump_names: {} };
          // Extract names from pump data if available
          if (pumpsData.pumps) {
            pumpsData.pumps.forEach(pump => {
              if (pump.name) config.pump_names[pump.id] = pump.name;
            });
          }
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
          { id: 6, name: 'PK Synergy', status: 'idle', progress: 0, target_volume: 0 },
          { id: 7, name: 'Runclean', status: 'idle', progress: 0, target_volume: 0 },
          { id: 8, name: 'pH Down', status: 'idle', progress: 0, target_volume: 0 }
        ];
      }
    } catch (error) {
      console.error('Error fetching pump config:', error);
      // Error fallback using config.py names
      pumps = [
        { id: 1, name: 'Veg A', status: 'idle', progress: 0, target_volume: 0 },
        { id: 2, name: 'Veg B', status: 'idle', progress: 0, target_volume: 0 },
        { id: 3, name: 'Bloom A', status: 'idle', progress: 0, target_volume: 0 },
        { id: 4, name: 'Bloom B', status: 'idle', progress: 0, target_volume: 0 },
        { id: 5, name: 'Cake', status: 'idle', progress: 0, target_volume: 0 },
        { id: 6, name: 'PK Synergy', status: 'idle', progress: 0, target_volume: 0 },
        { id: 7, name: 'Runclean', status: 'idle', progress: 0, target_volume: 0 },
        { id: 8, name: 'pH Down', status: 'idle', progress: 0, target_volume: 0 }
      ];
    }
  }

  // React to SSE status updates using $effect
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) return;

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
      const response = await fetch(`/api/flow/${flowMeters[0].id}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gallons: 25 })
      });

      if (response.ok) {
        tankStatus[tankId] = { ...tankStatus[tankId], status: 'filling' };
        addLog(`Tank ${tankId} filling started - 25 gallons`);
      }
    } catch (error) {
      addLog(`Error filling Tank ${tankId}: ${error.message}`);
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
      const response = await fetch(`/api/relay/${relayId}/${action}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(`Relay ${relayId} ${action.toUpperCase()}: ${result.message || 'Success'}`);
        
        // Update local state
        relays = relays.map(relay => 
          relay.id === relayId ? { ...relay, status: action } : relay
        );
      } else {
        const error = await response.json();
        addLog(`Relay ${relayId} error: ${error.error}`);
      }
    } catch (error) {
      addLog(`Relay ${relayId} error: ${error.message}`);
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
      const response = await fetch(`/api/pump/${pumpId}/dispense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(`Dispensing ${amount}ml from ${pumps.find(p => p.id === pumpId)?.name}`);
        
        // Update pump status
        pumps = pumps.map(pump => 
          pump.id === pumpId 
            ? { ...pump, status: 'dispensing', target_volume: amount, progress: 0 }
            : pump
        );
      } else {
        const error = await response.json();
        addLog(`Pump ${pumpId} error: ${error.error}`);
      }
    } catch (error) {
      addLog(`Pump ${pumpId} error: ${error.message}`);
    }
  }

  async function stopPump(pumpId) {
    try {
      const response = await fetch(`/api/pump/${pumpId}/stop`, {
        method: 'POST'
      });
      
      if (response.ok) {
        addLog(`Stopped pump ${pumpId}`);
        pumps = pumps.map(pump => 
          pump.id === pumpId 
            ? { ...pump, status: 'idle', progress: 0, target_volume: 0 }
            : pump
        );
      }
    } catch (error) {
      addLog(`Error stopping pump ${pumpId}: ${error.message}`);
    }
  }

  // Emergency Stop
  async function emergencyStop() {
    try {
      const response = await fetch('/api/relay/all/off', {
        method: 'POST'
      });
      
      if (response.ok) {
        addLog('🛑 EMERGENCY STOP - All relays turned off');
        relays = relays.map(relay => ({ ...relay, status: 'off' }));
        
        // Reset tank statuses
        tankStatus[1].status = 'idle';
        tankStatus[2].status = 'idle';
        tankStatus[3].status = 'idle';
      }
    } catch (error) {
      addLog(`Emergency stop error: ${error.message}`);
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
<div class="compact-status-bar">
  <div class="status-section status-relays">
    <div class="status-label">RELAYS</div>
    <div class="relay-indicators">
      {#each relays as relay}
        <div class="relay-indicator {relay.status === 'on' ? 'relay-on' : 'relay-off'}"
             title="{relay.name}: {relay.status.toUpperCase()}">
        </div>
      {/each}
    </div>
  </div>

  <div class="status-divider"></div>

  <div class="status-section status-sensors">
    <div class="status-label">SENSORS</div>
    <div class="sensor-readings">
      <div class="sensor-item" title="pH Level">
        <span class="sensor-label">pH:</span>
        <span class="sensor-value">--</span>
      </div>
      <div class="sensor-item" title="EC Level">
        <span class="sensor-label">EC:</span>
        <span class="sensor-value">--</span>
      </div>
    </div>
  </div>

  <div class="status-divider"></div>

  <div class="status-section status-jobs">
    <div class="status-label">ACTIVE JOBS</div>
    <div class="job-indicators">
      <div class="job-item">
        <span class="job-label">Pumps:</span>
        <span class="job-count">{activePumps.length}</span>
      </div>
      <div class="job-item">
        <span class="job-label">Flow:</span>
        <span class="job-count">{flowMeters.filter(m => m.status !== 'idle' && m.status !== 'development').length}</span>
      </div>
    </div>
  </div>

  <div class="status-spacer"></div>

  <Button
    class="emergency-stop-btn"
    onclick={emergencyStop}
    size="sm"
  >
    <svg class="emergency-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="currentColor"/>
      <rect x="9" y="9" width="6" height="6" fill="white"/>
    </svg>
    EMERGENCY STOP
  </Button>
</div>

<!-- Main Dashboard Grid -->
<div class="dashboard-grid">

  <!-- Top Row: Tank Status, Nute Pumps, Relay Controls -->
  <div class="top-controls-row">

    <!-- Tank Status - Compact -->
    <Card class="tank-status-card compact-card">
      <CardHeader>
        <CardTitle class="section-title-compact">Tank Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="tank-compact-grid">
          {#each [1, 2, 3] as tankId}
            {@const config = TANK_CONFIG[tankId]}
            {@const status = tankStatus[tankId]}
            {@const statusBadge = getTankStatusBadge(status.status)}

            <div class="tank-compact-card">
              <div class="tank-compact-header">
                <div class="tank-compact-info">
                  <span class="tank-compact-label">Tank {tankId}</span>
                  <Badge class={statusBadge.class}>{statusBadge.text}</Badge>
                </div>
                <div class="tank-compact-volume">{status.volume} gal</div>
              </div>

              <Progress value={status.volume} max={100} class="tank-progress" />

              <div class="tank-compact-controls">
                <Button
                  class="tank-compact-btn"
                  onclick={() => fillTank(tankId)}
                  disabled={isProcessing}
                  size="sm"
                >
                  Fill
                </Button>

                <Button
                  class="tank-compact-btn"
                  onclick={() => mixTank(tankId)}
                  disabled={isProcessing}
                  size="sm"
                >
                  Mix
                </Button>

                <Button
                  class="tank-compact-btn"
                  onclick={() => sendTank(tankId)}
                  disabled={isProcessing}
                  size="sm"
                >
                  Send
                </Button>
              </div>
            </div>
          {/each}
        </div>
      </CardContent>
    </Card>

    <!-- Nutrient Pumps - Compact -->
    <Card class="nute-pumps-card compact-card">
      <CardHeader>
        <CardTitle class="section-title-compact">Nutrient Pumps</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="nute-pumps-compact-grid">
          {#each pumps as pump}
            <Button
              class="pump-btn-compact {pump.status === 'dispensing' ? 'pump-active' : 'pump-idle'}"
              onclick={() => dispensePump(pump.id, dosingAmount)}
              disabled={pump.status === 'dispensing'}
            >
              <div class="pump-content-compact">
                <div class="pump-id-compact">P{pump.id}</div>
                <div class="pump-name-compact">{pump.name}</div>
                {#if pump.status === 'dispensing'}
                  <div class="pump-status-compact">{pump.progress}%</div>
                {:else}
                  <div class="pump-status-compact">{dosingAmount}ml</div>
                {/if}
              </div>
            </Button>
          {/each}
        </div>
        <div class="dosing-amount-selector">
          <input
            type="range"
            class="dosing-slider-compact"
            min="1"
            max="2000"
            value={dosingAmount}
            step="1"
            oninput={handleSliderInput}
          />
          <div class="dosing-value-compact">{dosingAmount}ml</div>
        </div>
      </CardContent>
    </Card>

    <!-- Manual Relay Controls - Compact -->
    <Card class="relay-control-card compact-card">
      <CardHeader>
        <CardTitle class="section-title-compact">Relay Controls</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="relay-compact-grid">
          <!-- Tank 1 Relays -->
          <div class="relay-tank-section">
            <div class="tank-relay-header">Tank 1</div>
            <div class="tank-relays">
              {#each [1, 4, 7] as relayId}
                {@const relay = relays.find(r => r.id === relayId)}
                <Button
                  class="relay-btn tank1-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
                  onclick={() => toggleRelay(relay.id)}
                  variant="ghost"
                >
                  <div class="relay-content">
                    <div class="relay-id">{relay.id}</div>
                    <div class="relay-name">{relay.name}</div>
                    <div class="relay-status">{relay.status.toUpperCase()}</div>
                  </div>
                </Button>
              {/each}
            </div>
          </div>

          <!-- Tank 2 Relays -->
          <div class="relay-tank-section">
            <div class="tank-relay-header">Tank 2</div>
            <div class="tank-relays">
              {#each [2, 5, 8] as relayId}
                {@const relay = relays.find(r => r.id === relayId)}
                <Button
                  class="relay-btn tank2-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
                  onclick={() => toggleRelay(relay.id)}
                  variant="ghost"
                >
                  <div class="relay-content">
                    <div class="relay-id">{relay.id}</div>
                    <div class="relay-name">{relay.name}</div>
                    <div class="relay-status">{relay.status.toUpperCase()}</div>
                  </div>
                </Button>
              {/each}
            </div>
          </div>

          <!-- Tank 3 Relays -->
          <div class="relay-tank-section">
            <div class="tank-relay-header">Tank 3</div>
            <div class="tank-relays">
              {#each [3, 6, 9] as relayId}
                {@const relay = relays.find(r => r.id === relayId)}
                <Button
                  class="relay-btn tank3-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
                  onclick={() => toggleRelay(relay.id)}
                  variant="ghost"
                >
                  <div class="relay-content">
                    <div class="relay-id">{relay.id}</div>
                    <div class="relay-name">{relay.name}</div>
                    <div class="relay-status">{relay.status.toUpperCase()}</div>
                  </div>
                </Button>
              {/each}
            </div>
          </div>

          <!-- Room & Drain Relays -->
          <div class="relay-tank-section">
            <div class="tank-relay-header">Rooms & Drain</div>
            <div class="tank-relays">
              {#each [10, 11, 12, 13] as relayId}
                {@const relay = relays.find(r => r.id === relayId)}
                <Button
                  class="relay-btn rooms-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
                  onclick={() => toggleRelay(relay.id)}
                  variant="ghost"
                >
                  <div class="relay-content">
                    <div class="relay-id">{relay.id}</div>
                    <div class="relay-name">{relay.name}</div>
                    <div class="relay-status">{relay.status.toUpperCase()}</div>
                  </div>
                </Button>
              {/each}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>

  <!-- Monitoring Panel -->
  <div class="monitoring-panel">
    
    <!-- Flow Monitoring -->
    <Card class="monitoring-card">
      <CardHeader>
        <CardTitle class="section-title">
          <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 9V5a3 3 0 0 0-6 0v4"/>
            <rect x="2" y="9" width="20" height="12" rx="2"/>
          </svg>
          Flow Monitoring
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flow-monitors">
          {#each flowMeters as meter}
            <div class="flow-meter {meter.status === 'development' ? 'flow-development' : 'flow-active'}">
              <div class="meter-header">
                <div class="meter-name">{meter.name}</div>
                <Badge class={meter.status === 'development' ? 'status-development' : 'status-operational'}>
                  {meter.status === 'development' ? 'DEV' : 'ACTIVE'}
                </Badge>
              </div>
              
              {#if meter.status === 'development'}
                <div class="meter-status">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M7 2h10l5 10-5 10H7l-5-10z"/>
                  </svg>
                  Under Development
                </div>
              {:else}
                <div class="meter-readings">
                  <div class="flow-rate">{meter.flow_rate} <span class="unit">gal/min</span></div>
                  <div class="total-flow">Total: {meter.total_gallons} gal</div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </CardContent>
    </Card>

    <!-- System Sensors -->
    <Card class="monitoring-card">
      <CardHeader>
        <CardTitle class="section-title">
          <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 12c-2-2.67-4-4-6-4a4 4 0 1 0 0 8c2 0 4-1.33 6-4z"/>
            <path d="M12 12c2-2.67 4-4 6-4a4 4 0 1 1 0 8c-2 0-4-1.33-6-4z"/>
          </svg>
          pH/EC Monitoring
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="sensor-grid">
          <div class="sensor-card sensor-development">
            <div class="sensor-header">
              <div class="sensor-name">pH Level</div>
              <Badge class="status-development">DEV</Badge>
            </div>
            <div class="sensor-status">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M7 2h10l5 10-5 10H7l-5-10z"/>
              </svg>
              Under Development
            </div>
          </div>
          
          <div class="sensor-card sensor-development">
            <div class="sensor-header">
              <div class="sensor-name">EC Level</div>
              <Badge class="status-development">DEV</Badge>
            </div>
            <div class="sensor-status">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M7 2h10l5 10-5 10H7l-5-10z"/>
              </svg>
              Under Development
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Activity Log -->
    <Card class="log-card">
      <CardHeader class="log-header">
        <CardTitle class="section-title">
          <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10,9 9,9 8,9"/>
          </svg>
          System Activity
        </CardTitle>
        <Button 
          class="clear-logs-btn"
          onclick={clearLogs}
          size="sm"
          variant="outline"
        >
          Clear
        </Button>
      </CardHeader>
      <CardContent>
        <div class="log-container">
          {#each logs.slice(0, 15) as log}
            <div class="log-entry">
              <div class="log-time">{log.time}</div>
              <div class="log-message">{log.message}</div>
            </div>
          {/each}
          
          {#if logs.length === 0}
            <div class="log-empty">No recent activity</div>
          {/if}
        </div>
      </CardContent>
    </Card>
  </div>
</div>
</div>

<style>
  :root {
    /* Professional Industrial Color Palette */
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;

    /* Muted Accent Colors */
    --accent-steel: #64748b;
    --accent-slate: #475569;
    --accent-blue-muted: #3b82f6;

    /* Professional Status Colors (Muted) */
    --status-success: #059669;
    --status-warning: #d97706;
    --status-error: #dc2626;
    --status-info: #0284c7;
    --status-development: #ca8a04;

    /* Text Colors */
    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;
    --text-disabled: #64748b;
    --text-button: #f8fafc;

    /* Borders */
    --border-subtle: #334155;
    --border-emphasis: #475569;

    /* Spacing Scale */
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;

    /* Typography Scale */
    --text-3xl: 1.875rem;
    --text-2xl: 1.5rem;
    --text-xl: 1.25rem;
    --text-lg: 1.125rem;
    --text-base: 1rem;
    --text-sm: 0.875rem;
    --text-xs: 0.75rem;

    /* Shadows - Subtle */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 2px 4px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 4px 8px rgba(0, 0, 0, 0.5);

    /* Border Radius - Professional */
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
  }

  /* Global Styles */

  /* Compact Status Bar */
  .compact-status-bar {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-subtle);
    padding: var(--space-sm) var(--space-md);
    margin-bottom: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);
    height: 48px;
  }

  .status-section {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .status-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .relay-indicators {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .relay-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid var(--border-subtle);
    transition: all 0.2s ease;
  }

  .relay-on {
    background: var(--text-primary);
    border-color: var(--text-primary);
    box-shadow: 0 0 8px rgba(241, 245, 249, 0.4);
  }

  .relay-off {
    background: var(--bg-primary);
    border-color: var(--border-subtle);
  }

  .sensor-readings {
    display: flex;
    gap: var(--space-md);
  }

  .sensor-item {
    display: flex;
    align-items: baseline;
    gap: var(--space-xs);
  }

  .sensor-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 500;
  }

  .sensor-value {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  .job-indicators {
    display: flex;
    gap: var(--space-md);
  }

  .job-item {
    display: flex;
    align-items: baseline;
    gap: var(--space-xs);
  }

  .job-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 500;
  }

  .job-count {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: 600;
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    min-width: 20px;
    text-align: center;
  }

  .status-divider {
    width: 1px;
    height: 24px;
    background: var(--border-subtle);
  }

  .status-spacer {
    flex: 1;
  }

  .emergency-stop-btn {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
    border: 1px solid rgba(220, 38, 38, 0.4) !important;
    font-weight: 600 !important;
    font-size: var(--text-xs) !important;
    padding: var(--space-xs) var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.025em;
    white-space: nowrap;
  }

  .emergency-stop-btn:active {
    background: #b91c1c !important;
    opacity: 0.9;
  }

  .emergency-stop-btn:hover {
    background: #b91c1c !important;
    border-color: rgba(220, 38, 38, 0.6) !important;
  }

  .emergency-icon {
    width: 14px;
    height: 14px;
  }

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

  .compact-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    height: 100%;
  }

  .section-title-compact {
    font-size: var(--text-base) !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
  }

  /* Nutrient Pumps - Compact Grid */
  .nute-pumps-compact-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
    margin-bottom: var(--space-md);
  }

  :global(.pump-btn-compact) {
    padding: var(--space-xs) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease !important;
    min-height: 60px !important;
    height: 60px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .pump-content-compact {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    width: 100%;
  }

  .pump-id-compact {
    font-size: 0.625rem;
    font-weight: 500;
    color: var(--text-muted);
  }

  .pump-name-compact {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-primary);
    text-align: center;
  }

  .pump-status-compact {
    font-size: 0.625rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .dosing-amount-selector {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding-top: var(--space-sm);
    border-top: 1px solid var(--border-subtle);
  }

  .dosing-slider-compact {
    flex: 1;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .dosing-slider-compact::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: var(--accent-steel);
    border: 2px solid var(--border-emphasis);
    border-radius: 50%;
    cursor: pointer;
  }

  .dosing-slider-compact::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: var(--accent-steel);
    border: 2px solid var(--border-emphasis);
    border-radius: 50%;
    cursor: pointer;
  }

  .dosing-value-compact {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    min-width: 60px;
    text-align: right;
  }

  /* Relay Compact Grid */
  .relay-compact-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
  }

  .tank-status-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--text-primary) !important;
    font-size: var(--text-lg) !important;
    font-weight: 600 !important;
  }

  .section-icon {
    color: var(--accent-steel);
  }

  /* Compact Tank Grid */
  .tank-compact-grid {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .tank-compact-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: var(--space-md);
    transition: all 0.2s ease;
  }

  .tank-compact-card:hover {
    border-color: var(--border-emphasis);
    background: var(--bg-card-hover);
  }

  .tank-compact-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
  }

  .tank-compact-info {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .tank-compact-label {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .tank-compact-volume {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  :global(.tank-progress) {
    margin-bottom: var(--space-md);
    height: 6px !important;
    background: var(--bg-tertiary) !important;
  }

  .tank-compact-controls {
    display: flex;
    gap: var(--space-sm);
  }

  :global(.tank-compact-btn) {
    flex: 1;
    font-size: var(--text-xs) !important;
    padding: var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  :global(.tank-compact-btn:hover) {
    background: var(--accent-steel) !important;
    border-color: var(--border-emphasis) !important;
  }

  :global(.tank-compact-btn:active) {
    opacity: 0.85;
  }

  /* Relay Control */
  .relay-control-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  .relay-tank-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-md);
  }

  .relay-tank-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .tank-relay-header {
    font-weight: 600;
    color: var(--text-secondary);
    text-align: center;
    font-size: var(--text-xs);
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-sm);
    margin-bottom: var(--space-xs);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-subtle);
  }

  .tank-relays {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  :global(.relay-btn) {
    padding: var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease !important;
    min-height: 56px !important;
    height: 56px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: var(--bg-secondary) !important;
    color: var(--text-muted) !important;
  }

  :global(.relay-btn:active) {
    opacity: 0.85;
  }

  /* Unified Relay Styling - No Color Coding */
  :global(.relay-btn.relay-active) {
    background: var(--accent-steel) !important;
    border-color: var(--border-emphasis) !important;
    color: var(--text-primary) !important;
  }

  :global(.relay-btn.relay-inactive) {
    background: var(--bg-secondary) !important;
    border-color: var(--border-subtle) !important;
    color: var(--text-muted) !important;
  }

  :global(.relay-btn.relay-inactive:hover) {
    background: var(--bg-tertiary) !important;
    border-color: var(--border-emphasis) !important;
  }

  .relay-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--space-xs);
    text-align: center;
    width: 100%;
    height: 100%;
  }

  .relay-id {
    font-weight: 500;
    font-size: 0.625rem;
    margin-bottom: 2px;
    opacity: 0.7;
  }

  .relay-name {
    font-size: var(--text-xs);
    line-height: 1.2;
    font-weight: 600;
    margin-bottom: 2px;
    color: inherit;
  }

  .relay-status {
    font-size: 0.625rem;
    font-weight: 500;
    padding: 1px 6px;
    border-radius: var(--radius-sm);
    background: rgba(0, 0, 0, 0.2);
    color: inherit;
    letter-spacing: 0.05em;
  }

  /* Dosing Panel */
  .dosing-panel {
    display: flex;
    flex-direction: column;
  }

  .dosing-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    height: fit-content;
  }

  :global(.dosing-content) {
    display: flex !important;
    flex-direction: column !important;
    gap: var(--space-lg) !important;
    min-height: 320px !important;
    justify-content: space-between !important;
    padding: var(--space-lg) !important;
  }

  .dosing-controls {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
    align-items: center;
    flex: 1;
    justify-content: space-evenly;
    height: 100%;
  }

  .amount-display {
    display: flex;
    align-items: baseline;
    gap: var(--space-xs);
  }

  .amount-value {
    font-size: 2rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .amount-unit {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-muted);
  }

  .slider-container {
    position: relative;
    width: 100%;
    margin: 0 0 var(--space-xl) 0;
  }

  .slider-markers {
    position: absolute;
    top: 10px;
    left: 0;
    right: 0;
    height: 8px;
    pointer-events: none;
  }

  .marker {
    position: absolute;
    transform: translateX(-50%);
    height: 100%;
  }

  .marker-line {
    width: 1px;
    height: 6px;
    background: var(--border-emphasis);
    border-radius: 1px;
  }

  .marker-label {
    position: absolute;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    font-size: var(--text-xs);
    color: var(--text-muted);
    text-align: center;
    white-space: nowrap;
    font-weight: 500;
  }

  .dosing-slider {
    width: calc(100% + 20px);
    margin-left: -10px;
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .dosing-slider::-webkit-slider-thumb {
    appearance: none;
    width: 20px;
    height: 20px;
    background: var(--accent-steel);
    border: 2px solid var(--border-emphasis);
    border-radius: 50%;
    cursor: pointer;
  }

  .dosing-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: var(--accent-steel);
    border: 2px solid var(--border-emphasis);
    border-radius: 50%;
    cursor: pointer;
  }

  .preset-controls {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .preset-row {
    display: flex;
    gap: var(--space-sm);
    justify-content: center;
  }

  .preset-btn {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-secondary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
    padding: var(--space-sm) var(--space-md) !important;
    transition: all 0.2s ease !important;
  }

  .preset-btn:active {
    opacity: 0.85;
  }

  .preset-btn:hover {
    background: var(--accent-steel) !important;
    border-color: var(--border-emphasis) !important;
    color: var(--text-primary) !important;
  }

  /* Pump Grid */
  .pump-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-md);
  }

  :global(.pump-btn) {
    padding: var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease !important;
    min-height: 80px !important;
    height: auto !important;
  }

  :global(.pump-btn:active) {
    opacity: 0.85;
  }

  /* Unified Pump Styling - No Nutrient Color Coding */
  :global(.pump-idle) {
    background: var(--bg-secondary) !important;
    border-color: var(--border-subtle) !important;
    color: var(--text-primary) !important;
  }

  :global(.pump-idle:hover) {
    background: var(--bg-tertiary) !important;
    border-color: var(--border-emphasis) !important;
  }

  :global(.pump-active) {
    background: var(--status-warning) !important;
    border-color: var(--status-warning) !important;
    color: var(--bg-primary) !important;
  }

  .pump-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
    width: 100%;
    height: 100%;
  }

  .pump-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .pump-id {
    font-weight: 500;
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .stop-btn {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
    border: none !important;
    font-weight: 500 !important;
    font-size: var(--text-xs) !important;
    padding: var(--space-xs) var(--space-sm) !important;
    transition: all 0.2s ease !important;
  }

  .stop-btn:active {
    opacity: 0.85;
  }

  .pump-nutrient {
    font-size: var(--text-sm);
    font-weight: 600;
    text-align: center;
    line-height: 1.2;
    flex: 1;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pump-progress {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .progress-bar {
    height: 4px !important;
    background: rgba(0, 0, 0, 0.3) !important;
  }

  .progress-text {
    font-size: var(--text-xs);
    text-align: center;
    font-weight: 500;
  }

  .pump-amount {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-muted);
    text-align: center;
  }

  /* Active Operations Alert */
  .active-operations-alert {
    background: rgba(217, 119, 6, 0.1) !important;
    border: 1px solid var(--status-warning) !important;
    border-radius: var(--radius-md) !important;
  }

  .alert-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .alert-title {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    font-weight: 600;
    color: var(--status-warning);
  }

  .alert-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-sm);
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
  }

  .alert-stop-btn {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
    border: none !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
  }

  .alert-stop-btn:active {
    opacity: 0.85;
  }

  /* Monitoring Panel */
  .monitoring-panel {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .monitoring-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  .flow-monitors {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .flow-meter {
    padding: var(--space-md);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
    background: var(--bg-secondary);
  }

  .flow-active {
    border-color: var(--accent-steel);
  }

  .flow-development {
    border-color: var(--status-development);
    opacity: 0.7;
  }

  .meter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
  }

  .meter-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .meter-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--status-development);
    font-size: var(--text-xs);
  }

  .meter-readings {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .flow-rate {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
  }

  .total-flow {
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .unit {
    font-size: var(--text-sm);
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Sensor Grid */
  .sensor-grid {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .sensor-card {
    padding: var(--space-md);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
    background: var(--bg-secondary);
  }

  .sensor-development {
    border-color: var(--status-development);
    opacity: 0.7;
  }

  .sensor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
  }

  .sensor-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .sensor-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--status-development);
    font-size: var(--text-xs);
  }

  /* Activity Log */
  .log-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .clear-logs-btn {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-muted) !important;
    font-size: var(--text-xs) !important;
  }

  .clear-logs-btn:hover {
    background: var(--bg-tertiary) !important;
    border-color: var(--border-emphasis) !important;
  }

  .log-container {
    max-height: 300px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .log-entry {
    padding: var(--space-sm) var(--space-md);
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    border-left: 2px solid var(--accent-steel);
  }

  .log-time {
    font-size: var(--text-xs);
    color: var(--text-muted);
    margin-bottom: var(--space-xs);
    font-variant-numeric: tabular-nums;
  }

  .log-message {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .log-empty {
    text-align: center;
    color: var(--text-muted);
    font-style: italic;
    padding: var(--space-xl);
  }

  /* Status Badge Classes */
  .status-connected {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-error {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-active {
    background: var(--status-warning) !important;
    color: var(--bg-primary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-idle {
    background: var(--bg-tertiary) !important;
    color: var(--text-muted) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-filling {
    background: var(--status-info) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-mixing {
    background: var(--status-warning) !important;
    color: var(--bg-primary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-sending {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-ready {
    background: var(--accent-steel) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-development {
    background: var(--status-development) !important;
    color: var(--bg-primary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  .status-operational {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  /* Responsive Design */
  @media (max-width: 1400px) {
    .dashboard-grid {
      grid-template-columns: 1fr 340px 280px;
    }
  }

  @media (max-width: 1200px) {
    .dashboard-grid {
      grid-template-columns: 1fr 320px;
      gap: var(--space-lg);
    }

    .monitoring-panel {
      grid-column: 1 / -1;
      grid-row: 3;
    }

    .relay-tank-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .dashboard-grid {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
      padding: 0 var(--space-md);
    }

    .dashboard-header {
      padding: var(--space-md);
    }

    .status-bar {
      flex-direction: column;
      gap: var(--space-md);
      text-align: center;
    }

    .tank-overview {
      grid-template-columns: 1fr;
      gap: var(--space-md);
    }

    .relay-tank-grid {
      grid-template-columns: 1fr;
    }

    .pump-grid {
      grid-template-columns: 1fr;
    }

    .tank-controls {
      flex-direction: column;
      gap: var(--space-sm);
    }

    .preset-controls {
      flex-direction: column;
      width: 100%;
    }

    .emergency-stop-btn {
      width: 100% !important;
      justify-content: center !important;
    }
  }

  /* Touch Optimizations */
  @media (pointer: coarse) {
    .tank-action-btn,
    .relay-btn,
    .pump-btn,
    .preset-btn {
      min-height: 44px !important;
      touch-action: manipulation !important;
    }

    .dosing-slider {
      height: 10px !important;
    }

    .dosing-slider::-webkit-slider-thumb {
      width: 28px !important;
      height: 28px !important;
    }

    .dosing-slider::-moz-range-thumb {
      width: 28px !important;
      height: 28px !important;
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