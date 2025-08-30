<!-- src/routes/Status.svelte - FIXED VERSION -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { hardwareStore } from '../lib/stores/hardware.svelte.js';
  import StatusIndicator from '../lib/components/StatusIndicator.svelte';
  import NotificationToast from '../lib/components/NotificationToast.svelte';

  const { status, hardware, systemStatus } = hardwareStore;
  
  let pollInterval;

  // Handle polling with proper lifecycle
  onMount(() => {
    // Start initial status update
    hardwareStore.updateSystemStatus();
    
    // Set up polling
    pollInterval = setInterval(() => {
      hardwareStore.updateSystemStatus();
    }, 10000); // Every 10 seconds
  });

  onDestroy(() => {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });
</script>

<!-- Include NotificationToast in component -->
<NotificationToast />

<div class="container-fluid mt-4">
  <div class="row">
    <div class="col-12">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>
          <i class="fas fa-chart-line me-2"></i>System Status
        </h2>
        
        <div class="d-flex gap-3 align-items-center">
          <StatusIndicator />
          
          <button
            class="btn btn-outline-primary"
            onclick={() => hardwareStore.updateSystemStatus()}
            disabled={hardwareStore.ui.loading}
          >
            <i class="fas fa-sync-alt me-2"></i>Refresh
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- System Overview -->
  <div class="row mb-4">
    <div class="col-md-6 col-lg-3 mb-3">
      <div class="card bg-primary text-white">
        <div class="card-body">
          <div class="d-flex justify-content-between">
            <div>
              <h6 class="card-title">System Status</h6>
              <h4>{status.running ? 'Running' : 'Stopped'}</h4>
            </div>
            <div class="align-self-center">
              <i class="fas fa-power-off fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-md-6 col-lg-3 mb-3">
      <div class="card bg-success text-white">
        <div class="card-body">
          <div class="d-flex justify-content-between">
            <div>
              <h6 class="card-title">Active Pumps</h6>
              <h4>{hardwareStore.activePumps} / {hardwareStore.totalPumps}</h4>
            </div>
            <div class="align-self-center">
              <i class="fas fa-tint fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-md-6 col-lg-3 mb-3">
      <div class="card bg-warning text-white">
        <div class="card-body">
          <div class="d-flex justify-content-between">
            <div>
              <h6 class="card-title">Active Relays</h6>
              <h4>{hardwareStore.activeRelays} / {hardwareStore.totalRelays}</h4>
            </div>
            <div class="align-self-center">
              <i class="fas fa-bolt fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-md-6 col-lg-3 mb-3">
      <div class="card bg-info text-white">
        <div class="card-body">
          <div class="d-flex justify-content-between">
            <div>
              <h6 class="card-title">Connection</h6>
              <h4>{hardwareStore.isOnline ? 'Online' : 'Offline'}</h4>
            </div>
            <div class="align-self-center">
              <i class="fas fa-{hardwareStore.isOnline ? 'wifi' : 'exclamation-triangle'} fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Detailed Status Sections -->
  <div class="row">
    <!-- Pumps Status -->
    <div class="col-md-6 mb-4">
      <div class="card">
        <div class="card-header">
          <h5 class="card-title mb-0">
            <i class="fas fa-tint me-2"></i>Pumps Status
          </h5>
        </div>
        <div class="card-body">
          {#if Object.keys(status.pumps).length === 0}
            <p class="text-muted">No pump data available</p>
          {:else}
            {#each Object.entries(status.pumps) as [pumpId, pump]}
              <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                <div>
                  <strong>Pump {pumpId}</strong>
                  <div class="small text-muted">
                    Volume: {pump.volume_dispensed || 0}ml
                  </div>
                </div>
                <div>
                  <span class="badge bg-{pump.active ? 'success' : 'secondary'}">
                    {pump.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>

    <!-- Relays Status -->
    <div class="col-md-6 mb-4">
      <div class="card">
        <div class="card-header">
          <h5 class="card-title mb-0">
            <i class="fas fa-bolt me-2"></i>Relays Status
          </h5>
        </div>
        <div class="card-body">
          {#if Object.keys(status.relays).length === 0}
            <p class="text-muted">No relay data available</p>
          {:else}
            {#each Object.entries(status.relays) as [relayId, relay]}
              <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                <div>
                  <strong>Relay {relayId}</strong>
                  <div class="small text-muted">
                    Pin: {relay.pin || 'N/A'}
                  </div>
                </div>
                <div>
                  <span class="badge bg-{relay.state ? 'success' : 'secondary'}">
                    {relay.state ? 'ON' : 'OFF'}
                  </span>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- EC/pH Status -->
  {#if status.ec_ph && Object.keys(status.ec_ph).length > 0}
    <div class="row">
      <div class="col-12 mb-4">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">
              <i class="fas fa-vial me-2"></i>EC/pH Readings
            </h5>
          </div>
          <div class="card-body">
            <div class="row">
              {#each Object.entries(status.ec_ph) as [sensor, reading]}
                <div class="col-md-4 mb-3">
                  <div class="text-center p-3 border rounded">
                    <h6>{sensor.toUpperCase()}</h6>
                    <h4 class="text-primary">{reading || 'N/A'}</h4>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Last Update Info -->
  <div class="row">
    <div class="col-12">
      <div class="small text-muted text-center">
        {#if systemStatus.lastUpdate}
          Last updated: {new Date(systemStatus.lastUpdate).toLocaleTimeString()}
        {/if}
        {#if systemStatus.error}
          <div class="text-danger">Error: {systemStatus.error}</div>
        {/if}
      </div>
    </div>
  </div>
</div>