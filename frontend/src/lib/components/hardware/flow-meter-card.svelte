<script>
  import { Activity, Play, Square } from "@lucide/svelte/icons";

  let {
    flowMeters = [],
    selectedFlowMeter = $bindable(""),
    flowGallons = $bindable(1.0),
    onStartFlow,
    onStopFlow
  } = $props();

  // Ensure flowMeters is always an array to prevent null reference errors
  let safeFlowMeters = $derived(Array.isArray(flowMeters) ? flowMeters : []);
  let selectedFlowMeterData = $derived(selectedFlowMeter && selectedFlowMeter !== "" ? safeFlowMeters.find(f => f.id === selectedFlowMeter) : null);
  let isFlowing = $derived(selectedFlowMeterData?.status === 'flowing');
  let progress = $derived(() => {
    if (!selectedFlowMeterData || !isFlowing) return 0;
    return (selectedFlowMeterData.current_gallons / selectedFlowMeterData.target_gallons) * 100;
  });

  function handleStartFlow() {
    if (selectedFlowMeter && flowGallons > 0) {
      onStartFlow?.(selectedFlowMeter, flowGallons);
    }
  }

  function handleStopFlow() {
    if (selectedFlowMeter) {
      onStopFlow?.(selectedFlowMeter);
    }
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center gap-2">
      <Activity class="icon" />
      <span class="card-title">Flow Meter Control</span>
    </div>
  </div>
  <div class="card-content">
    <div class="control-group">
      <label for="flow-select" class="label">Select Flow Meter</label>
      <select
        bind:value={selectedFlowMeter}
        class="select-input"
      >
        <option value="" disabled>
          {safeFlowMeters.length > 0 ? "Choose a flow meter..." : "No flow meters available"}
        </option>
        {#if safeFlowMeters.length > 0}
          {#each safeFlowMeters as flowMeter}
            <option value={flowMeter.id}>
              Flow Meter {flowMeter.id} - {flowMeter.name || 'Unnamed'}
            </option>
          {/each}
        {/if}
      </select>
    </div>

    {#if selectedFlowMeterData}
      <div class="flow-details">
        <div class="status-row">
          <span class="status-label">Status</span>
          <span class="status-badge {selectedFlowMeterData.status === 'idle' ? 'status-inactive' : 'status-active'}">
            {selectedFlowMeterData.status.toUpperCase()}
          </span>
        </div>

        {#if isFlowing}
          <div class="progress-container">
            <div class="progress-header">
              <span class="progress-label">Progress</span>
              <span class="progress-value">{selectedFlowMeterData.current_gallons || 0} / {selectedFlowMeterData.target_gallons || 0} gal</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: {progress}%"></div>
            </div>
          </div>
        {/if}

        <div class="control-panel">
          <div class="input-group">
            <label for="flow-gallons" class="label">Volume (gallons)</label>
            <input
              id="flow-gallons"
              type="number"
              bind:value={flowGallons}
              min="0.1"
              max="100"
              step="0.1"
              disabled={isFlowing}
              class="number-input"
            />
          </div>
          <button
            onclick={handleStartFlow}
            disabled={isFlowing || !selectedFlowMeter}
            class="btn-primary"
          >
            <Play class="btn-icon" />
            Start
          </button>
          <button
            onclick={handleStopFlow}
            disabled={!isFlowing}
            class="btn-danger"
          >
            <Square class="btn-icon" />
            Stop
          </button>
        </div>
      </div>
    {/if}
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

  .card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 0.375rem;
  }

  .card-header {
    padding: var(--space-md) var(--space-md) var(--space-sm);
    border-bottom: 1px solid var(--border-subtle);
  }

  .card-title {
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .card-content {
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .icon {
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-secondary);
  }

  .select-input {
    height: 2.5rem;
    width: 100%;
    background: var(--bg-primary);
    border: 1px solid var(--border-emphasis);
    border-radius: 0.25rem;
    color: var(--text-primary);
    font-size: var(--text-sm);
    padding: 0 var(--space-md);
    outline: none;
    transition: border-color 0.15s ease;
  }

  .select-input:focus {
    border-color: var(--accent-steel);
  }

  .select-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .flow-details {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .status-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-secondary);
  }

  .status-badge {
    height: 1.25rem;
    padding: 0 0.5rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
  }

  .status-active {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border: 1px solid rgba(5, 150, 105, 0.3);
  }

  .status-inactive {
    background: rgba(100, 116, 139, 0.15);
    color: var(--text-muted);
    border: 1px solid var(--border-subtle);
  }

  .progress-container {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .progress-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-secondary);
  }

  .progress-value {
    font-size: var(--text-xs);
    font-family: ui-monospace, monospace;
    color: var(--text-muted);
  }

  .progress-bar {
    height: 0.5rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent-steel);
    transition: width 0.3s ease;
  }

  .control-panel {
    display: flex;
    gap: var(--space-sm);
    align-items: flex-end;
  }

  .input-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .number-input {
    height: 2.5rem;
    width: 100%;
    background: var(--bg-primary);
    border: 1px solid var(--border-emphasis);
    border-radius: 0.25rem;
    color: var(--text-primary);
    font-size: var(--text-sm);
    padding: 0 var(--space-md);
    outline: none;
    transition: border-color 0.15s ease;
  }

  .number-input:focus {
    border-color: var(--accent-steel);
  }

  .number-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary, .btn-danger {
    height: 2.5rem;
    padding: 0 0.875rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    border: 1px solid transparent;
  }

  .btn-primary {
    background: var(--bg-tertiary);
    border-color: var(--border-emphasis);
    color: var(--text-primary);
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--accent-slate);
  }

  .btn-danger {
    background: rgba(220, 38, 38, 0.15);
    border-color: rgba(220, 38, 38, 0.3);
    color: var(--status-error);
  }

  .btn-danger:hover:not(:disabled) {
    background: rgba(220, 38, 38, 0.25);
  }

  .btn-primary:disabled, .btn-danger:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .btn-icon {
    width: 0.875rem;
    height: 0.875rem;
  }

  .flex {
    display: flex;
  }

  .items-center {
    align-items: center;
  }

  .gap-2 {
    gap: 0.5rem;
  }
</style>
