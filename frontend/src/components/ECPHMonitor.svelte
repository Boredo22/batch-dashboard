<script>
  let { ecValue = 0, phValue = 0, ecPhMonitoring = false, onStartMonitoring, onStopMonitoring } = $props();

  async function handleStart() {
    if (onStartMonitoring) {
      await onStartMonitoring();
    }
  }

  async function handleStop() {
    if (onStopMonitoring) {
      await onStopMonitoring();
    }
  }
</script>

<div class="ecph-monitor-container">
  <div class="section-header">
    <h3><i class="fas fa-heartbeat"></i> EC/pH Monitoring</h3>
    <div class="monitoring-status {ecPhMonitoring ? 'active' : 'inactive'}">
      <div class="status-dot"></div>
      {ecPhMonitoring ? 'Monitoring' : 'Stopped'}
    </div>
  </div>
  
  <div class="ecph-content">
    <div class="readings-grid">
      <div class="reading-card ec-card">
        <div class="reading-icon">
          <i class="fas fa-tint"></i>
        </div>
        <div class="reading-info">
          <div class="reading-label">EC Value</div>
          <div class="reading-value">{ecValue.toFixed(2)}</div>
          <div class="reading-unit">mS/cm</div>
        </div>
      </div>
      
      <div class="reading-card ph-card">
        <div class="reading-icon">
          <i class="fas fa-flask"></i>
        </div>
        <div class="reading-info">
          <div class="reading-label">pH Value</div>
          <div class="reading-value">{phValue.toFixed(2)}</div>
          <div class="reading-unit">pH</div>
        </div>
      </div>
    </div>
    
    <div class="control-buttons">
      <button
        class="action-btn start-btn {ecPhMonitoring ? 'active' : ''}"
        onclick={handleStart}
        disabled={ecPhMonitoring}
        aria-label="Start EC/pH monitoring"
      >
        <i class="fas fa-play" aria-hidden="true"></i> Start Monitoring
      </button>
      <button
        class="action-btn stop-btn {!ecPhMonitoring ? 'active' : ''}"
        onclick={handleStop}
        disabled={!ecPhMonitoring}
        aria-label="Stop EC/pH monitoring"
      >
        <i class="fas fa-stop" aria-hidden="true"></i> Stop Monitoring
      </button>
    </div>
    
    <div class="log-info">
      <div class="log-info-header">
        <i class="fas fa-info-circle"></i>
        Log Messages
      </div>
      <div class="log-examples">
        <div class="log-example success">
          <span class="log-type">Success:</span> "Started EC/pH monitoring" | "EC: 2.1 mS/cm, pH: 6.8"
        </div>
        <div class="log-example error">
          <span class="log-type">Error:</span> "Sensor calibration required" | "pH probe disconnected"
        </div>
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

  .ecph-monitor-container {
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

  .monitoring-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    height: 1.25rem;
    padding: 0 0.5rem;
    border-radius: 0.25rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border: 1px solid transparent;
  }

  .monitoring-status.active {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .monitoring-status.inactive {
    background: rgba(100, 116, 139, 0.15);
    color: var(--text-muted);
    border-color: var(--border-subtle);
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .monitoring-status.active .status-dot {
    background: var(--status-success);
  }

  .monitoring-status.inactive .status-dot {
    background: var(--text-muted);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .ecph-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .readings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }

  .reading-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);
  }

  .ec-card {
    border-color: rgba(100, 116, 139, 0.4);
  }

  .ph-card {
    border-color: rgba(100, 116, 139, 0.4);
  }

  .reading-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    background: var(--bg-secondary);
    color: var(--accent-steel);
  }

  .reading-info {
    flex: 1;
  }

  .reading-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
    font-weight: 500;
  }

  .reading-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary);
    font-family: ui-monospace, monospace;
    margin-bottom: 0.125rem;
  }

  .reading-unit {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 500;
  }

  .control-buttons {
    display: flex;
    gap: var(--space-md);
  }

  .action-btn {
    flex: 1;
    height: 2.5rem;
    padding: 0 1rem;
    border-radius: 0.25rem;
    font-weight: 500;
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    border: 1px solid;
  }

  .action-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .start-btn {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .start-btn:hover:not(:disabled) {
    background: rgba(5, 150, 105, 0.25);
  }

  .stop-btn {
    background: rgba(220, 38, 38, 0.15);
    color: var(--status-error);
    border-color: rgba(220, 38, 38, 0.3);
  }

  .stop-btn:hover:not(:disabled) {
    background: rgba(220, 38, 38, 0.25);
  }

  @media (max-width: 600px) {
    .readings-grid {
      grid-template-columns: 1fr;
    }
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