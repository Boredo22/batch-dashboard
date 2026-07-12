<script>
  import { Beaker } from "@lucide/svelte/icons";

  let {
    tankMonitors = {}
  } = $props();

  // Convert the monitors object (keyed by tank_id) to a sorted array
  let monitorList = $derived(
    Object.values(tankMonitors)
      .filter(m => m && m.tank_id)
      .sort((a, b) => a.tank_id - b.tank_id)
  );

  function getPhStatus(ph) {
    if (!ph || ph <= 0) return 'none';
    if (ph < 5.5) return 'low';
    if (ph > 6.5) return 'high';
    return 'optimal';
  }

  function getEcStatus(ec) {
    if (!ec || ec <= 0) return 'none';
    if (ec < 1.0) return 'low';
    if (ec > 2.5) return 'high';
    return 'optimal';
  }

  function formatTime(isoString) {
    if (!isoString) return 'Never';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="header-row">
      <div class="header-left">
        <Beaker class="icon" />
        <span class="card-title">Tank Monitors</span>
      </div>
      <span class="monitor-count">{monitorList.length} tank{monitorList.length !== 1 ? 's' : ''}</span>
    </div>
  </div>
  <div class="card-content">
    {#if monitorList.length === 0}
      <div class="empty-state">No tank monitors connected</div>
    {:else}
      {#each monitorList as monitor}
        <div class="tank-row">
          <div class="tank-header">
            <span class="tank-name">Tank {monitor.tank_id}</span>
            <span class="connection-badge {monitor.connected ? 'connected' : 'disconnected'}">
              {monitor.connected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
          <div class="readings-row">
            <div class="reading">
              <span class="reading-value status-{getPhStatus(monitor.ph)}">
                {monitor.ph > 0 ? monitor.ph.toFixed(2) : '--'}
              </span>
              <span class="reading-label">pH</span>
            </div>
            <div class="reading-divider"></div>
            <div class="reading">
              <span class="reading-value status-{getEcStatus(monitor.ec)}">
                {monitor.ec > 0 ? monitor.ec.toFixed(2) : '--'}
              </span>
              <span class="reading-label">EC (mS)</span>
            </div>
          </div>
          {#if monitor.last_update}
            <div class="last-update">Updated {formatTime(monitor.last_update)}</div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;

    --accent-steel: #64748b;

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

  .header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .card-title {
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .icon {
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
  }

  .monitor-count {
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .card-content {
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .empty-state {
    text-align: center;
    color: var(--text-muted);
    font-size: var(--text-sm);
    padding: var(--space-md);
  }

  .tank-row {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.375rem;
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .tank-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .tank-name {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-primary);
  }

  .connection-badge {
    height: 1.125rem;
    padding: 0 0.375rem;
    font-size: 0.5625rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    border-radius: 0.1875rem;
    display: flex;
    align-items: center;
  }

  .connection-badge.connected {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border: 1px solid rgba(5, 150, 105, 0.3);
  }

  .connection-badge.disconnected {
    background: rgba(220, 38, 38, 0.15);
    color: var(--status-error);
    border: 1px solid rgba(220, 38, 38, 0.3);
  }

  .readings-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-md);
  }

  .reading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
    flex: 1;
  }

  .reading-value {
    font-size: 1.5rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
  }

  .reading-value.status-optimal {
    color: var(--status-success);
  }

  .reading-value.status-low,
  .reading-value.status-high {
    color: var(--status-warning);
  }

  .reading-value.status-none {
    color: var(--text-muted);
  }

  .reading-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 500;
  }

  .reading-divider {
    width: 1px;
    height: 2rem;
    background: var(--border-subtle);
  }

  .last-update {
    font-size: 0.5625rem;
    color: var(--text-muted);
    text-align: center;
  }
</style>
