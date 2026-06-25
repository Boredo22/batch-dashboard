<script>
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';

  let { flowMeters = [] } = $props();
</script>

<Card class="monitoring-card card-elevated">
  <CardHeader>
    <CardTitle class="section-title">
      <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 9V5a3 3 0 0 0-6 0v4"/>
        <rect x="2" y="9" width="20" height="12" rx="2"/>
      </svg>
      Flow Monitoring
    </CardTitle>
  </CardHeader>
  <CardContent>
    <div class="flow-monitors">
      {#each flowMeters as meter}
        <div class="flow-meter {meter.status === 'development' ? 'flow-development' : 'flow-active'}">
          <div class="meter-header">
            <div class="meter-name">{meter.name}</div>
            <Badge class={meter.status === 'development' ? 'status-development' : 'status-operational'}>
              {meter.status === 'development' ? 'DEV' : 'ACTIVE'}
            </Badge>
          </div>

          {#if meter.status === 'development'}
            <div class="meter-status">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M7 2h10l5 10-5 10H7l-5-10z"/>
              </svg>
              Under Development
            </div>
          {:else}
            <div class="meter-readings">
              <div class="flow-rate">{meter.flow_rate} <span class="unit">gal/min</span></div>
              <div class="total-flow">Total: {meter.total_gallons} gal</div>
            </div>
          {/if}
        </div>
      {/each}
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

  .monitoring-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  .flow-monitors {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .flow-meter {
    padding: var(--space-md);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
    background: var(--bg-secondary);
  }

  .flow-active {
    border-color: var(--accent-steel);
  }

  .flow-development {
    border-color: var(--status-development);
    opacity: 0.7;
  }

  .meter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
  }

  .meter-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .meter-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--status-development);
    font-size: var(--text-xs);
  }

  .meter-readings {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .flow-rate {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
  }

  .total-flow {
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .unit {
    font-size: var(--text-sm);
    font-weight: 400;
    color: var(--text-muted);
  }

  /* Flow Status Badge Classes */
  :global(.status-development) {
    background: var(--status-development) !important;
    color: var(--bg-primary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }

  :global(.status-operational) {
    background: var(--status-success) !important;
    color: var(--text-button) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }
</style>
