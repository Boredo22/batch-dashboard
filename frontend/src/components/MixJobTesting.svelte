<script>
  let { activeJob = null, onStartJob, onStopJob } = $props();
  
  let selectedTank = $state(1);
  
  const tanks = [
    { id: 1, name: 'Tank 1', mix_relays: [4, 7], pumps: [1, 2, 3] },
    { id: 2, name: 'Tank 2', mix_relays: [5, 8], pumps: [4, 5, 6] },
    { id: 3, name: 'Tank 3', mix_relays: [6, 9], pumps: [7, 8] }
  ];

  function getMixSteps(tankId) {
    const tank = tanks.find(t => t.id === tankId);
    const gallons = 25; // Example gallons for dosage calculation
    
    return [
      { 
        id: 'init', 
        name: 'Initialize', 
        description: 'Validate tank and check minimum 20 gallons present',
        commands: [],
        responses: ['Tank validation complete', 'Volume check: 25 gallons available']
      },
      {
        id: 'mix_relays_on',
        name: 'Start Mixing',
        description: 'Turn on tank mixing relays via GPIO (circulation pumps)',
        commands: tank ? tank.mix_relays.map(id => `POST /api/relay/${id}/on`) : [],
        responses: tank ? tank.mix_relays.map(id => `"Relay ${id} turned ON"`) : []
      },
      { 
        id: 'mixing_delay', 
        name: 'Mixing Delay', 
        description: 'Wait 20 seconds for initial circulation',
        commands: [],
        responses: ['Timer: 20 seconds', 'Initial circulation complete']
      },
      {
        id: 'ecph_start',
        name: 'Start EC/pH Monitor',
        description: 'Begin monitoring solution parameters via EZO I2C sensors (0x63/0x64)',
        commands: [`POST /api/ecph/start`],
        responses: [`"Started EC/pH monitoring - EZO sensors ready"`]
      },
      {
        id: 'pump_dosing',
        name: 'Nutrient Dosing',
        description: 'Run EZO peristaltic pumps for calculated dosage rates via I2C',
        commands: tank ? [
          `POST /api/pump/${tank.pumps[0]}/dispense (${Math.round(gallons * 2.5)}ml)`, // Nutrient A
          `POST /api/pump/${tank.pumps[1]}/dispense (${Math.round(gallons * 2.5)}ml)`, // Nutrient B
          `POST /api/pump/${tank.pumps[2]}/dispense (${Math.round(gallons * 1.0)}ml)`   // Cal-Mag
        ] : [],
        responses: tank ? [
          `"Started dispensing ${Math.round(gallons * 2.5)}ml from pump ${tank.pumps[0]}"`, // Nutrient A
          `"Started dispensing ${Math.round(gallons * 2.5)}ml from pump ${tank.pumps[1]}"`, // Nutrient B
          `"Started dispensing ${Math.round(gallons * 1.0)}ml from pump ${tank.pumps[2]}"`   // Cal-Mag
        ] : []
      },
      { 
        id: 'pump_complete', 
        name: 'Dosing Complete', 
        description: 'All nutrient pumps finished dosing',
        commands: [],
        responses: ['All pumps finished', 'Nutrient dosing complete']
      },
      { 
        id: 'final_mixing', 
        name: 'Final Mixing', 
        description: '1 minute mixing period for complete integration',
        commands: [],
        responses: ['Timer: 60 seconds', 'Final mixing in progress']
      },
      { 
        id: 'final_readings', 
        name: 'Final Readings', 
        description: 'Record final EC/pH values',
        commands: [],
        responses: ['Reading sensors...', 'EC: 1.8 mS/cm, pH: 6.2']
      },
      {
        id: 'ecph_stop',
        name: 'Stop Monitoring',
        description: 'Stop EC/pH monitoring on EZO I2C sensors',
        commands: [`POST /api/ecph/stop`],
        responses: [`"Stopped EC/pH monitoring"`]
      },
      {
        id: 'mix_relays_off',
        name: 'Stop Mixing',
        description: 'Turn off tank mixing relays via GPIO',
        commands: tank ? tank.mix_relays.map(id => `POST /api/relay/${id}/off`) : [],
        responses: tank ? tank.mix_relays.map(id => `"Relay ${id} turned OFF"`) : []
      },
      { 
        id: 'validation', 
        name: 'Validation', 
        description: 'Check if readings are within acceptable range',
        commands: [],
        responses: ['Readings within acceptable range', 'EC: 1.2-2.2 mS/cm ✓', 'pH: 5.8-6.5 ✓']
      },
      { 
        id: 'complete', 
        name: 'Job Complete', 
        description: 'Mix job finished - alert if readings out of range',
        commands: [],
        responses: ['Mix job completed successfully']
      }
    ];
  }

  let mixSteps = $derived(getMixSteps(selectedTank));

  async function handleStart() {
    if (onStartJob) {
      await onStartJob(selectedTank);
    }
  }

  async function handleStop() {
    if (onStopJob) {
      await onStopJob();
    }
  }

  function getStepStatus(stepId) {
    if (!activeJob) return 'pending';
    if (activeJob.current_step === stepId) return 'active';
    if (activeJob.completed_steps && activeJob.completed_steps.includes(stepId)) return 'completed';
    return 'pending';
  }

  function getProgressPercentage() {
    if (!activeJob || !activeJob.completed_steps) return 0;
    return Math.round((activeJob.completed_steps.length / mixSteps.length) * 100);
  }

  function formatTimer(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<div class="mix-job-container">
  <div class="section-header">
    <h3><i class="fas fa-flask"></i> Mix Job Testing</h3>
    <div class="job-status {activeJob ? 'active' : 'idle'}">
      <div class="status-dot"></div>
      {activeJob ? 'Running' : 'Idle'}
    </div>
  </div>

  {#if !activeJob}
    <div class="job-config">
      <div class="config-info">
        <div class="info-card">
          <i class="fas fa-info-circle"></i>
          <div class="info-text">
            <strong>Prerequisites:</strong> Tank must have at least 20 gallons from a completed fill job before mixing can begin.
          </div>
        </div>
      </div>
      
      <div class="input-group">
        <label for="tank-select">Tank Selection</label>
        <select id="tank-select" bind:value={selectedTank}>
          {#each tanks as tank}
            <option value={tank.id}>{tank.name}</option>
          {/each}
        </select>
      </div>
      
      <button class="action-btn start-btn" onclick={handleStart} aria-label="Start mix job for selected tank">
        <i class="fas fa-play" aria-hidden="true"></i> Start Mix Job
      </button>
    </div>
  {:else}
    <div class="job-progress">
      <div class="progress-header">
        <div class="job-info">
          <span class="job-label">Active Job:</span>
          <span class="job-details">Tank {activeJob.tank_id} - Mixing Process</span>
          {#if activeJob.timer_remaining}
            <span class="timer">⏱️ {formatTimer(activeJob.timer_remaining)}</span>
          {/if}
        </div>
        <div class="progress-percent">{getProgressPercentage()}%</div>
      </div>
      
      <div class="progress-bar">
        <div class="progress-fill" style="width: {getProgressPercentage()}%"></div>
      </div>

      {#if activeJob.current_readings}
        <div class="live-readings">
          <div class="reading-item">
            <span class="reading-label">EC:</span>
            <span class="reading-value" class:warning={activeJob.current_readings.ec_warning}>
              {activeJob.current_readings.ec} mS/cm
            </span>
          </div>
          <div class="reading-item">
            <span class="reading-label">pH:</span>
            <span class="reading-value" class:warning={activeJob.current_readings.ph_warning}>
              {activeJob.current_readings.ph}
            </span>
          </div>
        </div>
      {/if}
      
      <button class="action-btn stop-btn" onclick={handleStop} aria-label="Stop active mix job">
        <i class="fas fa-stop" aria-hidden="true"></i> Stop Mix Job
      </button>
    </div>
  {/if}

  <div class="process-steps">
    <div class="steps-header">
      <h4>Mix Process Steps</h4>
    </div>
    
    <div class="steps-list">
      {#each mixSteps as step}
        <div class="step-item {getStepStatus(step.id)}">
          <div class="step-indicator">
            {#if getStepStatus(step.id) === 'completed'}
              <i class="fas fa-check"></i>
            {:else if getStepStatus(step.id) === 'active'}
              <i class="fas fa-spinner fa-spin"></i>
            {:else}
              <i class="fas fa-circle"></i>
            {/if}
          </div>
          <div class="step-content">
            <div class="step-name">{step.name}</div>
            <div class="step-description">{step.description}</div>
            
            {#if step.commands && step.commands.length > 0}
              <div class="step-commands">
                <div class="commands-label">Commands Sent:</div>
                {#each step.commands as command}
                  <div class="command-item">{command}</div>
                {/each}
              </div>
            {/if}
            
            {#if step.responses && step.responses.length > 0}
              <div class="step-responses">
                <div class="responses-label">Expected Responses:</div>
                {#each step.responses as response}
                  <div class="response-item">{response}</div>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>

  <div class="hardware-info">
    <div class="hardware-header">
      <h4>Hardware Involved</h4>
    </div>
    <div class="hardware-list">
      <div class="hardware-item">
        <i class="fas fa-toggle-on"></i>
        <span>Mixing Relays (Relays {tanks.find(t => t.id === selectedTank)?.mix_relays.join(', ')})</span>
      </div>
      <div class="hardware-item">
        <i class="fas fa-pump-medical"></i>
        <span>Nutrient Pumps (Pumps {tanks.find(t => t.id === selectedTank)?.pumps.join(', ')})</span>
      </div>
      <div class="hardware-item">
        <i class="fas fa-heartbeat"></i>
        <span>EZO EC/pH Sensors (I2C 0x63/0x64 via Atlas isolation shield)</span>
      </div>
    </div>
  </div>

  <div class="dosage-info">
    <div class="dosage-header">
      <h4>Dosage Calculations</h4>
    </div>
    <div class="dosage-list">
      <div class="dosage-item">
        <span class="nutrient-name">Nutrient A:</span>
        <span class="dosage-rate">2.5 ml/gallon</span>
      </div>
      <div class="dosage-item">
        <span class="nutrient-name">Nutrient B:</span>
        <span class="dosage-rate">2.5 ml/gallon</span>
      </div>
      <div class="dosage-item">
        <span class="nutrient-name">Cal-Mag:</span>
        <span class="dosage-rate">1.0 ml/gallon</span>
      </div>
    </div>
  </div>

  <div class="log-info">
    <div class="log-info-header">
      <i class="fas fa-info-circle"></i>
      Command Examples
    </div>
    <div class="log-examples">
      <div class="log-example command">
        <span class="log-type">API Calls:</span> POST /api/relay/4/on | POST /api/pump/1/dispense | POST /api/ecph/start
      </div>
      <div class="log-example success">
        <span class="log-type">Success:</span> "Mix job started" | "Dosing complete" | "Final EC: 1.8, pH: 6.2"
      </div>
      <div class="log-example warning">
        <span class="log-type">Warning:</span> "EC out of range (2.8 mS/cm)" | "pH too high (7.2)" | "Manual adjustment needed"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Insufficient volume (&lt;20 gal)" | "Pump malfunction" | "Sensor failure"
      </div>
    </div>
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;
    --accent-steel: #64748b;
    --accent-slate: #475569;
    --status-success: #059669;
    --status-warning: #d97706;
    --status-error: #dc2626;
    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;
    --border-subtle: #334155;
    --border-emphasis: #475569;
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 0.75rem;
    --text-xs: 0.6875rem;
    --text-sm: 0.8125rem;
    --text-base: 0.9375rem;
  }

  .mix-job-container {
    background: var(--bg-card);
    border-radius: 0.375rem;
    padding: var(--space-md);
    border: 1px solid var(--border-subtle);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
    padding-bottom: var(--space-sm);
    border-bottom: 1px solid var(--border-subtle);
  }

  .section-header h3 {
    margin: 0;
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .section-header i {
    margin-right: var(--space-sm);
    color: var(--accent-steel);
  }

  .job-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    height: 1.25rem;
    padding: 0 0.5rem;
    border-radius: 0.25rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border: 1px solid transparent;
  }

  .job-status.active {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .job-status.idle {
    background: rgba(100, 116, 139, 0.15);
    color: var(--text-muted);
    border-color: var(--border-subtle);
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .job-status.active .status-dot {
    background: var(--status-success);
  }

  .job-status.idle .status-dot {
    background: var(--text-muted);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .job-config {
    margin-bottom: var(--space-md);
  }

  .config-info {
    margin-bottom: var(--space-md);
  }

  .info-card {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    padding: var(--space-md);
    background: var(--bg-primary);
    border: 1px solid var(--status-warning);
    border-radius: 0.375rem;
  }

  .info-card i {
    color: var(--status-warning);
    font-size: var(--text-base);
  }

  .info-text {
    color: var(--text-secondary);
    font-size: var(--text-sm);
    line-height: 1.4;
  }

  .input-group {
    margin-bottom: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .input-group label {
    font-weight: 500;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .input-group select {
    width: 100%;
    height: 2.5rem;
    padding: 0 var(--space-md);
    border: 1px solid var(--border-emphasis);
    border-radius: 0.25rem;
    font-size: var(--text-sm);
    transition: border-color 0.15s ease;
    background: var(--bg-primary);
    color: var(--text-primary);
    outline: none;
  }

  .input-group select:focus {
    border-color: var(--accent-steel);
  }

  .job-progress {
    margin-bottom: var(--space-md);
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .job-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .job-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .job-details {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: 500;
  }

  .timer {
    font-size: var(--text-sm);
    color: var(--status-success);
    font-weight: 500;
  }

  .progress-percent {
    font-size: 1.125rem;
    font-weight: 600;
    font-family: ui-monospace, monospace;
    color: var(--accent-steel);
  }

  .progress-bar {
    width: 100%;
    height: 0.5rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    overflow: hidden;
    margin-bottom: var(--space-md);
  }

  .progress-fill {
    height: 100%;
    background: var(--accent-steel);
    transition: width 0.3s ease;
  }

  .live-readings {
    display: flex;
    gap: var(--space-md);
    margin-bottom: var(--space-md);
    padding: var(--space-md);
    background: var(--bg-primary);
    border-radius: 0.25rem;
    border: 1px solid var(--border-subtle);
  }

  .reading-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .reading-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .reading-value {
    font-size: var(--text-base);
    font-weight: 500;
    font-family: ui-monospace, monospace;
    color: var(--text-primary);
  }

  .reading-value.warning {
    color: var(--status-warning);
    animation: pulse 1s infinite;
  }

  .action-btn {
    width: 100%;
    height: 2.5rem;
    padding: 0 1rem;
    border-radius: 0.25rem;
    font-weight: 500;
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    border: 1px solid;
  }

  .start-btn {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .start-btn:hover {
    background: rgba(5, 150, 105, 0.25);
  }

  .stop-btn {
    background: rgba(220, 38, 38, 0.15);
    color: var(--status-error);
    border-color: rgba(220, 38, 38, 0.3);
  }

  .stop-btn:hover {
    background: rgba(220, 38, 38, 0.25);
  }

  .process-steps {
    margin-bottom: var(--space-md);
  }

  .steps-header {
    margin-bottom: var(--space-md);
  }

  .steps-header h4 {
    margin: 0;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
  }

  .steps-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
    max-height: 300px;
    overflow-y: auto;
  }

  .step-item {
    display: flex;
    align-items: flex-start;
    gap: var(--space-md);
    padding: var(--space-md);
    border-radius: 0.25rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    transition: all 0.15s ease;
  }

  .step-item.active {
    background: rgba(100, 116, 139, 0.1);
    border-color: var(--accent-steel);
  }

  .step-item.completed {
    background: rgba(5, 150, 105, 0.1);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .step-indicator {
    width: 1.25rem;
    height: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--text-xs);
    margin-top: 0.125rem;
  }

  .step-item.pending .step-indicator {
    color: var(--text-muted);
  }

  .step-item.active .step-indicator {
    color: var(--accent-steel);
  }

  .step-item.completed .step-indicator {
    color: var(--status-success);
  }

  .step-content {
    flex: 1;
  }

  .step-name {
    font-weight: 500;
    color: var(--text-primary);
    font-size: var(--text-sm);
    margin-bottom: 0.25rem;
  }

  .step-description {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    line-height: 1.4;
    margin-bottom: var(--space-sm);
  }

  .step-commands, .step-responses {
    margin-top: var(--space-sm);
  }

  .commands-label, .responses-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
  }

  .commands-label {
    color: var(--status-warning);
  }

  .responses-label {
    color: var(--status-success);
  }

  .command-item, .response-item {
    font-size: var(--text-xs);
    font-family: ui-monospace, monospace;
    background: var(--bg-secondary);
    padding: 0.25rem var(--space-sm);
    border-radius: 0.25rem;
    margin-bottom: 0.125rem;
    border-left: 2px solid;
  }

  .command-item {
    border-left-color: var(--status-warning);
    color: var(--status-warning);
  }

  .response-item {
    border-left-color: var(--status-success);
    color: var(--status-success);
  }

  .hardware-info, .dosage-info {
    margin-bottom: var(--space-md);
  }

  .hardware-header, .dosage-header {
    margin-bottom: var(--space-md);
  }

  .hardware-header h4, .dosage-header h4 {
    margin: 0;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
  }

  .hardware-list, .dosage-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .hardware-item, .dosage-item {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .hardware-item i {
    color: var(--accent-steel);
    width: 1rem;
  }

  .dosage-item {
    justify-content: space-between;
    padding: 0.375rem 0;
  }

  .nutrient-name {
    font-weight: 500;
  }

  .dosage-rate {
    color: var(--status-success);
    font-weight: 500;
    font-family: ui-monospace, monospace;
  }

  .log-info {
    padding-top: var(--space-md);
    border-top: 1px solid var(--border-subtle);
  }

  .log-info-header {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-sm);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-muted);
  }

  .log-info-header i {
    color: var(--accent-steel);
  }

  .log-examples {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .log-example {
    font-size: var(--text-xs);
    padding: 0.25rem 0;
    color: var(--text-secondary);
  }

  .log-type {
    font-weight: 500;
  }

  .log-example.command .log-type {
    color: var(--status-warning);
  }

  .log-example.success .log-type {
    color: var(--status-success);
  }

  .log-example.warning .log-type {
    color: var(--status-warning);
  }

  .log-example.error .log-type {
    color: var(--status-error);
  }

  @media (max-width: 600px) {
    .progress-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-sm);
    }

    .live-readings {
      flex-direction: column;
      gap: var(--space-md);
    }

    .dosage-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.25rem;
    }
  }
</style>