<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    variant = 'default',
    size = 'default',
    active = false,
    disabled = false,
    loading = false,
    tooltip = '',
    href,
    onclick,
    onkeydown,
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');

  const handleClick = (event) => {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    onclick?.(event);
  };

  const handleKeydown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick(event);
    }
    onkeydown?.(event);
  };
</script>

{#if href}
  <a
    {href}
    class="sidebar-menu-button {variant} {size} {className}"
    class:collapsed={!sidebar.isOpen}
    class:active
    class:disabled
    class:loading
    data-sidebar="menu-button"
    data-tooltip={sidebar.isOpen ? '' : tooltip}
    role="menuitem"
    tabindex={disabled ? -1 : 0}
    onclick={handleClick}
    onkeydown={handleKeydown}
    {...restProps}
  >
    {@render children?.()}
  </a>
{:else}
  <button
    class="sidebar-menu-button {variant} {size} {className}"
    class:collapsed={!sidebar.isOpen}
    class:active
    class:disabled
    class:loading
    data-sidebar="menu-button"
    data-tooltip={sidebar.isOpen ? '' : tooltip}
    role="menuitem"
    tabindex={disabled ? -1 : 0}
    {disabled}
    onclick={handleClick}
    onkeydown={handleKeydown}
    {...restProps}
  >
    {@render children?.()}
  </button>
{/if}

<style>
  .sidebar-menu-button {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: none;
    background: transparent;
    color: var(--sidebar-foreground);
    text-align: left;
    text-decoration: none;
    cursor: pointer;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    line-height: 1.25;
    transition: all 0.2s ease;
    position: relative;
  }

  .sidebar-menu-button.collapsed {
    padding: 0.5rem;
    justify-content: center;
    gap: 0;
  }

  /* Variant styles */
  .sidebar-menu-button.default:hover:not(.disabled):not(.active) {
    background: hsl(217.2 32.6% 17.5% / 0.5);
  }

  .sidebar-menu-button.ghost:hover:not(.disabled):not(.active) {
    background: hsl(217.2 32.6% 17.5% / 0.3);
  }

  .sidebar-menu-button.outline {
    border: 1px solid var(--sidebar-border);
  }

  .sidebar-menu-button.outline:hover:not(.disabled):not(.active) {
    background: hsl(217.2 32.6% 17.5% / 0.5);
    border-color: hsl(217.2 32.6% 25%);
  }

  /* Size variants */
  .sidebar-menu-button.sm {
    padding: 0.375rem 0.5rem;
    font-size: 0.8125rem;
    min-height: 2rem;
  }

  .sidebar-menu-button.sm.collapsed {
    padding: 0.375rem;
  }

  .sidebar-menu-button.lg {
    padding: 0.625rem 1rem;
    font-size: 0.9375rem;
    min-height: 2.75rem;
  }

  .sidebar-menu-button.lg.collapsed {
    padding: 0.625rem;
  }

  .sidebar-menu-button.default {
    min-height: 2.25rem;
  }

  /* Active state */
  .sidebar-menu-button.active {
    background: var(--sidebar-accent);
    color: var(--sidebar-accent-foreground);
  }

  .sidebar-menu-button.active::before {
    content: '';
    position: absolute;
    left: -0.75rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--sidebar-primary);
    border-radius: 0 1px 1px 0;
  }

  .sidebar-menu-button.collapsed.active::before {
    display: none;
  }

  /* Focus state */
  .sidebar-menu-button:focus {
    outline: none;
    background: hsl(217.2 32.6% 17.5% / 0.7);
    box-shadow: 0 0 0 2px var(--sidebar-ring);
  }

  /* Disabled state */
  .sidebar-menu-button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  /* Loading state */
  .sidebar-menu-button.loading {
    cursor: wait;
  }

  .sidebar-menu-button.loading :global(.sidebar-menu-icon) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* Icon styling */
  .sidebar-menu-button :global(.sidebar-menu-icon) {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
  }

  .sidebar-menu-button.collapsed :global(.sidebar-menu-icon) {
    width: 1.5rem;
    height: 1.5rem;
  }

  .sidebar-menu-button.sm :global(.sidebar-menu-icon) {
    width: 1rem;
    height: 1rem;
  }

  .sidebar-menu-button.sm.collapsed :global(.sidebar-menu-icon) {
    width: 1.25rem;
    height: 1.25rem;
  }

  .sidebar-menu-button.lg :global(.sidebar-menu-icon) {
    width: 1.5rem;
    height: 1.5rem;
  }

  .sidebar-menu-button.lg.collapsed :global(.sidebar-menu-icon) {
    width: 1.75rem;
    height: 1.75rem;
  }

  /* Text styling */
  .sidebar-menu-button :global(.sidebar-menu-text) {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sidebar-menu-button.collapsed :global(.sidebar-menu-text) {
    display: none;
  }

  /* Badge/count styling */
  .sidebar-menu-button :global(.sidebar-menu-badge) {
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

  .sidebar-menu-button.collapsed :global(.sidebar-menu-badge) {
    position: absolute;
    top: -0.25rem;
    right: -0.25rem;
    min-width: 1rem;
    height: 1rem;
    padding: 0 0.25rem;
    font-size: 0.6875rem;
  }

  /* Shortcut/keyboard hint styling */
  .sidebar-menu-button :global(.sidebar-menu-shortcut) {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-left: auto;
    font-size: 0.75rem;
    color: hsl(215.4 16.3% 46.9%);
    font-family: ui-monospace, SFMono-Regular, "SF Mono", monospace;
  }

  .sidebar-menu-button.collapsed :global(.sidebar-menu-shortcut) {
    display: none;
  }

  /* Arrow/chevron styling */
  .sidebar-menu-button :global(.sidebar-menu-arrow) {
    width: 1rem;
    height: 1rem;
    margin-left: auto;
    transition: transform 0.2s ease;
  }

  .sidebar-menu-button.collapsed :global(.sidebar-menu-arrow) {
    display: none;
  }

  .sidebar-menu-button[data-expanded="true"] :global(.sidebar-menu-arrow) {
    transform: rotate(90deg);
  }

  /* Tooltip for collapsed state */
  .sidebar-menu-button.collapsed:hover::after {
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
    pointer-events: none;
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

  /* Link specific styles */
  a.sidebar-menu-button {
    color: inherit;
  }

  a.sidebar-menu-button:visited {
    color: inherit;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-menu-button {
      padding: 0.625rem 0.75rem;
      min-height: 2.5rem;
    }
    
    .sidebar-menu-button.collapsed {
      padding: 0.625rem;
    }
    
    .sidebar-menu-button.sm {
      padding: 0.5rem 0.625rem;
      min-height: 2.25rem;
    }
    
    .sidebar-menu-button.sm.collapsed {
      padding: 0.5rem;
    }
  }
</style>