<script>
  import { onMount } from 'svelte';

  // Reactive state using Svelte 5 runes
  let testResults = $state([]);
  let activeTests = $state(new Set());
  let systemStats = $state({
    totalTests: 0,
    successfulTests: 0,
    activeRelays: 0,
    connectedPumps: 0
  });
  
  let logEntries = $state([]);
  let autoScroll = $state(true);
  let selectedHardware = $state('relays');

  // Hardware configuration (will be loaded from API)
  let hardware = $state({
    relays: { ids: [], names: {} },
    pumps: { ids: [], names: {} },
    flow_meters: { ids: [], names: {} }
  });

  // Test configurations
  const testConfigs = {
    relay: {
      basic: { duration: 1.0 },
      advanced: { relay_set: [4, 7], duration: 2.0 }
    },
    pump: {
      basic: { amount: 1.0 },
      recipe: { 
        recipe: [
          { pump_id: 1, amount: 2.0 },
          { pump_id: 2, amount: 1.5 }
        ] 
      }
    },
    flow: {
      basic: { gallons: 1 },
      pulse_test: { gallons: 2, duration: 10.0 }
    },
    sensor: {
      basic: {},
      continuous: { duration: 30.0 }
    }
  };

  // Load hardware configuration
  onMount(async () => {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      
      if (data.success) {
        hardware = data.hardware;
        updateSystemStats();
      }
    } catch (error) {
      logMessage('error', 'Failed to load hardware configuration', error.message);
    }

    // Start periodic status updates
    setInterval(updateSystemStats, 10000);
  });

  // Test execution functions
  async function runTest(type, id, testType) {
    const testKey = `${type}-${id}-${testType}`;
    
    if (activeTests.has(testKey)) {
      logMessage('warning', `Test ${testKey} already running`);
      return;
    }

    activeTests.add(testKey);
    logMessage('info', `Starting ${testType} test for ${type} ${id}`);

    try {
      let endpoint = '';
      let payload = { test_type: testType };

      switch (type) {
        case 'relay':
          endpoint = `/api/test/relay/${id}`;
          payload = { ...payload, ...testConfigs.relay[testType] };
          break;
        case 'pump':
          endpoint = `/api/test/pump/${id}`;
          payload = { ...payload, ...testConfigs.pump[testType] };
          break;
        case 'flow':
          endpoint = `/api/test/flow/${id}`;
          payload = { ...payload, ...testConfigs.flow[testType] };
          break;
        case 'sensor':
          endpoint = '/api/test/sensor/ecph';
          payload = { ...payload, ...testConfigs.sensor[testType] };
          break;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      // Log commands and responses
      if (result.commands && result.responses) {
        result.commands.forEach((cmd, index) => {
          logMessage('command', `TX: ${cmd}`, `Command ${index + 1}`);
        });
        
        result.responses.forEach((resp, index) => {
          const status = resp.success ? 'Success' : 'Failed';
          logMessage('response', `RX: ${status}`, JSON.stringify(resp));
        });
      }

      // Store result
      testResults.push({
        id: testKey,
        type,
        itemId: id,
        testType,
        result,
        timestamp: new Date().toISOString()
      });

      // Update stats
      systemStats.totalTests++;
      if (result.success) {
        systemStats.successfulTests++;
        logMessage('success', `${testType} test completed for ${type} ${id}`, `Success rate: ${Math.round(systemStats.successfulTests / systemStats.totalTests * 100)}%`);
      } else {
        logMessage('error', `${testType} test failed for ${type} ${id}`, result.error || 'Unknown error');
      }

    } catch (error) {
      logMessage('error', `Test failed: ${testKey}`, error.message);
    } finally {
      activeTests.delete(testKey);
    }
  }

  function logMessage(level, message, details = '') {
    const entry = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      level,
      message,
      details
    };
    
    logEntries.push(entry);

    // Auto-scroll to bottom if enabled
    if (autoScroll) {
      setTimeout(() => {
        const logContainer = document.getElementById('log-container');
        if (logContainer) {
          logContainer.scrollTop = logContainer.scrollHeight;
        }
      }, 50);
    }

    // Keep only last 1000 entries
    if (logEntries.length > 1000) {
      logEntries = logEntries.slice(-1000);
    }
  }

  function clearLog() {
    logEntries = [];
    logMessage('info', 'Log cleared');
  }

  function updateSystemStats() {
    // This would normally fetch real hardware status
    logMessage('info', 'System stats updated');
  }

  async function emergencyStop() {
    logMessage('warning', '🚨 EMERGENCY STOP ACTIVATED 🚨');
    
    try {
      const response = await fetch('/api/emergency/stop', { method: 'POST' });
      const result = await response.json();
      
      if (result.success) {
        logMessage('success', 'Emergency stop completed');
      } else {
        logMessage('error', 'Emergency stop failed', result.error);
      }
    } catch (error) {
      logMessage('error', 'Emergency stop request failed', error.message);
    }
  }

  // Get CSS class for log level
  function getLogClass(level) {
    const classes = {
      info: 'log-info',
      success: 'log-success', 
      warning: 'log-warning',
      error: 'log-error',
      command: 'log-command',
      response: 'log-response'
    };
    return classes[level] || 'log-info';
  }
