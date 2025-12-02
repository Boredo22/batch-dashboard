<script>
  import { onMount, onDestroy } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Progress } from '$lib/components/ui/progress';
  import { Alert, AlertDescription } from '$lib/components/ui/alert';
  import { Separator } from '$lib/components/ui/separator';

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
  let systemStatus = $state('Connected');
  let isProcessing = $state(false);

  // EC/pH monitoring state
  let ecPhMonitoring = $state(false);
  let ecPhData = $state({ ph: null, ec: null, timestamp: null });

  // Collapsible section states using $state
  let expandedSections = $state({
    tanks: true,
    relays: true,
    pumps: true,
    monitoring: true,
    logs: true
  });

  let statusInterval;

  // Tank configuration
  const TANK_CONFIG = {
    1: { fillRelay: 1, mixRelays: [4, 7], sendRelay: 10, pumps: [1, 2, 3], color: 'blue', label: 'Veg' },
    2: { fillRelay: 2, mixRelays: [5, 8], sendRelay: 11, pumps: [4, 5, 6], color: 'green', label: 'Bloom' },
    3: { fillRelay: 3, mixRelays: [6, 9], sendRelay: 12, pumps: [7, 8], color: 'yellow', label: 'Flush' }
  };

  // Derived values using $derived
  let activePumps = $derived(pumps.filter(pump => pump.status === 'dispensing'));
  let anyRelayActive = $derived(relays.some(relay => relay.status === 'on'));
  let activeTankCount = $derived(
    Object.values(tankStatus).filter(t => t.status !== 'idle').length
  );
  let activeRelayCount = $derived(relays.filter(r => r.status === 'on').length);

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

  // API Functions
  async function fetchSystemStatus() {
    try {
      const response = await fetch('/api/hardware/status');
      if (response.ok) {
        const data = await response.json();

        if (data.relays) {
          relays = relays.map(relay => {
            const apiRelay = data.relays.find(r => r.id === relay.id);
            return apiRelay ? { ...relay, status: apiRelay.state ? 'on' : 'off' } : relay;
          });
        }

        if (data.pumps) {
          pumps = pumps.map(pump => {
            const apiPump = data.pumps.find(p => p.id === pump.id);
            if (apiPump) {
              return {
                ...pump,
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

        systemStatus = 'Connected';
      } else {
        systemStatus = 'Error';
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
      systemStatus = 'Disconnected';
    }
  }

  // EC/pH Monitoring Functions
  async function startEcPhMonitoring() {
    try {
      const response = await fetch('/api/ecph/start', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        ecPhMonitoring = true;
        addLog('EC/pH monitoring started');
      } else {
        const error = await response.json();
        addLog(`EC/pH monitoring error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error starting EC/pH monitoring:', error);
      addLog(`EC/pH monitoring error: ${error.message}`);
    }
  }

  async function stopEcPhMonitoring() {
    try {
      const response = await fetch('/api/ecph/stop', {
        method: 'POST'
      });

      if (response.ok) {
        ecPhMonitoring = false;
        addLog('EC/pH monitoring stopped');
      }
    } catch (error) {
      console.error('Error stopping EC/pH monitoring:', error);
    }
  }

  async function fetchEcPhReadings() {
    if (!ecPhMonitoring) return;

    try {
      const response = await fetch('/api/sensors/ecph/read');

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          ecPhData = {
            ph: result.data.ph,
            ec: result.data.ec,
            timestamp: result.data.timestamp
          };
        }
      }
    } catch (error) {
      console.error('Error fetching EC/pH readings:', error);
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

  // Relay Set Control - for tank operations
  async function controlRelaySet(relayIds, action, operationName) {
    if (isProcessing) return;
    isProcessing = true;

    try {
      addLog(`${operationName} - activating relays ${relayIds.join(', ')}`);

      for (const relayId of relayIds) {
        await controlRelay(relayId, action);
      }

      addLog(`${operationName} - relays ${relayIds.join(', ')} are now ${action.toUpperCase()}`);
    } catch (error) {
      addLog(`${operationName} error: ${error.message}`);
    } finally {
      isProcessing = false;
    }
  }

  // Tank operation helpers
  async function toggleTankFill(tankId) {
    const config = TANK_CONFIG[tankId];
    const fillRelay = relays.find(r => r.id === config.fillRelay);
    const newAction = fillRelay.status === 'on' ? 'off' : 'on';
    await controlRelaySet([config.fillRelay], newAction, `Tank ${tankId} Fill`);
  }

  async function toggleTankMix(tankId) {
    const config = TANK_CONFIG[tankId];
    const firstMixRelay = relays.find(r => r.id === config.mixRelays[0]);
    const newAction = firstMixRelay.status === 'on' ? 'off' : 'on';
    await controlRelaySet(config.mixRelays, newAction, `Tank ${tankId} Mix`);
  }

  async function toggleTankSend(tankId) {
    const config = TANK_CONFIG[tankId];
    const sendRelay = relays.find(r => r.id === config.sendRelay);
    const newAction = sendRelay.status === 'on' ? 'off' : 'on';
    await controlRelaySet([config.sendRelay], newAction, `Tank ${tankId} Send`);
  }

  // Check if relay set is active
  function areRelaysActive(relayIds) {
    return relayIds.every(id => {
      const relay = relays.find(r => r.id === id);
      return relay && relay.status === 'on';
    });
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

  function toggleSection(section) {
    expandedSections[section] = !expandedSections[section];
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

  // Lifecycle with $effect for status updates
  onMount(async () => {
    addLog('Growers dashboard started');
    await fetchPumpConfig();
    await fetchSystemStatus();

    // Start EC/pH monitoring automatically
    await startEcPhMonitoring();
  });

  $effect(() => {
    const interval = setInterval(fetchSystemStatus, 2000);
    return () => clearInterval(interval);
  });

  // Separate effect for EC/pH readings polling
  $effect(() => {
    const interval = setInterval(fetchEcPhReadings, 3000);
    return () => clearInterval(interval);
  });

  onDestroy(() => {
    if (statusInterval) clearInterval(statusInterval);
    // Stop monitoring when component is destroyed
    stopEcPhMonitoring();
  });
</script>

<div class="dashboard-container">
  <!-- Status Bar -->
  <div class="status-bar">
    <div class="status-group">
      <div class="status-label">SYSTEM</div>
      <div class="flex items-center gap-2">
        <div class="status-dot {systemStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'}"></div>
        <span class="text-sm font-medium text-slate-200">{systemStatus}</span>
      </div>
    </div>

    <div class="status-divider"></div>

    <div class="status-group">
      <div class="status-label">RELAYS</div>
      <div class="relay-dots">
        {#each relays as relay}
          <div class="relay-dot {relay.status === 'on' ? 'bg-purple-500 shadow-[0_0_12px_rgba(139,92,246,0.7)]' : 'bg-slate-800'}"
               title="{relay.name}: {relay.status.toUpperCase()}">
          </div>
        {/each}
      </div>
    </div>

    <div class="status-divider"></div>

    <div class="status-group flex-1">
      <div class="status-label">ACTIVE</div>
      <div class="flex gap-4">
        <div class="flex items-baseline gap-1">
          <span class="text-xs text-slate-400">Pumps:</span>
          <span class="text-sm font-bold text-slate-200">{activePumps.length}</span>
        </div>
        <div class="flex items-baseline gap-1">
          <span class="text-xs text-slate-400">Flow:</span>
          <span class="text-sm font-bold text-slate-200">{flowMeters.filter(m => m.status !== 'idle' && m.status !== 'development').length}</span>
        </div>
      </div>
    </div>

    <Button
      variant="destructive"
      class="emergency-btn"
      onclick={emergencyStop}
    >
      <svg class="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" />
        <rect x="9" y="9" width="6" height="6" fill="currentColor" stroke="none"/>
      </svg>
      STOP ALL
    </Button>
  </div>

  <!-- Main Grid Layout -->
  <div class="main-grid">
    
    <!-- Left Column: Tanks & Pumps (Controls) -->
    <div class="grid-column">
      <!-- Tanks Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('tanks')}
              aria-expanded={expandedSections.tanks}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">Tank Operations</span>
                <Badge variant="secondary" class="section-count-badge">{activeTankCount}</Badge>
              </div>
              <svg
                class="chevron-icon {expandedSections.tanks ? 'chevron-expanded' : ''}"
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
        {#if expandedSections.tanks}
        <CardContent>
          <div class="flex flex-col gap-4">
            {#each [1, 2, 3] as tankId}
              {@const config = TANK_CONFIG[tankId]}
              {@const status = tankStatus[tankId]}
              {@const fillActive = areRelaysActive([config.fillRelay])}
              {@const mixActive = areRelaysActive(config.mixRelays)}
              {@const sendActive = areRelaysActive([config.sendRelay])}
              
              <div class="tank-row tank-theme-{config.color}">
                <div class="tank-info">
                  <div class="tank-icon">
                    <span class="text-lg font-bold">{tankId}</span>
                  </div>
                  <div class="flex flex-col">
                    <span class="tank-label">{config.label}</span>
                    <span class="tank-status-text">
                      {#if fillActive}Filling
                      {:else if mixActive}Mixing
                      {:else if sendActive}Sending
                      {:else}Idle{/if}
                    </span>
                  </div>
                </div>

                <div class="tank-controls">
                  <button 
                    class="control-btn {fillActive ? 'active' : ''}" 
                    onclick={() => toggleTankFill(tankId)}
                    disabled={isProcessing}
                  >
                    <span class="btn-label">Fill</span>
                    <div class="btn-indicator"></div>
                  </button>
                  
                  <button 
                    class="control-btn {mixActive ? 'active' : ''}" 
                    onclick={() => toggleTankMix(tankId)}
                    disabled={isProcessing}
                  >
                    <span class="btn-label">Mix</span>
                    <div class="btn-indicator"></div>
                  </button>
                  
                  <button 
                    class="control-btn {sendActive ? 'active' : ''}" 
                    onclick={() => toggleTankSend(tankId)}
                    disabled={isProcessing}
                  >
                    <span class="btn-label">Send</span>
                    <div class="btn-indicator"></div>
                  </button>
                </div>
              </div>
            {/each}
          </div>
        </CardContent>
        {/if}
      </Card>

      <!-- Pumps Card (Moved to Left) -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('pumps')}
              aria-expanded={expandedSections.pumps}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">Nutrient Pumps</span>
                <Badge variant="secondary" class="section-count-badge">{activePumps.length}</Badge>
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
          </div>
        </CardHeader>
        {#if expandedSections.pumps}
        <CardContent>
          <!-- Dosing Control -->
          <div class="mb-6 p-5 bg-gradient-to-br from-slate-900/60 to-slate-900/40 rounded-xl border border-purple-500/20 shadow-lg">
            <div class="flex justify-between items-end mb-4">
              <span class="text-xs font-bold text-purple-400 uppercase tracking-wider">Dosing Amount</span>
              <div class="text-3xl font-bold text-purple-400 font-mono tracking-tight">
                {dosingAmount}<span class="text-sm text-slate-500 ml-1 font-sans">ml</span>
              </div>
            </div>

            <input
              type="range"
              class="dosing-slider w-full h-2 mb-5"
              min="1"
              max="2000"
              value={dosingAmount}
              step="1"
              oninput={handleSliderInput}
            />

            <div class="flex gap-2 justify-between">
              {#each [25, 50, 100, 250, 500] as amount}
                <button
                  class="preset-btn px-3 py-2 text-xs font-bold rounded-lg transition-all"
                  class:active={dosingAmount === amount}
                  onclick={() => setDosingPreset(amount)}
                >
                  {amount}ml
                </button>
              {/each}
            </div>
          </div>

          <!-- Pump Grid -->
          <div class="grid grid-cols-2 gap-3">
            {#each pumps as pump}
              <button
                class="pump-card {pump.status === 'dispensing' ? 'active' : ''}"
                onclick={() => dispensePump(pump.id, dosingAmount)}
                disabled={pump.status === 'dispensing'}
              >
                <div class="flex justify-between items-start w-full mb-2">
                  <span class="text-xs font-mono font-bold text-purple-400/60">P{pump.id}</span>
                  {#if pump.status === 'dispensing'}
                    <span class="pump-status-badge">ACTIVE</span>
                  {/if}
                </div>
                <div class="text-base font-bold text-slate-100 text-center leading-snug mb-2">
                  {pump.name}
                </div>
                {#if pump.status === 'dispensing'}
                  <div class="w-full bg-slate-900/80 h-2 rounded-full overflow-hidden border border-green-500/30">
                    <div class="pump-progress-bar h-full transition-all duration-500" style="width: {pump.progress}%"></div>
                  </div>
                {:else}
                  <div class="text-xs text-slate-500 text-center font-medium">Tap to dispense</div>
                {/if}
              </button>
            {/each}
          </div>
        </CardContent>
        {/if}
      </Card>
    </div>

    <!-- Right Column: Monitoring & Relays & Logs -->
    <div class="grid-column">
      <!-- Monitoring Card -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('monitoring')}
              aria-expanded={expandedSections.monitoring}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">System Monitoring</span>
              </div>
              <svg
                class="chevron-icon {expandedSections.monitoring ? 'chevron-expanded' : ''}"
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
        {#if expandedSections.monitoring}
        <CardContent>
          <div class="grid grid-cols-2 gap-3">
            {#each flowMeters as meter}
              <div class="monitor-item {meter.status === 'development' ? 'opacity-60' : ''}">
                <div class="flex justify-between items-start mb-1">
                  <span class="text-xs font-medium text-slate-400 uppercase">{meter.name}</span>
                  {#if meter.status === 'development'}
                    <Badge variant="outline" class="text-[10px] h-4 px-1">DEV</Badge>
                  {/if}
                </div>
                <div class="text-xl font-mono font-semibold text-slate-200">
                  {meter.flow_rate} <span class="text-xs text-slate-500 font-sans">GPM</span>
                </div>
                <div class="text-xs text-slate-500 mt-1">
                  Total: {meter.total_gallons} gal
                </div>
              </div>
            {/each}
            
            <!-- Sensors -->
            <div class="monitor-item">
              <div class="flex justify-between items-start mb-1">
                <span class="text-xs font-medium text-slate-400 uppercase">pH Level</span>
                {#if ecPhMonitoring}
                  <Badge variant="outline" class="text-[10px] h-4 px-1 bg-green-500/10 text-green-400 border-green-500/30">LIVE</Badge>
                {:else}
                  <Badge variant="outline" class="text-[10px] h-4 px-1">OFF</Badge>
                {/if}
              </div>
              <div class="text-xl font-mono font-semibold text-slate-200">
                {ecPhData.ph !== null ? ecPhData.ph.toFixed(2) : '--'}
              </div>
            </div>

            <div class="monitor-item">
              <div class="flex justify-between items-start mb-1">
                <span class="text-xs font-medium text-slate-400 uppercase">EC Level</span>
                {#if ecPhMonitoring}
                  <Badge variant="outline" class="text-[10px] h-4 px-1 bg-green-500/10 text-green-400 border-green-500/30">LIVE</Badge>
                {:else}
                  <Badge variant="outline" class="text-[10px] h-4 px-1">OFF</Badge>
                {/if}
              </div>
              <div class="text-xl font-mono font-semibold text-slate-200">
                {ecPhData.ec !== null ? ecPhData.ec.toFixed(2) : '--'} <span class="text-xs text-slate-500 font-sans">mS/cm</span>
              </div>
            </div>
          </div>
        </CardContent>
        {/if}
      </Card>

      <!-- Other Relays (Moved to Right) -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="section-header-collapsible">
            <button
              class="section-toggle-btn"
              onclick={() => toggleSection('relays')}
              aria-expanded={expandedSections.relays}
            >
              <div class="flex items-center gap-2">
                <span class="section-title-text">Auxiliary Controls</span>
                <Badge variant="secondary" class="section-count-badge">{activeRelayCount}</Badge>
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
          <div class="grid grid-cols-2 gap-3">
            {#each [10, 11, 12, 13] as relayId}
              {@const relay = relays.find(r => r.id === relayId)}
              {#if relay}
                <button
                  class="aux-relay-btn {relay.status === 'on' ? 'active' : ''}"
                  onclick={() => toggleRelay(relay.id)}
                >
                  <div class="flex flex-col items-center gap-2 relative z-10">
                    <span class="text-sm font-bold">{relay.name}</span>
                    <div class="relay-status-indicator {relay.status === 'on' ? 'active' : ''}">
                      <span class="text-[10px] uppercase tracking-wider font-extrabold">
                        {relay.status === 'on' ? 'ACTIVE' : 'STANDBY'}
                      </span>
                    </div>
                  </div>
                </button>
              {/if}
            {/each}
          </div>
        </CardContent>
        {/if}
      </Card>

      <!-- Logs (Moved to Right) -->
      <Card class="dashboard-card">
        <CardHeader class="pb-3">
          <div class="flex justify-between items-center w-full">
            <div class="section-header-collapsible">
              <button
                class="section-toggle-btn"
                onclick={() => toggleSection('logs')}
                aria-expanded={expandedSections.logs}
              >
                <div class="flex items-center gap-2">
                  <span class="section-title-text">Activity Log</span>
                </div>
                <svg
                  class="chevron-icon {expandedSections.logs ? 'chevron-expanded' : ''}"
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
            <Button variant="ghost" size="sm" class="h-6 text-xs text-slate-500" onclick={clearLogs}>Clear</Button>
          </div>
        </CardHeader>
        {#if expandedSections.logs}
        <CardContent>
          <div class="h-32 overflow-y-auto pr-2 space-y-2 custom-scrollbar">
            {#each logs as log}
              <div class="log-entry">
                <span class="log-timestamp">{log.time}</span>
                <span class="log-message">{log.message}</span>
              </div>
            {/each}
            {#if logs.length === 0}
              <div class="text-center text-xs text-slate-600 py-8 italic">No recent activity</div>
            {/if}
          </div>
        </CardContent>
        {/if}
      </Card>
    </div>
  </div>
</div>

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

  /* Status Bar - Enhanced with gradient and better spacing */
  .status-bar {
    width: 100%;
    background: linear-gradient(135deg, #1a1f35 0%, #151929 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 0.75rem;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    box-shadow:
      0 4px 16px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(139, 92, 246, 0.1) inset;
    box-sizing: border-box;
    backdrop-filter: blur(10px);
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

  .relay-dots {
    display: flex;
    gap: 0.375rem;
    flex-wrap: wrap;
    max-width: 140px;
  }

  .relay-dot {
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 0.25rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
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
      grid-template-columns: 1.3fr 1fr;
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
  }

  .section-toggle-btn {
    width: 100%;
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

  /* Tank Rows - More prominent with better visual hierarchy */
  .tank-row {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(10, 15, 30, 0.9) 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 0.75rem;
    padding: 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1.25rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .tank-row:hover {
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    transform: translateY(-2px);
  }

  .tank-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .tank-icon {
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1e293b;
    color: #94a3b8;
    font-size: 1.5rem;
    font-weight: 800;
    border: 2px solid;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.3) inset;
  }

  .tank-theme-blue .tank-icon {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(168, 85, 247, 0.1));
    color: #a78bfa;
    border-color: rgba(139, 92, 246, 0.3);
  }
  .tank-theme-green .tank-icon {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(52, 211, 153, 0.1));
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.3);
  }
  .tank-theme-yellow .tank-icon {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(16, 185, 129, 0.1));
    color: #10b981;
    border-color: rgba(16, 185, 129, 0.3);
  }

  .tank-label {
    font-weight: 700;
    font-size: 1.125rem;
    color: #f1f5f9;
    letter-spacing: -0.025em;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }

  .tank-status-text {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.125rem;
  }

  .tank-controls {
    display: flex;
    gap: 0.75rem;
  }

  .control-btn {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1.5px solid rgba(51, 65, 85, 0.8);
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    min-width: 4.5rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
  }

  .control-btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0), rgba(139, 92, 246, 0.1));
    opacity: 0;
    transition: opacity 0.3s;
  }

  .control-btn:hover::before {
    opacity: 1;
  }

  .control-btn:hover {
    border-color: rgba(139, 92, 246, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
  }

  .control-btn.active {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    border-color: #a78bfa;
    color: white;
    box-shadow:
      0 0 20px rgba(139, 92, 246, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .tank-theme-green .control-btn.active {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border-color: #34d399;
    box-shadow:
      0 0 20px rgba(16, 185, 129, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }
  .tank-theme-yellow .control-btn.active {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border-color: #34d399;
    box-shadow:
      0 0 20px rgba(16, 185, 129, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .btn-label {
    font-size: 0.8125rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    z-index: 1;
  }

  .btn-indicator {
    width: 2rem;
    height: 0.25rem;
    border-radius: 9999px;
    background: rgba(51, 65, 85, 0.8);
    transition: all 0.3s;
    z-index: 1;
  }

  .control-btn.active .btn-indicator {
    background: rgba(255, 255, 255, 0.6);
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.4);
  }

  /* Monitor Items - Enhanced cards */
  .monitor-item {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(10, 15, 30, 0.9) 100%);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 0.75rem;
    padding: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .monitor-item:hover {
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
  }

  /* Pump Cards - More sophisticated design */
  .pump-card {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(10, 15, 30, 0.9) 100%);
    border: 1.5px solid rgba(139, 92, 246, 0.2);
    border-radius: 0.75rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 5.5rem;
    position: relative;
    overflow: hidden;
  }

  .pump-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0), rgba(139, 92, 246, 0.1));
    opacity: 0;
    transition: opacity 0.3s;
  }

  .pump-card:hover::before {
    opacity: 1;
  }

  .pump-card:hover {
    border-color: rgba(139, 92, 246, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.15);
  }

  .pump-card.active {
    border-color: #10b981;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
    box-shadow:
      0 0 24px rgba(16, 185, 129, 0.3),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .pump-card.active::before {
    opacity: 1;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
  }

  /* Aux Relay Buttons - Enhanced */
  .aux-relay-btn {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(10, 15, 30, 0.9) 100%);
    border: 1.5px solid rgba(139, 92, 246, 0.2);
    border-radius: 0.75rem;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  .aux-relay-btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0), rgba(139, 92, 246, 0.1));
    opacity: 0;
    transition: opacity 0.3s;
  }

  .aux-relay-btn:hover::before {
    opacity: 1;
  }

  .aux-relay-btn:hover {
    border-color: rgba(139, 92, 246, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.15);
  }

  .aux-relay-btn.active {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    border-color: #a78bfa;
    color: white;
    box-shadow:
      0 0 24px rgba(139, 92, 246, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .aux-relay-btn.active::before {
    opacity: 0;
  }

  /* Custom Scrollbar - Enhanced */
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }

  .custom-scrollbar::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 3px;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: linear-gradient(to bottom, #8b5cf6, #7c3aed);
    border-radius: 3px;
    transition: background 0.3s;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(to bottom, #a78bfa, #8b5cf6);
  }

  /* Badge styling overrides */
  :global(.section-count-badge) {
    background: rgba(139, 92, 246, 0.15) !important;
    color: #a78bfa !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
  }

  /* Emergency button enhancement */
  :global(.emergency-btn) {
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
  }

  :global(.emergency-btn:hover) {
    box-shadow: 0 0 30px rgba(239, 68, 68, 0.5) !important;
    transform: scale(1.05) !important;
  }

  /* Animation for active states */
  @keyframes pulse-glow {
    0%, 100% {
      box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }
    50% {
      box-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
    }
  }

  .pump-card.active {
    animation: pulse-glow 2s ease-in-out infinite;
  }

  /* Dosing Slider - Custom styled range input */
  .dosing-slider {
    -webkit-appearance: none;
    appearance: none;
    background: linear-gradient(to right, rgba(139, 92, 246, 0.3), rgba(139, 92, 246, 0.1));
    border-radius: 9999px;
    outline: none;
    cursor: pointer;
    border: 1px solid rgba(139, 92, 246, 0.2);
  }

  .dosing-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1.25rem;
    height: 1.25rem;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow:
      0 0 0 3px rgba(139, 92, 246, 0.2),
      0 4px 8px rgba(0, 0, 0, 0.3);
  }

  .dosing-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow:
      0 0 0 5px rgba(139, 92, 246, 0.3),
      0 6px 12px rgba(0, 0, 0, 0.4);
  }

  .dosing-slider::-webkit-slider-thumb:active {
    transform: scale(1.05);
  }

  .dosing-slider::-moz-range-thumb {
    width: 1.25rem;
    height: 1.25rem;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow:
      0 0 0 3px rgba(139, 92, 246, 0.2),
      0 4px 8px rgba(0, 0, 0, 0.3);
  }

  .dosing-slider::-moz-range-thumb:hover {
    transform: scale(1.15);
    box-shadow:
      0 0 0 5px rgba(139, 92, 246, 0.3),
      0 6px 12px rgba(0, 0, 0, 0.4);
  }

  /* Preset Buttons */
  .preset-btn {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(139, 92, 246, 0.2);
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    position: relative;
    overflow: hidden;
  }

  .preset-btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05));
    opacity: 0;
    transition: opacity 0.3s;
  }

  .preset-btn:hover {
    border-color: rgba(139, 92, 246, 0.4);
    color: #e2e8f0;
    transform: translateY(-1px);
  }

  .preset-btn:hover::before {
    opacity: 1;
  }

  .preset-btn.active {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border-color: #a78bfa;
    color: white;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
  }

  .preset-btn.active::before {
    opacity: 0;
  }

  /* Pump Status Badge */
  .pump-status-badge {
    font-size: 0.625rem;
    font-weight: 800;
    color: #10b981;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 0.125rem 0.5rem;
    border-radius: 0.25rem;
    letter-spacing: 0.05em;
    animation: pulse-badge 1.5s ease-in-out infinite;
  }

  @keyframes pulse-badge {
    0%, 100% {
      opacity: 1;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);
    }
    50% {
      opacity: 0.8;
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.5);
    }
  }

  /* Pump Progress Bar */
  .pump-progress-bar {
    background: linear-gradient(90deg, #10b981, #34d399);
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.5);
    animation: shimmer 2s ease-in-out infinite;
  }

  @keyframes shimmer {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.85;
    }
  }

  /* Relay Status Indicator */
  .relay-status-indicator {
    padding: 0.25rem 0.75rem;
    border-radius: 0.375rem;
    background: rgba(71, 85, 105, 0.4);
    border: 1px solid rgba(100, 116, 139, 0.3);
    color: #94a3b8;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .relay-status-indicator.active {
    background: rgba(168, 85, 247, 0.2);
    border-color: rgba(168, 85, 247, 0.4);
    color: #c4b5fd;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.3);
  }

  /* Log Entries */
  .log-entry {
    display: flex;
    gap: 0.75rem;
    padding: 0.625rem 0.75rem;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.6), rgba(10, 15, 30, 0.7));
    border-left: 2px solid rgba(139, 92, 246, 0.3);
    border-radius: 0.375rem;
    transition: all 0.2s;
    font-size: 0.75rem;
  }

  .log-entry:hover {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(10, 15, 30, 0.9));
    border-left-color: rgba(139, 92, 246, 0.5);
    transform: translateX(2px);
  }

  .log-timestamp {
    font-family: 'Courier New', monospace;
    font-weight: 600;
    color: #8b5cf6;
    min-width: 4.5rem;
    flex-shrink: 0;
  }

  .log-message {
    color: #cbd5e1;
    line-height: 1.4;
    font-weight: 500;
  }

  /* Responsive adjustments */
  @media (max-width: 767px) {
    .dashboard-container {
      padding: 0.75rem;
      gap: 1rem;
    }

    .status-bar {
      flex-wrap: wrap;
      gap: 1rem;
      padding: 1rem;
    }

    .tank-row {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;
    }

    .tank-info {
      justify-content: center;
    }

    .tank-controls {
      width: 100%;
      justify-content: space-evenly;
    }

    .control-btn {
      flex: 1;
      min-width: 0;
    }
  }

  @media (max-width: 480px) {
    .section-title-text {
      font-size: 1rem;
    }

    .tank-icon {
      width: 3rem;
      height: 3rem;
      font-size: 1.25rem;
    }

    .tank-label {
      font-size: 1rem;
    }

    .pump-card {
      min-height: 5rem;
      padding: 0.75rem;
    }
  }
</style>