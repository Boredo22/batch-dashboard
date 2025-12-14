<script>
  import { Droplets, Play, Square } from "@lucide/svelte/icons";

  let {
    pumps = [],
    selectedPump = $bindable(""),
    pumpAmount = $bindable(10),
    onDispensePump,
    onStopPump
  } = $props();

  // Ensure pumps is always an array to prevent null reference errors
  let safePumps = $derived(Array.isArray(pumps) ? pumps : []);
  // Convert selectedPump to string to ensure compatibility
  let selectedPumpStr = $derived(selectedPump ? String(selectedPump) : "");
  let selectedPumpData = $derived(selectedPumpStr && selectedPumpStr !== "" ? safePumps.find(p => String(p.id) === selectedPumpStr) : null);
  let isDispensing = $derived(selectedPumpData?.status === 'dispensing');
  let progress = $derived(() => {
    if (!selectedPumpData || !isDispensing) return 0;
    return (selectedPumpData.current_volume / selectedPumpData.target_volume) * 100;
  });

  function handleDispense() {
    if (selectedPump && pumpAmount > 0) {
      onDispensePump?.(selectedPump, pumpAmount);
    }
  }

  function handleStop() {
    if (selectedPump) {
      onStopPump?.(selectedPump);
    }
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center gap-2">
      <Droplets class="icon" />
      <span class="card-title">Pump Control</span>
    </div>
  </div>
  <div class="card-content">
    <div class="control-group">
      <label for="pump-select" class="label">Select Pump</label>
      <select
        bind:value={selectedPumpStr}
        onchange={(e) => selectedPump = e.target.value ? parseInt(e.target.value) : ""}
        class="select-input"
      >
        <option value="" disabled>
          {safePumps.length > 0 ? "Choose a pump..." : "No pumps available"}
        </option>
        {#if safePumps.length > 0}
          {#each safePumps as pump}
            <option value={String(pump.id)}>
              Pump {pump.id} - {pump.name || 'Unnamed'}
            </option>
          {/each}
        {/if}
      </select>
    </div>

    {#if selectedPumpData}
      <div class="pump-details">
        <div class="status-row">
          <span class="status-label">Status</span>
          <span class="status-badge {selectedPumpData.status === 'idle' ? 'status-inactive' : 'status-active'}">
            {selectedPumpData.status.toUpperCase()}
          </span>
        </div>

        {#if isDispensing}
          <div class="progress-container">
            <div class="progress-header">
              <span class="progress-label">Progress</span>
              <span class="progress-value">{selectedPumpData.current_volume || 0}ml / {selectedPumpData.target_volume || 0}ml</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: {progress}%"></div>
            </div>
          </div>
        {/if}

        <div class="control-panel">
          <div class="input-group">
            <label for="pump-amount" class="label">Amount (ml)</label>
            <input
              id="pump-amount"
              type="number"
              bind:value={pumpAmount}
              min="1"
              max="1000"
              disabled={isDispensing}
              class="number-input"
            />
          </div>
          <button
            onclick={handleDispense}
            disabled={isDispensing || !selectedPump}
            class="btn-primary"
          >
            <Play class="btn-icon" />
            Start
          </button>
          <button
            onclick={handleStop}
            disabled={!isDispensing}
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

  .pump-details {
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
