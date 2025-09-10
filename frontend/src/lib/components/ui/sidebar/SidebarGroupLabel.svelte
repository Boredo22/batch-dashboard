<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    asChild = false,
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');
</script>

{#if asChild}
  {@render children?.({ class: `sidebar-group-label ${className}`, collapsed: !sidebar.isOpen, ...restProps })}
{:else}
  <div
    class="sidebar-group-label {className}"
    class:collapsed={!sidebar.isOpen}
    data-sidebar="group-label"
    {...restProps}
  >
    {@render children?.()}
  </div>
{/if}

<style>
  .sidebar-group-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0 0.25rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
    color: hsl(215.4 16.3% 46.9%);
    line-height: 1.5;
  }

  .sidebar-group-label.collapsed {
    justify-content: center;
    padding: 0.5rem 0;
  }

  /* Hide text when collapsed */
  .sidebar-group-label.collapsed :global(.sidebar-label-text) {
    display: none;
  }

  /* Icon styling */
  .sidebar-group-label :global(.sidebar-group-icon) {
    width: 1rem;
    height: 1rem;
    flex-shrink: 0;
  }

  .sidebar-group-label.collapsed :global(.sidebar-group-icon) {
    width: 1.25rem;
    height: 1.25rem;
  }

  /* Divider line */
  .sidebar-group-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--sidebar-border);
    opacity: 0.3;
    margin-left: 0.5rem;
  }

  .sidebar-group-label.collapsed::after {
    display: none;
  }

  /* Tooltip for collapsed state */
  .sidebar-group-label.collapsed {
    position: relative;
  }

  .sidebar-group-label.collapsed:hover::before {
    content: attr(data-tooltip);
    position: absolute;
    left: calc(100% + 0.5rem);
    top: 50%;
    transform: translateY(-50%);
    background: hsl(222.2 84% 4.9%);
    color: var(--sidebar-foreground);
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: none;
    letter-spacing: normal;
    white-space: nowrap;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--sidebar-border);
    z-index: 50;
    opacity: 0;
    animation: tooltip-in 0.15s ease-out forwards;
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

  /* Ensure proper alignment */
  .sidebar-group-label {
    min-height: 1.5rem;
  }

  /* Hover effect */
  .sidebar-group-label:hover {
    color: var(--sidebar-foreground);
  }

  /* Focus styles for accessibility */
  .sidebar-group-label:focus {
    outline: none;
    color: var(--sidebar-foreground);
  }

  /* Animation for transitions */
  .sidebar-group-label {
    transition: color 0.2s ease, padding 0.2s ease, justify-content 0.2s ease;
  }

  .sidebar-group-label::after {
    transition: opacity 0.2s ease;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-group-label {
      font-size: 0.6875rem;
    }
  }
</style>