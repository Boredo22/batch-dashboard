<!-- src/routes/Status.svelte -->
<script>
  import { hardwareStore } from '../lib/stores/hardware.svelte.js';
  import StatusIndicator from '../lib/components/StatusIndicator.svelte';

  // Access the store
  const { hardware, status, systemStatus, ui } = hardwareStore;

  // Auto-refresh toggle
  let autoRefresh = $state(true);
  let refreshInterval = $state(null);

  // Toggle auto-refresh
  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    
    if (autoRefresh && !refreshInterval) {
      refreshInterval = setInterval(() => {
        hardwareStore.updateSystemStatus();
      }, 5000); // Every 5 seconds for status page
    } else if (!autoRefresh && refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  // Manual refresh
  async function refreshStatus() {
    await hardwareStore.updateSystemStatus();
  }

  // Cleanup interval on destroy
  $effect(() => {
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  });

  // Format timestamp
  function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  }

  // Get status badge class
  function getStatusBadge(isActive, isConnected = true) {
    if (!isConnected) return 'danger';
    return isActive ? 'success' : 'secondary';
  }

  // Get status text
  function getStatusText(isActive, isConnected = true) {
    if (!isConnected) return 'Disconnected';
    return isActive ? 'Active' : 'Idle';
  }
</script>

