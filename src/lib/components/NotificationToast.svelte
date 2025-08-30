<script>
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
          aria-label="Close notification"
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
</style>