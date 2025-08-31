<script>
  import { onMount } from 'svelte';

  // Reactive state using Svelte 5 runes
  let systemOnline = $state(true);
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

  // API functions
  async function toggleRelay(relayId) {
    try {
      const response = await fetch(`/api/relay/${relayId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const relay = relays.find(r => r.id === relayId);
        if (relay) {
          relay.enabled = !relay.enabled;
        }
      }
    } catch (error) {
      console.error('Error toggling relay:', error);
    }
  }

  async function togglePump(pumpId) {
    try {
      const response = await fetch(`/api/pump/${pumpId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const pump = nutrientPumps.find(p => p.id === pumpId);
        if (pump) {
          pump.status = pump.status === 'Stopped' ? 'Running' : 'Stopped';
        }
      }
    } catch (error) {
      console.error('Error toggling pump:', error);
    }
  }

  async function testPump(pumpId) {
    try {
      const response = await fetch(`/api/pump/${pumpId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: 30 }) // 30ML test
      });
      
      if (response.ok) {
        console.log(`Testing pump ${pumpId} - 30ML`);
      }
    } catch (error) {
      console.error('Error testing pump:', error);
    }
  }

  async function testAllRelays() {
    try {
      const response = await fetch('/api/relays/test-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        console.log('Testing all relays');
      }
    } catch (error) {
      console.error('Error testing all relays:', error);
    }
  }

  async function calibrateSensor() {
    try {
      const response = await fetch('/api/sensor/ph-ec/calibrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        console.log('Calibrating pH/EC sensor');
      }
    } catch (error) {
      console.error('Error calibrating sensor:', error);
    }
  }

  // Load hardware status on mount
  onMount(async () => {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      
      if (data.success) {
        // Update hardware status from API
        console.log('Hardware status loaded');
      }
    } catch (error) {
      console.error('Failed to load hardware status:', error);
    }

    // Start periodic updates
    setInterval(async () => {
      // Update flow meter readings and other live data
      try {
        const response = await fetch('/api/flow-meter/status');
        const data = await response.json();
        if (data.success) {
          flowMeter.currentFlow = data.current_flow;
          flowMeter.totalVolume = data.total_volume;
        }
      } catch (error) {
        console.error('Error updating flow meter:', error);
      }
    }, 10000);
  });
</script>

<div class="hardware-testing-page">
  <!-- Header Section -->
  <div class="header-section">
    <div class="title-container">
      <h1>Hardware Testing Suite</h1>
      <span class="status-indicator {systemOnline ? 'online' : 'offline'}">
        {systemOnline ? 'System Online' : 'System Offline'}
      </span>
    </div>
  </div>

  <div class="main-layout">
    <!-- Hardware Grid (3/4 width) -->
    <div class="hardware-grid">
      <!-- Relays Section -->
      <div class="hardware-section">
        <div class="section-header">
          <h2>Relays (13)</h2>
          <button class="test-all-btn" on:click={testAllRelays}>Test All</button>
        </div>
        
        <div class="relays-container">
          {#each relays as relay}
            <div class="relay-item">
              <div class="relay-status">
                <span class="status-dot {relay.status}"></span>
                <span class="relay-label">{relay.id}</span>
              </div>
              <label class="toggle-switch">
                <input 
                  type="checkbox" 
                  bind:checked={relay.enabled}
                  on:change={() => toggleRelay(relay.id)}
                />
                <span class="toggle-slider"></span>
              </label>
            </div>
          {/each}
        </div>
      </div>

      <!-- Nutrient Pumps Section -->
      <div class="hardware-section">
        <div class="section-header">
          <h2>Nutrient Pumps (8)</h2>
        </div>
        
        <div class="pumps-container">
          {#each nutrientPumps as pump}
            <div class="pump-item">
              <div class="pump-header">
                <span class="status-dot working"></span>
                <div class="pump-info">
                  <span class="pump-name">{pump.name}</span>
                  <span class="pump-status">{pump.status}</span>
                </div>
                <label class="toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={pump.status !== 'Stopped'}
                    on:change={() => togglePump(pump.id)}
                  />
                  <span class="toggle-slider"></span>
                </label>
              </div>
              
              <button class="test-button" on:click={() => testPump(pump.id)}>
                30ML Test
              </button>
            </div>
          {/each}
        </div>
      </div>

      <!-- Flow Meters Section -->
      <div class="hardware-section">
        <div class="section-header">
          <h2>Flow Meters (2)</h2>
        </div>
        
        <div class="flow-container">
          <div class="flow-item">
            <div class="flow-header">
              <span class="status-dot working"></span>
              <span class="flow-name">{flowMeter.name}</span>
            </div>
            
            <div class="flow-readings">
              <div class="reading">
                <span class="reading-label">Current Flow</span>
                <span class="reading-value">{flowMeter.currentFlow} {flowMeter.unit}</span>
              </div>
              <div class="reading">
                <span class="reading-label">Total Volume</span>
                <span class="reading-value">{flowMeter.totalVolume} L</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- pH/EC Sensor Section -->
      <div class="hardware-section">
        <div class="section-header">
          <h2>pH/EC Sensor</h2>
          <button class="calibrate-btn" on:click={calibrateSensor}>Calibrate</button>
        </div>
        
        <div class="sensor-container">
          <div class="sensor-status">
            <span class="status-dot working"></span>
            <span class="sensor-status-text">Status: {phEcSensor.status}</span>
          </div>
          
          <div class="sensor-readings">
            <div class="sensor-reading">
              <span class="reading-label">pH Level</span>
              <span class="reading-value">{phEcSensor.phLevel}</span>
              <div class="reading-bar">
                <div class="progress-bar" style="width: {(phEcSensor.phLevel / 14) * 100}%"></div>
              </div>
            </div>
            
            <div class="sensor-reading">
              <span class="reading-label">EC Level</span>
              <span class="reading-value">{phEcSensor.ecLevel}</span>
              <div class="reading-bar">
                <div class="progress-bar" style="width: {(phEcSensor.ecLevel / 3) * 100}%"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Terminal Log Panel (1/4 width) -->
    <div class="log-panel">
      <div class="log-header">
        <h3>System Log</h3>
        <button class="clear-btn" on:click={() => console.log('Clear log')}>Clear</button>
      </div>
      <div class="log-content">
        <div class="log-entry">[2024-01-15 10:30:15] System initialized</div>
        <div class="log-entry">[2024-01-15 10:30:16] Hardware status check completed</div>
        <div class="log-entry">[2024-01-15 10:30:17] Relay R1 state changed to OFF</div>
        <div class="log-entry">[2024-01-15 10:30:18] Pump 1 test started (30ML)</div>
        <div class="log-entry">[2024-01-15 10:30:19] Flow meter readings updated</div>
        <div class="log-entry">[2024-01-15 10:30:20] pH/EC sensor calibration initiated</div>
        <div class="log-entry">[2024-01-15 10:30:21] All relays test sequence started</div>
        <div class="log-entry">[2024-01-15 10:30:22] Pump 2 state changed to RUNNING</div>
      </div>
    </div>
  </div>
</div>

<style>
  .hardware-testing-page {
    min-height: 100vh;
    background: #1a1a1a;
    color: #ffffff;
    padding: 20px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  }

  .header-section {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #333;
  }

  .title-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .title-container h1 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #00ff88;
    margin: 0;
  }

  .status-indicator {
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    font-family: monospace;
  }

  .status-indicator.online {
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border: 1px solid #00ff88;
  }

  .status-indicator.offline {
    background: rgba(255, 68, 68, 0.1);
    color: #ff4444;
    border: 1px solid #ff4444;
  }

  .main-layout {
    display: grid;
    grid-template-columns: 3fr 1fr;
    gap: 24px;
    height: calc(100vh - 140px);
  }

  /* Hardware Grid (3/4 width) */
  .hardware-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 16px;
  }

  .hardware-section {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .section-header h2 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    color: #e0e0e0;
  }

  .test-all-btn, .calibrate-btn, .clear-btn {
    padding: 4px 8px;
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    color: #ccc;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: monospace;
  }

  .test-all-btn:hover, .calibrate-btn:hover, .clear-btn:hover {
    background: #444;
    border-color: #00ff88;
    color: #00ff88;
  }

  /* Relays Container */
  .relays-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
    gap: 8px;
    flex: 1;
  }

  .relay-item {
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
  }

  .relay-status {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .status-dot.working {
    background: #00ff88;
  }

  .status-dot.warning {
    background: #ffaa00;
  }

  .relay-label {
    font-weight: 500;
    color: #e0e0e0;
    font-size: 0.7rem;
  }

  /* Pumps Container */
  .pumps-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    overflow-y: auto;
  }

  .pump-item {
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 8px;
  }

  .pump-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .pump-info {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .pump-name {
    font-size: 0.8rem;
    font-weight: 500;
    color: #e0e0e0;
  }

  .pump-status {
    font-size: 0.7rem;
    color: #999;
  }

  .test-button {
    width: 100%;
    padding: 4px;
    background: #444;
    border: 1px solid #666;
    border-radius: 4px;
    color: #ccc;
    font-size: 0.7rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: monospace;
  }

  .test-button:hover {
    background: #555;
    border-color: #00ff88;
    color: #00ff88;
  }

  /* Flow Container */
  .flow-container {
    flex: 1;
  }

  .flow-item {
    background: #333;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 12px;
  }

  .flow-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .flow-name {
    font-size: 0.8rem;
    font-weight: 500;
    color: #e0e0e0;
  }

  .flow-readings {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .reading {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .reading-label {
    font-size: 0.7rem;
    color: #999;
  }

  .reading-value {
    font-size: 0.8rem;
    font-weight: 500;
    color: #00ff88;
  }

  /* Sensor Container */
  .sensor-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .sensor-status {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .sensor-status-text {
    font-size: 0.8rem;
    color: #e0e0e0;
  }

  .sensor-readings {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .sensor-reading {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .reading-bar {
    width: 100%;
    height: 4px;
    background: #333;
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: #00ff88;
    border-radius: 2px;
    transition: width 0.3s ease;
  }

  /* Toggle Switch */
  .toggle-switch {
    position: relative;
    display: inline-block;
    width: 32px;
    height: 16px;
  }

  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #555;
    border-radius: 16px;
    transition: 0.3s;
  }

  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 12px;
    width: 12px;
    left: 2px;
    bottom: 2px;
    background-color: white;
    border-radius: 50%;
    transition: 0.3s;
  }

  input:checked + .toggle-slider {
    background-color: #00ff88;
  }

  input:checked + .toggle-slider:before {
    transform: translateX(16px);
  }

  /* Log Panel (1/4 width) */
  .log-panel {
    background: #1e1e1e;
    border: 1px solid #444;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border-bottom: 1px solid #333;
  }

  .log-header h3 {
    margin: 0;
    color: #00ff88;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .log-content {
    flex: 1;
    padding: 8px;
    overflow-y: auto;
    font-size: 0.7rem;
    line-height: 1.3;
  }

  .log-entry {
    margin-bottom: 2px;
    padding: 2px 4px;
    color: #ccc;
    font-family: 'Courier New', monospace;
    word-break: break-all;
  }

  .log-entry:hover {
    background: rgba(0, 255, 136, 0.1);
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .main-layout {
      grid-template-columns: 1fr;
      grid-template-rows: 3fr 1fr;
    }
    
    .hardware-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 768px) {
    .hardware-testing-page {
      padding: 12px;
    }

    .main-layout {
      gap: 16px;
      height: calc(100vh - 120px);
    }

    .hardware-grid {
      grid-template-columns: 1fr;
      grid-template-rows: repeat(4, 1fr);
    }

    .relays-container {
      grid-template-columns: repeat(auto-fit, minmax(50px, 1fr));
      gap: 4px;
    }

    .title-container {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .title-container h1 {
      font-size: 1.2rem;
    }
  }
</style>