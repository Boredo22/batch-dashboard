<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');

  let hoverTimeout = $state(null);

  function handleMouseEnter() {
    if (sidebar.isMobile) return;

    // Clear any existing timeout
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      hoverTimeout = null;
    }

    // Expand immediately on hover
    if (!sidebar.isOpen) {
      sidebar.openSidebar();
    }
  }

  function handleMouseLeave() {
    if (sidebar.isMobile) return;

    // Collapse after a short delay when mouse leaves
    hoverTimeout = setTimeout(() => {
      sidebar.closeSidebar();
      hoverTimeout = null;
    }, 300);
  }

  function handleClick() {
    if (sidebar.isMobile) return;

    // Clear any pending collapse timeout
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      hoverTimeout = null;
    }

    // Toggle sidebar on click
    sidebar.toggleSidebar();
  }
</script>

<aside
  class="sidebar {className}"
  class:collapsed={!sidebar.isOpen}
  class:mobile={sidebar.isMobile}
  data-sidebar
  data-side={sidebar.side}
  data-variant={sidebar.variant}
  data-collapsible={sidebar.collapsible}
  data-state={sidebar.isOpen ? 'expanded' : 'collapsed'}
  onmouseenter={handleMouseEnter}
  onmouseleave={handleMouseLeave}
  onclick={handleClick}
  {...restProps}
>
  {@render children?.()}
</aside>

<style>
  .sidebar {
    position: relative;
    display: flex;
    flex-direction: column;
    width: var(--sidebar-width);
    height: 100vh;
    border-right: 1px solid var(--sidebar-border);
    background: var(--sidebar-background);
    color: var(--sidebar-foreground);
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s ease;
    cursor: pointer;
    z-index: 50;
  }

  .sidebar.collapsed {
    width: var(--sidebar-width-icon);
  }

  .sidebar:not(.mobile):hover {
    box-shadow: 4px 0 24px rgba(139, 92, 246, 0.15);
  }

  .sidebar.mobile {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 40;
    height: 100vh;
    width: var(--sidebar-width-mobile);
    transform: translateX(-100%);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  }

  .sidebar.mobile:not(.collapsed) {
    transform: translateX(0);
  }

  .sidebar[data-side='right'] {
    border-right: none;
    border-left: 1px solid var(--sidebar-border);
  }

  .sidebar[data-side='right'].mobile {
    left: auto;
    right: 0;
    transform: translateX(100%);
  }

  .sidebar[data-side='right'].mobile:not(.collapsed) {
    transform: translateX(0);
  }

  .sidebar[data-variant='floating'] {
    border: 1px solid var(--sidebar-border);
    border-radius: 0.5rem;
    margin: 0.5rem;
    height: calc(100vh - 1rem);
    width: calc(var(--sidebar-width) - 1rem);
  }

  .sidebar[data-variant='floating'].collapsed {
    width: calc(var(--sidebar-width-icon) - 1rem);
  }

  .sidebar[data-variant='inset'] {
    border-radius: 0.5rem;
    background: hsl(222.2 84% 4.9% / 0.8);
    backdrop-filter: blur(8px);
  }

  /* Scrollbar styling for dark theme */
  .sidebar :global(*) {
    scrollbar-width: thin;
    scrollbar-color: hsl(217.2 32.6% 17.5%) transparent;
  }

  .sidebar :global(*::-webkit-scrollbar) {
    width: 0.5rem;
  }

  .sidebar :global(*::-webkit-scrollbar-track) {
    background: transparent;
  }

  .sidebar :global(*::-webkit-scrollbar-thumb) {
    background: hsl(217.2 32.6% 17.5%);
    border-radius: 0.25rem;
  }

  .sidebar :global(*::-webkit-scrollbar-thumb:hover) {
    background: hsl(217.2 32.6% 25%);
  }
</style>