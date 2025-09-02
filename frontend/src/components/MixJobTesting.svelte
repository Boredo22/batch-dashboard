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
        description: 'Turn on tank mixing relays (circulation pumps)',
        commands: tank ? tank.mix_relays.map(id => `"Start;Relay;${id};ON;end"`) : [],
        responses: tank ? tank.mix_relays.map(id => `"Relay ${id} ON"`) : []
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
        description: 'Begin monitoring solution parameters',
        commands: [`"Start;EcPh;ON;end"`],
        responses: [`"Started EC/pH monitoring"`]
      },
      { 
        id: 'pump_dosing', 
        name: 'Nutrient Dosing', 
        description: 'Run peristaltic pumps for calculated dosage rates',
        commands: tank ? [
          `"Start;Dispense;${tank.pumps[0]};${Math.round(gallons * 2.5)};end"`, // Nutrient A
          `"Start;Dispense;${tank.pumps[1]};${Math.round(gallons * 2.5)};end"`, // Nutrient B  
          `"Start;Dispense;${tank.pumps[2]};${Math.round(gallons * 1.0)};end"`   // Cal-Mag
        ] : [],
        responses: tank ? [
          `"Dispensing ${Math.round(gallons * 2.5)}ml from pump ${tank.pumps[0]}"`, // Nutrient A
          `"Dispensing ${Math.round(gallons * 2.5)}ml from pump ${tank.pumps[1]}"`, // Nutrient B
          `"Dispensing ${Math.round(gallons * 1.0)}ml from pump ${tank.pumps[2]}"`   // Cal-Mag
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
        description: 'Stop EC/pH monitoring system',
        commands: [`"Start;EcPh;OFF;end"`],
        responses: [`"Stopped EC/pH monitoring"`]
      },
      { 
        id: 'mix_relays_off', 
        name: 'Stop Mixing', 
        description: 'Turn off tank mixing relays',
        commands: tank ? tank.mix_relays.map(id => `"Start;Relay;${id};OFF;end"`) : [],
        responses: tank ? tank.mix_relays.map(id => `"Relay ${id} OFF"`) : []
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
      
      <button class="action-btn start-btn" onclick={handleStart}>
        <i class="fas fa-play"></i> Start Mix Job
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
      
      <button class="action-btn stop-btn" onclick={handleStop}>
        <i class="fas fa-stop"></i> Stop Mix Job
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
        <span>EC/pH Monitoring System</span>
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
        <span class="log-type">Commands:</span> "Start;Relay;4;ON;end" | "Start;Dispense;1;50;end" | "Start;EcPh;ON;end"
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
  .mix-job-container {
    background: #2d3748;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    border: 1px solid #4a5568;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid #4a5568;
  }

  .section-header h3 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .section-header i {
    margin-right: 8px;
    color: #10b981;
  }

  .job-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .job-status.active {
    background: #1a2e1a;
    color: #4ade80;
  }

  .job-status.idle {
    background: #2d2d2d;
    color: #a0aec0;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .job-status.active .status-dot {
    background: #22c55e;
  }

  .job-status.idle .status-dot {
    background: #6b7280;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .job-config {
    margin-bottom: 24px;
  }

  .config-info {
    margin-bottom: 16px;
  }

  .info-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #1a202c;
    border: 1px solid #f59e0b;
    border-radius: 8px;
  }

  .info-card i {
    color: #f59e0b;
    font-size: 1.2rem;
  }

  .info-text {
    color: #e2e8f0;
    font-size: 0.9rem;
    line-height: 1.4;
  }

  .input-group {
    margin-bottom: 16px;
  }

  .input-group label {
    display: block;
    font-weight: 500;
    color: #e2e8f0;
    font-size: 0.9rem;
    margin-bottom: 6px;
  }

  .input-group select {
    width: 100%;
    padding: 12px;
    border: 2px solid #4a5568;
    border-radius: 8px;
    font-size: 0.9rem;
    transition: border-color 0.2s;
    background: #1a202c;
    color: #e2e8f0;
  }

  .input-group select:focus {
    outline: none;
    border-color: #10b981;
  }

  .job-progress {
    margin-bottom: 24px;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .job-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .job-label {
    font-size: 0.8rem;
    color: #a0aec0;
    font-weight: 500;
  }

  .job-details {
    font-size: 0.9rem;
    color: #e2e8f0;
    font-weight: 600;
  }

  .timer {
    font-size: 0.85rem;
    color: #10b981;
    font-weight: 600;
  }

  .progress-percent {
    font-size: 1.2rem;
    font-weight: bold;
    color: #10b981;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: #1a202c;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 16px;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #10b981, #059669);
    transition: width 0.3s ease;
  }

  .live-readings {
    display: flex;
    gap: 24px;
    margin-bottom: 16px;
    padding: 12px;
    background: #1a202c;
    border-radius: 8px;
    border: 1px solid #4a5568;
  }

  .reading-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .reading-label {
    font-size: 0.8rem;
    color: #a0aec0;
    font-weight: 500;
  }

  .reading-value {
    font-size: 1.1rem;
    font-weight: bold;
    color: #e2e8f0;
  }

  .reading-value.warning {
    color: #f59e0b;
    animation: pulse 1s infinite;
  }

  .action-btn {
    width: 100%;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .start-btn {
    background: #10b981;
    color: white;
  }

  .start-btn:hover {
    background: #059669;
    transform: translateY(-1px);
  }

  .stop-btn {
    background: #ef4444;
    color: white;
  }

  .stop-btn:hover {
    background: #dc2626;
    transform: translateY(-1px);
  }

  .process-steps {
    margin-bottom: 24px;
  }

  .steps-header {
    margin-bottom: 12px;
  }

  .steps-header h4 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
  }

  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 300px;
    overflow-y: auto;
  }

  .step-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    background: #1a202c;
    border: 1px solid #4a5568;
    transition: all 0.2s;
  }

  .step-item.active {
    background: #1a2e1a;
    border-color: #10b981;
  }

  .step-item.completed {
    background: #1a2e1a;
    border-color: #22c55e;
  }

  .step-indicator {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    margin-top: 2px;
  }

  .step-item.pending .step-indicator {
    color: #6b7280;
  }

  .step-item.active .step-indicator {
    color: #10b981;
  }

  .step-item.completed .step-indicator {
    color: #22c55e;
  }

  .step-content {
    flex: 1;
  }

  .step-name {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 0.9rem;
    margin-bottom: 4px;
  }

  .step-description {
    font-size: 0.8rem;
    color: #a0aec0;
    line-height: 1.4;
    margin-bottom: 8px;
  }

  .step-commands, .step-responses {
    margin-top: 8px;
  }

  .commands-label, .responses-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #cbd5e0;
    margin-bottom: 4px;
  }

  .commands-label {
    color: #f59e0b;
  }

  .responses-label {
    color: #22c55e;
  }

  .command-item, .response-item {
    font-size: 0.75rem;
    font-family: 'Courier New', monospace;
    background: #0f172a;
    padding: 4px 8px;
    border-radius: 4px;
    margin-bottom: 2px;
    border-left: 2px solid;
  }

  .command-item {
    border-left-color: #f59e0b;
    color: #fbbf24;
  }

  .response-item {
    border-left-color: #22c55e;
    color: #86efac;
  }

  .hardware-info, .dosage-info {
    margin-bottom: 20px;
  }

  .hardware-header, .dosage-header {
    margin-bottom: 12px;
  }

  .hardware-header h4, .dosage-header h4 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
  }

  .hardware-list, .dosage-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .hardware-item, .dosage-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    color: #cbd5e0;
  }

  .hardware-item i {
    color: #10b981;
    width: 16px;
  }

  .dosage-item {
    justify-content: space-between;
    padding: 6px 0;
  }

  .nutrient-name {
    font-weight: 500;
  }

  .dosage-rate {
    color: #10b981;
    font-weight: 600;
  }

  .log-info {
    padding-top: 16px;
    border-top: 1px solid #4a5568;
  }

  .log-info-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #a0aec0;
  }

  .log-info-header i {
    color: #10b981;
  }

  .log-examples {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .log-example {
    font-size: 0.8rem;
    padding: 4px 0;
    color: #cbd5e0;
  }

  .log-type {
    font-weight: 600;
  }

  .log-example.command .log-type {
    color: #f59e0b;
  }

  .log-example.success .log-type {
    color: #22c55e;
  }

  .log-example.warning .log-type {
    color: #f59e0b;
  }

  .log-example.error .log-type {
    color: #ef4444;
  }

  @media (max-width: 600px) {
    .progress-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
    
    .live-readings {
      flex-direction: column;
      gap: 12px;
    }

    .dosage-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
  }
</style>