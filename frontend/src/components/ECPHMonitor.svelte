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
  .ecph-monitor-container {
    background: #2d3748;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    border: 1px solid #4a5568;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid #4a5568;
  }

  .section-header h3 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .section-header i {
    margin-right: 8px;
    color: #10b981;
  }

  .monitoring-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .monitoring-status.active {
    background: #1a2e1a;
    color: #4ade80;
  }

  .monitoring-status.inactive {
    background: #2d1a1a;
    color: #f87171;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .monitoring-status.active .status-dot {
    background: #22c55e;
  }

  .monitoring-status.inactive .status-dot {
    background: #ef4444;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .ecph-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .readings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .reading-card {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 10px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.2s;
  }

  .reading-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  }

  .ec-card {
    border-color: #06b6d4;
  }

  .ph-card {
    border-color: #8b5cf6;
  }

  .reading-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
  }

  .ec-card .reading-icon {
    background: #1a2a2e;
    color: #06b6d4;
  }

  .ph-card .reading-icon {
    background: #2a1a2e;
    color: #8b5cf6;
  }

  .reading-info {
    flex: 1;
  }

  .reading-label {
    font-size: 0.85rem;
    color: #a0aec0;
    margin-bottom: 4px;
    font-weight: 500;
  }

  .reading-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #e2e8f0;
    margin-bottom: 2px;
  }

  .reading-unit {
    font-size: 0.8rem;
    color: #718096;
    font-weight: 500;
  }

  .control-buttons {
    display: flex;
    gap: 12px;
  }

  .action-btn {
    flex: 1;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .start-btn {
    background: #10b981;
    color: white;
  }

  .start-btn:hover:not(:disabled) {
    background: #059669;
    transform: translateY(-1px);
  }

  .stop-btn {
    background: #ef4444;
    color: white;
  }

  .stop-btn:hover:not(:disabled) {
    background: #dc2626;
    transform: translateY(-1px);
  }

  @media (max-width: 600px) {
    .readings-grid {
      grid-template-columns: 1fr;
    }
  }

  .log-info {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #4a5568;
  }

  .log-info-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #a0aec0;
  }

  .log-info-header i {
    color: #10b981;
  }

  .log-examples {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .log-example {
    font-size: 0.8rem;
    padding: 4px 0;
    color: #cbd5e0;
  }

  .log-type {
    font-weight: 600;
  }

  .log-example.success .log-type {
    color: #22c55e;
  }

  .log-example.error .log-type {
    color: #ef4444;
  }
</style>