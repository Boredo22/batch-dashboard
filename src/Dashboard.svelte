<script>
  import { onMount, onDestroy } from 'svelte';
  import RelayGrid from './components/RelayGrid.svelte';
  import PumpControl from './components/PumpControl.svelte';
  import FlowMeterControl from './components/FlowMeterControl.svelte';
  import ECPHMonitor from './components/ECPHMonitor.svelte';
  import SystemLog from './components/SystemLog.svelte';

  // State variables using Svelte 5 runes
  let logs = $state([]);
  let systemStatus = $state('Disconnected');
  let errorMessage = $state('');
  
  // Hardware data
  let relays = $state([]);
  let pumps = $state([]);
  let flowMeters = $state([]);
  let ecPhMonitoring = $state(false);
  let ecValue = $state(0);
  let phValue = $state(0);
  
  // Form inputs
  let selectedPump = $state('');
  let pumpAmount = $state(10);
  let selectedFlowMeter = $state('');
  let flowGallons = $state(1);
  
  let statusInterval;

  // API functions
  async function fetchHardwareData() {
    try {
      const response = await fetch('/api/hardware/status');
      if (response.ok) {
        const data = await response.json();
        relays = data.relays || [];
        pumps = data.pumps || [];
        flowMeters = data.flow_meters || [];
        systemStatus = 'Connected';
        errorMessage = '';
      } else {
        throw new Error('Failed to fetch hardware data');
      }
    } catch (error) {
      console.error('Error fetching hardware data:', error);
      systemStatus = 'Error';
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
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  }

  async function controlRelay(relayId, state) {
    try {
      const response = await fetch(`/api/relay/${relayId}/${state ? 'on' : 'off'}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(result.message || `Relay ${relayId} ${state ? 'ON' : 'OFF'}`);
        await fetchHardwareData();
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error controlling relay:', error);
      addLog(`Error controlling relay: ${error.message}`);
    }
  }

  async function dispensePump() {
    if (!selectedPump || !pumpAmount) {
      addLog('Please select a pump and amount');
      return;
    }
    
    try {
      const response = await fetch(`/api/pump/${selectedPump}/dispense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: pumpAmount })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(result.message || `Dispensing ${pumpAmount}ml from pump ${selectedPump}`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error dispensing pump:', error);
      addLog(`Error dispensing pump: ${error.message}`);
    }
  }

  async function stopPump() {
    if (!selectedPump) {
      addLog('Please select a pump');
      return;
    }
    
    try {
      const response = await fetch(`/api/pump/${selectedPump}/stop`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(result.message || `Stopped pump ${selectedPump}`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error stopping pump:', error);
      addLog(`Error stopping pump: ${error.message}`);
    }
  }

  async function startFlow() {
    if (!selectedFlowMeter || !flowGallons) {
      addLog('Please select a flow meter and gallons');
      return;
    }
    
    try {
      const response = await fetch(`/api/flow/${selectedFlowMeter}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gallons: flowGallons })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(result.message || `Started flow meter ${selectedFlowMeter} for ${flowGallons} gallons`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error starting flow meter:', error);
      addLog(`Error starting flow meter: ${error.message}`);
    }
  }

  async function stopFlow() {
    if (!selectedFlowMeter) {
      addLog('Please select a flow meter');
      return;
    }
    
    try {
      const response = await fetch(`/api/flow/${selectedFlowMeter}/stop`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(result.message || `Stopped flow meter ${selectedFlowMeter}`);
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
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
        addLog(result.message || 'Started EC/pH monitoring');
        ecPhMonitoring = true;
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
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
        addLog(result.message || 'Stopped EC/pH monitoring');
        ecPhMonitoring = false;
      } else {
        const error = await response.json();
        addLog(`Error: ${error.error}`);
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

<div class="app">
  <div class="top-bar">
    <h1>Hardware Testing Dashboard</h1>
    <div class="status-badge {systemStatus.toLowerCase()}">
      {systemStatus}
    </div>
  </div>

  <div class="main-grid">
    <div class="left-panel">
      <RelayGrid {relays} onRelayControl={controlRelay} />
      <PumpControl {pumps} bind:selectedPump bind:pumpAmount onDispensePump={dispensePump} onStopPump={stopPump} />
      <FlowMeterControl {flowMeters} bind:selectedFlowMeter bind:flowGallons onStartFlow={startFlow} onStopFlow={stopFlow} />
      <ECPHMonitor {ecValue} {phValue} {ecPhMonitoring} onStartMonitoring={startEcPhMonitoring} onStopMonitoring={stopEcPhMonitoring} />
    </div>

    <div class="right-panel">
      <SystemLog {logs} />
    </div>
  </div>
</div>

<style>
  .app {
    width: 100vw;
    height: 100vh;
    background: #1a1a1a;
    color: white;
    display: flex;
    flex-direction: column;
  }

  .top-bar {
    background: #2d3748;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #4a5568;
  }

  .top-bar h1 {
    margin: 0;
    color: white;
    font-size: 1.5rem;
  }

  .status-badge {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.875rem;
  }

  .status-badge.connected {
    background: #22c55e;
    color: white;
  }

  .status-badge.disconnected {
    background: #ef4444;
    color: white;
  }

  .status-badge.error {
    background: #f97316;
    color: white;
  }

  .main-grid {
    flex: 1;
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
    padding: 1.5rem;
    overflow: hidden;
    max-width: 100%;
  }

  .left-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
    overflow-y: auto;
    padding-right: 0.5rem;
  }

  .right-panel {
    background: #2d3748;
    border-radius: 0.5rem;
    border: 1px solid #4a5568;
    min-height: 0;
  }

  @media (max-width: 1400px) {
    .main-grid {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr auto;
      gap: 1rem;
    }
    
    .right-panel {
      height: 350px;
    }
    
    .left-panel {
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }
  }

  @media (max-width: 1000px) {
    .left-panel {
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }
  }

  @media (max-width: 768px) {
    .top-bar {
      flex-direction: column;
      gap: 0.5rem;
      padding: 1rem;
    }
    
    .main-grid {
      padding: 1rem;
    }
    
    .left-panel {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
    
    .right-panel {
      height: 300px;
    }
  }
</style>