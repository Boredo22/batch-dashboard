<script>
  import { TestTube, Play, Square } from "@lucide/svelte/icons";

  let {
    ecValue = 0,
    phValue = 0,
    ecPhMonitoring = false,
    onStartMonitoring,
    onStopMonitoring
  } = $props();

  function getValueStatus(value, type) {
    if (type === 'ec') {
      if (value < 800) return 'low';
      if (value > 1200) return 'high';
      return 'optimal';
    } else {
      if (value < 5.5) return 'low';
      if (value > 6.5) return 'high';
      return 'optimal';
    }
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <TestTube class="icon" />
        <span class="card-title">EC/pH Monitor</span>
      </div>
      <span class="status-badge {ecPhMonitoring ? 'status-active' : 'status-inactive'}">
        {ecPhMonitoring ? 'ACTIVE' : 'INACTIVE'}
      </span>
    </div>
  </div>
  <div class="card-content">
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-value status-{getValueStatus(ecValue, 'ec')}">
          {ecValue.toFixed(1)}
        </div>
        <div class="metric-label">EC (µS/cm)</div>
        <div class="metric-range">
          <span class="range-indicator">●</span> 800-1200
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-value status-{getValueStatus(phValue, 'ph')}">
          {phValue.toFixed(2)}
        </div>
        <div class="metric-label">pH Level</div>
        <div class="metric-range">
          <span class="range-indicator">●</span> 5.5-6.5
        </div>
      </div>
    </div>

    <div class="control-buttons">
      <button
        onclick={onStartMonitoring}
        disabled={ecPhMonitoring}
        class="btn-primary"
      >
        <Play class="btn-icon" />
        Start
      </button>
      <button
        onclick={onStopMonitoring}
        disabled={!ecPhMonitoring}
        class="btn-danger"
      >
        <Square class="btn-icon" />
        Stop
      </button>
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
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .icon {
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
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

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-md);
  }

  .metric-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.375rem;
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.375rem;
  }

  .metric-value {
    font-size: 1.75rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
  }

  .metric-value.status-optimal {
    color: var(--status-success);
  }

  .metric-value.status-low,
  .metric-value.status-high {
    color: var(--text-muted);
  }

  .metric-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-muted);
  }

  .metric-range {
    font-size: 0.625rem;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .range-indicator {
    color: var(--status-success);
  }

  .control-buttons {
    display: flex;
    gap: var(--space-sm);
  }

  .btn-primary, .btn-danger {
    flex: 1;
    height: 2.5rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
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

  .justify-between {
    justify-content: space-between;
  }

  .gap-2 {
    gap: 0.5rem;
  }
</style>
