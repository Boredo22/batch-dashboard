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
  class="sidebar-header {className}"
  class:collapsed={!sidebar.isOpen}
  data-sidebar="header"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    border-bottom: 1px solid var(--sidebar-border);
    background: var(--sidebar-background);
  }

  .sidebar-header.collapsed {
    padding: 1rem 0.5rem;
    align-items: center;
  }

  /* Logo/brand area */
  .sidebar-header :global(.sidebar-brand) {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--sidebar-foreground);
  }

  .sidebar-header.collapsed :global(.sidebar-brand) {
    justify-content: center;
  }

  .sidebar-header.collapsed :global(.sidebar-brand-text) {
    display: none;
  }

  /* Search input area */
  .sidebar-header :global(.sidebar-search) {
    position: relative;
    margin-top: 0.5rem;
  }

  .sidebar-header.collapsed :global(.sidebar-search) {
    display: none;
  }

  .sidebar-header :global(.sidebar-search input) {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--sidebar-border);
    border-radius: 0.375rem;
    background: hsl(217.2 32.6% 17.5% / 0.5);
    color: var(--sidebar-foreground);
    font-size: 0.875rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .sidebar-header :global(.sidebar-search input:focus) {
    outline: none;
    border-color: var(--sidebar-primary);
    box-shadow: 0 0 0 2px hsl(263.4 70% 50.4% / 0.2);
  }

  .sidebar-header :global(.sidebar-search input::placeholder) {
    color: hsl(215.4 16.3% 46.9%);
  }

  /* Header actions */
  .sidebar-header :global(.sidebar-header-actions) {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-left: auto;
  }

  .sidebar-header.collapsed :global(.sidebar-header-actions) {
    margin-left: 0;
  }

  /* Header button styling */
  .sidebar-header :global(.sidebar-header-button) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    border: none;
    border-radius: 0.25rem;
    background: transparent;
    color: var(--sidebar-foreground);
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease;
  }

  .sidebar-header :global(.sidebar-header-button:hover) {
    background: var(--sidebar-accent);
  }

  .sidebar-header :global(.sidebar-header-button:focus) {
    outline: none;
    box-shadow: 0 0 0 2px var(--sidebar-ring);
  }
</style>