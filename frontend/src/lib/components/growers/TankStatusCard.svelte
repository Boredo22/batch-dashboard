<script>
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Progress } from '$lib/components/ui/progress';

  let {
    tankConfig = {},
    tankStatus = {},
    isProcessing = false,
    getTankStatusBadge,
    onFill,
    onMix,
    onSend
  } = $props();
</script>

<Card class="tank-status-card compact-card">
  <CardHeader>
    <CardTitle class="section-title-compact">Tank Status</CardTitle>
  </CardHeader>
  <CardContent>
    <div class="tank-compact-grid">
      {#each [1, 2, 3] as tankId}
        {@const config = tankConfig[tankId]}
        {@const status = tankStatus[tankId]}
        {@const statusBadge = getTankStatusBadge(status.status)}

        <div class="tank-compact-card">
          <div class="tank-compact-header">
            <div class="tank-compact-info">
              <span class="tank-compact-label">Tank {tankId}</span>
              <Badge class={statusBadge.class}>{statusBadge.text}</Badge>
            </div>
            <div class="tank-compact-volume">{status.volume} gal</div>
          </div>

          <Progress value={status.volume} max={100} class="tank-progress" />

          <div class="tank-compact-controls">
            <Button
              class="tank-compact-btn"
              onclick={() => onFill(tankId)}
              disabled={isProcessing}
              size="sm"
            >
              Fill
            </Button>

            <Button
              class="tank-compact-btn"
              onclick={() => onMix(tankId)}
              disabled={isProcessing}
              size="sm"
            >
              Mix
            </Button>

            <Button
              class="tank-compact-btn"
              onclick={() => onSend(tankId)}
              disabled={isProcessing}
              size="sm"
            >
              Send
            </Button>
          </div>
        </div>
      {/each}
    </div>
  </CardContent>
</Card>

<style>
  .compact-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    height: 100%;
  }

  .section-title-compact {
    font-size: var(--text-base) !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
  }

  .tank-status-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  /* Compact Tank Grid */
  .tank-compact-grid {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .tank-compact-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: var(--space-md);
    transition: all 0.2s ease;
  }

  .tank-compact-card:hover {
    border-color: var(--border-emphasis);
    background: var(--bg-card-hover);
  }

  .tank-compact-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
  }

  .tank-compact-info {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .tank-compact-label {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .tank-compact-volume {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  :global(.tank-progress) {
    margin-bottom: var(--space-md);
    height: 6px !important;
    background: var(--bg-tertiary) !important;
  }

  .tank-compact-controls {
    display: flex;
    gap: var(--space-sm);
  }

  :global(.tank-compact-btn) {
    flex: 1;
    font-size: var(--text-xs) !important;
    padding: var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  :global(.tank-compact-btn:hover) {
    background: var(--accent-steel) !important;
    border-color: var(--border-emphasis) !important;
  }

  :global(.tank-compact-btn:active) {
    opacity: 0.85;
  }

  /* Tank Status Badge Classes */
  :global(.status-idle) {
    background: var(--bg-tertiary) !important;
    color: var(--text-muted) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  :global(.status-filling) {
    background: var(--status-info) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  :global(.status-mixing) {
    background: var(--status-warning) !important;
    color: var(--bg-primary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  :global(.status-sending) {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  :global(.status-ready) {
    background: var(--accent-steel) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }
</style>
