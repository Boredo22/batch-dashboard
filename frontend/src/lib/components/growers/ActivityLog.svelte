<script>
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';

  let { logs = [], onClear } = $props();
</script>

<Card class="log-card">
  <CardHeader class="log-header">
    <CardTitle class="section-title">
      <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14,2 14,8 20,8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10,9 9,9 8,9"/>
      </svg>
      System Activity
    </CardTitle>
    <Button
      class="clear-logs-btn"
      onclick={onClear}
      size="sm"
      variant="outline"
    >
      Clear
    </Button>
  </CardHeader>
  <CardContent>
    <div class="log-container">
      {#each logs.slice(0, 15) as log}
        <div class="log-entry">
          <div class="log-time">{log.time}</div>
          <div class="log-message">{log.message}</div>
        </div>
      {/each}

      {#if logs.length === 0}
        <div class="log-empty">No recent activity</div>
      {/if}
    </div>
  </CardContent>
</Card>

<style>
  /* shared section-title/icon (also used by other growers cards) */
  .section-title {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--text-primary) !important;
    font-size: var(--text-lg) !important;
    font-weight: 600 !important;
  }

  .section-icon {
    color: var(--accent-steel);
  }

  .log-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .clear-logs-btn {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-muted) !important;
    font-size: var(--text-xs) !important;
  }

  .clear-logs-btn:hover {
    background: var(--bg-tertiary) !important;
    border-color: var(--border-emphasis) !important;
  }

  .log-container {
    max-height: 300px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .log-entry {
    padding: var(--space-sm) var(--space-md);
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    border-left: 2px solid var(--accent-steel);
  }

  .log-time {
    font-size: var(--text-xs);
    color: var(--text-muted);
    margin-bottom: var(--space-xs);
    font-variant-numeric: tabular-nums;
  }

  .log-message {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .log-empty {
    text-align: center;
    color: var(--text-muted);
    font-style: italic;
    padding: var(--space-xl);
  }
</style>
