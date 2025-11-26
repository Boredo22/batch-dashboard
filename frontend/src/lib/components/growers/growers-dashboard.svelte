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
  });

  $effect(() => {
    const interval = setInterval(fetchSystemStatus, 2000);
    return () => clearInterval(interval);
  });

  onDestroy(() => {
    if (statusInterval) clearInterval(statusInterval);
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
          <div class="relay-dot {relay.status === 'on' ? 'bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.6)]' : 'bg-slate-700'}"
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
          <div class="mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-800">
            <div class="flex justify-between items-end mb-4">
              <span class="text-sm font-medium text-slate-400">Dosing Amount</span>
              <div class="text-2xl font-bold text-blue-400">{dosingAmount}<span class="text-sm text-slate-500 ml-1">ml</span></div>
            </div>
            
            <input
              type="range"
              class="w-full h-3 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500 mb-4"
              min="1"
              max="2000"
              value={dosingAmount}
              step="1"
              oninput={handleSliderInput}
            />
            
            <div class="flex gap-2 justify-between">
              {#each [25, 50, 100, 250, 500] as amount}
                <button 
                  class="px-2 py-1 text-xs font-medium rounded bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition-colors"
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
                <div class="flex justify-between items-start w-full mb-1">
                  <span class="text-xs font-mono text-slate-500">P{pump.id}</span>
                  {#if pump.status === 'dispensing'}
                    <span class="text-xs font-bold text-amber-400 animate-pulse">RUNNING</span>
                  {/if}
                </div>
                <div class="text-sm font-semibold text-slate-200 text-center leading-tight mb-2">
                  {pump.name}
                </div>
                {#if pump.status === 'dispensing'}
                  <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-amber-500 h-full transition-all duration-500" style="width: {pump.progress}%"></div>
                  </div>
                {:else}
                  <div class="text-xs text-slate-500 text-center">Tap to dose</div>
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
            <div class="monitor-item opacity-60">
              <div class="flex justify-between items-start mb-1">
                <span class="text-xs font-medium text-slate-400 uppercase">pH Level</span>
                <Badge variant="outline" class="text-[10px] h-4 px-1">DEV</Badge>
              </div>
              <div class="text-xl font-mono font-semibold text-slate-200">--</div>
            </div>
            
            <div class="monitor-item opacity-60">
              <div class="flex justify-between items-start mb-1">
                <span class="text-xs font-medium text-slate-400 uppercase">EC Level</span>
                <Badge variant="outline" class="text-[10px] h-4 px-1">DEV</Badge>
              </div>
              <div class="text-xl font-mono font-semibold text-slate-200">--</div>
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
                  <div class="flex flex-col items-center gap-1">
                    <span class="text-sm font-medium">{relay.name}</span>
                    <span class="text-[10px] uppercase tracking-wider {relay.status === 'on' ? 'text-blue-200' : 'text-slate-500'}">
                      {relay.status === 'on' ? 'ACTIVE' : 'OFF'}
                    </span>
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
              <div class="text-xs p-2 rounded bg-slate-900/50 border-l-2 border-slate-600">
                <span class="text-slate-500 mr-2 font-mono">{log.time}</span>
                <span class="text-slate-300">{log.message}</span>
              </div>
            {/each}
            {#if logs.length === 0}
              <div class="text-center text-xs text-slate-600 py-4 italic">No recent activity</div>
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
    background-color: #0f172a;
    color: #e2e8f0;
  }

  .dashboard-container {
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    padding: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-sizing: border-box;
  }

  /* Status Bar */
  .status-bar {
    width: 100%;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    box-sizing: border-box;
  }

  .status-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .status-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.05em;
  }

  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 9999px;
  }

  .status-divider {
    width: 1px;
    height: 2rem;
    background: #334155;
  }

  .relay-dots {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
    max-width: 120px;
  }

  .relay-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 0.125rem;
    transition: all 0.2s;
  }

  /* Main Grid */
  .main-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    width: 100%;
  }

  @media (min-width: 768px) {
    .main-grid {
      grid-template-columns: 1.2fr 1fr;
    }
  }

  .grid-column {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Cards */
  :global(.dashboard-card) {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
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
  }

  .section-title-text {
    font-size: 1rem;
    font-weight: 600;
  }

  .chevron-icon {
    color: #64748b;
    transition: transform 0.2s;
  }

  .chevron-expanded {
    transform: rotate(180deg);
  }

  /* Tank Rows */
  .tank-row {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  .tank-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .tank-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1e293b;
    color: #94a3b8;
  }

  .tank-theme-blue .tank-icon { background: rgba(59, 130, 246, 0.1); color: #60a5fa; }
  .tank-theme-green .tank-icon { background: rgba(34, 197, 94, 0.1); color: #4ade80; }
  .tank-theme-yellow .tank-icon { background: rgba(234, 179, 8, 0.1); color: #facc15; }

  .tank-label {
    font-weight: 600;
    font-size: 0.875rem;
    color: #f1f5f9;
  }

  .tank-status-text {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
  }

  .tank-controls {
    display: flex;
    gap: 0.5rem;
  }

  .control-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.25rem;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    min-width: 4rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .control-btn:hover {
    background: #334155;
  }

  .control-btn.active {
    background: #3b82f6;
    border-color: #2563eb;
    color: white;
  }

  .tank-theme-green .control-btn.active { background: #22c55e; border-color: #16a34a; }
  .tank-theme-yellow .control-btn.active { background: #eab308; border-color: #ca8a04; color: #0f172a; }

  .btn-label {
    font-size: 0.75rem;
    font-weight: 600;
  }

  .btn-indicator {
    width: 1.5rem;
    height: 0.25rem;
    border-radius: 9999px;
    background: #334155;
  }

  .control-btn.active .btn-indicator {
    background: rgba(255, 255, 255, 0.5);
  }
  
  .tank-theme-yellow .control-btn.active .btn-indicator {
    background: rgba(0, 0, 0, 0.3);
  }

  /* Monitor Items */
  .monitor-item {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.75rem;
  }

  /* Pump Cards */
  .pump-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transition: all 0.2s;
    min-height: 5rem;
  }

  .pump-card:hover {
    border-color: #475569;
    background: #1e293b;
  }

  .pump-card.active {
    border-color: #d97706;
    background: rgba(217, 119, 6, 0.1);
  }

  /* Aux Relay Buttons */
  .aux-relay-btn {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .aux-relay-btn:hover {
    background: #1e293b;
  }

  .aux-relay-btn.active {
    background: #1e3a8a;
    border-color: #3b82f6;
    color: #bfdbfe;
  }

  /* Custom Scrollbar */
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  
  .custom-scrollbar::-webkit-scrollbar-track {
    background: #0f172a; 
  }
  
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #334155; 
    border-radius: 2px;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #475569; 
  }
</style>