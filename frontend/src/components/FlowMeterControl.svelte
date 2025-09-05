<script>
  let { flowMeters = [], selectedFlowMeter = $bindable(''), flowGallons = $bindable(1), onStartFlow, onStopFlow } = $props();

  async function handleStart() {
    if (onStartFlow) {
      await onStartFlow();
    }
  }

  async function handleStop() {
    if (onStopFlow) {
      await onStopFlow();
    }
  }
</script>

<div class="flow-control-container">
  <div class="section-header">
    <h3><i class="fas fa-water"></i> Flow Meter Controls</h3>
    <div class="controls-header">
      <div class="input-group">
        <label for="flow-gallons">Gallons</label>
        <input 
          id="flow-gallons" 
          type="number" 
          bind:value={flowGallons} 
          min="1" 
          max="50" 
          step="1"
        />
      </div>
    </div>
  </div>
  
  <div class="flow-grid">
    {#each flowMeters as meter}
      <div class="flow-card {selectedFlowMeter == meter.id ? 'selected' : ''} {meter.status === 'running' ? 'active' : 'inactive'}">
        <div class="flow-header">
          <span class="flow-name">{meter.name}</span>
          <div class="status-dot {meter.status === 'running' ? 'on' : 'off'}"></div>
        </div>
        <div class="flow-info">
          <div class="info-row">
            <span class="info-label">Rate:</span>
            <span class="info-value">{meter.flow_rate || 0} gpm</span>
          </div>
          <div class="info-row">
            <span class="info-label">Total:</span>
            <span class="info-value">{meter.total_gallons || 0} gal</span>
          </div>
        </div>
        <div class="flow-controls">
          <button
            class="control-btn start-btn {selectedFlowMeter == meter.id ? 'selected' : ''}"
            onclick={() => { selectedFlowMeter = meter.id; handleStart(); }}
            aria-label="Start {meter.name}"
          >
            <i class="fas fa-play" aria-hidden="true"></i> START
          </button>
          <button
            class="control-btn stop-btn"
            onclick={() => { selectedFlowMeter = meter.id; handleStop(); }}
            disabled={meter.status !== 'running'}
            aria-label="Stop {meter.name}"
          >
            <i class="fas fa-stop" aria-hidden="true"></i> STOP
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
        <span class="log-type">Success:</span> "Started flow meter 1 for 5 gallons" | "Stopped flow meter 2"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Flow meter not calibrated" | "Target volume exceeded"
      </div>
    </div>
  </div>
</div>

<style>
  .flow-control-container {
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
    color: #06b6d4;
  }

  .controls-header {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .input-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .input-group label {
    font-weight: 500;
    color: #e2e8f0;
    font-size: 0.9rem;
    white-space: nowrap;
  }

  .input-group input {
    padding: 8px 12px;
    border: 2px solid #4a5568;
    border-radius: 6px;
    font-size: 0.9rem;
    transition: border-color 0.2s;
    background: #1a202c;
    color: #e2e8f0;
    width: 60px;
  }

  .input-group input:focus {
    outline: none;
    border-color: #06b6d4;
  }

  .flow-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .flow-card {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s;
  }

  .flow-card.selected {
    border-color: #06b6d4;
    background: #1a2a32;
  }

  .flow-card.active {
    background: #1a2e1a;
    border-color: #22c55e;
  }

  .flow-card.inactive {
    background: #1a202c;
    border-color: #4a5568;
  }

  .flow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .flow-name {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 0.9rem;
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .status-dot.on {
    background: #22c55e;
  }

  .status-dot.off {
    background: #6b7280;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .flow-info {
    margin-bottom: 12px;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
  }

  .info-label {
    font-size: 0.8rem;
    color: #a0aec0;
    font-weight: 500;
  }

  .info-value {
    font-size: 0.8rem;
    font-weight: 600;
    color: #e2e8f0;
  }

  .flow-controls {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .control-btn {
    padding: 8px;
    border: none;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }

  .control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .start-btn {
    background: #1a2a32;
    color: #0fb3d0;
    border: 1px solid #06b6d4;
  }

  .start-btn.selected {
    background: #06b6d4;
    color: white;
  }

  .start-btn:hover:not(:disabled) {
    background: #06b6d4;
    color: white;
    transform: translateY(-1px);
  }

  .stop-btn {
    background: #2d1a1a;
    color: #f87171;
    border: 1px solid #ef4444;
  }

  .stop-btn:hover:not(:disabled) {
    background: #ef4444;
    color: white;
    transform: translateY(-1px);
  }

  @media (max-width: 600px) {
    .section-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;
    }
    
    .flow-grid {
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
    color: #06b6d4;
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