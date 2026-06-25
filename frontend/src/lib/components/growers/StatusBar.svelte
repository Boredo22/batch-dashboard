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
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-subtle);
    padding: var(--space-sm) var(--space-md);
    margin-bottom: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);
    height: 48px;
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
    background: var(--text-primary);
    border-color: var(--text-primary);
    box-shadow: 0 0 8px rgba(241, 245, 249, 0.4);
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

  .emergency-stop-btn {
    background: var(--status-error) !important;
    color: var(--text-button) !important;
    border: 1px solid rgba(220, 38, 38, 0.4) !important;
    font-weight: 600 !important;
    font-size: var(--text-xs) !important;
    padding: var(--space-xs) var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.025em;
    white-space: nowrap;
  }

  .emergency-stop-btn:active {
    background: #b91c1c !important;
    opacity: 0.9;
  }

  .emergency-stop-btn:hover {
    background: #b91c1c !important;
    border-color: rgba(220, 38, 38, 0.6) !important;
  }

  .emergency-icon {
    width: 14px;
    height: 14px;
  }

  @media (max-width: 768px) {
    .emergency-stop-btn {
      width: 100% !important;
      justify-content: center !important;
    }
  }
</style>
