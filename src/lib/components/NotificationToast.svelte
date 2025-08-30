<!-- src/lib/components/NotificationToast.svelte -->
<script>
  import { hardwareStore } from '../stores/hardware.svelte.js';
  
  const { ui } = hardwareStore;
  
  function getToastClass(type) {
    switch (type) {
      case 'success': return 'border-success text-success';
      case 'danger': return 'border-danger text-danger';
      case 'warning': return 'border-warning text-warning';
      case 'info': return 'border-info text-info';
      default: return 'border-primary text-primary';
    }
  }
  
  function getToastIcon(type) {
    switch (type) {
      case 'success': return 'fa-check-circle';
      case 'danger': return 'fa-exclamation-circle';
      case 'warning': return 'fa-exclamation-triangle';
      case 'info': return 'fa-info-circle';
      default: return 'fa-bell';
    }
  }
</script>

<!-- Toast Container -->
<div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1100;">
  {#each ui.notifications as notification (notification.id)}
    <div class="toast show {getToastClass(notification.type)}" role="alert">
      <div class="toast-header">
        <i class="fas {getToastIcon(notification.type)} me-2"></i>
        <strong class="me-auto">System</strong>
        <small class="text-muted">
          {Math.round((Date.now() - notification.timestamp) / 1000)}s ago
        </small>
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
  .toast {
    margin-bottom: 0.5rem;
    border-left: 4px solid;
  }
  
  .toast.border-success { border-left-color: #28a745; }
  .toast.border-danger { border-left-color: #dc3545; }
  .toast.border-warning { border-left-color: #ffc107; }
  .toast.border-info { border-left-color: #17a2b8; }
  .toast.border-primary { border-left-color: #007bff; }
</style>