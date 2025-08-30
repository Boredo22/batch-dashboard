<!-- src/lib/components/PumpControl.svelte -->
<script>
  import { hardwareStore } from '../stores/hardware.svelte.js';
  
  let { pumpId } = $props();
  
  const { status, ui } = hardwareStore;
  
  // Local form state
  let amount = $state('');
  let rate = $state('');
  
  // Get pump status
  function getPump() {
    return status.pumps?.[pumpId] || {};
  }
  
  // Dispense pump
  async function dispensePump(event) {
    event.preventDefault();
    if (!amount) return;
    
    await hardwareStore.dispensePump(pumpId, parseFloat(amount));
    amount = ''; // Reset form
  }
  
  // Start continuous pump
  async function startPump() {
    if (!rate) return;
    
    try {
      const response = await fetch(`/api/pump/${pumpId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rate: parseFloat(rate) })
      });
      
      const data = await response.json();
      if (data.success) {
        hardwareStore.showNotification(`Pump ${pumpId} started at ${rate} ml/min`, 'success');
        await hardwareStore.updateSystemStatus();
      } else {
        hardwareStore.showNotification(`Pump ${pumpId} start failed: ${data.error}`, 'danger');
      }
    } catch (error) {
      hardwareStore.showNotification(`Pump ${pumpId} error: ${error.message}`, 'danger');
    }
  }
  
  // Stop pump
  async function stopPump() {
    try {
      const response = await fetch(`/api/pump/${pumpId}/stop`, { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        hardwareStore.showNotification(`Pump ${pumpId} stopped`, 'info');
        await hardwareStore.updateSystemStatus();
      } else {
        hardwareStore.showNotification(`Pump ${pumpId} stop failed: ${data.error}`, 'danger');
      }
    } catch (error) {
      hardwareStore.showNotification(`Pump ${pumpId} error: ${error.message}`, 'danger');
    }
  }
  
  // Pause/Resume pump
  async function togglePump() {
    const pump = getPump();
    const action = pump.paused ? 'resume' : 'pause';
    
    try {
      const response = await fetch(`/api/pump/${pumpId}/${action}`, { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        hardwareStore.showNotification(`Pump ${pumpId} ${action}d`, 'info');
        await hardwareStore.updateSystemStatus();
      } else {
        hardwareStore.showNotification(`Pump ${pumpId} ${action} failed: ${data.error}`, 'danger');
      }
    } catch (error) {
      hardwareStore.showNotification(`Pump ${pumpId} error: ${error.message}`, 'danger');
    }
  }
</script>

<div class="pump-control card">
  <div class="card-header d-flex justify-content-between align-items-center">
    <h6 class="mb-0">Pump {pumpId}</h6>
    <span class="badge bg-{getPump().active ? 'success' : 'secondary'}">
      {getPump().active ? (getPump().paused ? 'Paused' : 'Active') : 'Idle'}
    </span>
  </div>
  
  <div class="card-body p-3">
    <!-- Progress bar if active -->
    {#if getPump().active && getPump().progress !== undefined}
      <div class="progress mb-2" style="height: 8px;">
        <div 
          class="progress-bar bg-primary" 
          style="width: {getPump().progress}%"
        ></div>
      </div>
      <small class="text-muted d-block mb-2">
        Progress: {getPump().progress}%
        {#if getPump().rate}
          • {getPump().rate} ml/min
        {/if}
      </small>
    {/if}
    
    <!-- Quick Dispense Form -->
    <form onsubmit={dispensePump} class="mb-2">
      <div class="input-group input-group-sm mb-2">
        <input 
          type="number" 
          bind:value={amount}
          placeholder="Amount (ml)" 
          class="form-control" 
          min="0.1" 
          step="0.1"
          disabled={getPump().active}
        />
        <button 
          type="submit" 
          class="btn btn-primary btn-sm"
          disabled={ui.loading || !amount || getPump().active}
        >
          Dispense
        </button>
      </div>
    </form>
    
    <!-- Continuous Operation -->
    <div class="input-group input-group-sm mb-2">
      <input 
        type="number" 
        bind:value={rate}
        placeholder="Rate (ml/min)" 
        class="form-control" 
        min="1"
        disabled={getPump().active}
      />
      <button 
        type="button" 
        class="btn btn-success btn-sm"
        onclick={startPump}
        disabled={ui.loading || !rate || getPump().active}
      >
        Start
      </button>
    </div>
    
    <!-- Control Buttons -->
    <div class="btn-group w-100" role="group">
      {#if getPump().active}
        <button 
          type="button" 
          class="btn btn-warning btn-sm"
          onclick={togglePump}
          disabled={ui.loading}
        >
          {getPump().paused ? 'Resume' : 'Pause'}
        </button>
        <button 
          type="button" 
          class="btn btn-danger btn-sm"
          onclick={stopPump}
          disabled={ui.loading}
        >
          Stop
        </button>
      {/if}
    </div>
  </div>
</div>

<style>
  .pump-control {
    height: 100%;
    min-height: 200px;
  }
</style>