<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');
</script>

<main
  class="sidebar-inset {className}"
  class:sidebar-collapsed={!sidebar?.isOpen}
  class:sidebar-mobile={sidebar?.isMobile}
  data-sidebar="inset"
  data-sidebar-state={sidebar?.isOpen ? 'expanded' : 'collapsed'}
  {...restProps}
>
  {@render children?.()}
</main>

<style>
  .sidebar-inset {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    min-width: 0;
    background: transparent;
    transition: margin-left 0.2s ease, width 0.2s ease;
  }

  /* When sidebar is expanded */
  .sidebar-inset:not(.sidebar-collapsed) {
    margin-left: 0;
    width: calc(100% - var(--sidebar-width));
  }

  /* When sidebar is collapsed */
  .sidebar-inset.sidebar-collapsed {
    margin-left: 0;
    width: calc(100% - var(--sidebar-width-icon));
  }

  /* Mobile behavior */
  .sidebar-inset.sidebar-mobile {
    width: 100% !important;
    margin-left: 0 !important;
  }

  /* Mobile overlay when sidebar is open */
  .sidebar-inset.sidebar-mobile:not(.sidebar-collapsed)::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
    z-index: 30;
    opacity: 0;
    animation: overlay-in 0.2s ease-out forwards;
  }

  @keyframes overlay-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  /* Content area styling */
  .sidebar-inset {
    position: relative;
    overflow-x: hidden;
  }

  /* Ensure proper content spacing */
  .sidebar-inset :global(.sidebar-inset-content) {
    flex: 1;
    padding: 1rem;
    max-width: 100%;
  }

  /* Header area within inset */
  .sidebar-inset :global(.sidebar-inset-header) {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-bottom: 1px solid hsl(var(--border));
    background: hsl(var(--background) / 0.8);
    min-height: 3.5rem;
  }

  .sidebar-inset :global(.sidebar-inset-header h1) {
    font-size: 1.5rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin: 0;
  }

  /* Breadcrumb styling */
  .sidebar-inset :global(.sidebar-breadcrumb) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
  }

  .sidebar-inset :global(.sidebar-breadcrumb-separator) {
    color: hsl(var(--muted-foreground) / 0.6);
  }

  .sidebar-inset :global(.sidebar-breadcrumb-item) {
    color: inherit;
    text-decoration: none;
    transition: color 0.2s ease;
  }

  .sidebar-inset :global(.sidebar-breadcrumb-item:hover) {
    color: hsl(var(--foreground));
  }

  .sidebar-inset :global(.sidebar-breadcrumb-item[aria-current="page"]) {
    color: hsl(var(--foreground));
    font-weight: 500;
  }

  /* Page actions area */
  .sidebar-inset :global(.sidebar-inset-actions) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-left: auto;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-inset :global(.sidebar-inset-header) {
      padding: 1rem 0.75rem;
    }
    
    .sidebar-inset :global(.sidebar-inset-content) {
      padding: 1rem 0.75rem;
    }
  }

  /* Scroll behavior */
  .sidebar-inset {
    overflow-y: auto;
  }

  /* Focus management */
  .sidebar-inset:focus {
    outline: none;
  }

  /* Accessibility improvements */
  .sidebar-inset[data-sidebar-state="collapsed"] {
    /* Announce state change for screen readers */
  }

  /* Animation for smooth transitions */

  /* Handle different sidebar variants */
  :global([data-variant="floating"]) + .sidebar-inset {
    margin-left: 0.5rem;
  }

  :global([data-variant="floating"]) + .sidebar-inset:not(.sidebar-collapsed) {
    width: calc(100% - var(--sidebar-width) - 0.5rem);
  }

  :global([data-variant="floating"]) + .sidebar-inset.sidebar-collapsed {
    width: calc(100% - var(--sidebar-width-icon) - 0.5rem);
  }

  :global([data-variant="inset"]) + .sidebar-inset {
    border-radius: 0.5rem;
    margin: 0.5rem;
    min-height: calc(100vh - 1rem);
  }

  /* Print styles */
  @media print {
    .sidebar-inset {
      width: 100% !important;
      margin-left: 0 !important;
    }
    
    .sidebar-inset::before {
      display: none !important;
    }
  }

  /* High contrast mode */
  @media (prefers-contrast: high) {
    .sidebar-inset {
      border-left: 1px solid currentColor;
    }
  }

  /* Reduced motion */
  @media (prefers-reduced-motion: reduce) {
    .sidebar-inset {
      transition: none !important;
      animation: none !important;
    }
  }
</style>