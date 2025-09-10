// Sidebar component exports
export { default as Sidebar } from './Sidebar.svelte';
export { default as SidebarInset } from './SidebarInset.svelte';
export { default as SidebarTrigger } from './SidebarTrigger.svelte';

// Short name exports for namespace imports
export { default as Root } from './SidebarRoot.svelte';
export { default as Header } from './SidebarHeader.svelte';
export { default as Content } from './SidebarContent.svelte';
export { default as Footer } from './SidebarFooter.svelte';
export { default as Group } from './SidebarGroup.svelte';
export { default as GroupLabel } from './SidebarGroupLabel.svelte';
export { default as GroupContent } from './SidebarGroupContent.svelte';
export { default as Menu } from './SidebarMenu.svelte';
export { default as MenuItem } from './SidebarMenuItem.svelte';
export { default as MenuButton } from './SidebarMenuButton.svelte';
export { default as Trigger } from './SidebarTrigger.svelte';

// Full name exports for explicit imports
export { default as SidebarRoot } from './SidebarRoot.svelte';
export { default as SidebarHeader } from './SidebarHeader.svelte';
export { default as SidebarContent } from './SidebarContent.svelte';
export { default as SidebarFooter } from './SidebarFooter.svelte';
export { default as SidebarGroup } from './SidebarGroup.svelte';
export { default as SidebarGroupLabel } from './SidebarGroupLabel.svelte';
export { default as SidebarGroupContent } from './SidebarGroupContent.svelte';
export { default as SidebarMenu } from './SidebarMenu.svelte';
export { default as SidebarMenuItem } from './SidebarMenuItem.svelte';
export { default as SidebarMenuButton } from './SidebarMenuButton.svelte';

// Common sidebar utilities and configurations
export const sidebarConfig = {
  // Default sidebar widths
  width: '16rem',
  widthMobile: '18rem',
  widthIcon: '3rem',
  
  // Breakpoints
  breakpoints: {
    mobile: 768,
    tablet: 1024,
    desktop: 1280,
  },
  
  // Animation durations
  transitions: {
    default: '0.2s',
    fast: '0.15s',
    slow: '0.3s',
  },
  
  // Sidebar variants
  variants: {
    sidebar: 'sidebar',
    floating: 'floating',
    inset: 'inset',
  },
  
  // Collapsible modes
  collapsible: {
    offcanvas: 'offcanvas',
    icon: 'icon',
    none: 'none',
  },
  
  // Sides
  sides: {
    left: 'left',
    right: 'right',
  },
};

// Sidebar context utilities
export const sidebarUtils = {
  /**
   * Get responsive sidebar width based on screen size and state
   * @param {boolean} isOpen - Whether sidebar is open
   * @param {boolean} isMobile - Whether on mobile device
   * @returns {string} CSS width value
   */
  getWidth: (isOpen, isMobile) => {
    if (isMobile) {
      return isOpen ? sidebarConfig.widthMobile : '0';
    }
    return isOpen ? sidebarConfig.width : sidebarConfig.widthIcon;
  },
  
  /**
   * Check if current screen size is mobile
   * @param {number} width - Current window width
   * @returns {boolean} Is mobile size
   */
  isMobile: (width) => width < sidebarConfig.breakpoints.mobile,
  
  /**
   * Generate CSS custom properties for sidebar
   * @param {object} options - Configuration options
   * @returns {object} CSS custom properties
   */
  getCSSProps: (options = {}) => {
    const {
      width = sidebarConfig.width,
      widthMobile = sidebarConfig.widthMobile,
      widthIcon = sidebarConfig.widthIcon,
    } = options;
    
    return {
      '--sidebar-width': width,
      '--sidebar-width-mobile': widthMobile,
      '--sidebar-width-icon': widthIcon,
    };
  },
};

// Sidebar keyboard shortcuts
export const sidebarShortcuts = {
  toggle: ['Meta+b', 'Ctrl+b'],
  close: ['Escape'],
  focusContent: ['Tab'],
  focusTrigger: ['Shift+Tab'],
};

// Sidebar accessibility helpers
export const sidebarA11y = {
  roles: {
    sidebar: 'complementary',
    menu: 'menu',
    menuitem: 'menuitem',
    button: 'button',
    navigation: 'navigation',
  },
  
  ariaLabels: {
    sidebar: 'Main navigation',
    toggle: 'Toggle sidebar',
    close: 'Close sidebar',
    menu: 'Navigation menu',
  },
  
  /**
   * Get ARIA attributes for sidebar components
   * @param {string} component - Component type
   * @param {object} props - Component props
   * @returns {object} ARIA attributes
   */
  getAriaProps: (component, props = {}) => {
    switch (component) {
      case 'sidebar':
        return {
          'role': sidebarA11y.roles.sidebar,
          'aria-label': props.label || sidebarA11y.ariaLabels.sidebar,
        };
      case 'trigger':
        return {
          'aria-label': props.label || sidebarA11y.ariaLabels.toggle,
          'aria-expanded': props.isOpen || false,
          'aria-controls': props.controls || 'sidebar',
        };
      case 'menu':
        return {
          'role': sidebarA11y.roles.menu,
          'aria-label': props.label || sidebarA11y.ariaLabels.menu,
        };
      default:
        return {};
    }
  },
};

// Theme configurations for sidebar
export const sidebarThemes = {
  dark: {
    background: 'hsl(222.2 84% 4.9%)',
    foreground: 'hsl(210 40% 98%)',
    border: 'hsl(217.2 32.6% 17.5%)',
    accent: 'hsl(217.2 32.6% 17.5%)',
    accentForeground: 'hsl(210 40% 98%)',
    primary: 'hsl(263.4 70% 50.4%)',
    primaryForeground: 'hsl(210 40% 98%)',
    ring: 'hsl(263.4 70% 50.4%)',
  },
  
  light: {
    background: 'hsl(0 0% 100%)',
    foreground: 'hsl(222.2 84% 4.9%)',
    border: 'hsl(214.3 31.8% 91.4%)',
    accent: 'hsl(210 40% 96%)',
    accentForeground: 'hsl(222.2 84% 4.9%)',
    primary: 'hsl(263.4 70% 50.4%)',
    primaryForeground: 'hsl(210 40% 98%)',
    ring: 'hsl(263.4 70% 50.4%)',
  },
  
  /**
   * Apply theme to sidebar
   * @param {string} theme - Theme name
   * @returns {object} CSS custom properties
   */
  apply: (theme) => {
    const themeConfig = sidebarThemes[theme] || sidebarThemes.dark;
    const cssProps = {};
    
    Object.entries(themeConfig).forEach(([key, value]) => {
      cssProps[`--sidebar-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`] = value;
    });
    
    return cssProps;
  },
};