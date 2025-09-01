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
    <h3><i class="fas fa-pump-medical"></i> Pump Testing</h3>
  </div>
  
  <div class="pump-content">
    <div class="pump-form">
      <div class="form-row">
        <div class="input-group">
          <label for="pump-select">Pump</label>
          <select id="pump-select" bind:value={selectedPump}>
            <option value="">Select Pump...</option>
            {#each pumps as pump}
              <option value={pump.id}>{pump.name}</option>
            {/each}
          </select>
        </div>
        
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
      
      <div class="button-group">
        <button class="action-btn dispense-btn" onclick={handleDispense} disabled={!selectedPump}>
          <i class="fas fa-play"></i> Dispense
        </button>
        <button class="action-btn stop-btn" onclick={handleStop} disabled={!selectedPump}>
          <i class="fas fa-stop"></i> Stop
        </button>
      </div>
    </div>

    <div class="pump-status">
      <div class="status-card">
        <div class="status-label">Selected Pump</div>
        <div class="status-value">{selectedPump ? pumps.find(p => p.id == selectedPump)?.name : 'None'}</div>
      </div>
      <div class="status-card">
        <div class="status-label">Volume</div>
        <div class="status-value">{pumpAmount} ml</div>
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

  .pump-content {
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
    border-color: #3b82f6;
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

  .dispense-btn {
    background: #10b981;
    color: white;
  }

  .dispense-btn:hover:not(:disabled) {
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

  .pump-status {
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
    
    .pump-status {
      grid-template-columns: 1fr;
    }
  }
</style>