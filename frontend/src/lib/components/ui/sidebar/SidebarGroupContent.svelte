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
  class="sidebar-group-content {className}"
  class:collapsed={!sidebar.isOpen}
  data-sidebar="group-content"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-group-content {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .sidebar-group-content.collapsed {
    align-items: center;
    gap: 0.25rem;
  }

  /* Ensure proper spacing for menu items */
  .sidebar-group-content :global(.sidebar-menu) {
    display: flex;
    flex-direction: column;
    gap: inherit;
  }

  .sidebar-group-content.collapsed :global(.sidebar-menu) {
    align-items: center;
  }

  /* Handle nested group content */

  /* Animation for smooth transitions */
  .sidebar-group-content {
    transition: gap 0.2s ease, align-items 0.2s ease;
  }

  /* Ensure consistent spacing with direct children */
  .sidebar-group-content > :global(*) {
    transition: opacity 0.2s ease, transform 0.2s ease;
  }

  /* Handle overflow for collapsed state */
  .sidebar-group-content.collapsed {
    overflow: visible;
  }

  /* Focus management */
  .sidebar-group-content:focus-within {
    outline: none;
  }

  /* Responsive behavior */
  @media (max-width: 768px) {
    .sidebar-group-content {
      gap: 0.25rem;
    }
    
    .sidebar-group-content.collapsed {
      gap: 0.375rem;
    }
  }

  /* Special handling for different content types */
  .sidebar-group-content :global(.sidebar-separator) {
    height: 1px;
    background: var(--sidebar-border);
    opacity: 0.3;
    margin: 0.5rem 0;
  }

  .sidebar-group-content.collapsed :global(.sidebar-separator) {
    width: 2rem;
    margin: 0.5rem auto;
  }

  /* Ensure proper alignment for different content types */
  .sidebar-group-content :global(.sidebar-item) {
    width: 100%;
  }

  .sidebar-group-content.collapsed :global(.sidebar-item) {
    width: auto;
    min-width: 2.5rem;
    display: flex;
    justify-content: center;
  }
</style>