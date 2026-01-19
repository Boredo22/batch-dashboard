<script>
  import { onMount, onDestroy } from 'svelte';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';
  import WorkflowFlowchart from './components/filltank/WorkflowFlowchart.svelte';
  import ConfigPanel from './components/filltank/ConfigPanel.svelte';
  import DiagnosticsPanel from './components/filltank/DiagnosticsPanel.svelte';
  import SystemLog from './components/filltank/SystemLog.svelte';

  // SSE Status
  const sseStatus = getSystemStatus();
  let unsubscribe = null;
  let lastProcessedTimestamp = '';

  // ============ CONFIGURATION STATE ============
  let selectedTank = $state(1);
  let targetVolume = $state(25);
  let selectedRecipe = $state('veg_formula');
  let ecTarget = $state({ min: 1.0, max: 2.0 });
  let phTarget = $state({ min: 5.5, max: 6.5 });
  let nutrientOverrides = $state({});

  // Send Configuration
  let selectedRoom = $state(1);
  let sendVolume = $state(25);

  // Phase Enable/Disable
  let enabledPhases = $state({ fill: true, mix: true, send: true });

  // ============ WORKFLOW STATE ============
  let workflowPhase = $state('idle'); // 'idle' | 'filling' | 'mixing' | 'sending' | 'paused' | 'complete' | 'error'
  let currentStepIndex = $state(-1);
  let completedSteps = $state([]);
  let isPaused = $state(false);
  let isTestingMode = $state(false);
  let timerRemaining = $state(null);

  // ============ REAL-TIME DATA (from SSE) ============
  let ecValue = $state(0);
  let phValue = $state(0);
  let ecPhMonitoring = $state(false);
  let flowData = $state({ current: 0, target: 0, rate: 0 });
  let relays = $state([]);
  let pumps = $state([]);
  let flowMeters = $state([]);

  // ============ LOGGING ============
  let logs = $state([]);

  // ============ STATIC DATA ============
  // Tank configuration
  const tanks = [
    { id: 1, name: 'Tank 1 - Grow 1', capacity_gallons: 100, fill_relay: 1, mix_relays: [4, 7], send_relay: 10 },
    { id: 2, name: 'Tank 2 - Grow 2', capacity_gallons: 100, fill_relay: 2, mix_relays: [5, 8], send_relay: 11 },
    { id: 3, name: 'Tank 3 - Nursery', capacity_gallons: 35, fill_relay: 3, mix_relays: [6, 9], send_relay: 12 }
  ];

  // Room configuration
  const rooms = [
    { id: 1, name: 'Grow Room 1', relay: 10 }
  ];

  // Recipes (will be loaded from API)
  let recipes = $state({
    veg_formula: { 'Veg A': 30, 'Veg B': 30, 'pH Down': 0.5, 'Runclean': 0.2 },
    bloom_formula: { 'Bloom A': 30, 'Bloom B': 30, 'pH Down': 0.5, 'Runclean': 0.2 }
  });

  // Pump name to ID mapping
  const pumpNameToId = {
    'Veg A': 1, 'Veg B': 2, 'Bloom A': 3, 'Bloom B': 4,
    'Cake': 5, 'PK Synergy': 6, 'Runclean': 7, 'pH Down': 8
  };

  // ============ DERIVED STATE ============
  let currentTank = $derived(tanks.find(t => t.id === selectedTank) || tanks[0]);
  let currentRoom = $derived(rooms.find(r => r.id === selectedRoom) || rooms[0]);
  let isConnected = $derived(sseStatus.isConnected);
  let isRunning = $derived(workflowPhase !== 'idle' && workflowPhase !== 'complete' && workflowPhase !== 'error');

  // Calculate nutrient doses
  let calculatedDoses = $derived(() => {
    const recipe = recipes[selectedRecipe] || {};
    const doses = {};
    for (const [nutrient, mlPerGallon] of Object.entries(recipe)) {
      const override = nutrientOverrides[nutrient];
      doses[nutrient] = (override ?? mlPerGallon) * targetVolume;
    }
    return doses;
  });

  // Generate workflow steps based on configuration
  let workflowSteps = $derived(() => {
    const steps = [];
    const tank = currentTank;
    const room = currentRoom;

    // Fill Phase
    if (enabledPhases.fill) {
      steps.push(
        { id: 'fill_init', phase: 'fill', name: 'Initialize', description: 'Validate tank and volume', commands: [] },
        { id: 'fill_valve_open', phase: 'fill', name: 'Open Tank Valve', description: `Turn on fill relay ${tank.fill_relay}`, commands: [`Start;Relay;${tank.fill_relay};ON;end`] },
        { id: 'fill_flow_start', phase: 'fill', name: 'Start Flow Meter', description: `Monitor flow for ${targetVolume} gallons`, commands: [`Start;StartFlow;1;${targetVolume};220;end`] },
        { id: 'fill_progress', phase: 'fill', name: 'Filling Tank', description: 'Monitoring flow progress', commands: [], waitCondition: { type: 'flow_complete', flowId: 1 } },
        { id: 'fill_flow_stop', phase: 'fill', name: 'Stop Flow Meter', description: 'Target volume reached', commands: [`Start;StartFlow;1;0;end`] },
        { id: 'fill_valve_close', phase: 'fill', name: 'Close Tank Valve', description: `Turn off fill relay ${tank.fill_relay}`, commands: [`Start;Relay;${tank.fill_relay};OFF;end`] },
        { id: 'fill_complete', phase: 'fill', name: 'Fill Complete', description: 'Tank filled successfully', commands: [] }
      );
    }

    // Mix Phase
    if (enabledPhases.mix) {
      const mixRelayCommands = tank.mix_relays.map(id => `Start;Relay;${id};ON;end`);
      const mixRelayOffCommands = tank.mix_relays.map(id => `Start;Relay;${id};OFF;end`);
      const doses = calculatedDoses();
      const dosingCommands = Object.entries(doses)
        .filter(([_, dose]) => dose > 0)
        .map(([nutrient, dose]) => `Start;Dispense;${pumpNameToId[nutrient]};${Math.round(dose)};end`);

      steps.push(
        { id: 'mix_start', phase: 'mix', name: 'Start Mixing', description: `Turn on mix relays ${tank.mix_relays.join(', ')}`, commands: mixRelayCommands },
        { id: 'mix_circulate', phase: 'mix', name: 'Initial Circulation', description: '20 second mixing delay', commands: [], waitCondition: { type: 'delay', duration: 20000 } },
        { id: 'mix_ecph_start', phase: 'mix', name: 'Start EC/pH Monitor', description: 'Begin monitoring solution', commands: ['Start;EcPh;ON;end'] },
        { id: 'mix_dosing', phase: 'mix', name: 'Nutrient Dosing', description: `Dispensing ${Object.keys(doses).length} nutrients`, commands: dosingCommands, waitCondition: { type: 'pumps_complete' } },
        { id: 'mix_final', phase: 'mix', name: 'Final Mixing', description: '60 second integration period', commands: [], waitCondition: { type: 'delay', duration: 60000 } },
        { id: 'mix_readings', phase: 'mix', name: 'Final Readings', description: 'Recording EC/pH values', commands: [] },
        { id: 'mix_ecph_stop', phase: 'mix', name: 'Stop Monitoring', description: 'Stop EC/pH monitoring', commands: ['Start;EcPh;OFF;end'] },
        { id: 'mix_stop', phase: 'mix', name: 'Stop Mixing', description: `Turn off mix relays ${tank.mix_relays.join(', ')}`, commands: mixRelayOffCommands },
        { id: 'mix_validate', phase: 'mix', name: 'Validation', description: `Check EC (${ecTarget.min}-${ecTarget.max}) and pH (${phTarget.min}-${phTarget.max})`, commands: [] }
      );
    }

    // Send Phase
    if (enabledPhases.send) {
      steps.push(
        { id: 'send_init', phase: 'send', name: 'Initialize Send', description: `Preparing to send ${sendVolume} gallons to ${room.name}`, commands: [] },
        { id: 'send_tank_open', phase: 'send', name: 'Open Tank Valve', description: `Turn on send relay ${tank.send_relay}`, commands: [`Start;Relay;${tank.send_relay};ON;end`] },
        { id: 'send_room_open', phase: 'send', name: 'Open Room Valve', description: `Turn on room relay ${room.relay}`, commands: [`Start;Relay;${room.relay};ON;end`] },
        { id: 'send_flow_start', phase: 'send', name: 'Start Flow Meter', description: `Monitor outbound flow for ${sendVolume} gallons`, commands: [`Start;StartFlow;2;${sendVolume};220;end`] },
        { id: 'send_progress', phase: 'send', name: 'Sending to Room', description: 'Monitoring flow progress', commands: [], waitCondition: { type: 'flow_complete', flowId: 2 } },
        { id: 'send_flow_stop', phase: 'send', name: 'Stop Flow Meter', description: 'Target volume reached', commands: [`Start;StartFlow;2;0;end`] },
        { id: 'send_valves_close', phase: 'send', name: 'Close All Valves', description: 'Turn off all valves', commands: [`Start;Relay;${room.relay};OFF;end`, `Start;Relay;${tank.send_relay};OFF;end`] },
        { id: 'send_complete', phase: 'send', name: 'Send Complete', description: 'Solution sent successfully', commands: [] }
      );
    }

    return steps;
  });

  // ============ SSE DATA PROCESSING ============
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) return;
    if (data.timestamp === lastProcessedTimestamp) return;
    lastProcessedTimestamp = data.timestamp;

    // Update EC/pH
    ecValue = data.ec_value || 0;
    phValue = data.ph_value || 0;
    ecPhMonitoring = data.ec_ph_monitoring || false;

    // Update hardware status
    relays = data.relays || [];
    pumps = data.pumps || [];
    flowMeters = data.flow_meters || [];

    // Update flow data from flow meters
    const activeMeter = flowMeters.find(m => m.status === 'running');
    if (activeMeter) {
      flowData = {
        current: activeMeter.total_gallons || 0,
        target: activeMeter.target_gallons || targetVolume,
        rate: activeMeter.flow_rate || 0
      };
    }
  });

  // ============ LOGGING FUNCTIONS ============
  function addLog(message, type = 'info', step = null) {
    const entry = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      type,
      message,
      step
    };
    logs = [entry, ...logs].slice(0, 200);
  }

  // ============ COMMAND EXECUTION ============
  async function executeCommand(cmdString) {
    const parts = cmdString.split(';');
    const type = parts[1];
    const stepName = workflowSteps()[currentStepIndex]?.name || '';

    addLog(cmdString, 'cmd', stepName);

    try {
      let response;
      const headers = { 'Content-Type': 'application/json' };

      switch (type) {
        case 'Relay': {
          const relayId = parseInt(parts[2]);
          const state = parts[3].toLowerCase();
          response = await fetch(`/api/relay/${relayId}/${state}`, { method: 'POST' });
          break;
        }
        case 'StartFlow': {
          const flowId = parseInt(parts[2]);
          const gallons = parseInt(parts[3]);
          if (gallons === 0) {
            response = await fetch(`/api/flow/${flowId}/stop`, { method: 'POST' });
          } else {
            response = await fetch(`/api/flow/${flowId}/start`, {
              method: 'POST',
              headers,
              body: JSON.stringify({ gallons })
            });
          }
          break;
        }
        case 'Dispense': {
          const pumpId = parseInt(parts[2]);
          const amount = parseFloat(parts[3]);
          response = await fetch(`/api/pump/${pumpId}/dispense`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ amount })
          });
          break;
        }
        case 'EcPh': {
          const state = parts[2];
          const endpoint = state === 'ON' ? '/api/ecph/start' : '/api/ecph/stop';
          response = await fetch(endpoint, { method: 'POST' });
          break;
        }
        default:
          throw new Error(`Unknown command type: ${type}`);
      }

      const result = await response.json();
      if (result.success) {
        addLog(`Response: ${result.message || 'OK'}`, 'rsp', stepName);
      } else {
        addLog(`Error: ${result.error || 'Unknown error'}`, 'err', stepName);
        throw new Error(result.error);
      }
      return result;
    } catch (error) {
      addLog(`Failed: ${error.message}`, 'err', stepName);
      throw error;
    }
  }

  // ============ WAIT CONDITIONS ============
  async function waitForCondition(condition) {
    const stepName = workflowSteps()[currentStepIndex]?.name || '';

    switch (condition.type) {
      case 'delay': {
        const seconds = condition.duration / 1000;
        addLog(`Waiting ${seconds} seconds...`, 'info', stepName);
        timerRemaining = seconds;

        return new Promise((resolve) => {
          const interval = setInterval(() => {
            timerRemaining = Math.max(0, timerRemaining - 1);
            if (timerRemaining <= 0) {
              clearInterval(interval);
              timerRemaining = null;
              resolve();
            }
          }, 1000);
        });
      }
      case 'flow_complete': {
        addLog(`Waiting for flow meter ${condition.flowId} to complete...`, 'info', stepName);
        return new Promise((resolve, reject) => {
          const checkInterval = setInterval(() => {
            const meter = flowMeters.find(m => m.id === condition.flowId);
            if (!meter || meter.status !== 'running') {
              clearInterval(checkInterval);
              resolve();
            }
            // Update flow data
            if (meter) {
              flowData = {
                current: meter.total_gallons || 0,
                target: meter.target_gallons || targetVolume,
                rate: meter.flow_rate || 0
              };
            }
          }, 500);

          // Timeout after 30 minutes
          setTimeout(() => {
            clearInterval(checkInterval);
            reject(new Error('Flow timeout'));
          }, 30 * 60 * 1000);
        });
      }
      case 'pumps_complete': {
        addLog(`Waiting for all pumps to complete...`, 'info', stepName);
        return new Promise((resolve) => {
          const checkInterval = setInterval(() => {
            const anyActive = pumps.some(p => p.is_dispensing);
            if (!anyActive) {
              clearInterval(checkInterval);
              resolve();
            }
          }, 500);
        });
      }
      default:
        return Promise.resolve();
    }
  }

  // ============ WORKFLOW CONTROL ============
  async function startWorkflow() {
    if (isRunning) return;

    addLog('Starting workflow...', 'info');
    completedSteps = [];
    currentStepIndex = 0;
    isPaused = false;

    const steps = workflowSteps();

    for (let i = 0; i < steps.length; i++) {
      // Check for pause
      while (isPaused) {
        await new Promise(r => setTimeout(r, 100));
      }

      // Check for stop
      if (workflowPhase === 'idle' || workflowPhase === 'error') {
        break;
      }

      currentStepIndex = i;
      const step = steps[i];

      // Update workflow phase
      workflowPhase = step.phase === 'fill' ? 'filling' : step.phase === 'mix' ? 'mixing' : 'sending';

      addLog(`Step ${i + 1}/${steps.length}: ${step.name}`, 'info', step.name);

      try {
        // Execute commands
        for (const cmd of step.commands) {
          await executeCommand(cmd);
          // Small delay between commands
          await new Promise(r => setTimeout(r, 300));
        }

        // Wait for condition if needed
        if (step.waitCondition) {
          await waitForCondition(step.waitCondition);
        }

        // Validation step
        if (step.id === 'mix_validate') {
          const ecOk = ecValue >= ecTarget.min && ecValue <= ecTarget.max;
          const phOk = phValue >= phTarget.min && phValue <= phTarget.max;

          if (!ecOk || !phOk) {
            addLog(`Warning: Values out of range - EC: ${ecValue.toFixed(2)} (${ecTarget.min}-${ecTarget.max}), pH: ${phValue.toFixed(2)} (${phTarget.min}-${phTarget.max})`, 'warn', step.name);
          } else {
            addLog(`Validation passed - EC: ${ecValue.toFixed(2)}, pH: ${phValue.toFixed(2)}`, 'success', step.name);
          }
        }

        completedSteps = [...completedSteps, step.id];
        addLog(`Completed: ${step.name}`, 'success', step.name);

      } catch (error) {
        addLog(`Step failed: ${error.message}`, 'err', step.name);
        workflowPhase = 'error';
        await emergencyCleanup();
        return;
      }
    }

    workflowPhase = 'complete';
    currentStepIndex = -1;
    addLog('Workflow completed successfully!', 'success');
  }

  function pauseWorkflow() {
    if (!isRunning) return;
    isPaused = true;
    workflowPhase = 'paused';
    addLog('Workflow paused', 'warn');
  }

  function resumeWorkflow() {
    if (workflowPhase !== 'paused') return;
    isPaused = false;
    const step = workflowSteps()[currentStepIndex];
    workflowPhase = step?.phase === 'fill' ? 'filling' : step?.phase === 'mix' ? 'mixing' : 'sending';
    addLog('Workflow resumed', 'info');
  }

  async function stopWorkflow() {
    addLog('Stopping workflow...', 'warn');
    workflowPhase = 'idle';
    isPaused = false;
    currentStepIndex = -1;
    timerRemaining = null;
    await emergencyCleanup();
    addLog('Workflow stopped', 'warn');
  }

  async function emergencyStop() {
    addLog('EMERGENCY STOP', 'err');
    workflowPhase = 'error';
    isPaused = false;
    currentStepIndex = -1;
    timerRemaining = null;

    try {
      await fetch('/api/emergency/stop', { method: 'POST' });
      addLog('Emergency stop executed - all hardware stopped', 'err');
    } catch (error) {
      addLog(`Emergency stop error: ${error.message}`, 'err');
    }
  }

  async function emergencyCleanup() {
    // Turn off all relays that might be on
    const tank = currentTank;
    const room = currentRoom;

    const relaysToOff = [tank.fill_relay, ...tank.mix_relays, tank.send_relay, room.relay];

    for (const relayId of relaysToOff) {
      try {
        await fetch(`/api/relay/${relayId}/off`, { method: 'POST' });
      } catch (e) {
        // Ignore errors during cleanup
      }
    }

    // Stop flow meters
    try {
      await fetch('/api/flow/1/stop', { method: 'POST' });
      await fetch('/api/flow/2/stop', { method: 'POST' });
    } catch (e) {}

    // Stop EC/pH monitoring
    try {
      await fetch('/api/ecph/stop', { method: 'POST' });
    } catch (e) {}
  }

  // Skip step (testing mode only)
  function skipStep() {
    if (!isTestingMode || !isRunning) return;
    const step = workflowSteps()[currentStepIndex];
    if (step) {
      addLog(`[TEST] Skipping step: ${step.name}`, 'warn', step.name);
      completedSteps = [...completedSteps, step.id];
    }
  }

  // Toggle testing mode
  function toggleTestingMode(enabled) {
    isTestingMode = enabled;
    addLog(`Testing mode ${enabled ? 'enabled' : 'disabled'}`, 'info');
  }

  // ============ LIFECYCLE ============
  onMount(async () => {
    addLog('Fill Tank page initialized', 'info');
    unsubscribe = subscribe();

    // Load nutrients config
    try {
      const response = await fetch('/api/nutrients');
      if (response.ok) {
        const data = await response.json();
        if (data.veg_formula) recipes.veg_formula = data.veg_formula;
        if (data.bloom_formula) recipes.bloom_formula = data.bloom_formula;
        addLog('Loaded nutrient recipes', 'info');
      }
    } catch (error) {
      addLog(`Failed to load recipes: ${error.message}`, 'warn');
    }
  });

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
  });
