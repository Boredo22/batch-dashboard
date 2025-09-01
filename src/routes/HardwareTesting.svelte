<script>
  import { onMount } from 'svelte';

  // Reactive state using Svelte 5 runes
  let systemOnline = $state(true);
  let logEntries = $state([]);
  
  let relays = $state([
    { id: 'R1', status: 'working', enabled: false },
    { id: 'R2', status: 'working', enabled: true },
    { id: 'R3', status: 'working', enabled: false },
    { id: 'R4', status: 'working', enabled: false },
    { id: 'R5', status: 'warning', enabled: false },
    { id: 'R6', status: 'working', enabled: false },
    { id: 'R7', status: 'warning', enabled: false },
    { id: 'R8', status: 'working', enabled: true },
    { id: 'R9', status: 'working', enabled: false },
    { id: 'R10', status: 'warning', enabled: false },
    { id: 'R11', status: 'working', enabled: true },
    { id: 'R12', status: 'working', enabled: false },
    { id: 'R13', status: 'working', enabled: false }
  ]);

  let nutrientPumps = $state([
    { id: 1, name: 'Pump 1', status: 'Stopped' },
    { id: 2, name: 'Pump 2', status: 'Stopped' },
    { id: 3, name: 'Pump 3', status: 'Stopped' },
    { id: 4, name: 'Pump 4', status: 'Stopped' },
    { id: 5, name: 'Pump 5', status: 'Stopped' },
    { id: 6, name: 'Pump 6', status: 'Stopped' },
    { id: 7, name: 'Pump 7', status: 'Stopped' },
    { id: 8, name: 'Pump 8', status: 'Stopped' }
  ]);

  let flowMeter = $state({
    name: 'Main Line Flow Meter',
    currentFlow: 141.4,
    totalVolume: 16025.6,
    unit: 'L/min'
  });

  let phEcSensor = $state({
    status: 'Online',
    phLevel: 7.05,
    ecLevel: 1.30
  });

  // Logging functions
  function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    logEntries.unshift({ timestamp, message, type });
    if (logEntries.length > 100) {
      logEntries = logEntries.slice(0, 100);
    }
  }

  function clearLog() {
    logEntries.length = 0;
    addLog('Log cleared', 'system');
  }

  // API functions with logging
  async function toggleRelay(relayId) {
    try {
      addLog(`Toggling relay ${relayId}...`, 'info');
      const response = await fetch(`/api/relay/${relayId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const relay = relays.find(r => r.id === relayId);
        if (relay) {
          relay.enabled = !relay.enabled;
          addLog(`Relay ${relayId} ${relay.enabled ? 'ON' : 'OFF'}`, 'success');
        }
      } else {
        addLog(`Failed to toggle relay ${relayId}`, 'error');
      }
    } catch (error) {
      addLog(`Error toggling relay ${relayId}: ${error.message}`, 'error');
    }
  }

  async function togglePump(pumpId) {
    try {
      addLog(`Toggling pump ${pumpId}...`, 'info');
      const response = await fetch(`/api/pump/${pumpId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const pump = nutrientPumps.find(p => p.id === pumpId);
        if (pump) {
          pump.status = pump.status === 'Stopped' ? 'Running' : 'Stopped';
          addLog(`Pump ${pumpId} ${pump.status.toLowerCase()}`, 'success');
        }
      } else {
        addLog(`Failed to toggle pump ${pumpId}`, 'error');
      }
    } catch (error) {
      addLog(`Error toggling pump ${pumpId}: ${error.message}`, 'error');
    }
  }

  async function testPump(pumpId, amount = 30) {
    try {
      addLog(`Testing pump ${pumpId} - ${amount}ML...`, 'info');
      const response = await fetch(`/api/pump/${pumpId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount })
      });
      
      if (response.ok) {
        addLog(`Pump ${pumpId} test started - ${amount}ML`, 'success');
      } else {
        addLog(`Failed to test pump ${pumpId}`, 'error');
      }
    } catch (error) {
      addLog(`Error testing pump ${pumpId}: ${error.message}`, 'error');
    }
  }

  async function testAllRelays() {
    try {
      addLog('Testing all relays...', 'info');
      const response = await fetch('/api/relays/test-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        addLog('All relays test sequence started', 'success');
      } else {
        addLog('Failed to start relay test sequence', 'error');
      }
    } catch (error) {
      addLog(`Error testing relays: ${error.message}`, 'error');
    }
  }

  async function calibrateSensor() {
    try {
      addLog('Calibrating pH/EC sensor...', 'info');
      const response = await fetch('/api/sensor/ph-ec/calibrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        addLog('pH/EC sensor calibration started', 'success');
      } else {
        addLog('Failed to start sensor calibration', 'error');
      }
    } catch (error) {
      addLog(`Error calibrating sensor: ${error.message}`, 'error');
    }
  }

  async function testFlow() {
    try {
      addLog('Testing flow meter...', 'info');
      // Simulate flow test - replace with actual API call
      setTimeout(() => {
        addLog('Flow meter test completed', 'success');
      }, 2000);
    } catch (error) {
      addLog(`Error testing flow meter: ${error.message}`, 'error');
    }
  }

  // Load hardware status on mount
  onMount(async () => {
    addLog('Hardware Testing Suite initialized', 'system');
    
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      
      if (data.success) {
        addLog('Hardware status loaded successfully', 'success');
      } else {
        addLog('Failed to load hardware status', 'warning');
      }
    } catch (error) {
      addLog(`Failed to connect to hardware API: ${error.message}`, 'error');
    }

    // Start periodic updates
    setInterval(async () => {
      try {
        const response = await fetch('/api/flow-meter/status');
        const data = await response.json();
        if (data.success) {
          flowMeter.currentFlow = data.current_flow;
          flowMeter.totalVolume = data.total_volume;
        }
      } catch (error) {
        // Silent error - don't spam the log with connection issues
      }
    }, 10000);
  });
</script>

<div class="dashboard-container">
  <!-- Header -->
  <div class="dashboard-header">
    <div class="header-left">
      <h1><i class="fas fa-cogs"></i> Hardware Testing Suite</h1>
      <span class="system-status {systemOnline ? 'online' : 'offline'}">
        <i class="fas fa-{systemOnline ? 'check-circle' : 'exclamation-triangle'}"></i>
        {systemOnline ? 'System Online' : 'System Offline'}
      </span>
    </div>
  </div>

  <!-- Main Dashboard Layout -->
  <div class="dashboard-main">
    <!-- Hardware Controls Panel -->
    <div class="controls-panel">
      
      <!-- Relays Section -->
      <div class="control-section">
        <div class="section-title">
          <h2><i class="fas fa-toggle-on"></i> Relays</h2>
          <button class="btn btn-secondary" onclick={testAllRelays}>Test All</button>
        </div>
        <div class="relays-grid">
          {#each relays as relay}
            <div class="relay-card">
              <div class="relay-header">
                <span class="relay-id">{relay.id}</span>
                <div class="status-indicator {relay.status}"></div>
              </div>
              <div class="relay-controls">
                <label class="switch">
                  <input 
                    type="checkbox" 
                    bind:checked={relay.enabled}
                    onchange={() => toggleRelay(relay.id)}
                  />
                  <span class="slider"></span>
                </label>
                <span class="state-label">{relay.enabled ? 'ON' : 'OFF'}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Pumps Section -->
      <div class="control-section">
        <div class="section-title">
          <h2><i class="fas fa-tint"></i> Nutrient Pumps</h2>
        </div>
        <div class="pumps-grid">
          {#each nutrientPumps as pump}
            <div class="pump-card">
              <div class="pump-header">
                <span class="pump-name">{pump.name}</span>
                <div class="status-indicator working"></div>
              </div>
              <div class="pump-status">Status: <strong>{pump.status}</strong></div>
              <div class="pump-controls">
                <button class="btn btn-sm btn-primary" onclick={() => togglePump(pump.id)}>
                  {pump.status === 'Stopped' ? 'Start' : 'Stop'}
                </button>
                <div class="test-controls">
                  <button class="btn btn-sm btn-outline" onclick={() => testPump(pump.id, 10)}>10ML</button>
                  <button class="btn btn-sm btn-outline" onclick={() => testPump(pump.id, 30)}>30ML</button>
                  <button class="btn btn-sm btn-outline" onclick={() => testPump(pump.id, 50)}>50ML</button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Sensors and Flow Section -->
      <div class="sensors-flow-row">
        <!-- Flow Meter -->
        <div class="control-section flow-section">
          <div class="section-title">
            <h2><i class="fas fa-water"></i> Flow Meter</h2>
            <button class="btn btn-secondary" onclick={testFlow}>Test</button>
          </div>
          <div class="flow-card">
            <div class="flow-header">
              <span class="flow-name">{flowMeter.name}</span>
              <div class="status-indicator working"></div>
            </div>
            <div class="flow-metrics">
              <div class="metric">
                <span class="metric-label">Current Flow</span>
                <span class="metric-value">{flowMeter.currentFlow} <small>{flowMeter.unit}</small></span>
              </div>
              <div class="metric">
                <span class="metric-label">Total Volume</span>
                <span class="metric-value">{flowMeter.totalVolume} <small>L</small></span>
              </div>
            </div>
          </div>
        </div>

        <!-- pH/EC Sensor -->
        <div class="control-section sensor-section">
          <div class="section-title">
            <h2><i class="fas fa-flask"></i> pH/EC Sensor</h2>
            <button class="btn btn-secondary" onclick={calibrateSensor}>Calibrate</button>
          </div>
          <div class="sensor-card">
            <div class="sensor-header">
              <span class="sensor-status">Status: {phEcSensor.status}</span>
              <div class="status-indicator working"></div>
            </div>
            <div class="sensor-readings">
              <div class="sensor-metric">
                <div class="metric-header">
                  <span class="metric-label">pH Level</span>
                  <span class="metric-value">{phEcSensor.phLevel}</span>
                </div>
                <div class="progress-bar-container">
                  <div class="progress-bar" style="width: {(phEcSensor.phLevel / 14) * 100}%"></div>
                </div>
              </div>
              <div class="sensor-metric">
                <div class="metric-header">
                  <span class="metric-label">EC Level</span>
                  <span class="metric-value">{phEcSensor.ecLevel}</span>
                </div>
                <div class="progress-bar-container">
                  <div class="progress-bar" style="width: {(phEcSensor.ecLevel / 3) * 100}%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Log Panel -->
    <div class="log-panel">
      <div class="log-header">
        <h3><i class="fas fa-terminal"></i> System Log</h3>
        <button class="btn btn-sm btn-outline" onclick={clearLog}>Clear</button>
      </div>
      <div class="log-content">
        {#each logEntries as entry}
          <div class="log-entry log-{entry.type}">
            <span class="log-timestamp">{entry.timestamp}</span>
            <span class="log-message">{entry.message}</span>
          </div>
        {/each}
        {#if logEntries.length === 0}
          <div class="log-entry log-system">
            <span class="log-message">No log entries yet...</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  /* Modern Dashboard Styles */
  .dashboard-container {
    min-height: 100vh;
    background: #0f1419;
    color: #e6e6e6;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  /* Header */
  .dashboard-header {
    background: #1e2328;
    border-bottom: 1px solid #30363d;
    padding: 1rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .header-left h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #58a6ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .system-status {
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .system-status.online {
    background: rgba(46, 160, 67, 0.15);
    color: #3fb950;
    border: 1px solid rgba(46, 160, 67, 0.3);
  }

  .system-status.offline {
    background: rgba(248, 81, 73, 0.15);
    color: #f85149;
    border: 1px solid rgba(248, 81, 73, 0.3);
  }

  /* Main Layout */
  .dashboard-main {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 1.5rem;
    padding: 1.5rem;
    height: calc(100vh - 80px);
  }

  /* Controls Panel */
  .controls-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    overflow-y: auto;
  }

  /* Control Sections */
  .control-section {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1.25rem;
  }

  .section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #30363d;
  }

  .section-title h2 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #e6e6e6;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* Buttons */
  .btn {
    padding: 0.5rem 1rem;
    border: 1px solid #30363d;
    border-radius: 6px;
    background: #21262d;
    color: #e6e6e6;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .btn:hover {
    background: #30363d;
    border-color: #58a6ff;
  }

  .btn-primary {
    background: #238636;
    border-color: #238636;
    color: white;
  }

  .btn-primary:hover {
    background: #2ea043;
    border-color: #2ea043;
  }

  .btn-secondary {
    background: #373e47;
    border-color: #444c56;
  }

  .btn-secondary:hover {
    background: #444c56;
    border-color: #58a6ff;
  }

  .btn-outline {
    background: transparent;
    border-color: #30363d;
  }

  .btn-outline:hover {
    background: #30363d;
    border-color: #58a6ff;
  }

  .btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
  }

  /* Relays Grid */
  .relays-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.75rem;
  }

  .relay-card {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0.75rem;
    text-align: center;
    transition: all 0.2s ease;
  }

  .relay-card:hover {
    border-color: #58a6ff;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  .relay-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .relay-id {
    font-weight: 600;
    font-size: 0.875rem;
    color: #e6e6e6;
  }

  .relay-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .state-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #7d8590;
  }

  /* Status Indicators */
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .status-indicator.working {
    background: #3fb950;
    box-shadow: 0 0 6px rgba(63, 185, 80, 0.4);
  }

  .status-indicator.warning {
    background: #d29922;
    box-shadow: 0 0 6px rgba(210, 153, 34, 0.4);
  }

  /* Toggle Switch */
  .switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #6e7681;
    border-radius: 24px;
    transition: 0.3s;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    border-radius: 50%;
    transition: 0.3s;
  }

  input:checked + .slider {
    background-color: #238636;
  }

  input:checked + .slider:before {
    transform: translateX(20px);
  }

  /* Pumps Grid */
  .pumps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .pump-card {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .pump-card:hover {
    border-color: #58a6ff;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  .pump-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .pump-name {
    font-weight: 600;
    font-size: 0.875rem;
    color: #e6e6e6;
  }

  .pump-status {
    font-size: 0.75rem;
    color: #7d8590;
    margin-bottom: 0.75rem;
  }

  .pump-controls {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .test-controls {
    display: flex;
    gap: 0.5rem;
    justify-content: space-between;
  }

  /* Sensors and Flow Row */
  .sensors-flow-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .flow-section, .sensor-section {
    margin-bottom: 0;
  }

  /* Flow and Sensor Cards */
  .flow-card, .sensor-card {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 1rem;
  }

  .flow-header, .sensor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #30363d;
  }

  .flow-name, .sensor-status {
    font-weight: 600;
    font-size: 0.875rem;
    color: #e6e6e6;
  }

  /* Metrics */
  .flow-metrics {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .metric {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .metric-label {
    font-size: 0.75rem;
    color: #7d8590;
  }

  .metric-value {
    font-size: 1.125rem;
    font-weight: 600;
    color: #58a6ff;
  }

  .metric-value small {
    font-size: 0.75rem;
    font-weight: 400;
    color: #7d8590;
    margin-left: 0.25rem;
  }

  /* Sensor Readings */
  .sensor-readings {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .sensor-metric {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .progress-bar-container {
    width: 100%;
    height: 6px;
    background: #30363d;
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #58a6ff, #3fb950);
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  /* Log Panel */
  .log-panel {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #30363d;
    background: #161b22;
  }

  .log-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #58a6ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .log-content {
    flex: 1;
    padding: 0.5rem;
    overflow-y: auto;
    font-size: 0.75rem;
    line-height: 1.4;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  }

  .log-entry {
    display: flex;
    gap: 0.75rem;
    padding: 0.25rem 0.5rem;
    margin-bottom: 1px;
    border-radius: 3px;
    transition: background-color 0.15s ease;
  }

  .log-entry:hover {
    background: rgba(88, 166, 255, 0.1);
  }

  .log-timestamp {
    color: #7d8590;
    font-weight: 500;
    min-width: 80px;
  }

  .log-message {
    color: #e6e6e6;
    word-break: break-word;
  }

  .log-entry.log-success .log-message {
    color: #3fb950;
  }

  .log-entry.log-error .log-message {
    color: #f85149;
  }

  .log-entry.log-warning .log-message {
    color: #d29922;
  }

  .log-entry.log-system .log-message {
    color: #58a6ff;
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .dashboard-main {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr 300px;
    }
    
    .sensors-flow-row {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 768px) {
    .dashboard-main {
      padding: 1rem;
      grid-template-rows: 1fr 250px;
    }

    .relays-grid {
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      gap: 0.5rem;
    }

    .pumps-grid {
      grid-template-columns: 1fr;
    }

    .test-controls {
      flex-wrap: wrap;
    }

    .header-left {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .header-left h1 {
      font-size: 1.25rem;
    }
  }
</style>