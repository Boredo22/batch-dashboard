<script>
  let { relays = [], onRelayControl } = $props();

  async function handleRelayControl(relayId, state) {
    if (onRelayControl) {
      await onRelayControl(relayId, state);
    }
  }
</script>

<div class="relay-grid-container">
  <div class="section-header">
    <h3><i class="fas fa-toggle-on"></i> Relay Controls</h3>
    <button class="emergency-btn" onclick={() => handleRelayControl(0, false)} aria-label="Turn off all relays">
      <i class="fas fa-power-off" aria-hidden="true"></i> ALL OFF
    </button>
  </div>
  
  <div class="relay-grid">
    {#each relays as relay}
      <div class="relay-card {relay.state ? 'active' : 'inactive'}">
        <div class="relay-header">
          <span class="relay-name">{relay.name}</span>
          <div class="status-dot {relay.state ? 'on' : 'off'}"></div>
        </div>
        <div class="relay-controls">
          <button
            class="control-btn on-btn {relay.state ? 'active' : ''}"
            onclick={() => handleRelayControl(relay.id, true)}
            aria-label="Turn on {relay.name}"
          >
            ON
          </button>
          <button
            class="control-btn off-btn {!relay.state ? 'active' : ''}"
            onclick={() => handleRelayControl(relay.id, false)}
            aria-label="Turn off {relay.name}"
          >
            OFF
          </button>
        </div>
      </div>
    {/each}
  </div>
  
  <div class="log-info">
    <div class="log-info-header">
      <i class="fas fa-info-circle"></i>
      Log Messages
    </div>
    <div class="log-examples">
      <div class="log-example success">
        <span class="log-type">Success:</span> "Relay 5 ON" | "All relays OFF"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Invalid relay ID" | "Hardware communication failed"
      </div>
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

  .relay-grid-container {
    background: var(--bg-card);
    border-radius: 0.375rem;
    padding: var(--space-md);
    border: 1px solid var(--border-subtle);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
    padding-bottom: var(--space-sm);
    border-bottom: 1px solid var(--border-subtle);
  }

  .section-header h3 {
    margin: 0;
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .section-header i {
    margin-right: var(--space-sm);
    color: var(--accent-steel);
  }

  .emergency-btn {
    height: 2.5rem;
    padding: 0 1rem;
    background: rgba(220, 38, 38, 0.15);
    border: 1px solid rgba(220, 38, 38, 0.3);
    color: var(--status-error);
    border-radius: 0.25rem;
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .emergency-btn:hover {
    background: rgba(220, 38, 38, 0.25);
  }

  .relay-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }

  .relay-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-md);
    transition: all 0.15s ease;
  }

  .relay-card.active {
    background: rgba(5, 150, 105, 0.1);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .relay-card.inactive {
    background: var(--bg-primary);
    border-color: var(--border-subtle);
  }

  .relay-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-md);
  }

  .relay-name {
    font-weight: 500;
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .status-dot.on {
    background: var(--status-success);
  }

  .status-dot.off {
    background: var(--status-error);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .relay-controls {
    display: flex;
    gap: 0.375rem;
  }

  .control-btn {
    flex: 1;
    height: 2.5rem;
    padding: 0 0.875rem;
    border-radius: 0.25rem;
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    border: 1px solid;
  }

  .control-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .on-btn {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .on-btn.active {
    background: var(--status-success);
    color: white;
    border-color: var(--status-success);
  }

  .on-btn:hover:not(:disabled) {
    background: rgba(5, 150, 105, 0.25);
  }

  .off-btn {
    background: rgba(220, 38, 38, 0.15);
    color: var(--status-error);
    border-color: rgba(220, 38, 38, 0.3);
  }

  .off-btn.active {
    background: var(--status-error);
    color: white;
    border-color: var(--status-error);
  }

  .off-btn:hover:not(:disabled) {
    background: rgba(220, 38, 38, 0.25);
  }

  .log-info {
    margin-top: var(--space-md);
    padding-top: var(--space-md);
    border-top: 1px solid var(--border-subtle);
  }

  .log-info-header {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-sm);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-muted);
  }

  .log-info-header i {
    color: var(--accent-steel);
  }

  .log-examples {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .log-example {
    font-size: var(--text-xs);
    padding: 0.25rem 0;
    color: var(--text-secondary);
  }

  .log-type {
    font-weight: 500;
  }

  .log-example.success .log-type {
    color: var(--status-success);
  }

  .log-example.error .log-type {
    color: var(--status-error);
  }
</style>