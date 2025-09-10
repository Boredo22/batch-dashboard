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

  let statusInterval;

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
    await fetchPumpConfig();
    await fetchSystemStatus();
    statusInterval = setInterval(fetchSystemStatus, 2000);
  });

  onDestroy(() => {
    if (statusInterval) clearInterval(statusInterval);
  });
</script>

<!-- System Status Header -->
<div class="scaled-dashboard">
<div class="dashboard-header">
  <div class="status-bar">
    <div class="system-info">
      <div class="dashboard-title">Growers Dashboard</div>
      <div class="system-health">
        <Badge class={systemStatus === 'Connected' ? 'status-connected' : 'status-error'}>
          {systemStatus}
        </Badge>
        {#if anyRelayActive}
          <Badge class="status-active">
            ACTIVE OPERATIONS
          </Badge>
        {/if}
      </div>
    </div>
    
    <Button 
      class="emergency-stop-btn"
      onclick={emergencyStop}
      size="lg"
    >
      <svg class="emergency-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" fill="currentColor"/>
        <rect x="9" y="9" width="6" height="6" fill="white"/>
      </svg>
      EMERGENCY STOP
    </Button>
  </div>
</div>

<!-- Main Dashboard Grid -->
<div class="dashboard-grid">
  
  <!-- Tank Operations Panel -->
  <div class="operations-panel">
    
    <!-- Tank Visual Status -->
    <Card class="tank-status-card">
      <CardHeader>
        <CardTitle class="section-title">
          <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="6" width="20" height="12" rx="2"/>
            <path d="m2 12 20 0"/>
          </svg>
          Tank Status Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="tank-overview">
          {#each [1, 2, 3] as tankId}
            {@const config = TANK_CONFIG[tankId]}
            {@const status = tankStatus[tankId]}
            {@const tankInfo = getTankIcon(tankId)}
            {@const statusBadge = getTankStatusBadge(status.status)}
            
            <div class="tank-visual-card tank-{config.color}">
              <div class="tank-header">
                <div class="tank-number">Tank {tankId}</div>
                <Badge class={statusBadge.class}>{statusBadge.text}</Badge>
              </div>
              
              <div class="tank-visual">
                <div class="tank-container">
                  <div 
                    class="tank-fill"
                    style="height: {Math.max(status.volume / 100 * 100, 5)}%"
                  ></div>
                  <div class="tank-level">{status.volume} gal</div>
                </div>
              </div>
              
              <div class="tank-controls">
                <Button
                  class="tank-action-btn fill-btn"
                  onclick={() => fillTank(tankId)}
                  disabled={isProcessing}
                  size="sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M7 16.5V19a3 3 0 0 0 3 3h4a3 3 0 0 0 3-3v-2.5"/>
                    <path d="M8 8s0-2 2.5-4.5S15 1 15 1s3 2 3 7c0 1.657-.895 3-2 3s-2-1.343-2-3c0-2.5-1.5-4-2-4s-2 1.5-2 4"/>
                  </svg>
                  Fill
                </Button>
                
                <Button
                  class="tank-action-btn mix-btn"
                  onclick={() => mixTank(tankId)}
                  disabled={isProcessing}
                  size="sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M8 2v4l-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8l-2-2V2"/>
                    <path d="M8 6h8"/>
                    <path d="m10 8 4 4"/>
                    <path d="m14 8-4 4"/>
                  </svg>
                  Mix
                </Button>
                
                <Button
                  class="tank-action-btn send-btn"
                  onclick={() => sendTank(tankId)}
                  disabled={isProcessing}
                  size="sm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14"/>
                    <path d="m12 5 7 7-7 7"/>
                  </svg>
                  Send
                </Button>
              </div>
            </div>
          {/each}
        </div>
      </CardContent>
    </Card>

    <!-- Manual Relay Grid -->
    <Card class="relay-control-card">
      <CardHeader>
        <CardTitle class="section-title">
          <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="9" cy="21" r="1"/>
            <circle cx="20" cy="21" r="1"/>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
          </svg>
          Manual Relay Controls
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="relay-tank-grid">
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

  <!-- Nutrient Dosing Panel -->
  <div class="dosing-panel">
    <Card class="dosing-card">
      <CardHeader>
        <CardTitle class="section-title">
          <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 3v18h18"/>
            <path d="m7 16 4-4 4 4 6-6"/>
          </svg>
          Nutrient Dosing Control
        </CardTitle>
      </CardHeader>
      <CardContent class="dosing-content">
        
        <!-- Dosing Amount Control -->
        <div class="dosing-controls">
          <div class="amount-display">
            <div class="amount-value">{dosingAmount}</div>
            <div class="amount-unit">ml</div>
          </div>
          
          <div class="slider-container">
            <div class="slider-markers">
              <div class="marker" style="left: 0%">
                <div class="marker-label">1</div>
                <div class="marker-line"></div>
              </div>
              <div class="marker" style="left: 25%">
                <div class="marker-label">500</div>
                <div class="marker-line"></div>
              </div>
              <div class="marker" style="left: 50%">
                <div class="marker-label">1000</div>
                <div class="marker-line"></div>
              </div>
              <div class="marker" style="left: 75%">
                <div class="marker-label">1500</div>
                <div class="marker-line"></div>
              </div>
              <div class="marker" style="left: 100%">
                <div class="marker-label">2000</div>
                <div class="marker-line"></div>
              </div>
            </div>
            
            <input 
              type="range" 
              class="dosing-slider"
              min="1" 
              max="2000" 
              value={dosingAmount}
              step="1"
              oninput={handleSliderInput}
            />
          </div>

          <div class="preset-controls">
            <div class="preset-row">
              {#each [10, 50, 100, 250] as preset}
                <Button
                  class="preset-btn"
                  onclick={() => setDosingPreset(preset)}
                  size="sm"
                  variant="outline"
                >
                  {preset}ml
                </Button>
              {/each}
            </div>
            <div class="preset-row">
              {#each [500, 1000, 1500, 2000] as preset}
                <Button
                  class="preset-btn"
                  onclick={() => setDosingPreset(preset)}
                  size="sm"
                  variant="outline"
                >
                  {preset}ml
                </Button>
              {/each}
            </div>
          </div>
        </div>

        <Separator />

        <!-- Pump Grid -->
        <div class="pump-grid">
          {#each pumps as pump}
            <Button
              class="pump-btn {pump.status === 'dispensing' ? 'pump-active' : 'pump-idle'} {getNutrientClass(pump.name)}"
              onclick={() => dispensePump(pump.id, dosingAmount)}
              disabled={pump.status === 'dispensing'}
            >
              <div class="pump-content">
                <div class="pump-header">
                  <div class="pump-id">P{pump.id}</div>
                  {#if pump.status === 'dispensing'}
                    <Button 
                      class="stop-btn"
                      onclick={() => stopPump(pump.id)}
                      size="sm"
                    >
                      STOP
                    </Button>
                  {/if}
                </div>
                
                <div class="pump-nutrient">{pump.name}</div>
                
                {#if pump.status === 'dispensing'}
                  <div class="pump-progress">
                    <Progress value={pump.progress} class="progress-bar" />
                    <div class="progress-text">{pump.progress}% ({pump.target_volume}ml)</div>
                  </div>
                {:else}
                  <div class="pump-amount">{dosingAmount}ml</div>
                {/if}
              </div>
            </Button>
          {/each}
        </div>

        <!-- Active Operations Alert -->
        {#if activePumps.length > 0}
          <Alert class="active-operations-alert">
            <AlertDescription>
              <div class="alert-content">
                <div class="alert-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M12 1v6m0 6v6"/>
                    <path d="m21 12-6 0m-6 0-6 0"/>
                  </svg>
                  Currently Dispensing
                </div>
                {#each activePumps as pump}
                  <div class="alert-item">
                    <span>{pump.name}: {pump.target_volume}ml</span>
                    <Button 
                      class="alert-stop-btn"
                      onclick={() => stopPump(pump.id)}
                      size="sm"
                    >
                      STOP
                    </Button>
                  </div>
                {/each}
              </div>
            </AlertDescription>
          </Alert>
        {/if}
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
  /* Global 15% scale reduction */
  .scaled-dashboard {
    transform: scale(0.85);
    transform-origin: top left;
    width: 117.647%; /* 100% / 0.85 to compensate for scaling */
    height: 117.647%; /* 100% / 0.85 to compensate for scaling */
  }

  :root {
    /* Design System Foundation */
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --bg-tertiary: #3a3a3a;
    --bg-card: #0f172a;
    --bg-card-hover: #1e293b;

    /* Accent Colors */
    --accent-purple: #8b5cf6;
    --accent-purple-light: #a855f7;
    --accent-green: #10b981;
    --accent-green-light: #34d399;
    --accent-blue: #3b82f6;
    --accent-yellow: #f59e0b;

    /* Status Colors */
    --status-success: #10b981;
    --status-warning: #f59e0b;
    --status-error: #ef4444;
    --status-info: #3b82f6;
    --status-development: #f59e0b;

    /* Text Colors */
    --text-primary: #f8fafc;
    --text-secondary: #e2e8f0;
    --text-muted: #cbd5e1;
    --text-accent: #06b6d4;
    --text-button: #f1f5f9;

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

    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.2);
    --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.25);

    /* Border Radius */
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
  }

  /* Global Styles */
  .dashboard-header {
    background: var(--bg-primary);
    border-bottom: 2px solid var(--bg-tertiary);
    padding: calc(var(--space-lg) / 2);
    margin-bottom: calc(var(--space-xl) / 2);
  }

  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1400px;
    margin: 0 auto;
  }

  .system-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .dashboard-title {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  .system-health {
    display: flex;
    gap: var(--space-md);
    align-items: center;
  }

  .emergency-stop-btn {
    background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
    color: var(--text-button) !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: var(--text-lg) !important;
    padding: var(--space-lg) var(--space-2xl) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: 0 0 20px rgba(220, 38, 38, 0.5) !important;
    animation: emergency-glow 2s infinite !important;
    transition: all 0.15s ease !important;
    transform: scale(1) !important;
  }

  .emergency-stop-btn:active {
    transform: scale(0.92) !important;
    box-shadow: inset 0 6px 12px rgba(0, 0, 0, 0.4), 0 0 30px rgba(220, 38, 38, 0.8) !important;
  }

  .emergency-stop-btn:hover {
    background: linear-gradient(135deg, #b91c1c, #991b1b) !important;
    transform: scale(1.05) !important;
  }

  .emergency-icon {
    width: 20px;
    height: 20px;
  }

  @keyframes emergency-glow {
    0%, 100% { box-shadow: 0 0 10px rgba(220, 38, 38, 0.5); }
    50% { box-shadow: 0 0 30px rgba(220, 38, 38, 0.8); }
  }

  /* Main Dashboard Layout */
  .dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 350px 300px;
    gap: var(--space-xl);
    width: 100%;
    padding: 0 var(--space-lg);
  }

  /* Operations Panel */
  .operations-panel {
    display: flex;
    flex-direction: column;
    gap: var(--space-xl);
  }

  .tank-status-card {
    background: var(--bg-card) !important;
    border: 2px solid var(--bg-tertiary) !important;
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
    color: var(--accent-purple);
  }

  .tank-overview {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-xl);
  }

  .tank-visual-card {
    background: var(--bg-secondary);
    border: 2px solid var(--bg-tertiary);
    border-radius: var(--radius-lg);
    padding: var(--space-xl);
    transition: all 0.3s ease;
    min-height: 200px;
  }

  .tank-visual-card:hover {
    border-color: var(--accent-purple);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }

  .tank-blue { border-left: 4px solid var(--accent-blue); }
  .tank-green { border-left: 4px solid var(--accent-green); }
  .tank-yellow { border-left: 4px solid var(--accent-yellow); }

  .tank-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .tank-number {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-base);
  }

  .tank-visual {
    display: flex;
    justify-content: center;
    margin: var(--space-lg) 0;
  }

  .tank-container {
    width: 80px;
    height: 100px;
    border: 3px solid var(--accent-purple);
    border-radius: var(--radius-md);
    position: relative;
    background: var(--bg-primary);
    overflow: hidden;
  }

  .tank-fill {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(180deg, var(--accent-blue), var(--accent-green));
    transition: height 0.5s ease;
    border-radius: 0 0 calc(var(--radius-md) - 3px) calc(var(--radius-md) - 3px);
  }

  .tank-level {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-primary);
    z-index: 2;
  }

  .tank-controls {
    display: flex;
    gap: var(--space-sm);
    justify-content: space-between;
  }

  .tank-action-btn {
    flex: 1;
    font-size: var(--text-xs) !important;
    padding: var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
    transform: scale(1) !important;
  }

  .tank-action-btn:active {
    transform: scale(0.95) !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
  }

  .fill-btn {
    background: var(--accent-blue) !important;
    color: var(--text-button) !important;
    border: none !important;
  }

  .mix-btn {
    background: var(--accent-yellow) !important;
    color: var(--bg-primary) !important;
    border: none !important;
  }

  .send-btn {
    background: var(--accent-green) !important;
    color: var(--text-button) !important;
    border: none !important;
  }

  /* Relay Control */
  .relay-control-card {
    background: var(--bg-card) !important;
    border: 2px solid var(--bg-tertiary) !important;
  }

  .relay-tank-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-lg);
  }

  .relay-tank-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .tank-relay-header {
    font-weight: 700;
    color: var(--text-primary);
    text-align: center;
    font-size: var(--text-xl);
    padding: var(--space-sm);
    border-radius: var(--radius-sm);
    margin-bottom: var(--space-sm);
  }

  /* Tank Header Colors */
  .relay-tank-section:first-child .tank-relay-header {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid var(--accent-blue);
    color: var(--accent-blue);
    text-shadow: 0 1px 2px rgba(59, 130, 246, 0.8);
  }

  .relay-tank-section:nth-child(2) .tank-relay-header {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid var(--accent-green);
    color: var(--accent-green);
    text-shadow: 0 1px 2px rgba(16, 185, 129, 0.8);
  }

  .relay-tank-section:nth-child(3) .tank-relay-header {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid var(--accent-yellow);
    color: var(--accent-yellow);
    text-shadow: 0 1px 2px rgba(245, 158, 11, 0.8);
  }

  .relay-tank-section:nth-child(4) .tank-relay-header {
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid var(--accent-purple);
    color: var(--accent-purple);
    text-shadow: 0 1px 2px rgba(139, 92, 246, 0.8);
  }

  .tank-relays {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  :global(.relay-btn) {
    padding: var(--space-lg) !important;
    border-radius: var(--radius-md) !important;
    border: 2px solid var(--bg-tertiary) !important;
    transition: all 0.15s ease !important;
    min-height: 80px !important;
    height: 80px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: var(--bg-secondary) !important;
    color: var(--text-muted) !important;
    box-shadow: none !important;
    transform: scale(1) !important;
  }

  :global(.relay-btn:active) {
    transform: scale(0.95) !important;
    box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.3) !important;
  }

  /* Tank 1 Relay Colors (Blue Theme) */
  :global(.relay-btn.tank1-relay.relay-active) {
    background: var(--accent-blue) !important;
    border-color: var(--accent-blue) !important;
    color: var(--text-button) !important;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 0 40px rgba(59, 130, 246, 0.3) !important;
  }

  :global(.relay-btn.tank1-relay.relay-inactive) {
    background: rgba(59, 130, 246, 0.1) !important;
    border-color: var(--accent-blue) !important;
    color: var(--accent-blue) !important;
  }

  /* Tank 2 Relay Colors (Green Theme) */
  :global(.relay-btn.tank2-relay.relay-active) {
    background: var(--accent-green) !important;
    border-color: var(--accent-green) !important;
    color: var(--text-button) !important;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.6), 0 0 40px rgba(16, 185, 129, 0.3) !important;
  }

  :global(.relay-btn.tank2-relay.relay-inactive) {
    background: rgba(16, 185, 129, 0.1) !important;
    border-color: var(--accent-green) !important;
    color: var(--accent-green) !important;
  }

  /* Tank 3 Relay Colors (Yellow Theme) */
  :global(.relay-btn.tank3-relay.relay-active) {
    background: var(--accent-yellow) !important;
    border-color: var(--accent-yellow) !important;
    color: var(--bg-primary) !important;
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.6), 0 0 40px rgba(245, 158, 11, 0.3) !important;
  }

  :global(.relay-btn.tank3-relay.relay-inactive) {
    background: rgba(245, 158, 11, 0.1) !important;
    border-color: var(--accent-yellow) !important;
    color: var(--accent-yellow) !important;
  }

  /* Rooms & Drain Relay Colors (Purple Theme) */
  :global(.relay-btn.rooms-relay.relay-active) {
    background: var(--accent-purple) !important;
    border-color: var(--accent-purple) !important;
    color: var(--text-button) !important;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.6), 0 0 40px rgba(139, 92, 246, 0.3) !important;
  }

  :global(.relay-btn.rooms-relay.relay-inactive) {
    background: rgba(139, 92, 246, 0.1) !important;
    border-color: var(--accent-purple) !important;
    color: var(--accent-purple) !important;
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
    font-weight: 700;
    font-size: var(--text-base);
    margin-bottom: var(--space-xs);
  }

  .relay-name {
    font-size: var(--text-xl);
    line-height: 1.3;
    font-weight: 700;
    margin-bottom: var(--space-xs);
    color: inherit;
  }

  .relay-status {
    font-size: var(--text-lg);
    font-weight: 700;
    padding: 4px 10px;
    border-radius: var(--radius-sm);
    background: rgba(0, 0, 0, 0.3);
    color: inherit;
  }

  /* Tank-specific text shadows */
  :global(.relay-btn.tank1-relay .relay-name),
  :global(.relay-btn.tank1-relay .relay-status) {
    text-shadow: 0 1px 2px rgba(59, 130, 246, 0.8);
  }

  :global(.relay-btn.tank2-relay .relay-name),
  :global(.relay-btn.tank2-relay .relay-status) {
    text-shadow: 0 1px 2px rgba(16, 185, 129, 0.8);
  }

  :global(.relay-btn.tank3-relay .relay-name),
  :global(.relay-btn.tank3-relay .relay-status) {
    text-shadow: 0 1px 2px rgba(245, 158, 11, 0.8);
  }

  :global(.relay-btn.rooms-relay .relay-name),
  :global(.relay-btn.rooms-relay .relay-status) {
    text-shadow: 0 1px 2px rgba(139, 92, 246, 0.8);
  }

  /* Dosing Panel */
  .dosing-panel {
    display: flex;
    flex-direction: column;
  }

  .dosing-card {
    background: var(--bg-card) !important;
    border: 2px solid var(--bg-tertiary) !important;
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
    gap: var(--space-sm);
  }

  .amount-value {
    font-size: 3.5rem;
    font-weight: 700;
    color: var(--accent-purple);
  }

  .amount-unit {
    font-size: 2rem;
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
    width: 2px;
    height: 8px;
    background: var(--text-primary);
    border-radius: 1px;
    opacity: 0.6;
  }

  .marker-label {
    position: absolute;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    font-size: var(--text-xs);
    color: var(--text-muted);
    text-align: center;
    white-space: nowrap;
    font-weight: 500;
  }

  .dosing-slider {
    width: calc(100% + 24px);
    margin-left: -12px;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .dosing-slider::-webkit-slider-thumb {
    appearance: none;
    width: 24px;
    height: 24px;
    background: linear-gradient(135deg, var(--accent-purple), var(--accent-purple-light));
    border-radius: 50%;
    cursor: pointer;
    box-shadow: var(--shadow-md);
  }

  .dosing-slider::-moz-range-thumb {
    width: 24px;
    height: 24px;
    background: linear-gradient(135deg, var(--accent-purple), var(--accent-purple-light));
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: var(--shadow-md);
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
    background: var(--bg-secondary) !important;
    border: 2px solid var(--accent-purple) !important;
    color: var(--accent-purple) !important;
    font-size: var(--text-xs) !important;
    font-weight: 600 !important;
    padding: var(--space-sm) var(--space-md) !important;
    transition: all 0.15s ease !important;
    transform: scale(1) !important;
  }

  .preset-btn:active {
    transform: scale(0.9) !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
  }

  .preset-btn:hover {
    background: var(--accent-purple) !important;
    color: white !important;
  }

  /* Pump Grid */
  .pump-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-md);
  }

  :global(.pump-btn) {
    padding: var(--space-lg) !important;
    border-radius: var(--radius-lg) !important;
    border: 2px solid var(--bg-tertiary) !important;
    transition: all 0.15s ease !important;
    min-height: 120px !important;
    transform: scale(1) !important;
    height: auto !important;
  }

  :global(.pump-btn:active) {
    transform: scale(0.97) !important;
    box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.3) !important;
  }

  :global(.pump-idle) {
    background: var(--bg-secondary) !important;
    border-color: var(--accent-purple) !important;
    color: var(--text-primary) !important;
  }

  :global(.pump-idle:hover) {
    background: var(--accent-purple) !important;
    border-color: var(--accent-purple-light) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-lg) !important;
  }

  :global(.pump-active) {
    background: linear-gradient(135deg, var(--status-error), #dc2626) !important;
    border-color: var(--status-error) !important;
    color: var(--text-button) !important;
    animation: pump-pulse 2s infinite !important;
  }

  /* Nutrient Color Coding */
  :global(.pump-idle.nutrient-veg) {
    background: rgba(34, 197, 94, 0.1) !important;
    border-color: #22c55e !important;
    color: #22c55e !important;
  }

  :global(.pump-idle.nutrient-veg:hover) {
    background: #22c55e !important;
    color: white !important;
  }

  :global(.pump-idle.nutrient-bloom) {
    background: rgba(239, 68, 68, 0.1) !important;
    border-color: #ef4444 !important;
    color: #ef4444 !important;
  }

  :global(.pump-idle.nutrient-bloom:hover) {
    background: #ef4444 !important;
    color: white !important;
  }

  :global(.pump-idle.nutrient-pk) {
    background: rgba(249, 115, 22, 0.1) !important;
    border-color: #f97316 !important;
    color: #f97316 !important;
  }

  :global(.pump-idle.nutrient-pk:hover) {
    background: #f97316 !important;
    color: white !important;
  }

  :global(.pump-idle.nutrient-runclean) {
    background: rgba(6, 182, 212, 0.1) !important;
    border-color: #06b6d4 !important;
    color: #06b6d4 !important;
  }

  :global(.pump-idle.nutrient-runclean:hover) {
    background: #06b6d4 !important;
    color: white !important;
  }

  :global(.pump-idle.nutrient-ph) {
    background: rgba(6, 182, 212, 0.1) !important;
    border-color: #06b6d4 !important;
    color: #06b6d4 !important;
  }

  :global(.pump-idle.nutrient-ph:hover) {
    background: #06b6d4 !important;
    color: white !important;
  }

  :global(.pump-idle.nutrient-cake) {
    background: rgba(255, 255, 255, 0.1) !important;
    border-color: #ffffff !important;
    color: #ffffff !important;
  }

  :global(.pump-idle.nutrient-cake:hover) {
    background: #ffffff !important;
    color: var(--bg-primary) !important;
  }

  @keyframes pump-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
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
    font-weight: 700;
    font-size: var(--text-sm);
    color: var(--accent-purple);
  }

  .pump-active .pump-id {
    color: var(--text-button);
  }

  .stop-btn {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: var(--text-xs) !important;
    padding: var(--space-xs) var(--space-sm) !important;
    transition: all 0.15s ease !important;
    transform: scale(1) !important;
  }

  .stop-btn:active {
    transform: scale(0.85) !important;
    box-shadow: inset 0 3px 6px rgba(0, 0, 0, 0.4) !important;
  }

  .pump-nutrient {
    font-size: var(--text-xl);
    font-weight: 700;
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
    height: 6px !important;
    background: rgba(255, 255, 255, 0.2) !important;
  }

  .progress-text {
    font-size: var(--text-xs);
    text-align: center;
    font-weight: 600;
  }

  .pump-amount {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--accent-purple);
    text-align: center;
  }

  .pump-active .pump-amount {
    color: var(--text-button);
  }

  /* Pump ID and Amount Colors by Nutrient Type */
  :global(.pump-idle.nutrient-veg .pump-id),
  :global(.pump-idle.nutrient-veg .pump-amount) {
    color: #22c55e !important;
  }

  :global(.pump-idle.nutrient-bloom .pump-id),
  :global(.pump-idle.nutrient-bloom .pump-amount) {
    color: #ef4444 !important;
  }

  :global(.pump-idle.nutrient-pk .pump-id),
  :global(.pump-idle.nutrient-pk .pump-amount) {
    color: #f97316 !important;
  }

  :global(.pump-idle.nutrient-runclean .pump-id),
  :global(.pump-idle.nutrient-runclean .pump-amount) {
    color: #06b6d4 !important;
  }

  :global(.pump-idle.nutrient-ph .pump-id),
  :global(.pump-idle.nutrient-ph .pump-amount) {
    color: #06b6d4 !important;
  }

  :global(.pump-idle.nutrient-cake .pump-id),
  :global(.pump-idle.nutrient-cake .pump-amount) {
    color: #ffffff !important;
  }

  /* Pump Nutrient Name Text Shadows */
  :global(.pump-idle.nutrient-veg .pump-nutrient) {
    text-shadow: 0 1px 2px rgba(34, 197, 94, 0.8);
  }

  :global(.pump-idle.nutrient-bloom .pump-nutrient) {
    text-shadow: 0 1px 2px rgba(239, 68, 68, 0.8);
  }

  :global(.pump-idle.nutrient-pk .pump-nutrient) {
    text-shadow: 0 1px 2px rgba(249, 115, 22, 0.8);
  }

  :global(.pump-idle.nutrient-runclean .pump-nutrient) {
    text-shadow: 0 1px 2px rgba(6, 182, 212, 0.8);
  }

  :global(.pump-idle.nutrient-ph .pump-nutrient) {
    text-shadow: 0 1px 2px rgba(139, 92, 246, 0.8);
  }

  :global(.pump-idle.nutrient-cake .pump-nutrient) {
    text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  }

  /* Active Operations Alert */
  .active-operations-alert {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 2px solid var(--status-error) !important;
    border-radius: var(--radius-lg) !important;
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
    color: var(--status-error);
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
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
    transform: scale(1) !important;
  }

  .alert-stop-btn:active {
    transform: scale(0.9) !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
  }

  /* Monitoring Panel */
  .monitoring-panel {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
  }

  .monitoring-card {
    background: var(--bg-card) !important;
    border: 2px solid var(--bg-tertiary) !important;
  }

  .flow-monitors {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .flow-meter {
    padding: var(--space-lg);
    border-radius: var(--radius-lg);
    border: 2px solid var(--bg-tertiary);
  }

  .flow-active {
    background: rgba(59, 130, 246, 0.1);
    border-color: var(--accent-blue);
  }

  .flow-development {
    background: rgba(245, 158, 11, 0.1);
    border-color: var(--status-development);
  }

  .meter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .meter-name {
    font-weight: 600;
    color: var(--text-primary);
  }

  .meter-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--status-development);
    font-size: var(--text-sm);
  }

  .meter-readings {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .flow-rate {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--accent-blue);
  }

  .total-flow {
    font-size: var(--text-sm);
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
    padding: var(--space-lg);
    border-radius: var(--radius-lg);
    border: 2px solid var(--bg-tertiary);
  }

  .sensor-development {
    background: rgba(245, 158, 11, 0.1);
    border-color: var(--status-development);
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
  }

  .sensor-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--status-development);
    font-size: var(--text-sm);
  }

  /* Activity Log */
  .log-card {
    background: var(--bg-card) !important;
    border: 2px solid var(--bg-tertiary) !important;
  }

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .clear-logs-btn {
    background: var(--bg-secondary) !important;
    border: 2px solid var(--bg-tertiary) !important;
    color: var(--text-muted) !important;
    font-size: var(--text-xs) !important;
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
    border-left: 3px solid var(--accent-purple);
  }

  .log-time {
    font-size: var(--text-xs);
    color: var(--text-muted);
    margin-bottom: var(--space-xs);
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
  }

  .status-error {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
  }

  .status-active {
    background: var(--status-warning) !important;
    color: var(--bg-primary) !important;
    animation: status-pulse 2s infinite !important;
  }

  .status-idle {
    background: var(--bg-tertiary) !important;
    color: var(--text-muted) !important;
  }

  .status-filling {
    background: var(--accent-blue) !important;
    color: var(--text-button) !important;
  }

  .status-mixing {
    background: var(--status-warning) !important;
    color: var(--bg-primary) !important;
  }

  .status-sending {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
  }

  .status-ready {
    background: var(--accent-purple) !important;
    color: var(--text-button) !important;
  }

  .status-development {
    background: var(--status-development) !important;
    color: var(--bg-primary) !important;
  }

  .status-operational {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
  }

  @keyframes status-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .dashboard-grid {
      grid-template-columns: 1fr 300px;
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
      padding: calc(var(--space-md) / 2);
    }

    .status-bar {
      flex-direction: column;
      gap: var(--space-lg);
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
      min-height: 48px !important;
      touch-action: manipulation !important;
    }

    .dosing-slider {
      height: 12px !important;
    }

    .dosing-slider::-webkit-slider-thumb {
      width: 32px !important;
      height: 32px !important;
    }

    .dosing-slider::-moz-range-thumb {
      width: 32px !important;
      height: 32px !important;
    }
  }

  /* High Contrast Mode */
  @media (prefers-contrast: high) {
    :root {
      --bg-primary: #000000;
      --bg-secondary: #1a1a1a;
      --bg-tertiary: #333333;
      --text-primary: #ffffff;
      --text-secondary: #ffffff;
      --text-muted: #cccccc;
    }
  }

  /* Reduced Motion */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>