<!-- Status Page -->
<div class="container mt-4">
  <!-- Page Header -->
  <div class="d-flex justify-content-between align-items-center mb-4">
    <div>
      <h1 class="mb-2">
        <i class="fas fa-chart-line me-2"></i>System Status
      </h1>
      <StatusIndicator />
    </div>
    
    <div class="d-flex gap-2">
      <!-- Auto-refresh Toggle -->
      <div class="form-check form-switch">
        <input 
          class="form-check-input" 
          type="checkbox" 
          bind:checked={autoRefresh}
          onchange={toggleAutoRefresh}
          id="autoRefreshSwitch"
        />
        <label class="form-check-label" for="autoRefreshSwitch">
          Auto-refresh (5s)
        </label>
      </div>
      
      <!-- Manual Refresh -->
      <button 
        class="btn btn-outline-primary" 
        onclick={refreshStatus}
        disabled={ui.loading}
      >
        <i class="fas fa-sync-alt {ui.loading ? 'fa-spin' : ''} me-1"></i>
        Refresh
      </button>
    </div>
  </div>

  <!-- System Overview -->
  <div class="row mb-4">
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="fas fa-server fa-2x text-{systemStatus.connected ? 'success' : 'danger'} mb-2"></i>
          <h5>System</h5>
          <span class="badge bg-{systemStatus.connected ? 'success' : 'danger'}">
            {systemStatus.connected ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="fas fa-tint fa-2x text-primary mb-2"></i>
          <h5>Active Pumps</h5>
          <span class="badge bg-primary">{hardwareStore.activePumps}</span>
        </div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="fas fa-water fa-2x text-success mb-2"></i>
          <h5>Active Flows</h5>
          <span class="badge bg-success">{hardwareStore.activeFlows}</span>
        </div>
      </div>
    </div>
    
    <div class="col-md-3">
      <div class="card text-center">
        <div class="card-body">
          <i class="fas fa-clock fa-2x text-info mb-2"></i>
          <h5>Last Update</h5>
          <small class="text-muted">
            {formatTimestamp(systemStatus.timestamp)}
          </small>
        </div>
      </div>
    </div>
  </div>

  <!-- Hardware Status -->
  <div class="row">
    <!-- Pumps Status -->
    {#if hardware.pumps?.ids?.length}
      <div class="col-md-6 mb-4">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="fas fa-tint me-2"></i>Pumps Status
            </h5>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Pump</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {#each hardware.pumps.ids as pumpId}
                    {@const pump = status.pumps?.[pumpId] || {}}
                    <tr>
                      <td>Pump {pumpId}</td>
                      <td>
                        <span class="badge bg-{getStatusBadge(pump.active, systemStatus.connected)}">
                          {getStatusText(pump.active, systemStatus.connected)}
                        </span>
                      </td>
                      <td>
                        {#if pump.active && pump.progress !== undefined}
                          <div class="progress" style="width: 100px; height: 15px;">
                            <div 
                              class="progress-bar bg-primary" 
                              style="width: {pump.progress}%"
                            ></div>
                          </div>
                          {pump.progress}%
                        {:else}
                          <span class="text-muted">-</span>
                        {/if}
                      </td>
                      <td>
                        {pump.rate ? `${pump.rate} ml/min` : '-'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Flow Meters Status -->
    {#if hardware.flow_meters?.ids?.length}
      <div class="col-md-6 mb-4">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="fas fa-water me-2"></i>Flow Meters Status
            </h5>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Flow Meter</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {#each hardware.flow_meters.ids as flowId}
                    {@const flow = status.flows?.[flowId] || {}}
                    <tr>
                      <td>Flow {flowId}</td>
                      <td>
                        <span class="badge bg-{getStatusBadge(flow.active, systemStatus.connected)}">
                          {getStatusText(flow.active, systemStatus.connected)}
                        </span>
                      </td>
                      <td>
                        {#if flow.active && flow.progress !== undefined}
                          <div class="progress" style="width: 100px; height: 15px;">
                            <div 
                              class="progress-bar bg-success" 
                              style="width: {flow.progress}%"
                            ></div>
                          </div>
                          {flow.progress}%
                        {:else}
                          <span class="text-muted">-</span>
                        {/if}
                      </td>
                      <td>
                        {flow.rate ? `${flow.rate} gal/min` : '-'}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Tanks Status -->
  {#if Object.keys(status.tanks || {}).length}
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">
          <i class="fas fa-database me-2"></i>Tank Levels
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          {#each Object.entries(status.tanks) as [tankId, tank]}
            <div class="col-lg-3 col-md-6 mb-3">
              <div class="card border-{tank.level > 80 ? 'success' : tank.level > 20 ? 'warning' : 'danger'}">
                <div class="card-body text-center">
                  <h6 class="card-title">Tank {tankId}</h6>
                  
                  <!-- Level Progress -->
                  <div class="progress mb-2" style="height: 25px;">
                    <div 
                      class="progress-bar bg-{tank.level > 80 ? 'success' : tank.level > 20 ? 'warning' : 'danger'}" 
                      style="width: {tank.level}%"
                    >
                      {tank.level}%
                    </div>
                  </div>
                  
                  <!-- Tank Details -->
                  <small class="text-muted">
                    {#if tank.capacity}
                      {Math.round(tank.capacity * tank.level / 100)} / {tank.capacity} gallons
                    {:else}
                      Level: {tank.level}%
                    {/if}
                  </small>
                  
                  <!-- Temperature if available -->
                  {#if tank.temperature}
                    <div class="mt-2">
                      <small class="text-info">
                        <i class="fas fa-thermometer-half me-1"></i>
                        {tank.temperature}°F
                      </small>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Mock Hardware Settings -->
  {#if Object.keys(hardware.mock_settings || {}).length}
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">
          <i class="fas fa-cog me-2"></i>Hardware Configuration
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          {#each Object.entries(hardware.mock_settings) as [device, isMock]}
            <div class="col-md-3 mb-2">
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-capitalize">{device}</span>
                <span class="badge bg-{isMock ? 'warning' : 'success'}">
                  {isMock ? 'Mock' : 'Real'}
                </span>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Raw Status Data (Collapsible) -->
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <button 
          class="btn btn-link text-decoration-none p-0"
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#rawStatusCollapse"
        >
          <i class="fas fa-code me-2"></i>Raw Status Data
        </button>
      </h5>
    </div>
    <div class="collapse" id="rawStatusCollapse">
      <div class="card-body">
        <pre class="bg-light p-3 rounded" style="max-height: 400px; overflow-y: auto;">
          <code>{JSON.stringify({ 
            systemStatus, 
            hardware, 
            status 
          }, null, 2)}</code>
        </pre>
      </div>
    </div>
  </div>
</div>

<!-- Floating Refresh Button -->
<button
  class="btn btn-primary btn-lg refresh-btn"
  onclick={refreshStatus}
  title="Refresh Status"
  aria-label="Refresh Status"
  disabled={ui.loading}
>
  <i class="fas fa-sync-alt {ui.loading ? 'fa-spin' : ''}"></i>
</button>

<style>
  .refresh-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
  }
  
  .refresh-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
  }
</style>