<script>
  import { onMount, onDestroy } from 'svelte';
  import RelayControlCard from '$lib/components/hardware/relay-control-card.svelte';
  import PumpControlCard from '$lib/components/hardware/pump-control-card.svelte';
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
  let lastProgressReported = $state(new Map()); // pump_id -> last_percentage
  
  let statusInterval;

  // API functions
  async function fetchHardwareData() {
    try {
      const response = await fetch('/api/hardware/status');
      if (response.ok) {
        const data = await response.json();
        // Merge API data with defaults, keeping defaults if API doesn't provide
        if (data.relays && data.relays.length > 0) {
          // Update relays data, converting state to status for consistency
          relays = data.relays.map(relay => ({ 
            ...relay, 
            status: relay.state ? 'on' : 'off' 
          }));
          console.log('Loaded relays:', relays);
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
      // Keep default hardware data visible even when API fails
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
        
        // Update pump progress information from detailed status
        if (data.pumps) {
          pumps = pumps.map(pump => {
            const statusInfo = data.pumps[pump.id];
            if (statusInfo) {
              // Add progress log message for dispensing pumps (every 10% progress)
              if (statusInfo.is_dispensing && statusInfo.current_volume > 0 && statusInfo.target_volume > 0) {
                const currentPercent = Math.floor((statusInfo.current_volume / statusInfo.target_volume) * 100 / 10) * 10; // Round to nearest 10%
                const lastPercent = lastProgressReported.get(pump.id) || -10;
                
                if (currentPercent > lastPercent && currentPercent >= 10) {
                  const progressMsg = `Pump ${pump.id} (${pump.name}): ${statusInfo.current_volume.toFixed(1)}ml / ${statusInfo.target_volume.toFixed(1)}ml (${currentPercent}% complete)`;
                  addLog(progressMsg);
                  lastProgressReported.set(pump.id, currentPercent);
                }
              }
              
              // Check if pump just finished dispensing
              if (!statusInfo.is_dispensing && pump.is_dispensing) {
                const completionMsg = `Pump ${pump.id} (${pump.name}) completed dispensing: ${statusInfo.current_volume?.toFixed(1) || 0}ml dispensed`;
                addLog(completionMsg);
                lastProgressReported.delete(pump.id); // Clean up tracking
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
    await fetchHardwareData();
    await fetchSystemStatus();
    
    // Set up polling for system status
    statusInterval = setInterval(async () => {
      await fetchSystemStatus();
    }, 2000);
    
    if (pumps.length > 0) selectedPump = pumps[0].id;
    if (flowMeters.length > 0) selectedFlowMeter = flowMeters[0].id;
  });

  onDestroy(() => {
    if (statusInterval) {
      clearInterval(statusInterval);
    }
  });
</script>

<!-- Main dashboard grid -->
<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  <!-- Hardware Controls - Takes up 2 columns on large screens -->
  <div class="lg:col-span-2 space-y-4">
    <RelayControlCard {relays} onRelayControl={controlRelay} />
    
    <div class="grid gap-4 md:grid-cols-2">
      <PumpControlCard 
        {pumps} 
        bind:selectedPump 
        bind:pumpAmount 
        onDispensePump={dispensePump} 
        onStopPump={stopPump} 
      />
      
      <FlowMeterCard
        flowMeters={flowMeters}
        bind:selectedFlowMeter
        bind:flowGallons
        onStartFlow={startFlow}
        onStopFlow={stopFlow}
      />
    </div>
    
    <ECPHMonitorCard
      {ecValue}
      {phValue}
      {ecPhMonitoring}
      onStartMonitoring={startEcPhMonitoring}
      onStopMonitoring={stopEcPhMonitoring}
    />
  </div>

  <!-- System Log - Takes up 1 column -->
  <div class="lg:col-span-1">
    <SystemLogCard {logs} onClearLogs={clearLogs} />
  </div>
</div>