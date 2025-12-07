<script>
  import NuteDispenseProgress from './NuteDispenseProgress.svelte';
  
  let { pumps = [], selectedPump = $bindable(''), pumpAmount = $bindable(10), onDispensePump, onStopPump } = $props();

  async function handleDispense() {
    if (onDispensePump) {
      await onDispensePump();
    }
  }

  async function handleStop() {
    if (onStopPump) {
      await onStopPump();
    }
  }
</script>

<div class="pump-control-container">
  <div class="section-header">
    <h3><i class="fas fa-pump-medical"></i> Pump Controls</h3>
    <div class="controls-header">
      <div class="input-group">
        <label for="pump-amount">Amount (ml)</label>
        <input 
          id="pump-amount" 
          type="number" 
          bind:value={pumpAmount} 
          min="1" 
          max="1000" 
          step="1"
        />
      </div>
    </div>
  </div>
  
  <div class="pump-grid">
    {#each pumps as pump}
      <div class="pump-card {selectedPump == pump.id ? 'selected' : ''} {pump.status === 'running' ? 'active' : 'inactive'}">
        <div class="pump-header">
          <span class="pump-name">{pump.name}</span>
          <div class="pump-status-info">
            <div class="voltage-display">
              <span class="voltage-value {pump.voltage >= 5.0 && pump.voltage <= 12.0 ? 'voltage-normal' : 'voltage-warning'}">{pump.voltage?.toFixed(1) || '0.0'}V</span>
            </div>
            <div class="status-dot {pump.status === 'running' ? 'on' : 'off'}"></div>
          </div>
        </div>
        <!-- Progress bar for active dispensing -->
        {#if pump.is_dispensing || (pump.current_volume > 0)}
          <NuteDispenseProgress
            pumpId={pump.id}
            pumpName={pump.name}
            currentVolume={pump.current_volume || 0}
            targetVolume={pump.target_volume || 0}
            isDispensing={pump.is_dispensing || false}
            voltage={pump.voltage || 0}
            size="compact"
            showVoltage={false}
          />
        {/if}

        <div class="pump-controls">
          <button
            class="control-btn dispense-btn {selectedPump == pump.id ? 'selected' : ''}"
            onclick={() => { selectedPump = pump.id; handleDispense(); }}
            disabled={pump.is_dispensing}
            aria-label="Dispense from {pump.name}"
          >
            <i class="fas fa-play" aria-hidden="true"></i> DISPENSE
          </button>
          <button
            class="control-btn stop-btn"
            onclick={() => { selectedPump = pump.id; handleStop(); }}
            disabled={!pump.is_dispensing}
            aria-label="Stop {pump.name}"
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
        <span class="log-type">Success:</span> "Dispensing 50ml from pump 3" | "Stopped pump 1"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Invalid pump amount" | "Pump communication timeout"
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

  .pump-control-container {
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
    width: 80px;
    outline: none;
  }

  .input-group input:focus {
    border-color: var(--accent-steel);
  }

  .pump-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }

  .pump-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-md);
    transition: all 0.15s ease;
  }

  .pump-card.selected {
    border-color: var(--accent-steel);
    background: var(--bg-secondary);
  }

  .pump-card.active {
    background: rgba(5, 150, 105, 0.1);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .pump-card.inactive {
    background: var(--bg-primary);
    border-color: var(--border-subtle);
  }

  .pump-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .pump-name {
    font-weight: 500;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .pump-status-info {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .voltage-display {
    display: flex;
    align-items: center;
  }

  .voltage-value {
    height: 1.25rem;
    padding: 0 0.5rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid transparent;
    display: flex;
    align-items: center;
  }

  .voltage-normal {
    color: var(--status-success);
    background: rgba(5, 150, 105, 0.15);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .voltage-warning {
    color: var(--status-warning);
    background: rgba(217, 119, 6, 0.15);
    border-color: rgba(217, 119, 6, 0.3);
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

  .pump-controls {
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

  .dispense-btn {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .dispense-btn.selected {
    background: var(--status-success);
    color: white;
    border-color: var(--status-success);
  }

  .dispense-btn:hover:not(:disabled) {
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

    .pump-grid {
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