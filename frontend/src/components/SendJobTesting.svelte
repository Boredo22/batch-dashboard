<script>
  let { activeJob = null, onStartJob, onStopJob } = $props();
  
  let selectedRoom = $state(1);
  let gallons = $state(15);
  
  const growRooms = [
    { id: 1, name: 'Room 1', tank_id: 1, relay_id: 8, flow_meter_id: 2 },
    { id: 2, name: 'Room 2', tank_id: 2, relay_id: 9, flow_meter_id: 2 },
    { id: 3, name: 'Room 3', tank_id: 3, relay_id: 10, flow_meter_id: 2 }
  ];

  const sendSteps = [
    {
      id: 'init',
      name: 'Initialize',
      description: 'Validate room selection and volume parameters',
      commands: [],
      responses: ['Room validation complete']
    },
    {
      id: 'tank_relay_on',
      name: 'Open Tank Valve',
      description: 'Turn on tank outlet relay via GPIO',
      commands: [`POST /api/relay/${growRooms.find(r => r.id === selectedRoom)?.tank_id}/on`],
      responses: [`"Relay ${growRooms.find(r => r.id === selectedRoom)?.tank_id} turned ON"`]
    },
    {
      id: 'room_relay_on',
      name: 'Open Room Valve',
      description: 'Turn on destination room relay via GPIO',
      commands: [`POST /api/relay/${growRooms.find(r => r.id === selectedRoom)?.relay_id}/on`],
      responses: [`"Relay ${growRooms.find(r => r.id === selectedRoom)?.relay_id} turned ON"`]
    },
    {
      id: 'flow_start',
      name: 'Start Flow Meter',
      description: 'Begin monitoring outbound flow via GPIO pulse counter',
      commands: [`POST /api/flow/2/start (target: 15 gallons)`],
      responses: [`"Started flow meter 2 for 15 gallons"`]
    },
    { 
      id: 'sending', 
      name: 'Sending to Room', 
      description: 'Solution flowing to grow room, monitoring progress',
      commands: [],
      responses: ['Flow progress: 60% complete', 'Rate: 1.8 GPM']
    },
    {
      id: 'flow_complete',
      name: 'Target Reached',
      description: 'Stop flow meter when target volume reached',
      commands: [`POST /api/flow/2/stop`],
      responses: [`"Stopped flow meter 2 - target reached"`]
    },
    {
      id: 'room_relay_off',
      name: 'Close Room Valve',
      description: 'Turn off destination room relay via GPIO',
      commands: [`POST /api/relay/${growRooms.find(r => r.id === selectedRoom)?.relay_id}/off`],
      responses: [`"Relay ${growRooms.find(r => r.id === selectedRoom)?.relay_id} turned OFF"`]
    },
    {
      id: 'tank_relay_off',
      name: 'Close Tank Valve',
      description: 'Turn off tank outlet relay via GPIO',
      commands: [`POST /api/relay/${growRooms.find(r => r.id === selectedRoom)?.tank_id}/off`],
      responses: [`"Relay ${growRooms.find(r => r.id === selectedRoom)?.tank_id} turned OFF"`]
    },
    { 
      id: 'complete', 
      name: 'Job Complete', 
      description: 'Send job finished successfully',
      commands: [],
      responses: ['Send job completed successfully']
    }
  ];

  async function handleStart() {
    if (onStartJob) {
      await onStartJob(selectedRoom, gallons);
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
    return Math.round((activeJob.completed_steps.length / sendSteps.length) * 100);
  }
</script>

<div class="send-job-container">
  <div class="section-header">
    <h3><i class="fas fa-paper-plane"></i> Send Job Testing</h3>
    <div class="job-status {activeJob ? 'active' : 'idle'}">
      <div class="status-dot"></div>
      {activeJob ? 'Running' : 'Idle'}
    </div>
  </div>

  {#if !activeJob}
    <div class="job-config">
      <div class="config-grid">
        <div class="input-group">
          <label for="room-select">Grow Room</label>
          <select id="room-select" bind:value={selectedRoom}>
            {#each growRooms as room}
              <option value={room.id}>{room.name} (Tank {room.tank_id})</option>
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
            max="50" 
            step="1"
          />
        </div>
      </div>
      
      <button class="action-btn start-btn" onclick={handleStart} aria-label="Start send job for selected room">
        <i class="fas fa-play" aria-hidden="true"></i> Start Send Job
      </button>
    </div>
  {:else}
    <div class="job-progress">
      <div class="progress-header">
        <div class="job-info">
          <span class="job-label">Active Job:</span>
          <span class="job-details">Room {activeJob.room_id} - {activeJob.target_gallons} gallons</span>
        </div>
        <div class="progress-percent">{getProgressPercentage()}%</div>
      </div>
      
      <div class="progress-bar">
        <div class="progress-fill" style="width: {getProgressPercentage()}%"></div>
      </div>
      
      <button class="action-btn stop-btn" onclick={handleStop} aria-label="Stop active send job">
        <i class="fas fa-stop" aria-hidden="true"></i> Stop Send Job
      </button>
    </div>
  {/if}

  <div class="process-steps">
    <div class="steps-header">
      <h4>Send Process Steps</h4>
    </div>
    
    <div class="steps-list">
      {#each sendSteps as step}
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
        <span>Tank Outlet Relay (GPIO via ULN2803A - Relay {growRooms.find(r => r.id === selectedRoom)?.tank_id})</span>
      </div>
      <div class="hardware-item">
        <i class="fas fa-toggle-on"></i>
        <span>Room Valve Relay (GPIO via ULN2803A - Relay {growRooms.find(r => r.id === selectedRoom)?.relay_id})</span>
      </div>
      <div class="hardware-item">
        <i class="fas fa-water"></i>
        <span>Outbound Flow Meter (GPIO pulse counter - Flow Meter 2)</span>
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
        <span class="log-type">API Calls:</span> POST /api/relay/{growRooms.find(r => r.id === selectedRoom)?.relay_id}/on | POST /api/flow/2/start
      </div>
      <div class="log-example success">
        <span class="log-type">Success:</span> "Send job started" | "Valves opened" | "Solution delivered successfully"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Invalid room selection" | "Tank empty" | "Flow sensor malfunction"
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

  .send-job-container {
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

  .config-grid {
    display: grid;
    grid-template-columns: 1fr 120px;
    gap: var(--space-md);
    margin-bottom: var(--space-md);
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .input-group label {
    font-weight: 500;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .input-group select, .input-group input {
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

  .input-group select:focus, .input-group input:focus {
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

  .hardware-info {
    margin-bottom: var(--space-md);
  }

  .hardware-header {
    margin-bottom: var(--space-md);
  }

  .hardware-header h4 {
    margin: 0;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
  }

  .hardware-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .hardware-item {
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

  .log-example.error .log-type {
    color: var(--status-error);
  }

  @media (max-width: 600px) {
    .config-grid {
      grid-template-columns: 1fr;
    }

    .progress-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-sm);
    }
  }
</style>