</script>

<div class="testing-suite">
  <div class="testing-header">
    <h1>Hardware Testing Suite</h1>
    <div class="header-controls">
      <button class="btn btn-danger" on:click={emergencyStop}>Emergency Stop</button>
      <button class="btn btn-secondary" on:click={updateSystemStats}>Refresh</button>
    </div>
  </div>

  <!-- System Stats -->
  <div class="stats-section">
    <div class="stat-card">
      <div class="stat-value">{systemStats.totalTests}</div>
      <div class="stat-label">Tests Run</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">
        {systemStats.totalTests > 0 ? Math.round(systemStats.successfulTests / systemStats.totalTests * 100) : 100}%
      </div>
      <div class="stat-label">Success Rate</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{activeTests.size}</div>
      <div class="stat-label">Active Tests</div>
    </div>
  </div>

  <!-- Hardware Type Selection -->
  <div class="hardware-tabs">
    <button 
      class="tab {selectedHardware === 'relays' ? 'active' : ''}"
      on:click={() => selectedHardware = 'relays'}
    >
      Relays (GPIO)
    </button>
    <button 
      class="tab {selectedHardware === 'pumps' ? 'active' : ''}"
      on:click={() => selectedHardware = 'pumps'}
    >
      Nute Pumps (I2C)
    </button>
    <button 
      class="tab {selectedHardware === 'flow' ? 'active' : ''}"
      on:click={() => selectedHardware = 'flow'}
    >
      Flow Meters (GPIO Pulse)
    </button>
    <button 
      class="tab {selectedHardware === 'sensors' ? 'active' : ''}"
      on:click={() => selectedHardware = 'sensors'}
    >
      pH/EC Sensors (USB Serial)
    </button>
  </div>

  <div class="testing-content">
    <!-- Testing Panel -->
    <div class="testing-panel">
      
      {#if selectedHardware === 'relays'}
        <div class="hardware-section">
          <h3>Relay Testing (GPIO Control)</h3>
          <p class="section-description">Direct GPIO control with 5V inverted logic</p>
          
          <div class="hardware-grid">
            {#each hardware.relays.ids as relayId}
              <div class="hardware-item">
                <div class="item-header">
                  <span class="item-name">{hardware.relays.names[relayId] || `Relay ${relayId}`}</span>
                  <span class="item-id">ID: {relayId}</span>
                </div>
                <div class="item-controls">
                  <button 
                    class="btn btn-sm btn-primary"
                    on:click={() => runTest('relay', relayId, 'basic')}
                    disabled={activeTests.has(`relay-${relayId}-basic`)}
                  >
                    Basic Test
                  </button>
                  <button 
                    class="btn btn-sm btn-secondary"
                    on:click={() => runTest('relay', relayId, 'advanced')}
                    disabled={activeTests.has(`relay-${relayId}-advanced`)}
                  >
                    Advanced Test
                  </button>
                </div>
              </div>
            {/each}
          </div>

          <div class="test-info">
            <div class="info-item">
              <strong>Basic Test:</strong> Single relay ON/OFF sequence
            </div>
            <div class="info-item">
              <strong>Advanced Test:</strong> Tank mixing relay set (relays 4 & 7)
            </div>
          </div>
        </div>
      {/if}

      {#if selectedHardware === 'pumps'}
        <div class="hardware-section">
          <h3>Nute Pump Testing (I2C EZO Pumps)</h3>
          <p class="section-description">Atlas Scientific EZO pump communication over I2C</p>
          
          <div class="hardware-grid">
            {#each hardware.pumps.ids as pumpId}
              <div class="hardware-item">
                <div class="item-header">
                  <span class="item-name">{hardware.pumps.names[pumpId] || `Pump ${pumpId}`}</span>
                  <span class="item-id">ID: {pumpId}</span>
                </div>
                <div class="item-controls">
                  <button 
                    class="btn btn-sm btn-primary"
                    on:click={() => runTest('pump', pumpId, 'basic')}
                    disabled={activeTests.has(`pump-${pumpId}-basic`)}
                  >
                    Basic Test
                  </button>
                  <button 
                    class="btn btn-sm btn-secondary"
                    on:click={() => runTest('pump', pumpId, 'recipe')}
                    disabled={activeTests.has(`pump-${pumpId}-recipe`)}
                  >
                    Recipe Test
                  </button>
                </div>
              </div>
            {/each}
          </div>

          <div class="test-info">
            <div class="info-item">
              <strong>Basic Test:</strong> Single pump 1ml dispense
            </div>
            <div class="info-item">
              <strong>Recipe Test:</strong> Multi-pump nutrient recipe sequence
            </div>
          </div>
        </div>
      {/if}

      {#if selectedHardware === 'flow'}
        <div class="hardware-section">
          <h3>Flow Meter Testing (GPIO Pulse Counting)</h3>
          <p class="section-description">Analog pulse-based flow meters with GPIO interrupt handling</p>
          
          <div class="hardware-grid">
            {#each hardware.flow_meters.ids as flowId}
              <div class="hardware-item">
                <div class="item-header">
                  <span class="item-name">{hardware.flow_meters.names[flowId] || `Flow Meter ${flowId}`}</span>
                  <span class="item-id">ID: {flowId}</span>
                </div>
                <div class="item-controls">
                  <button 
                    class="btn btn-sm btn-primary"
                    on:click={() => runTest('flow', flowId, 'basic')}
                    disabled={activeTests.has(`flow-${flowId}-basic`)}
                  >
                    Basic Test
                  </button>
                  <button 
                    class="btn btn-sm btn-secondary"
                    on:click={() => runTest('flow', flowId, 'pulse_test')}
                    disabled={activeTests.has(`flow-${flowId}-pulse_test`)}
                  >
                    Pulse Test
                  </button>
                </div>
              </div>
            {/each}
          </div>

          <div class="test-info">
            <div class="info-item">
              <strong>Basic Test:</strong> Start/stop flow monitoring
            </div>
            <div class="info-item">
              <strong>Pulse Test:</strong> Monitor pulse count and rate (220 pulses/gal)
            </div>
          </div>
        </div>
      {/if}

      {#if selectedHardware === 'sensors'}
        <div class="hardware-section">
          <h3>pH/EC Sensor Testing (Arduino Uno via USB Serial)</h3>
          <p class="section-description">Arduino Uno connected via USB serial for sensor readings</p>
          
          <div class="hardware-grid">
            <div class="hardware-item">
              <div class="item-header">
                <span class="item-name">pH/EC Sensor Array</span>
                <span class="item-id">Arduino Uno</span>
              </div>
              <div class="item-controls">
                <button 
                  class="btn btn-sm btn-primary"
                  on:click={() => runTest('sensor', 'ecph', 'basic')}
                  disabled={activeTests.has('sensor-ecph-basic')}
                >
                  Basic Test
                </button>
                <button 
                  class="btn btn-sm btn-secondary"
                  on:click={() => runTest('sensor', 'ecph', 'continuous')}
                  disabled={activeTests.has('sensor-ecph-continuous')}
                >
                  Continuous Test
                </button>
              </div>
            </div>
          </div>

          <div class="test-info">
            <div class="info-item">
              <strong>Basic Test:</strong> Single pH/EC/Temperature reading
            </div>
            <div class="info-item">
              <strong>Continuous Test:</strong> 30-second continuous monitoring
            </div>
          </div>
        </div>
      {/if}

    </div>

    <!-- Live Log Panel -->
    <div class="log-panel">
      <div class="log-header">
        <h3>Command & Response Log</h3>
        <div class="log-controls">
          <label class="checkbox-label">
            <input type="checkbox" bind:checked={autoScroll}>
            Auto-scroll
          </label>
          <button class="btn btn-sm btn-secondary" on:click={clearLog}>
            Clear
          </button>
        </div>
      </div>

      <div class="log-container" id="log-container">
        {#each logEntries as entry}
          <div class="log-entry {getLogClass(entry.level)}">
            <span class="log-time">{entry.timestamp}</span>
            <span class="log-message">{entry.message}</span>
            {#if entry.details}
              <div class="log-details">{entry.details}</div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

<style>
  .testing-suite {
    background: #1a1a1a;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 20px;
    font-family: 'Consolas', 'Monaco', monospace;
  }

  .testing-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #333;
  }

  .testing-header h1 {
    color: #00ff88;
    font-size: 24px;
    margin: 0;
  }

  .header-controls {
    display: flex;
    gap: 10px;
  }

  .stats-section {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
  }

  .stat-card {
    background: #2a2a2a;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #444;
    text-align: center;
    min-width: 120px;
  }

  .stat-value {
    font-size: 24px;
    color: #00ff88;
    font-weight: bold;
  }

  .stat-label {
    font-size: 12px;
    color: #999;
    margin-top: 5px;
  }

  .hardware-tabs {
    display: flex;
    gap: 5px;
    margin-bottom: 20px;
    border-bottom: 1px solid #333;
  }

  .tab {
    background: #2a2a2a;
    border: 1px solid #444;
    border-bottom: none;
    padding: 10px 20px;
    color: #ccc;
    cursor: pointer;
    transition: all 0.2s;
  }

  .tab:hover {
    background: #333;
    color: #fff;
  }

  .tab.active {
    background: #00ff88;
    color: #1a1a1a;
    font-weight: bold;
  }

  .testing-content {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 20px;
    height: 600px;
  }

  .testing-panel {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 20px;
    overflow-y: auto;
  }

  .hardware-section h3 {
    color: #00ff88;
    margin: 0 0 10px 0;
    font-size: 18px;
  }

  .section-description {
    color: #ccc;
    font-size: 14px;
    margin-bottom: 20px;
  }

  .hardware-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
  }

  .hardware-item {
    background: #333;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 15px;
  }

  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .item-name {
    font-weight: bold;
    color: #fff;
  }

  .item-id {
    font-size: 12px;
    color: #bbb;
  }

  .item-controls {
    display: flex;
    gap: 8px;
  }

  .test-info {
    background: #1e1e1e;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 15px;
  }


  .info-item {
    margin-bottom: 8px;
    font-size: 13px;
    color: #ddd;
  }

  .info-item strong {
    color: #00ff88;
  }

  .log-panel {
    background: #1e1e1e;
    border: 1px solid #444;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
  }

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border-bottom: 1px solid #333;
  }

  .log-header h3 {
    margin: 0;
    color: #00ff88;
    font-size: 16px;
  }

  .log-controls {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 5px;
    color: #ddd;
    font-size: 12px;
  }

  .log-container {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    font-size: 12px;
    line-height: 1.4;
  }

  .log-entry {
    margin-bottom: 8px;
    padding: 6px;
    border-radius: 4px;
    border-left: 3px solid;
  }

  .log-time {
    color: #666;
    font-size: 10px;
    margin-right: 8px;
  }

  .log-message {
    color: #f0f0f0;
    font-weight: 500;
  }

  .log-details {
    margin-top: 4px;
    font-size: 11px;
    color: #ccc;
    padding-left: 12px;
  }

  .log-info {
    border-left-color: #0088ff;
    background: rgba(0, 136, 255, 0.1);
  }

  .log-success {
    border-left-color: #00ff88;
    background: rgba(0, 255, 136, 0.1);
  }

  .log-warning {
    border-left-color: #ffaa00;
    background: rgba(255, 170, 0, 0.1);
  }

  .log-error {
    border-left-color: #ff4444;
    background: rgba(255, 68, 68, 0.1);
  }

  .log-command {
    border-left-color: #ff00ff;
    background: rgba(255, 0, 255, 0.1);
  }

  .log-response {
    border-left-color: #00ffff;
    background: rgba(0, 255, 255, 0.1);
  }

  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #00ff88;
    color: #1a1a1a;
  }

  .btn-primary:hover:not(:disabled) {
    background: #00cc66;
  }

  .btn-secondary {
    background: #666;
    color: #fff;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #777;
  }

  .btn-danger {
    background: #ff4444;
    color: #fff;
  }

  .btn-danger:hover:not(:disabled) {
    background: #cc3333;
  }

  .btn-sm {
    padding: 6px 12px;
    font-size: 12px;
  }
</style>