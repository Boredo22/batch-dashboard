<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');
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
    transition: width 0.2s ease, transform 0.2s ease;
  }

  .sidebar.collapsed {
    width: var(--sidebar-width-icon);
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