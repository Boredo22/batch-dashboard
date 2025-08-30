<!-- src/lib/components/StatusIndicator.svelte -->
<script>
  import { hardwareStore } from '../stores/hardware.svelte.js';
  
  const { systemStatus, ui } = hardwareStore;
  
  // Get status indicator class
  function getStatusClass(connected, loading) {
    if (loading) return 'warning';
    return connected ? 'success' : 'danger';
  }
  
  // Get status icon
  function getStatusIcon(connected, loading) {
    if (loading) return 'fa-spinner fa-spin';
    return connected ? 'fa-check-circle' : 'fa-exclamation-circle';
  }
</script>

<div class="d-flex align-items-center">
  <span class="status-indicator status-{getStatusClass(systemStatus.connected, ui.loading)}"></span>
  <span class="me-3">
    <i class="fas {getStatusIcon(systemStatus.connected, ui.loading)} me-1"></i>
    {hardwareStore.statusText}
  </span>
  {#if systemStatus.timestamp}
    <small class="text-muted">
      Last updated: {systemStatus.timestamp}
    </small>
  {/if}
</div>

<style>
  .status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    display: inline-block;
  }
  
  .status-success { background-color: #28a745; }
  .status-warning { background-color: #ffc107; }
  .status-danger { background-color: #dc3545; }
</style>