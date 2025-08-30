<!-- src/routes/Dashboard.svelte -->
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

  // Quick actions
  function openFillAction(tankId) {
    actionModal.type = 'fill';
    actionModal.tankId = tankId;
    hardwareStore.openModal('action');
  }

  function openDrainAction(tankId) {
    actionModal.type = 'drain'; 
    actionModal.tankId = tankId;
    hardwareStore.openModal('action');
  }

  // Emergency stop
  async function handleEmergencyStop() {
    if (!confirm('Are you sure you want to activate emergency stop?')) return;
    await hardwareStore.emergencyStop();
  }

  // Stop all operations
  async function stopAllOperations() {
    if (!confirm('Stop all active operations?')) return;
    
    try {
      const response = await fetch('/api/stop-all', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        hardwareStore.showNotification('All operations stopped', 'success');
        await hardwareStore.updateSystemStatus();
      } else {
        hardwareStore.showNotification(`Failed to stop operations: ${data.error}`, 'danger');
      }
    } catch (error) {
      hardwareStore.showNotification(`Error stopping operations: ${error.message}`, 'danger');
    }
  }
</script>

<!-- Main Dashboard -->
<div class="container mt-4">
  <!-- System Status Header -->
  <div class="system-status mb-4">
    <div class="row align-items-center">
      <div class="col-md-8">
        <h1 class="mb-2">
          <i class="fas fa-flask me-2"></i>
          Nutrient Mixing System
        </h1>
        <StatusIndicator />
      </div>
      <div class="col-md-4 text-end">
        <button 
          class="btn btn-danger btn-lg me-2" 
          onclick={handleEmergencyStop}
          disabled={ui.loading}
        >
          <i class="fas fa-exclamation-triangle me-1"></i>
          Emergency Stop
        </button>
        <button 
          class="btn btn-outline-primary" 
          onclick={() => hardwareStore.updateSystemStatus()}
          disabled={ui.loading}
        >
          <i class="fas fa-sync-alt {ui.loading ? 'fa-spin' : ''} me-1"></i>
          Refresh
        </button>
      </div>
    </div>
  </div>

  <!-- Quick Controls Row -->
  <div class="row mb-4">
    <!-- Quick Dispense -->
    <div class="col-md-6">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-tint me-2"></i>Quick Dispense
          </h5>
        </div>
        <div class="card-body">
          <form onsubmit={handleQuickDispense}>
            <div class="row">
              <div class="col-md-4">
                <select bind:value={quickForm.pumpId} class="form-control" required>
                  <option value="">Pump</option>
                  {#each hardware.pumps?.ids || [] as pumpId}
                    <option value={pumpId}>Pump {pumpId}</option>
                  {/each}
                </select>
              </div>
              <div class="col-md-4">
                <input 
                  type="number" 
                  bind:value={quickForm.amount}
                  placeholder="Amount (ml)" 
                  class="form-control" 
                  min="0.1" 
                  step="0.1" 
                  required
                />
              </div>
              <div class="col-md-4">
                <button 
                  type="submit" 
                  class="btn btn-primary w-100"
                  disabled={ui.loading || !quickForm.pumpId || !quickForm.amount}
                >
                  {#if ui.loading}
                    <span class="spinner-border spinner-border-sm me-1"></span>
                  {/if}
                  Dispense
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Quick Flow -->
    <div class="col-md-6">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-water me-2"></i>Quick Flow
          </h5>
        </div>
        <div class="card-body">
          <form onsubmit={handleQuickFlow}>
            <div class="row">
              <div class="col-md-4">
                <select bind:value={quickForm.flowId} class="form-control" required>
                  <option value="">Flow Meter</option>
                  {#each hardware.flow_meters?.ids || [] as flowId}
                    <option value={flowId}>Flow {flowId}</option>
                  {/each}
                </select>
              </div>
              <div class="col-md-4">
                <input 
                  type="number" 
                  bind:value={quickForm.gallons}
                  placeholder="Gallons" 
                  class="form-control" 
                  min="1" 
                  required
                />
              </div>
              <div class="col-md-4">
                <button 
                  type="submit" 
                  class="btn btn-success w-100"
                  disabled={ui.loading || !quickForm.flowId || !quickForm.gallons}
                >
                  {#if ui.loading}
                    <span class="spinner-border spinner-border-sm me-1"></span>
                  {/if}
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
  {#if hardware.pumps?.ids?.length}
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">
          <i class="fas fa-cogs me-2"></i>Pump Controls
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          {#each hardware.pumps.ids as pumpId}
            <div class="col-lg-3 col-md-6 mb-3">
              <PumpControl {pumpId} />
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Tank Status -->
  {#if Object.keys(status.tanks || {}).length}
    <div class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          <i class="fas fa-database me-2"></i>Tank Status
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          {#each Object.entries(status.tanks) as [tankId, tank]}
            <div class="col-md-4 mb-3">
              <div class="card border-{tank.level > 80 ? 'success' : tank.level > 20 ? 'warning' : 'danger'}">
                <div class="card-body text-center">
                  <h6 class="card-title">Tank {tankId}</h6>
                  <div class="progress mb-2" style="height: 20px;">
                    <div 
                      class="progress-bar bg-{tank.level > 80 ? 'success' : tank.level > 20 ? 'warning' : 'danger'}" 
                      style="width: {tank.level}%"
                    >
                      {tank.level}%
                    </div>
                  </div>
                  <div class="btn-group w-100" role="group">
                    <button 
                      class="btn btn-outline-primary btn-sm" 
                      onclick={() => openFillAction(tankId)}
                    >
                      Fill
                    </button>
                    <button 
                      class="btn btn-outline-secondary btn-sm" 
                      onclick={() => openDrainAction(tankId)}
                    >
                      Drain
                    </button>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Active Operations -->
  {#if hardwareStore.activePumps > 0 || hardwareStore.activeFlows > 0}
    <div class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          <i class="fas fa-play-circle me-2"></i>Active Operations
        </h5>
        <button 
          class="btn btn-warning btn-sm" 
          onclick={stopAllOperations}
        >
          <i class="fas fa-stop me-1"></i>Stop All
        </button>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <h6>Active Pumps: <span class="badge bg-primary">{hardwareStore.activePumps}</span></h6>
          </div>
          <div class="col-md-6">
            <h6>Active Flows: <span class="badge bg-success">{hardwareStore.activeFlows}</span></h6>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<!-- Action Modal -->
{#if ui.activeModal?.id === 'action'}
  <Modal 
    title="{actionModal.type === 'fill' ? 'Fill' : 'Drain'} Tank {actionModal.tankId}"
    onClose={() => hardwareStore.closeModal()}
  >
    <form onsubmit={(e) => {
      e.preventDefault();
      // Handle tank action
      hardwareStore.closeModal();
    }}>
      <div class="form-group">
        <label for="tankAmount">Amount (gallons):</label>
        <input type="number" id="tankAmount" class="form-control" min="1" required />
      </div>
      <div class="form-actions">
        <button type="button" class="btn btn-secondary" onclick={() => hardwareStore.closeModal()}>
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          {actionModal.type === 'fill' ? 'Start Fill' : 'Start Drain'}
        </button>
      </div>
    </form>
  </Modal>
{/if}