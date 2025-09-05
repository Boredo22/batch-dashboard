<script>
  let { pumps = [], selectedPump = $bindable(''), pumpAmount = $bindable(10), onDispensePump, onStopPump } = $props();

  async function handleDispense() {
    if (onDispensePump) {
      await onDispensePump();
    }
  }

  async function handleStop() {
    if (onStopPump) {
      await onStopPump();
    }
  }
</script>

<div class="pump-control-container">
  <div class="section-header">
    <h3><i class="fas fa-pump-medical"></i> Pump Controls</h3>
    <div class="controls-header">
      <div class="input-group">
        <label for="pump-amount">Amount (ml)</label>
        <input 
          id="pump-amount" 
          type="number" 
          bind:value={pumpAmount} 
          min="1" 
          max="1000" 
          step="1"
        />
      </div>
    </div>
  </div>
  
  <div class="pump-grid">
    {#each pumps as pump}
      <div class="pump-card {selectedPump == pump.id ? 'selected' : ''} {pump.status === 'running' ? 'active' : 'inactive'}">
        <div class="pump-header">
          <span class="pump-name">{pump.name}</span>
          <div class="pump-status-info">
            <div class="voltage-display">
              <span class="voltage-value {pump.voltage >= 5.0 && pump.voltage <= 12.0 ? 'voltage-normal' : 'voltage-warning'}">{pump.voltage?.toFixed(1) || '0.0'}V</span>
            </div>
            <div class="status-dot {pump.status === 'running' ? 'on' : 'off'}"></div>
          </div>
        </div>
        <!-- Progress bar for active dispensing -->
        {#if pump.is_dispensing && pump.current_volume !== undefined && pump.target_volume !== undefined}
          <div class="progress-container">
            <div class="progress-header">
              <span class="progress-text">Dispensing: {pump.current_volume?.toFixed(1)}ml / {pump.target_volume?.toFixed(1)}ml</span>
              <span class="progress-percentage">{((pump.current_volume / pump.target_volume) * 100).toFixed(1)}%</span>
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                style="width: {Math.min((pump.current_volume / pump.target_volume) * 100, 100)}%"
              ></div>
            </div>
          </div>
        {/if}

        <div class="pump-controls">
          <button 
            class="control-btn dispense-btn {selectedPump == pump.id ? 'selected' : ''}" 
            onclick={() => { selectedPump = pump.id; handleDispense(); }}
            disabled={pump.is_dispensing}
          >
            <i class="fas fa-play"></i> DISPENSE
          </button>
          <button 
            class="control-btn stop-btn" 
            onclick={() => { selectedPump = pump.id; handleStop(); }}
            disabled={!pump.is_dispensing}
          >
            <i class="fas fa-stop"></i> STOP
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
        <span class="log-type">Success:</span> "Dispensing 50ml from pump 3" | "Stopped pump 1"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Invalid pump amount" | "Pump communication timeout"
      </div>
    </div>
  </div>
</div>

<style>
  .pump-control-container {
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
    color: #3b82f6;
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
    width: 80px;
  }

  .input-group input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .pump-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .pump-card {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s;
  }

  .pump-card.selected {
    border-color: #3b82f6;
    background: #1a2332;
  }

  .pump-card.active {
    background: #1a2e1a;
    border-color: #22c55e;
  }

  .pump-card.inactive {
    background: #1a202c;
    border-color: #4a5568;
  }

  .pump-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .pump-name {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 0.9rem;
  }

  .pump-status-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .voltage-display {
    display: flex;
    align-items: center;
  }

  .voltage-value {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid;
  }

  .voltage-normal {
    color: #22c55e;
    border-color: #22c55e;
  }

  .voltage-warning {
    color: #f59e0b;
    border-color: #f59e0b;
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

  .pump-controls {
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

  .dispense-btn {
    background: #1a2e1a;
    color: #4ade80;
    border: 1px solid #22c55e;
  }

  .dispense-btn.selected {
    background: #22c55e;
    color: white;
  }

  .dispense-btn:hover:not(:disabled) {
    background: #22c55e;
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
    
    .pump-grid {
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
    color: #3b82f6;
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

  .progress-container {
    margin: 12px 0;
    padding: 8px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 6px;
    border: 1px solid #4a5568;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .progress-text {
    font-size: 0.8rem;
    color: #e2e8f0;
    font-weight: 500;
  }

  .progress-percentage {
    font-size: 0.75rem;
    color: #22c55e;
    font-weight: 600;
  }

  .progress-bar {
    height: 8px;
    background: #1a202c;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #4a5568;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #22c55e, #4ade80);
    border-radius: 3px;
    transition: width 0.3s ease;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.3);
    animation: pulse-progress 2s infinite;
  }

  @keyframes pulse-progress {
    0%, 100% { 
      box-shadow: 0 0 6px rgba(34, 197, 94, 0.3);
    }
    50% { 
      box-shadow: 0 0 12px rgba(34, 197, 94, 0.6);
    }
  }
</style>