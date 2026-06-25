<script>
  import { Button } from '$lib/components/ui/button';

  let { relays = [], activePumps = [], flowMeters = [], onEmergencyStop } = $props();
</script>

<div class="compact-status-bar">
  <div class="status-section status-relays">
    <div class="status-label">RELAYS</div>
    <div class="relay-indicators">
      {#each relays as relay}
        <div class="relay-indicator {relay.status === 'on' ? 'relay-on' : 'relay-off'}"
             title="{relay.name}: {relay.status.toUpperCase()}">
        </div>
      {/each}
    </div>
  </div>

  <div class="status-divider"></div>

  <div class="status-section status-sensors">
    <div class="status-label">SENSORS</div>
    <div class="sensor-readings">
      <div class="sensor-item" title="pH Level">
        <span class="sensor-label">pH:</span>
        <span class="sensor-value">--</span>
      </div>
      <div class="sensor-item" title="EC Level">
        <span class="sensor-label">EC:</span>
        <span class="sensor-value">--</span>
      </div>
    </div>
  </div>

  <div class="status-divider"></div>

  <div class="status-section status-jobs">
    <div class="status-label">ACTIVE JOBS</div>
    <div class="job-indicators">
      <div class="job-item">
        <span class="job-label">Pumps:</span>
        <span class="job-count">{activePumps.length}</span>
      </div>
      <div class="job-item">
        <span class="job-label">Flow:</span>
        <span class="job-count">{flowMeters.filter(m => m.status !== 'idle' && m.status !== 'development').length}</span>
      </div>
    </div>
  </div>

  <div class="status-spacer"></div>

  <Button
    class="emergency-stop-btn"
    onclick={onEmergencyStop}
    size="sm"
  >
    <svg class="emergency-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" fill="currentColor"/>
      <rect x="9" y="9" width="6" height="6" fill="white"/>
    </svg>
    EMERGENCY STOP
  </Button>
</div>

<style>
  /* Compact Status Bar */
  .compact-status-bar {
    background: hsl(var(--card));
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: var(--space-sm) var(--space-md);
    margin-bottom: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);
    min-height: 52px;
  }

  .status-section {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .status-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .relay-indicators {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .relay-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid var(--border-subtle);
    transition: all 0.2s ease;
  }

  .relay-on {
    background: hsl(var(--brand));
    border-color: hsl(var(--brand));
    box-shadow: 0 0 8px hsl(var(--brand) / 0.6);
  }

  .relay-off {
    background: var(--bg-primary);
    border-color: var(--border-subtle);
  }

  .sensor-readings {
    display: flex;
    gap: var(--space-md);
  }

  .sensor-item {
    display: flex;
    align-items: baseline;
    gap: var(--space-xs);
  }

  .sensor-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 500;
  }

  .sensor-value {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  .job-indicators {
    display: flex;
    gap: var(--space-md);
  }

  .job-item {
    display: flex;
    align-items: baseline;
    gap: var(--space-xs);
  }

  .job-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 500;
  }

  .job-count {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: 600;
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    min-width: 20px;
    text-align: center;
  }

  .status-divider {
    width: 1px;
    height: 24px;
    background: var(--border-subtle);
  }

  .status-spacer {
    flex: 1;
  }

  /* :global because the class is applied to the <Button> child component */
  :global(.emergency-stop-btn) {
    background: var(--status-error) !important;
    color: #fff !important;
    border: 1px solid hsl(0 72% 60% / 0.5) !important;
    font-weight: 700 !important;
    font-size: var(--text-xs) !important;
    height: auto !important;
    padding: var(--space-sm) var(--space-md) !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    white-space: nowrap;
    box-shadow: 0 0 0 1px hsl(0 72% 48% / 0.3), 0 4px 14px hsl(0 72% 48% / 0.25) !important;
  }

  :global(.emergency-stop-btn:hover) {
    background: #dc2626 !important;
    border-color: hsl(0 72% 60% / 0.8) !important;
    box-shadow: 0 0 0 1px hsl(0 72% 55% / 0.5), 0 6px 20px hsl(0 72% 48% / 0.4) !important;
  }

  :global(.emergency-stop-btn:active) {
    background: #b91c1c !important;
    transform: translateY(1px);
  }

  .emergency-icon {
    width: 14px;
    height: 14px;
  }

  @media (max-width: 768px) {
    :global(.emergency-stop-btn) {
      width: 100% !important;
      justify-content: center !important;
    }
  }
</style>
