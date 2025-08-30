<!-- src/lib/components/Modal.svelte -->
<script>
  let { title = 'Modal', onClose, children } = $props();
  
  // Close modal when clicking backdrop
  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      onClose?.();
    }
  }
  
  // Close on escape key
  function handleKeydown(event) {
    if (event.key === 'Escape') {
      onClose?.();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="modal show" style="display: flex;" on:click={handleBackdropClick}>
  <div class="modal-content">
    <div class="modal-header">
      <h3>{title}</h3>
      <button class="modal-close" on:click={onClose}>&times;</button>
    </div>
    <div class="modal-body">
      {@render children()}
    </div>
  </div>
</div>

<style>
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    align-items: center;
    justify-content: center;
    z-index: 1050;
  }
  
  .modal-content {
    background: white;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
  }
  
  .modal-header h3 {
    margin: 0;
    font-size: 1.25rem;
  }
  
  .modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .modal-close:hover {
    background: #f8f9fa;
    border-radius: 4px;
  }
  
  .modal-body {
    padding: 1rem;
  }
</style>