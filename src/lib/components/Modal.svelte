<script>
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
</style>