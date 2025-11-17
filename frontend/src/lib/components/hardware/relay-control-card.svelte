<script>
  import { Zap } from "@lucide/svelte/icons";

  let { relays = [], onRelayControl } = $props();

  // Ensure relays is always an array to prevent null reference errors
  let safeRelays = $derived(Array.isArray(relays) ? relays : []);

  function handleRelayControl(relayId, action) {
    onRelayControl?.(relayId, action);
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Zap class="icon" />
        <span class="card-title">Relay Control</span>
      </div>
      <button
        onclick={() => handleRelayControl(0, 'off')}
        class="btn-secondary btn-sm"
      >
        All OFF
      </button>
    </div>
  </div>
  <div class="card-content">
    <!-- 3 columns for tablet layout -->
    <div class="relay-grid">
      {#each safeRelays as relay}
        <div class="relay-item">
          <div class="relay-header">
            <span class="relay-label">R{relay.id}</span>
            <span class="status-badge {relay.status === 'on' ? 'status-active' : 'status-inactive'}">
              {relay.status === 'on' ? 'ON' : 'OFF'}
            </span>
          </div>
          <div class="relay-controls">
            <button
              onclick={() => handleRelayControl(relay.id, 'on')}
              class="btn-control {relay.status === 'on' ? 'btn-control-active' : ''}"
            >
              ON
            </button>
            <button
              onclick={() => handleRelayControl(relay.id, 'off')}
              class="btn-control {relay.status === 'off' ? 'btn-control-active' : ''}"
            >
              OFF
            </button>
          </div>
        </div>
      {/each}
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
  }

  .icon {
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
  }

  .btn-secondary {
    background: transparent;
    border: 1px solid var(--border-emphasis);
    color: var(--text-secondary);
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--bg-tertiary);
  }

  .btn-sm {
    height: 1.75rem;
    padding: 0 0.625rem;
    font-size: var(--text-xs);
    font-weight: 500;
  }

  .relay-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-sm);
  }

  .relay-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .relay-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .relay-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-secondary);
  }

  .status-badge {
    height: 1rem;
    padding: 0 0.375rem;
    font-size: 0.625rem;
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

  .relay-controls {
    display: flex;
    gap: var(--space-xs);
  }

  .btn-control {
    flex: 1;
    height: 2.5rem;
    background: transparent;
    border: 1px solid var(--border-emphasis);
    color: var(--text-secondary);
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-control:hover:not(:disabled) {
    background: var(--bg-tertiary);
    border-color: var(--accent-steel);
  }

  .btn-control-active {
    background: var(--bg-tertiary);
    border-color: var(--accent-steel);
    color: var(--text-primary);
  }

  .flex {
    display: flex;
  }

  .items-center {
    align-items: center;
  }

  .justify-between {
    justify-content: space-between;
  }

  .gap-2 {
    gap: 0.5rem;
  }
</style>
