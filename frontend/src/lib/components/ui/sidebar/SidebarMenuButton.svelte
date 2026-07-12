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
    color: hsl(var(--sidebar-foreground));
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
    background: hsl(var(--sidebar-accent) / 0.7);
    color: hsl(var(--sidebar-accent-foreground));
  }

  .sidebar-menu-button.ghost:hover:not(.disabled):not(.active) {
    background: hsl(var(--sidebar-accent) / 0.5);
  }

  .sidebar-menu-button.outline {
    border: 1px solid hsl(var(--sidebar-border));
  }

  .sidebar-menu-button.outline:hover:not(.disabled):not(.active) {
    background: hsl(var(--sidebar-accent) / 0.7);
    border-color: hsl(var(--sidebar-border));
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
    background: linear-gradient(
      90deg,
      hsl(var(--sidebar-primary) / 0.14),
      hsl(var(--sidebar-accent) / 0.6)
    );
    color: hsl(var(--sidebar-accent-foreground));
    font-weight: 600;
  }

  .sidebar-menu-button.active :global(svg) {
    color: hsl(var(--sidebar-primary));
  }

  .sidebar-menu-button.active::before {
    content: '';
    position: absolute;
    left: -0.5rem;
    top: 0.35rem;
    bottom: 0.35rem;
    width: 3px;
    background: hsl(var(--sidebar-primary));
    border-radius: 0 2px 2px 0;
    box-shadow: 0 0 10px hsl(var(--sidebar-primary) / 0.6);
  }

  .sidebar-menu-button.collapsed.active::before {
    display: none;
  }

  /* Focus state */
  .sidebar-menu-button:focus-visible {
    outline: none;
    background: hsl(var(--sidebar-accent) / 0.7);
    box-shadow: 0 0 0 2px hsl(var(--sidebar-ring) / 0.7);
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
    font-weight: 600;
    background: hsl(var(--sidebar-primary));
    color: hsl(var(--sidebar-primary-foreground));
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
    color: hsl(var(--sidebar-foreground) / 0.6);
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
    background: hsl(var(--popover));
    color: hsl(var(--popover-foreground));
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
    box-shadow: var(--shadow-md);
    border: 1px solid hsl(var(--sidebar-border));
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