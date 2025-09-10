<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    active = false,
    disabled = false,
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');
</script>

<div
  class="sidebar-menu-item {className}"
  class:collapsed={!sidebar.isOpen}
  class:active
  class:disabled
  data-sidebar="menu-item"
  data-active={active}
  data-disabled={disabled}
  role="menuitem"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-menu-item {
    position: relative;
    display: flex;
    align-items: center;
    width: 100%;
    border-radius: 0.375rem;
    transition: all 0.2s ease;
  }

  .sidebar-menu-item.collapsed {
    width: auto;
    justify-content: center;
  }

  /* Base menu item styling */
  .sidebar-menu-item {
    min-height: 2.25rem;
  }

  /* Active state */
  .sidebar-menu-item.active {
    background: var(--sidebar-accent);
    color: var(--sidebar-accent-foreground);
  }

  .sidebar-menu-item.active::before {
    content: '';
    position: absolute;
    left: -1rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--sidebar-primary);
    border-radius: 0 1px 1px 0;
  }

  .sidebar-menu-item.collapsed.active::before {
    display: none;
  }

  /* Hover state */
  .sidebar-menu-item:not(.disabled):not(.active):hover {
    background: hsl(217.2 32.6% 17.5% / 0.5);
  }

  /* Focus state */
  .sidebar-menu-item:focus {
    outline: none;
    background: hsl(217.2 32.6% 17.5% / 0.7);
    box-shadow: 0 0 0 2px var(--sidebar-ring);
  }

  /* Disabled state */
  .sidebar-menu-item.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  /* Menu item content */
  .sidebar-menu-item :global(.sidebar-menu-button) {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: none;
    background: transparent;
    color: inherit;
    text-align: left;
    cursor: pointer;
    border-radius: inherit;
    transition: all 0.2s ease;
  }

  .sidebar-menu-item.collapsed :global(.sidebar-menu-button) {
    padding: 0.5rem;
    justify-content: center;
    gap: 0;
  }

  .sidebar-menu-item :global(.sidebar-menu-button:focus) {
    outline: none;
  }

  /* Icon styling */
  .sidebar-menu-item :global(.sidebar-menu-icon) {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
  }

  .sidebar-menu-item.collapsed :global(.sidebar-menu-icon) {
    width: 1.5rem;
    height: 1.5rem;
  }

  /* Text styling */
  .sidebar-menu-item :global(.sidebar-menu-text) {
    flex: 1;
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sidebar-menu-item.collapsed :global(.sidebar-menu-text) {
    display: none;
  }

  /* Badge/count styling */
  .sidebar-menu-item :global(.sidebar-menu-badge) {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 1.25rem;
    height: 1.25rem;
    padding: 0 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    background: var(--sidebar-primary);
    color: var(--sidebar-primary-foreground);
    border-radius: 0.75rem;
    margin-left: auto;
  }

  .sidebar-menu-item.collapsed :global(.sidebar-menu-badge) {
    display: none;
  }

  /* Chevron/arrow styling */
  .sidebar-menu-item :global(.sidebar-menu-arrow) {
    width: 1rem;
    height: 1rem;
    margin-left: auto;
    transition: transform 0.2s ease;
  }

  .sidebar-menu-item.collapsed :global(.sidebar-menu-arrow) {
    display: none;
  }

  .sidebar-menu-item[data-expanded="true"] :global(.sidebar-menu-arrow) {
    transform: rotate(90deg);
  }

  /* Tooltip for collapsed state */
  .sidebar-menu-item.collapsed:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    left: calc(100% + 0.5rem);
    top: 50%;
    transform: translateY(-50%);
    background: hsl(222.2 84% 4.9%);
    color: var(--sidebar-foreground);
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--sidebar-border);
    z-index: 50;
    opacity: 0;
    animation: tooltip-in 0.15s ease-out 0.3s forwards;
  }

  @keyframes tooltip-in {
    from {
      opacity: 0;
      transform: translateY(-50%) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(-50%) scale(1);
    }
  }

  /* Sub-menu indicator */
  .sidebar-menu-item :global(.sidebar-submenu-indicator) {
    width: 0.25rem;
    height: 0.25rem;
    background: var(--sidebar-primary);
    border-radius: 50%;
    position: absolute;
    top: 0.375rem;
    right: 0.375rem;
  }

  .sidebar-menu-item.collapsed :global(.sidebar-submenu-indicator) {
    top: 0.25rem;
    right: 0.25rem;
  }

  /* Loading state */
  .sidebar-menu-item[data-loading="true"] :global(.sidebar-menu-icon) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-menu-item {
      min-height: 2.5rem;
    }
    
    .sidebar-menu-item :global(.sidebar-menu-button) {
      padding: 0.625rem 0.75rem;
    }
    
    .sidebar-menu-item.collapsed :global(.sidebar-menu-button) {
      padding: 0.625rem;
    }
  }
</style>