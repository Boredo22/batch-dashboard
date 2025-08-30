<script>
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
</style>