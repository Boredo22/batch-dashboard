<script>
  import { hardwareStore } from '../lib/stores/hardware.svelte.js';
  import Modal from '../lib/components/Modal.svelte';
  import StatusIndicator from '../lib/components/StatusIndicator.svelte';
  import PumpControl from '../lib/components/PumpControl.svelte';

  // Access the store
  const { hardware, status, ui, systemStatus } = hardwareStore;

  // Quick dispense form state
  let quickForm = $state({
    pumpId: '',
    amount: '',
    flowId: '',
    gallons: ''
  });

  // Action modal state
  let actionModal = $state({
    type: null,
    tankId: '',
    actionData: {}
  });

  // Handle quick dispense
  async function handleQuickDispense(event) {
    event.preventDefault();
    if (!quickForm.pumpId || !quickForm.amount) return;
    
    ui.loading = true;
    await hardwareStore.dispensePump(
      parseInt(quickForm.pumpId), 
      parseFloat(quickForm.amount)
    );
    
    // Reset form
    quickForm.pumpId = '';
    quickForm.amount = '';
  }

  // Handle quick flow
  async function handleQuickFlow(event) {
    event.preventDefault();
    if (!quickForm.flowId || !quickForm.gallons) return;
    
    ui.loading = true;
    await hardwareStore.startFlow(
      parseInt(quickForm.flowId), 
      parseInt(quickForm.gallons)
    );
    
    // Reset form
    quickForm.flowId = '';
    quickForm.gallons = '';
  }

  // Emergency stop
  async function handleEmergencyStop() {
    if (!confirm('Are you sure you want to activate emergency stop?')) return;
    await hardwareStore.emergencyStop();
  }

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