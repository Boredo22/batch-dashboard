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
    <h3><i class="fas fa-water"></i> Flow Meter Testing</h3>
  </div>
  
  <div class="flow-content">
    <div class="flow-form">
      <div class="form-row">
        <div class="input-group">
          <label for="flow-select">Flow Meter</label>
          <select id="flow-select" bind:value={selectedFlowMeter}>
            <option value="">Select Flow Meter...</option>
            {#each flowMeters as meter}
              <option value={meter.id}>{meter.name}</option>
            {/each}
          </select>
        </div>
        
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
      
      <div class="button-group">
        <button class="action-btn start-btn" onclick={handleStart} disabled={!selectedFlowMeter}>
          <i class="fas fa-play"></i> Start Flow
        </button>
        <button class="action-btn stop-btn" onclick={handleStop} disabled={!selectedFlowMeter}>
          <i class="fas fa-stop"></i> Stop Flow
        </button>
      </div>
    </div>

    <div class="flow-status">
      <div class="status-card">
        <div class="status-label">Selected Meter</div>
        <div class="status-value">{selectedFlowMeter ? flowMeters.find(f => f.id == selectedFlowMeter)?.name : 'None'}</div>
      </div>
      <div class="status-card">
        <div class="status-label">Target Volume</div>
        <div class="status-value">{flowGallons} gal</div>
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

  .flow-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 120px;
    gap: 16px;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .input-group label {
    font-weight: 500;
    color: #e2e8f0;
    font-size: 0.9rem;
  }

  .input-group select, .input-group input {
    padding: 12px;
    border: 2px solid #4a5568;
    border-radius: 8px;
    font-size: 0.9rem;
    transition: border-color 0.2s;
    background: #1a202c;
    color: #e2e8f0;
  }

  .input-group select:focus, .input-group input:focus {
    outline: none;
    border-color: #06b6d4;
  }

  .button-group {
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
    background: #06b6d4;
    color: white;
  }

  .start-btn:hover:not(:disabled) {
    background: #0891b2;
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

  .flow-status {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .status-card {
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
  }

  .status-label {
    font-size: 0.8rem;
    color: #a0aec0;
    margin-bottom: 4px;
    font-weight: 500;
  }

  .status-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: #e2e8f0;
  }

  @media (max-width: 600px) {
    .form-row {
      grid-template-columns: 1fr;
    }
    
    .flow-status {
      grid-template-columns: 1fr;
    }
  }
</style>