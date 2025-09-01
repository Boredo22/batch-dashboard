<script>
  import { onMount, onDestroy } from 'svelte';

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

<div class="dashboard">
  <header class="header">
    <h1>Nutrient Mixing System Dashboard</h1>
    <div class="status">
      <span class="status-indicator {systemStatus.toLowerCase()}">{systemStatus}</span>
      {#if errorMessage}
        <span class="error">{errorMessage}</span>
      {/if}
    </div>
  </header>

  <main class="main-content">
    <div class="controls-grid">
      
      <!-- Relay Controls -->
      <section class="control-section">
        <h2>Relay Controls</h2>
        <div class="relay-grid">
          {#each relays as relay}
            <div class="relay-item">
              <span class="relay-name">{relay.name}</span>
              <div class="relay-controls">
                <button 
                  class="btn btn-on {relay.state ? 'active' : ''}" 
                  onclick={() => controlRelay(relay.id, true)}
                  disabled={relay.state}
                >
                  ON
                </button>
                <button 
                  class="btn btn-off {!relay.state ? 'active' : ''}" 
                  onclick={() => controlRelay(relay.id, false)}
                  disabled={!relay.state}
                >
                  OFF
                </button>
              </div>
            </div>
          {/each}
          
          <!-- All Relays Off Button -->
          <div class="relay-item all-off">
            <span class="relay-name">All Relays</span>
            <button class="btn btn-emergency" onclick={() => controlRelay(0, false)}>
              ALL OFF
            </button>
          </div>
        </div>
      </section>

      <!-- Pump Controls -->
      <section class="control-section">
        <h2>Pump Testing</h2>
        <div class="pump-controls">
          <div class="input-group">
            <label for="pump-select">Pump:</label>
            <select id="pump-select" bind:value={selectedPump}>
              {#each pumps as pump}
                <option value={pump.id}>{pump.name}</option>
              {/each}
            </select>
          </div>
          
          <div class="input-group">
            <label for="pump-amount">Amount (ml):</label>
            <input 
              id="pump-amount" 
              type="number" 
              bind:value={pumpAmount} 
              min="1" 
              max="1000" 
              step="1"
            />
          </div>
          
          <div class="button-group">
            <button class="btn btn-primary" onclick={dispensePump}>
              Dispense
            </button>
            <button class="btn btn-danger" onclick={stopPump}>
              Stop
            </button>
          </div>
        </div>
      </section>

      <!-- Flow Meter Controls -->
      <section class="control-section">
        <h2>Flow Meter Testing</h2>
        <div class="flow-controls">
          <div class="input-group">
            <label for="flow-select">Flow Meter:</label>
            <select id="flow-select" bind:value={selectedFlowMeter}>
              {#each flowMeters as meter}
                <option value={meter.id}>{meter.name}</option>
              {/each}
            </select>
          </div>
          
          <div class="input-group">
            <label for="flow-gallons">Gallons:</label>
            <input 
              id="flow-gallons" 
              type="number" 
              bind:value={flowGallons} 
              min="1" 
              max="50" 
              step="1"
            />
          </div>
          
          <div class="button-group">
            <button class="btn btn-primary" onclick={startFlow}>
              Start
            </button>
            <button class="btn btn-danger" onclick={stopFlow}>
              Stop
            </button>
          </div>
        </div>
      </section>

      <!-- EC/pH Monitoring -->
      <section class="control-section">
        <h2>EC/pH Monitoring</h2>
        <div class="ecph-controls">
          <div class="readings">
            <div class="reading">
              <span class="reading-label">EC Value:</span>
              <span class="value">{ecValue.toFixed(2)}</span>
            </div>
            <div class="reading">
              <span class="reading-label">pH Value:</span>
              <span class="value">{phValue.toFixed(2)}</span>
            </div>
          </div>
          
          <div class="button-group">
            <button 
              class="btn btn-primary {ecPhMonitoring ? 'active' : ''}" 
              onclick={startEcPhMonitoring}
              disabled={ecPhMonitoring}
            >
              Start Monitoring
            </button>
            <button 
              class="btn btn-danger {!ecPhMonitoring ? 'active' : ''}" 
              onclick={stopEcPhMonitoring}
              disabled={!ecPhMonitoring}
            >
              Stop Monitoring
            </button>
          </div>
        </div>
      </section>
    </div>

    <!-- System Log -->
    <section class="log-section">
      <h2>System Log</h2>
      <div class="log-container">
        {#each logs as log}
          <div class="log-entry">
            <span class="log-time">{log.time}</span>
            <span class="log-message">{log.message}</span>
          </div>
        {/each}
      </div>
    </section>
  </main>
</div>

<style>
  .dashboard {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .header h1 {
    margin: 0;
    font-size: 2rem;
  }

  .status {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .status-indicator {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.9rem;
  }

  .status-indicator.connected {
    background-color: #4CAF50;
    color: white;
  }

  .status-indicator.disconnected {
    background-color: #f44336;
    color: white;
  }

  .status-indicator.error {
    background-color: #ff9800;
    color: white;
  }

  .error {
    color: #ffcdd2;
    font-size: 0.8rem;
    margin-top: 5px;
  }

  .main-content {
    display: flex;
    flex-direction: column;
    gap: 30px;
  }

  .controls-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 25px;
  }

  .control-section {
    background: white;
    border-radius: 10px;
    padding: 25px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    border: 1px solid #e0e0e0;
  }

  .control-section h2 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 1.3rem;
    border-bottom: 2px solid #667eea;
    padding-bottom: 10px;
  }

  .relay-grid {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .relay-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 8px;
  }

  .relay-item.all-off {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
  }

  .relay-name {
    font-weight: 500;
    color: #333;
  }

  .relay-controls {
    display: flex;
    gap: 8px;
  }

  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-on {
    background-color: #e8f5e8;
    color: #2e7d2e;
    border: 1px solid #4CAF50;
  }

  .btn-on.active {
    background-color: #4CAF50;
    color: white;
  }

  .btn-off {
    background-color: #fce8e8;
    color: #c62828;
    border: 1px solid #f44336;
  }

  .btn-off.active {
    background-color: #f44336;
    color: white;
  }

  .btn-emergency {
    background-color: #ff5722;
    color: white;
    font-weight: bold;
  }

  .btn-emergency:hover {
    background-color: #d84315;
  }

  .btn-primary {
    background-color: #2196F3;
    color: white;
  }

  .btn-primary:hover {
    background-color: #1976D2;
  }

  .btn-primary.active {
    background-color: #1565C0;
  }

  .btn-danger {
    background-color: #f44336;
    color: white;
  }

  .btn-danger:hover {
    background-color: #d32f2f;
  }

  .pump-controls, .flow-controls, .ecph-controls {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .input-group label {
    font-weight: 500;
    color: #555;
  }

  .input-group select, .input-group input {
    padding: 10px;
    border: 2px solid #ddd;
    border-radius: 6px;
    font-size: 1rem;
  }

  .input-group select:focus, .input-group input:focus {
    outline: none;
    border-color: #667eea;
  }

  .button-group {
    display: flex;
    gap: 10px;
  }

  .readings {
    display: flex;
    gap: 20px;
  }

  .reading {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .reading-label {
    font-weight: 500;
    color: #555;
  }

  .reading .value {
    font-size: 1.2rem;
    font-weight: bold;
    color: #333;
    padding: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    text-align: center;
  }

  .log-section {
    background: white;
    border-radius: 10px;
    padding: 25px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    border: 1px solid #e0e0e0;
  }

  .log-section h2 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 1.3rem;
    border-bottom: 2px solid #667eea;
    padding-bottom: 10px;
  }

  .log-container {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 10px;
    background: #f8f9fa;
  }

  .log-entry {
    display: flex;
    gap: 15px;
    padding: 8px 0;
    border-bottom: 1px solid #eee;
  }

  .log-entry:last-child {
    border-bottom: none;
  }

  .log-time {
    color: #666;
    font-size: 0.85rem;
    min-width: 80px;
    font-family: monospace;
  }

  .log-message {
    color: #333;
    font-size: 0.9rem;
  }

  @media (max-width: 768px) {
    .controls-grid {
      grid-template-columns: 1fr;
    }
    
    .header {
      flex-direction: column;
      gap: 15px;
      text-align: center;
    }
    
    .readings {
      flex-direction: column;
      gap: 10px;
    }
    
    .button-group {
      flex-direction: column;
    }
  }
</style>