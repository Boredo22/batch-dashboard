<script>
  let { flowMeters = [], selectedFlowMeter = $bindable(''), flowGallons = $bindable(1), onStartFlow, onStopFlow } = $props();

  async function handleStart() {
    if (onStartFlow) {
      await onStartFlow();
    }
  }

  async function handleStop() {
    if (onStopFlow) {
      await onStopFlow();
    }
  }
</script>

<div class="flow-control-container">
  <div class="section-header">
    <h3><i class="fas fa-water"></i> Flow Meter Controls</h3>
    <div class="controls-header">
      <div class="input-group">
        <label for="flow-gallons">Gallons</label>
        <input 
          id="flow-gallons" 
          type="number" 
          bind:value={flowGallons} 
          min="1" 
          max="50" 
          step="1"
        />
      </div>
    </div>
  </div>
  
  <div class="flow-grid">
    {#each flowMeters as meter}
      <div class="flow-card {selectedFlowMeter == meter.id ? 'selected' : ''} {meter.status === 'running' ? 'active' : 'inactive'}">
        <div class="flow-header">
          <span class="flow-name">{meter.name}</span>
          <div class="status-dot {meter.status === 'running' ? 'on' : 'off'}"></div>
        </div>
        <div class="flow-info">
          <div class="info-row">
            <span class="info-label">Rate:</span>
            <span class="info-value">{meter.flow_rate || 0} gpm</span>
          </div>
          <div class="info-row">
            <span class="info-label">Total:</span>
            <span class="info-value">{meter.total_gallons || 0} gal</span>
          </div>
        </div>
        <div class="flow-controls">
          <button
            class="control-btn start-btn {selectedFlowMeter == meter.id ? 'selected' : ''}"
            onclick={() => { selectedFlowMeter = meter.id; handleStart(); }}
            aria-label="Start {meter.name}"
          >
            <i class="fas fa-play" aria-hidden="true"></i> START
          </button>
          <button
            class="control-btn stop-btn"
            onclick={() => { selectedFlowMeter = meter.id; handleStop(); }}
            disabled={meter.status !== 'running'}
            aria-label="Stop {meter.name}"
          >
            <i class="fas fa-stop" aria-hidden="true"></i> STOP
          </button>
        </div>
      </div>
    {/each}
  </div>
  
  <div class="log-info">
    <div class="log-info-header">
      <i class="fas fa-info-circle"></i>
      Log Messages
    </div>
    <div class="log-examples">
      <div class="log-example success">
        <span class="log-type">Success:</span> "Started flow meter 1 for 5 gallons" | "Stopped flow meter 2"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Flow meter not calibrated" | "Target volume exceeded"
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

  .flow-control-container {
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

  .controls-header {
    display: flex;
    align-items: center;
    gap: var(--space-md);
  }

  .input-group {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .input-group label {
    font-weight: 500;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    white-space: nowrap;
  }

  .input-group input {
    height: 2.5rem;
    padding: 0 var(--space-md);
    border: 1px solid var(--border-emphasis);
    border-radius: 0.25rem;
    font-size: var(--text-sm);
    transition: border-color 0.15s ease;
    background: var(--bg-primary);
    color: var(--text-primary);
    width: 60px;
    outline: none;
  }

  .input-group input:focus {
    border-color: var(--accent-steel);
  }

  .flow-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }

  .flow-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-md);
    transition: all 0.15s ease;
  }

  .flow-card.selected {
    border-color: var(--accent-steel);
    background: var(--bg-secondary);
  }

  .flow-card.active {
    background: rgba(5, 150, 105, 0.1);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .flow-card.inactive {
    background: var(--bg-primary);
    border-color: var(--border-subtle);
  }

  .flow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .flow-name {
    font-weight: 500;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .status-dot.on {
    background: var(--status-success);
  }

  .status-dot.off {
    background: var(--text-muted);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .flow-info {
    margin-bottom: var(--space-md);
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
  }

  .info-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .info-value {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-primary);
    font-family: ui-monospace, monospace;
  }

  .flow-controls {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .control-btn {
    height: 2.5rem;
    padding: 0 0.875rem;
    border-radius: 0.25rem;
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.25rem;
    border: 1px solid;
  }

  .control-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .start-btn {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .start-btn.selected {
    background: var(--status-success);
    color: white;
    border-color: var(--status-success);
  }

  .start-btn:hover:not(:disabled) {
    background: rgba(5, 150, 105, 0.25);
  }

  .stop-btn {
    background: rgba(220, 38, 38, 0.15);
    color: var(--status-error);
    border-color: rgba(220, 38, 38, 0.3);
  }

  .stop-btn:hover:not(:disabled) {
    background: rgba(220, 38, 38, 0.25);
  }

  @media (max-width: 600px) {
    .section-header {
      flex-direction: column;
      gap: var(--space-md);
      align-items: flex-start;
    }

    .flow-grid {
      grid-template-columns: 1fr;
    }
  }

  .log-info {
    margin-top: var(--space-md);
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

  .log-example.success .log-type {
    color: var(--status-success);
  }

  .log-example.error .log-type {
    color: var(--status-error);
  }
</style>