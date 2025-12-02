<script>
  import { createEventDispatcher, setContext } from 'svelte';

  const {
    side = 'left',
    variant = 'sidebar',
    collapsible = 'offcanvas',
    children,
    ...restProps
  } = $props();

  let isOpen = $state(false); // Start collapsed to show only icons
  let isMobile = $state(false);

  const dispatch = createEventDispatcher();

  // Context for child components
  setContext('sidebar', {
    get isOpen() { return isOpen; },
    get isMobile() { return isMobile; },
    get side() { return side; },
    get variant() { return variant; },
    get collapsible() { return collapsible; },
    toggleSidebar: () => {
      isOpen = !isOpen;
      dispatch('toggle', { isOpen });
    },
    openSidebar: () => {
      isOpen = true;
      dispatch('open', { isOpen });
    },
    closeSidebar: () => {
      isOpen = false;
      dispatch('close', { isOpen });
    }
  });

  // Handle mobile detection
  $effect(() => {
    const checkMobile = () => {
      isMobile = window.innerWidth < 768;
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  });

  // Close sidebar on mobile when clicking outside
  $effect(() => {
    if (isMobile && isOpen) {
      const handleClickOutside = (event) => {
        const sidebar = document.querySelector('[data-sidebar]');
        if (sidebar && !sidebar.contains(event.target)) {
          isOpen = false;
        }
      };

      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  });
</script>

<div 
  class="sidebar-provider"
  class:open={isOpen}
  class:mobile={isMobile}
  data-sidebar-provider
  data-side={side}
  data-variant={variant}
  data-collapsible={collapsible}
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  :global(.sidebar-provider) {
    /* Sidebar dimensions */
    --sidebar-width: 16rem;
    --sidebar-width-mobile: 18rem;
    --sidebar-width-icon: 4.5rem;

    /* Industrial dark theme colors */
    --sidebar-background: #0a0f1e;
    --sidebar-background-secondary: #1a1f35;
    --sidebar-foreground: #f1f5f9;
    --sidebar-muted-foreground: #94a3b8;

    /* Purple accent colors */
    --sidebar-primary: #8b5cf6;
    --sidebar-primary-light: #a78bfa;
    --sidebar-primary-dark: #7c3aed;
    --sidebar-primary-foreground: #ffffff;

    /* Green accent colors */
    --sidebar-accent-green: #10b981;
    --sidebar-accent-green-light: #34d399;

    /* Borders and dividers */
    --sidebar-border: rgba(139, 92, 246, 0.2);
    --sidebar-border-hover: rgba(139, 92, 246, 0.4);

    /* State colors */
    --sidebar-ring: #8b5cf6;
    --sidebar-hover-bg: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
    --sidebar-active-bg: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));

    /* Shadows */
    --sidebar-shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.3);
    --sidebar-shadow-md: 0 8px 24px rgba(0, 0, 0, 0.4);
    --sidebar-shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);

    /* Transitions */
    --sidebar-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    display: flex;
    min-height: 100vh;
    width: 100%;
  }

  :global(.sidebar-provider.mobile) {
    --sidebar-width: var(--sidebar-width-mobile);
  }

  :global([data-sidebar]) {
    background: linear-gradient(135deg, var(--sidebar-background-secondary) 0%, var(--sidebar-background) 100%);
    border-right: 1px solid var(--sidebar-border);
    transition: var(--sidebar-transition);
    box-shadow: var(--sidebar-shadow-md), 0 0 0 1px rgba(139, 92, 246, 0.08) inset;
  }

  :global(.sidebar-provider:not(.open)) {
    --sidebar-width: var(--sidebar-width-icon);
  }

  /* Custom scrollbar for sidebar */
  :global([data-sidebar] *::-webkit-scrollbar) {
    width: 6px;
  }

  :global([data-sidebar] *::-webkit-scrollbar-track) {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 3px;
  }

  :global([data-sidebar] *::-webkit-scrollbar-thumb) {
    background: linear-gradient(to bottom, #8b5cf6, #7c3aed);
    border-radius: 3px;
    transition: background 0.3s;
  }

  :global([data-sidebar] *::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(to bottom, #a78bfa, #8b5cf6);
  }

  @media (max-width: 768px) {
    :global(.sidebar-provider) {
      --sidebar-width: var(--sidebar-width-mobile);
    }
  }
</style>