</script>

<div class="fill-tank-page">
  <!-- Header Bar -->
  <header class="header-bar">
    <div class="header-left">
      <h1><i class="fas fa-fill-drip"></i> Fill Tank</h1>
      <div class="connection-badge" class:connected={isConnected}>
        <div class="status-dot"></div>
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>
    </div>

    <div class="header-center">
      <div class="phase-indicator {workflowPhase}">
        {#if workflowPhase === 'idle'}
          <i class="fas fa-pause"></i> Idle
        {:else if workflowPhase === 'filling'}
          <i class="fas fa-fill-drip fa-pulse"></i> Filling
        {:else if workflowPhase === 'mixing'}
          <i class="fas fa-flask fa-pulse"></i> Mixing
        {:else if workflowPhase === 'sending'}
          <i class="fas fa-share fa-pulse"></i> Sending
        {:else if workflowPhase === 'paused'}
          <i class="fas fa-pause-circle"></i> Paused
        {:else if workflowPhase === 'complete'}
          <i class="fas fa-check-circle"></i> Complete
        {:else if workflowPhase === 'error'}
          <i class="fas fa-exclamation-circle"></i> Error
        {/if}
      </div>

      {#if isRunning}
        <div class="progress-indicator">
          {completedSteps.length}/{workflowSteps().length} steps
        </div>
      {/if}
    </div>

    <div class="header-right">
      <button class="emergency-btn" onclick={emergencyStop} title="Emergency Stop">
        <i class="fas fa-power-off"></i> E-STOP
      </button>
    </div>
  </header>

  <!-- Main Content -->
  <main class="main-content">
    <!-- Left Panel: Configuration -->
    <aside class="config-panel-container">
      <ConfigPanel
        bind:selectedTank
        bind:targetVolume
        {tanks}
        bind:selectedRecipe
        {recipes}
        bind:nutrientOverrides
        bind:ecTarget
        bind:phTarget
        bind:selectedRoom
        bind:sendVolume
        {rooms}
        bind:enabledPhases
        {isRunning}
        {workflowPhase}
      />
    </aside>

    <!-- Center Panel: Workflow Flowchart -->
    <section class="flowchart-container">
      <WorkflowFlowchart
        steps={workflowSteps()}
        {currentStepIndex}
        {completedSteps}
        {workflowPhase}
        {isTestingMode}
      />
    </section>

    <!-- Right Panel: Diagnostics -->
    <aside class="diagnostics-container">
      <DiagnosticsPanel
        {ecValue}
        {phValue}
        {ecTarget}
        {phTarget}
        {ecPhMonitoring}
        {flowData}
        {relays}
        {pumps}
        {flowMeters}
        {isConnected}
        {timerRemaining}
      />
    </aside>
  </main>

  <!-- Control Bar -->
  <div class="control-bar">
    <div class="control-buttons">
      {#if workflowPhase === 'idle' || workflowPhase === 'complete' || workflowPhase === 'error'}
        <button class="control-btn start" onclick={startWorkflow} disabled={!isConnected}>
          <i class="fas fa-play"></i> Start Workflow
        </button>
      {:else if workflowPhase === 'paused'}
        <button class="control-btn resume" onclick={resumeWorkflow}>
          <i class="fas fa-play"></i> Resume
        </button>
        <button class="control-btn stop" onclick={stopWorkflow}>
          <i class="fas fa-stop"></i> Stop
        </button>
      {:else}
        <button class="control-btn pause" onclick={pauseWorkflow}>
          <i class="fas fa-pause"></i> Pause
        </button>
        <button class="control-btn stop" onclick={stopWorkflow}>
          <i class="fas fa-stop"></i> Stop
        </button>
      {/if}

      {#if isTestingMode && isRunning}
        <button class="control-btn skip" onclick={skipStep}>
          <i class="fas fa-forward"></i> Skip Step
        </button>
      {/if}
    </div>
  </div>

  <!-- System Log -->
  <footer class="log-container">
    <SystemLog
      bind:logs
      {isTestingMode}
      onToggleTestingMode={toggleTestingMode}
    />
  </footer>
</div>

<style>
  .fill-tank-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #1a1a1a;
    color: #e2e8f0;
  }

  /* Header Bar */
  .header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    background: #2d3748;
    border-bottom: 1px solid #4a5568;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-bar h1 {
    margin: 0;
    font-size: 1.25rem;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header-bar h1 i {
    color: #3b82f6;
  }

  .connection-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 500;
    background: #2d1a1a;
    color: #ef4444;
  }

  .connection-badge.connected {
    background: #1a2e1a;
    color: #22c55e;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .header-center {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .phase-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    background: #374151;
    color: #a0aec0;
  }

  .phase-indicator.filling {
    background: #1e3a5f;
    color: #3b82f6;
  }

  .phase-indicator.mixing {
    background: #1a3a2a;
    color: #22c55e;
  }

  .phase-indicator.sending {
    background: #3a2a1a;
    color: #f59e0b;
  }

  .phase-indicator.paused {
    background: #3a3a1a;
    color: #eab308;
  }

  .phase-indicator.complete {
    background: #1a2e1a;
    color: #22c55e;
  }

  .phase-indicator.error {
    background: #2d1a1a;
    color: #ef4444;
  }

  .fa-pulse {
    animation: fa-pulse 1s ease-in-out infinite;
  }

  @keyframes fa-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .progress-indicator {
    font-size: 0.85rem;
    color: #a0aec0;
    background: #374151;
    padding: 6px 12px;
    border-radius: 12px;
  }

  .header-right {
    display: flex;
    align-items: center;
  }

  .emergency-btn {
    background: #dc2626;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;
    text-transform: uppercase;
    font-size: 0.85rem;
  }

  .emergency-btn:hover {
    background: #b91c1c;
    transform: scale(1.02);
  }

  /* Main Content */
  .main-content {
    flex: 1;
    display: grid;
    grid-template-columns: 280px 1fr 280px;
    gap: 16px;
    padding: 16px;
    overflow: hidden;
    min-height: 0;
  }

  .config-panel-container,
  .diagnostics-container {
    overflow-y: auto;
    min-height: 0;
  }

  .flowchart-container {
    background: #2d3748;
    border-radius: 12px;
    border: 1px solid #4a5568;
    overflow: hidden;
    min-height: 0;
  }

  /* Control Bar */
  .control-bar {
    padding: 12px 24px;
    background: #2d3748;
    border-top: 1px solid #4a5568;
    border-bottom: 1px solid #4a5568;
  }

  .control-buttons {
    display: flex;
    gap: 12px;
    justify-content: center;
  }

  .control-btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;
    font-size: 0.9rem;
  }

  .control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .control-btn.start {
    background: #22c55e;
    color: white;
  }

  .control-btn.start:hover:not(:disabled) {
    background: #16a34a;
  }

  .control-btn.pause {
    background: #f59e0b;
    color: white;
  }

  .control-btn.pause:hover {
    background: #d97706;
  }

  .control-btn.resume {
    background: #3b82f6;
    color: white;
  }

  .control-btn.resume:hover {
    background: #2563eb;
  }

  .control-btn.stop {
    background: #ef4444;
    color: white;
  }

  .control-btn.stop:hover {
    background: #dc2626;
  }

  .control-btn.skip {
    background: #6366f1;
    color: white;
  }

  .control-btn.skip:hover {
    background: #4f46e5;
  }

  /* Log Container */
  .log-container {
    height: 220px;
    padding: 0 16px 16px;
  }

  /* Responsive */
  @media (max-width: 1200px) {
    .main-content {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr auto;
    }

    .config-panel-container,
    .diagnostics-container {
      max-height: 300px;
    }

    .flowchart-container {
      min-height: 400px;
    }
  }

  @media (max-width: 768px) {
    .header-bar {
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
    }

    .header-center {
      order: 3;
      width: 100%;
      justify-content: center;
    }

    .main-content {
      padding: 12px;
      gap: 12px;
    }

    .control-buttons {
      flex-wrap: wrap;
    }

    .control-btn {
      flex: 1;
      min-width: 120px;
      justify-content: center;
    }

    .log-container {
      height: 180px;
    }
  }
</style>
