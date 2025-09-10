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
  class="sidebar-menu {className}"
  class:collapsed={!sidebar.isOpen}
  data-sidebar="menu"
  role="menu"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-menu {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    width: 100%;
  }

  .sidebar-menu.collapsed {
    align-items: center;
    gap: 0.25rem;
  }

  /* Menu item spacing */
  .sidebar-menu :global(.sidebar-menu-item) {
    display: flex;
    width: 100%;
  }

  .sidebar-menu.collapsed :global(.sidebar-menu-item) {
    width: auto;
    justify-content: center;
  }

  /* Sub-menu styling */

  /* Menu divider */
  .sidebar-menu :global(.sidebar-menu-separator) {
    height: 1px;
    background: var(--sidebar-border);
    opacity: 0.3;
    margin: 0.5rem 0;
  }

  .sidebar-menu.collapsed :global(.sidebar-menu-separator) {
    width: 2rem;
    margin: 0.5rem auto;
  }

  /* Animation for menu transitions */
  .sidebar-menu {
    transition: gap 0.2s ease, align-items 0.2s ease, padding-left 0.2s ease;
  }


  /* Focus management for keyboard navigation */
  .sidebar-menu:focus {
    outline: none;
  }

  .sidebar-menu:focus-within {
    outline: none;
  }

  /* Ensure proper stacking for nested menus */
  .sidebar-menu {
    position: relative;
  }

  /* Menu item focus styles */
  .sidebar-menu :global(.sidebar-menu-item:focus-within) {
    z-index: 1;
  }

  /* Handle menu overflow */
  .sidebar-menu {
    overflow: visible;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-menu {
      gap: 0.25rem;
    }
    
    .sidebar-menu.collapsed {
      gap: 0.375rem;
    }
    
  }

  /* Menu accessibility improvements */
  .sidebar-menu[role="menu"] {
    list-style: none;
  }

  /* Ensure menu items are properly aligned */
  .sidebar-menu > :global(*) {
    width: 100%;
  }

  .sidebar-menu.collapsed > :global(*) {
    width: auto;
  }

  /* Special styling for active menu states */
  .sidebar-menu :global(.sidebar-menu-item[data-active="true"]) {
    background: var(--sidebar-accent);
    color: var(--sidebar-accent-foreground);
  }

  .sidebar-menu :global(.sidebar-menu-item[data-active="true"]::before) {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--sidebar-primary);
  }

  .sidebar-menu.collapsed :global(.sidebar-menu-item[data-active="true"]::before) {
    display: none;
  }
</style>