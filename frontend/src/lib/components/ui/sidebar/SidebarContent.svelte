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
  class="sidebar-content {className}"
  class:collapsed={!sidebar.isOpen}
  data-sidebar="content"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 1rem 0;
    min-height: 0;
  }

  .sidebar-content.collapsed {
    padding: 1rem 0;
  }

  /* Custom scrollbar for the content area */
  .sidebar-content {
    scrollbar-width: thin;
    scrollbar-color: hsl(217.2 32.6% 17.5%) transparent;
  }

  .sidebar-content::-webkit-scrollbar {
    width: 0.375rem;
  }

  .sidebar-content::-webkit-scrollbar-track {
    background: transparent;
    margin: 0.5rem 0;
  }

  .sidebar-content::-webkit-scrollbar-thumb {
    background: hsl(217.2 32.6% 17.5%);
    border-radius: 0.25rem;
  }

  .sidebar-content::-webkit-scrollbar-thumb:hover {
    background: hsl(217.2 32.6% 25%);
  }

  /* Content spacing when collapsed */
  .sidebar-content.collapsed {
    align-items: center;
  }

  /* Ensure content doesn't overflow when collapsed */
  .sidebar-content.collapsed :global(*) {
    min-width: 0;
  }

  /* Hide text content when collapsed for certain elements */
  .sidebar-content.collapsed :global(.sidebar-label),
  .sidebar-content.collapsed :global(.sidebar-text) {
    display: none;
  }

  /* Center icons when collapsed */
  .sidebar-content.collapsed :global(.sidebar-group),
  .sidebar-content.collapsed :global(.sidebar-menu) {
    align-items: center;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-content {
      padding: 1rem 0.5rem;
    }
  }

  /* Focus management for keyboard navigation */
  .sidebar-content:focus {
    outline: none;
  }

  /* Ensure proper stacking context for tooltips when collapsed */
  .sidebar-content.collapsed {
    position: relative;
    z-index: 1;
  }

  /* Animation for smooth transitions */

  /* Fade effect for collapsing content */
  .sidebar-content.collapsed :global(.fade-on-collapse) {
    opacity: 0;
    transform: translateX(-0.5rem);
  }

  .sidebar-content:not(.collapsed) :global(.fade-on-collapse) {
    opacity: 1;
    transform: translateX(0);
  }
</style>