<script>
  import { createEventDispatcher, setContext } from 'svelte';

  const {
    side = 'left',
    variant = 'sidebar',
    collapsible = 'offcanvas',
    children,
    ...restProps
  } = $props();

  let isOpen = $state(true);
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
    --sidebar-width: 16rem;
    --sidebar-width-mobile: 18rem;
    --sidebar-width-icon: 3rem;
    --sidebar-border: hsl(217.2 32.6% 17.5%);
    --sidebar-background: hsl(222.2 84% 4.9%);
    --sidebar-foreground: hsl(210 40% 98%);
    --sidebar-primary: hsl(263.4 70% 50.4%);
    --sidebar-primary-foreground: hsl(210 40% 98%);
    --sidebar-accent: hsl(217.2 32.6% 17.5%);
    --sidebar-accent-foreground: hsl(210 40% 98%);
    --sidebar-ring: hsl(263.4 70% 50.4%);
    
    display: flex;
    min-height: 100vh;
    width: 100%;
  }

  :global(.sidebar-provider.mobile) {
    --sidebar-width: var(--sidebar-width-mobile);
  }

  :global([data-sidebar]) {
    transition: all 0.2s ease;
  }

  :global(.sidebar-provider:not(.open)) {
    --sidebar-width: var(--sidebar-width-icon);
  }

  @media (max-width: 768px) {
    :global(.sidebar-provider) {
      --sidebar-width: var(--sidebar-width-mobile);
    }
  }
</style>