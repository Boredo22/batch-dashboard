<script>
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';
</script>

<Card class="monitoring-card">
  <CardHeader>
    <CardTitle class="section-title">
      <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 12c-2-2.67-4-4-6-4a4 4 0 1 0 0 8c2 0 4-1.33 6-4z"/>
        <path d="M12 12c2-2.67 4-4 6-4a4 4 0 1 1 0 8c-2 0-4-1.33-6-4z"/>
      </svg>
      pH/EC Monitoring
    </CardTitle>
  </CardHeader>
  <CardContent>
    <div class="sensor-grid">
      <div class="sensor-card sensor-development">
        <div class="sensor-header">
          <div class="sensor-name">pH Level</div>
          <Badge class="status-development">DEV</Badge>
        </div>
        <div class="sensor-status">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M7 2h10l5 10-5 10H7l-5-10z"/>
          </svg>
          Under Development
        </div>
      </div>

      <div class="sensor-card sensor-development">
        <div class="sensor-header">
          <div class="sensor-name">EC Level</div>
          <Badge class="status-development">DEV</Badge>
        </div>
        <div class="sensor-status">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M7 2h10l5 10-5 10H7l-5-10z"/>
          </svg>
          Under Development
        </div>
      </div>
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

  /* Sensor Grid */
  .sensor-grid {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .sensor-card {
    padding: var(--space-md);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-subtle);
    background: var(--bg-secondary);
  }

  .sensor-development {
    border-color: var(--status-development);
    opacity: 0.7;
  }

  .sensor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
  }

  .sensor-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .sensor-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    color: var(--status-development);
    font-size: var(--text-xs);
  }

  /* Sensor Status Badge Class */
  :global(.status-development) {
    background: var(--status-development) !important;
    color: var(--bg-primary) !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
  }
</style>
