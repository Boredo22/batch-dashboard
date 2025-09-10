<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');
</script>

<div
  class="sidebar-group {className}"
  class:collapsed={!sidebar.isOpen}
  data-sidebar="group"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0 1rem;
    margin-bottom: 1rem;
  }

  .sidebar-group.collapsed {
    padding: 0 0.5rem;
    align-items: center;
  }

  /* Remove bottom margin for last group */
  .sidebar-group:last-child {
    margin-bottom: 0;
  }

  /* Spacing adjustments when collapsed */
  .sidebar-group.collapsed {
    margin-bottom: 1rem;
  }

  /* Ensure proper alignment of group content */
  .sidebar-group :global(.sidebar-group-content) {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .sidebar-group.collapsed :global(.sidebar-group-content) {
    align-items: center;
    gap: 0.25rem;
  }

  /* Group separator */

  /* Focus management for keyboard navigation */
  .sidebar-group:focus-within {
    outline: none;
  }

  /* Animation for group transitions */
  .sidebar-group {
    transition: padding 0.2s ease, margin 0.2s ease;
  }


  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-group {
      padding: 0 0.5rem;
    }
    
    .sidebar-group.collapsed {
      padding: 0 0.25rem;
    }
  }

  /* Ensure proper spacing in nested structures */
</style>