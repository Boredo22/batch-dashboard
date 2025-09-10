<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    variant = 'ghost',
    size = 'icon',
    disabled = false,
    onclick,
    onkeydown,
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');

  const handleToggle = (event) => {
    if (disabled) {
      event.preventDefault();
      return;
    }
    
    sidebar.toggleSidebar();
    onclick?.(event);
  };

  const handleKeydown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToggle(event);
    }
    onkeydown?.(event);
  };
</script>

<button
  class="sidebar-trigger {variant} {size} {className}"
  class:disabled
  data-sidebar="trigger"
  aria-label="Toggle sidebar"
  aria-expanded={sidebar.isOpen}
  aria-controls="sidebar"
  {disabled}
  onclick={handleToggle}
  onkeydown={handleKeydown}
  {...restProps}
>
  {#if sidebar.isOpen}
    <!-- Collapse icon -->
    <svg
      class="sidebar-trigger-icon"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
      <line x1="9" y1="9" x2="15" y2="15"/>
      <line x1="15" y1="9" x2="9" y2="15"/>
    </svg>
  {:else}
    <!-- Expand icon -->
    <svg
      class="sidebar-trigger-icon"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
      <line x1="9" y1="9" x2="9" y2="15"/>
      <line x1="12" y1="12" x2="15" y2="15"/>
      <line x1="12" y1="12" x2="15" y2="9"/>
    </svg>
  {/if}
  
  <!-- Optional children content -->
  {@render children?.()}
</button>

<style>
  .sidebar-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    border: none;
    background: transparent;
    color: var(--sidebar-foreground);
    cursor: pointer;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    line-height: 1;
    transition: all 0.2s ease;
    position: relative;
  }

  /* Size variants */
  .sidebar-trigger.icon {
    width: 2.25rem;
    height: 2.25rem;
    padding: 0;
  }

  .sidebar-trigger.sm {
    width: 2rem;
    height: 2rem;
    padding: 0;
  }

  .sidebar-trigger.lg {
    width: 2.75rem;
    height: 2.75rem;
    padding: 0;
  }

  .sidebar-trigger.default {
    padding: 0.5rem 1rem;
    height: 2.25rem;
  }

  /* Variant styles */
  .sidebar-trigger.ghost:hover:not(.disabled) {
    background: hsl(217.2 32.6% 17.5% / 0.5);
  }

  .sidebar-trigger.outline {
    border: 1px solid var(--sidebar-border);
  }

  .sidebar-trigger.outline:hover:not(.disabled) {
    background: hsl(217.2 32.6% 17.5% / 0.5);
    border-color: hsl(217.2 32.6% 25%);
  }

  .sidebar-trigger.secondary {
    background: var(--sidebar-accent);
    color: var(--sidebar-accent-foreground);
  }

  .sidebar-trigger.secondary:hover:not(.disabled) {
    background: hsl(217.2 32.6% 25%);
  }

  .sidebar-trigger.primary {
    background: var(--sidebar-primary);
    color: var(--sidebar-primary-foreground);
  }

  .sidebar-trigger.primary:hover:not(.disabled) {
    background: hsl(263.4 70% 55%);
  }

  /* Focus state */
  .sidebar-trigger:focus {
    outline: none;
    box-shadow: 0 0 0 2px var(--sidebar-ring);
  }

  /* Active state */
  .sidebar-trigger:active:not(.disabled) {
    transform: scale(0.95);
  }

  /* Disabled state */
  .sidebar-trigger.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  /* Icon styling */
  .sidebar-trigger-icon {
    transition: transform 0.2s ease;
    flex-shrink: 0;
  }

  .sidebar-trigger:hover:not(.disabled) .sidebar-trigger-icon {
    transform: scale(1.1);
  }

  /* Text content when present */
  .sidebar-trigger :global(.sidebar-trigger-text) {
    white-space: nowrap;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-trigger.icon {
      width: 2.5rem;
      height: 2.5rem;
    }
    
    .sidebar-trigger-icon {
      width: 18px;
      height: 18px;
    }
  }

  /* Animation for icon transitions */
  @keyframes rotate-in {
    from {
      transform: rotate(-90deg) scale(0.8);
      opacity: 0;
    }
    to {
      transform: rotate(0deg) scale(1);
      opacity: 1;
    }
  }

  .sidebar-trigger-icon {
    animation: rotate-in 0.2s ease-out;
  }

  /* Mobile-specific behavior */
  @media (max-width: 768px) {
    .sidebar-trigger {
      position: relative;
      z-index: 50;
    }
  }

  /* Accessibility improvements */
  .sidebar-trigger[aria-expanded="true"] {
    background: hsl(217.2 32.6% 17.5% / 0.3);
  }

  .sidebar-trigger[aria-expanded="false"] {
    background: transparent;
  }

  /* Keyboard navigation */
  .sidebar-trigger:focus-visible {
    box-shadow: 0 0 0 2px var(--sidebar-ring);
    outline: none;
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .sidebar-trigger {
      border: 1px solid currentColor;
    }
    
    .sidebar-trigger.ghost {
      border: 1px solid transparent;
    }
    
    .sidebar-trigger:focus {
      box-shadow: 0 0 0 3px currentColor;
    }
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    .sidebar-trigger,
    .sidebar-trigger-icon {
      transition: none;
      animation: none;
    }
    
    .sidebar-trigger:active:not(.disabled) {
      transform: none;
    }
  }
</style>