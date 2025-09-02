<script>
  let { activeJob = null, onStartJob, onStopJob } = $props();
  
  let selectedTank = $state(1);
  let gallons = $state(20);
  
  const tanks = [
    { id: 1, name: 'Tank 1', relay_id: 1 },
    { id: 2, name: 'Tank 2', relay_id: 2 },
    { id: 3, name: 'Tank 3', relay_id: 3 }
  ];

  const fillSteps = [
    { 
      id: 'init', 
      name: 'Initialize', 
      description: 'Validate tank and volume parameters',
      commands: [],
      responses: ['Validation complete']
    },
    { 
      id: 'relay_on', 
      name: 'Open Tank Valve', 
      description: 'Turn on tank relay to open fill valve',
      commands: [`"Start;Relay;${tanks.find(t => t.id === selectedTank)?.relay_id};ON;end"`],
      responses: [`"Relay ${tanks.find(t => t.id === selectedTank)?.relay_id} ON"`]
    },
    { 
      id: 'flow_start', 
      name: 'Start Flow Meter', 
      description: 'Begin monitoring fresh water flow',
      commands: [`"Start;StartFlow;1;${gallons};220;end"`],
      responses: [`"Started flow meter 1 for ${gallons} gallons"`]
    },
    { 
      id: 'filling', 
      name: 'Filling Tank', 
      description: 'Water flowing into tank, monitoring progress',
      commands: [],
      responses: ['Flow progress: 45% complete', 'Rate: 2.3 GPM']
    },
    { 
      id: 'flow_complete', 
      name: 'Target Reached', 
      description: 'Stop flow meter when target volume reached',
      commands: [`"Start;StartFlow;1;0;end"`],
      responses: [`"Stopped flow meter 1"`]
    },
    { 
      id: 'relay_off', 
      name: 'Close Tank Valve', 
      description: 'Turn off tank relay to close fill valve',
      commands: [`"Start;Relay;${tanks.find(t => t.id === selectedTank)?.relay_id};OFF;end"`],
      responses: [`"Relay ${tanks.find(t => t.id === selectedTank)?.relay_id} OFF"`]
    },
    { 
      id: 'complete', 
      name: 'Job Complete', 
      description: 'Fill job finished successfully',
      commands: [],
      responses: ['Fill job completed successfully']
    }
  ];

  async function handleStart() {
    if (onStartJob) {
      await onStartJob(selectedTank, gallons);
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
    return Math.round((activeJob.completed_steps.length / fillSteps.length) * 100);
  }
</script>

<div class="fill-job-container">
  <div class="section-header">
    <h3><i class="fas fa-fill-drip"></i> Fill Job Testing</h3>
    <div class="job-status {activeJob ? 'active' : 'idle'}">
      <div class="status-dot"></div>
      {activeJob ? 'Running' : 'Idle'}
    </div>
  </div>

  {#if !activeJob}
    <div class="job-config">
      <div class="config-grid">
        <div class="input-group">
          <label for="tank-select">Tank Selection</label>
          <select id="tank-select" bind:value={selectedTank}>
            {#each tanks as tank}
              <option value={tank.id}>{tank.name} (Relay {tank.relay_id})</option>
            {/each}
          </select>
        </div>
        
        <div class="input-group">
          <label for="gallons-input">Gallons</label>
          <input 
            id="gallons-input"
            type="number" 
            bind:value={gallons} 
            min="1" 
            max="100" 
            step="1"
          />
        </div>
      </div>
      
      <button class="action-btn start-btn" onclick={handleStart}>
        <i class="fas fa-play"></i> Start Fill Job
      </button>
    </div>
  {:else}
    <div class="job-progress">
      <div class="progress-header">
        <div class="job-info">
          <span class="job-label">Active Job:</span>
          <span class="job-details">Tank {activeJob.tank_id} - {activeJob.target_gallons} gallons</span>
        </div>
        <div class="progress-percent">{getProgressPercentage()}%</div>
      </div>
      
      <div class="progress-bar">
        <div class="progress-fill" style="width: {getProgressPercentage()}%"></div>
      </div>
      
      <button class="action-btn stop-btn" onclick={handleStop}>
        <i class="fas fa-stop"></i> Stop Fill Job
      </button>
    </div>
  {/if}

  <div class="process-steps">
    <div class="steps-header">
      <h4>Fill Process Steps</h4>
    </div>
    
    <div class="steps-list">
      {#each fillSteps as step}
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
        <span>Tank Relay (Relay {tanks.find(t => t.id === selectedTank)?.relay_id})</span>
      </div>
      <div class="hardware-item">
        <i class="fas fa-water"></i>
        <span>Fresh Water Flow Meter (Flow Meter 1)</span>
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
        <span class="log-type">Commands:</span> "Start;Relay;{tanks.find(t => t.id === selectedTank)?.relay_id};ON;end" | "Start;StartFlow;1;{gallons};220;end"
      </div>
      <div class="log-example success">
        <span class="log-type">Success:</span> "Fill job started" | "Tank valve opened" | "Target volume reached"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Invalid tank selection" | "Flow meter timeout" | "Emergency stop triggered"
      </div>
    </div>
  </div>
</div>

<style>
  .fill-job-container {
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
    color: #06b6d4;
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

  .config-grid {
    display: grid;
    grid-template-columns: 1fr 120px;
    gap: 16px;
    margin-bottom: 16px;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .input-group label {
    font-weight: 500;
    color: #e2e8f0;
    font-size: 0.9rem;
  }

  .input-group select, .input-group input {
    padding: 12px;
    border: 2px solid #4a5568;
    border-radius: 8px;
    font-size: 0.9rem;
    transition: border-color 0.2s;
    background: #1a202c;
    color: #e2e8f0;
  }

  .input-group select:focus, .input-group input:focus {
    outline: none;
    border-color: #06b6d4;
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

  .progress-percent {
    font-size: 1.2rem;
    font-weight: bold;
    color: #06b6d4;
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
    background: linear-gradient(90deg, #06b6d4, #0891b2);
    transition: width 0.3s ease;
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
    background: #06b6d4;
    color: white;
  }

  .start-btn:hover {
    background: #0891b2;
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
    background: #1a2a32;
    border-color: #06b6d4;
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
    color: #06b6d4;
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

  .hardware-info {
    margin-bottom: 20px;
  }

  .hardware-header {
    margin-bottom: 12px;
  }

  .hardware-header h4 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
  }

  .hardware-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .hardware-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    color: #cbd5e0;
  }

  .hardware-item i {
    color: #06b6d4;
    width: 16px;
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
    color: #06b6d4;
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

  .log-example.error .log-type {
    color: #ef4444;
  }

  @media (max-width: 600px) {
    .config-grid {
      grid-template-columns: 1fr;
    }
    
    .progress-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
  }
</style>