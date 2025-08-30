// 1. Fix hardware.svelte.js store (line with typo)
// In src/lib/stores/hardware.svelte.js, replace the broken line:

  async dispensePump(pumpId, amount) {
    const response = await fetch(`/api/pump/${pumpId}/dispense`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount })
    });
    
    const data = await response.json();
    
    if (data.success) {
      this.showNotification(`Pump ${pumpId} dispensing ${amount}ml`, 'success');
      await this.updateSystemStatus(); // Fix: was "awaiinstructions.md"
    } else {
      this.showNotification(`Pump ${pumpId} failed: ${data.error}`, 'danger');
    }
    
    return data;
  }

// 2. Complete Dashboard.svelte component
// The stopAllOperations function was cut off - here's the complete version:

// Complete Dashboard.svelte - add this to finish the component:
  // Stop all operations
  async function stopAllOperations() {
    if (!confirm('Stop all active operations?')) return;
    await hardwareStore.stopAllOperations();
  }
</script>

<!-- Complete the Dashboard template -->
<div class="container-fluid mt-4">
  <!-- Header -->
  <div class="row mb-4">
    <div class="col">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h1 class="mb-2">
            <i class="fas fa-tachometer-alt me-2"></i>Dashboard
          </h1>
          <StatusIndicator />
        </div>
        
        <div class="d-flex gap-2">
          <button 
            class="btn btn-warning"
            onclick={stopAllOperations}
            disabled={ui.loading}
          >
            <i class="fas fa-stop me-1"></i>
            Stop All
          </button>
          <button 
            class="btn btn-danger"
            onclick={handleEmergencyStop}
            disabled={ui.loading}
          >
            <i class="fas fa-exclamation-triangle me-1"></i>
            Emergency Stop
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Quick Controls -->
  <div class="row mb-4">
    <div class="col-md-6">
      <div class="card">
        <div class="card-header">
          <h5><i class="fas fa-tint me-2"></i>Quick Dispense</h5>
        </div>
        <div class="card-body">
          <form onsubmit={handleQuickDispense}>
            <div class="row">
              <div class="col-sm-4">
                <select 
                  class="form-select" 
                  bind:value={quickForm.pumpId}
                  required
                >
                  <option value="">Select Pump</option>
                  {#each hardware.pumps?.ids || [] as pumpId}
                    <option value={pumpId}>Pump {pumpId}</option>
                  {/each}
                </select>
              </div>
              <div class="col-sm-4">
                <input 
                  type="number" 
                  class="form-control" 
                  bind:value={quickForm.amount}
                  placeholder="Amount (ml)" 
                  min="0.1" 
                  step="0.1"
                  required
                />
              </div>
              <div class="col-sm-4">
                <button 
                  type="submit" 
                  class="btn btn-primary w-100"
                  disabled={ui.loading || !quickForm.pumpId || !quickForm.amount}
                >
                  Dispense
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
    
    <div class="col-md-6">
      <div class="card">
        <div class="card-header">
          <h5><i class="fas fa-water me-2"></i>Quick Flow</h5>
        </div>
        <div class="card-body">
          <form onsubmit={handleQuickFlow}>
            <div class="row">
              <div class="col-sm-4">
                <select 
                  class="form-select" 
                  bind:value={quickForm.flowId}
                  required
                >
                  <option value="">Select Flow</option>
                  {#each hardware.flow_meters?.ids || [] as flowId}
                    <option value={flowId}>Flow {flowId}</option>
                  {/each}
                </select>
              </div>
              <div class="col-sm-4">
                <input 
                  type="number" 
                  class="form-control" 
                  bind:value={quickForm.gallons}
                  placeholder="Gallons" 
                  min="1"
                  required
                />
              </div>
              <div class="col-sm-4">
                <button 
                  type="submit" 
                  class="btn btn-success w-100"
                  disabled={ui.loading || !quickForm.flowId || !quickForm.gallons}
                >
                  Start Flow
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>

  <!-- Pump Controls -->
  <div class="row">
    {#each hardware.pumps?.ids || [] as pumpId}
      <div class="col-lg-3 col-md-4 col-sm-6 mb-3">
        <PumpControl {pumpId} />
      </div>
    {/each}
  </div>

  <!-- Action Modal -->
  {#if ui.activeModal?.id === 'action'}
    <Modal 
      title="Tank Action" 
      onclose={hardwareStore.closeModal}
    >
      <div class="text-center">
        <h5>
          {actionModal.type === 'fill' ? 'Fill' : 'Drain'} Tank {actionModal.tankId}
        </h5>
        <p>Action implementation would go here...</p>
        <button class="btn btn-secondary" onclick={hardwareStore.closeModal}>
          Cancel
        </button>
      </div>
    </Modal>
  {/if}
</div>

// 3. Add missing stopAllOperations method to hardware store
// Add this method to your hardware.svelte.js store:

  async stopAllOperations() {
    const response = await fetch('/api/operations/stop-all', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      this.showNotification('All operations stopped', 'warning');
      await this.updateSystemStatus();
    } else {
      this.showNotification(`Failed to stop operations: ${data.error}`, 'danger');
    }
    
    return data;
  }

// 4. Missing Component Implementations
// Here are the missing component implementations:

// src/lib/components/StatusIndicator.svelte
`<script>
  import { hardwareStore } from '../stores/hardware.svelte.js';
  
  const { systemStatus, statusText, isOnline } = hardwareStore;
</script>

<div class="status-indicator d-flex align-items-center gap-2">
  <div class="status-dot status-dot-{isOnline ? 'online' : 'offline'}"></div>
  <span class="status-text">{statusText}</span>
  {#if systemStatus.timestamp}
    <small class="text-muted">
      Last update: {systemStatus.timestamp}
    </small>
  {/if}
</div>

<style>
  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  
  .status-dot-online {
    background-color: #28a745;
    box-shadow: 0 0 8px rgba(40, 167, 69, 0.5);
  }
  
  .status-dot-offline {
    background-color: #dc3545;
  }
  
  .status-text {
    font-weight: 500;
  }
</style>`

// src/lib/components/Modal.svelte  
`<script>
  export let title = 'Modal';
  export let onclose = () => {};
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div class="modal-backdrop" onclick={onclose}>
  <div class="modal-dialog" onclick|stopPropagation>
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">{title}</h5>
        <button type="button" class="btn-close" onclick={onclose}></button>
      </div>
      <div class="modal-body">
        <slot></slot>
      </div>
    </div>
  </div>
</div>

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
  }
  
  .modal-dialog {
    max-width: 500px;
    width: 90%;
  }
  
  .modal-content {
    background: white;
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .btn-close {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
  }
</style>`

// src/lib/components/NotificationToast.svelte
`<script>
  import { hardwareStore } from '../stores/hardware.svelte.js';
  
  const { ui } = hardwareStore;
</script>

<div class="toast-container">
  {#each ui.notifications as notification (notification.id)}
    <div 
      class="toast show toast-{notification.type}"
      role="alert"
    >
      <div class="toast-header">
        <strong class="me-auto">
          {#if notification.type === 'success'}
            <i class="fas fa-check-circle text-success"></i>
          {:else if notification.type === 'danger'}
            <i class="fas fa-exclamation-circle text-danger"></i>
          {:else if notification.type === 'warning'}
            <i class="fas fa-exclamation-triangle text-warning"></i>
          {:else}
            <i class="fas fa-info-circle text-info"></i>
          {/if}
          Notification
        </strong>
        <button 
          type="button" 
          class="btn-close"
          onclick={() => hardwareStore.removeNotification(notification.id)}
        ></button>
      </div>
      <div class="toast-body">
        {notification.message}
      </div>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1055;
    max-width: 350px;
  }
  
  .toast {
    margin-bottom: 0.5rem;
    background-color: white;
    border: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  }
  
  .toast-header {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.75rem;
    background-color: rgba(0, 0, 0, 0.03);
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: 0.375rem 0.375rem 0 0;
  }
  
  .toast-body {
    padding: 0.75rem;
  }
  
  .btn-close {
    background: none;
    border: none;
    margin-left: auto;
    cursor: pointer;
  }
</style>`