<script>
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import {
    LayoutDashboard,
    FlaskConical,
    Settings,
    Activity,
    Droplets,
    Zap,
    Gauge
  } from "@lucide/svelte/icons";

  let { systemStatus = "disconnected" } = $props();

  const menuItems = [
    {
      title: "Head Grower",
      page: "headgrower",
      icon: LayoutDashboard,
      description: "Complete growing operations"
    },
    {
      title: "Nutrients",
      page: "nutrients",
      icon: FlaskConical,
      description: "Manual dispensing & recipes"
    },
    {
      title: "Stage 1: Hardware Testing",
      page: "stage1",
      icon: Zap,
      description: "Individual component testing"
    },
    {
      title: "Stage 2: Job Testing",
      page: "stage2",
      icon: Activity,
      description: "Complete job processes"
    },
    {
      title: "Flow Meter Diagnostics",
      page: "flowmeters",
      icon: Gauge,
      description: "GPIO monitoring & troubleshooting"
    },
    {
      title: "Settings",
      page: "settings",
      icon: Settings,
      description: "System configuration"
    }
  ];

  function handleNavigation(page) {
    if (globalThis.navigateTo) {
      globalThis.navigateTo(page);
    }
  }

  const hardwareItems = [
    { title: "Pumps", icon: Droplets, count: 8 },
    { title: "Relays", icon: Zap, count: 13 },
    { title: "Flow Meters", icon: Activity, count: 2 }
  ];
</script>

<Sidebar.Root variant="inset">
  <Sidebar.Header>
    <div class="sidebar-header">
      <div class="icon-wrapper">
        <FlaskConical class="header-icon" />
      </div>
      <div class="header-content">
        <span class="title">
          Nutrient System
        </span>
        <span class="subtitle">
          Control Panel
        </span>
      </div>
    </div>
  </Sidebar.Header>

  <Sidebar.Content>
    <Sidebar.Group>
      <Sidebar.GroupLabel class="group-label">Navigation</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each menuItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                onclick={() => handleNavigation(item.page)}
                tooltip={item.title}
                class="menu-button"
              >
                {@const Icon = item.icon}
                <Icon class="size-4 menu-icon" />
                <span class="menu-text">{item.title}</span>
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <div class="divider"></div>

    <Sidebar.Group class="group-data-[collapsible=icon]:hidden">
      <Sidebar.GroupLabel class="group-label">Hardware Status</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each hardwareItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton class="hardware-button">
                {@const Icon = item.icon}
                <Icon class="size-4 hardware-icon" />
                <span class="hardware-text">{item.title}</span>
                <Badge variant="secondary" class="hardware-badge">
                  {item.count}
                </Badge>
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer>
    <div class="sidebar-footer">
      <div class="footer-content">
        <div class="status-label">System Status</div>
        <Badge class="status-badge status-{String(systemStatus).toLowerCase()}">
          <div class="status-dot"></div>
          <span class="status-text">{systemStatus}</span>
        </Badge>
      </div>
    </div>
  </Sidebar.Footer>
</Sidebar.Root>

<style>
  /* Sidebar Header */
  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: linear-gradient(135deg, #1a1f35 0%, #151929 100%);
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
  }

  :global([data-state="collapsed"]) .sidebar-header {
    justify-content: center;
    padding: 1rem 0.5rem;
  }

  .icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    min-width: 2.5rem;
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    border-radius: 0.5rem;
    box-shadow:
      0 0 20px rgba(139, 92, 246, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar-header:hover .icon-wrapper {
    transform: translateY(-2px);
    box-shadow:
      0 0 30px rgba(139, 92, 246, 0.6),
      0 6px 16px rgba(0, 0, 0, 0.4);
  }

  .header-icon {
    width: 1.25rem;
    height: 1.25rem;
    color: white;
  }

  .header-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 0.125rem;
    min-width: 0;
    opacity: 1;
    transition: opacity 0.2s ease;
  }

  :global([data-state="collapsed"]) .header-content {
    opacity: 0;
    width: 0;
    overflow: hidden;
  }

  .title {
    font-size: 1rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.025em;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }

  .subtitle {
    font-size: 0.75rem;
    font-weight: 600;
    color: #8b5cf6;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Divider */
  .divider {
    height: 1px;
    margin: 0.75rem 1rem;
    background: linear-gradient(to right, transparent, rgba(139, 92, 246, 0.3), transparent);
    transition: opacity 0.2s ease;
  }

  :global([data-state="collapsed"]) .divider {
    opacity: 0;
    height: 0;
    margin: 0;
  }

  /* Group Labels */
  :global(.group-label) {
    font-size: 0.625rem !important;
    font-weight: 800 !important;
    color: #8b5cf6 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1rem !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    transition: opacity 0.2s ease !important;
  }

  :global([data-state="collapsed"]) :global(.group-label) {
    opacity: 0;
    height: 0;
    padding: 0 !important;
    overflow: hidden;
  }

  /* Menu Buttons */
  :global(.menu-button) {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    margin: 0.125rem 0.5rem;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 0.5rem;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  :global([data-state="collapsed"]) :global(.menu-button) {
    justify-content: center;
    padding: 0.75rem;
    margin: 0.125rem auto;
  }

  :global(.menu-button::before) {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(to bottom, #8b5cf6, #7c3aed);
    opacity: 0;
    transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global(.menu-button:hover) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
    border-color: rgba(139, 92, 246, 0.2);
    color: #f1f5f9;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
  }

  :global(.menu-button:hover::before) {
    opacity: 1;
  }

  :global(.menu-button[data-active="true"]) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
    border-color: rgba(139, 92, 246, 0.3);
    color: #f1f5f9;
    box-shadow:
      0 0 20px rgba(139, 92, 246, 0.2),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }

  :global(.menu-button[data-active="true"]::before) {
    opacity: 1;
  }

  :global(.menu-icon) {
    color: #8b5cf6;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global(.menu-button:hover .menu-icon) {
    color: #a78bfa;
    transform: scale(1.1);
  }

  :global(.menu-text) {
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    white-space: nowrap;
    opacity: 1;
    transition: opacity 0.2s ease;
  }

  :global([data-state="collapsed"]) :global(.menu-text) {
    opacity: 0;
    width: 0;
    overflow: hidden;
  }

  /* Hardware Buttons */
  :global(.hardware-button) {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.625rem 1rem;
    margin: 0.125rem 0.5rem;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 0.5rem;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global([data-state="collapsed"]) :global(.hardware-button) {
    justify-content: center;
    padding: 0.625rem;
    margin: 0.125rem auto;
  }

  :global(.hardware-button:hover) {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(124, 58, 237, 0.04));
    border-color: rgba(139, 92, 246, 0.15);
    transform: translateY(-1px);
  }

  :global(.hardware-icon) {
    color: #6b7280;
    transition: color 0.3s;
  }

  :global(.hardware-button:hover .hardware-icon) {
    color: #8b5cf6;
  }

  :global(.hardware-text) {
    font-size: 0.875rem;
    font-weight: 500;
    flex: 1;
    white-space: nowrap;
    opacity: 1;
    transition: opacity 0.2s ease;
  }

  :global([data-state="collapsed"]) :global(.hardware-text) {
    opacity: 0;
    width: 0;
    overflow: hidden;
  }

  :global(.hardware-badge) {
    background: rgba(139, 92, 246, 0.15) !important;
    color: #a78bfa !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    padding: 0.125rem 0.5rem !important;
    border-radius: 0.375rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  }

  :global([data-state="collapsed"]) :global(.hardware-badge) {
    opacity: 0;
    width: 0;
    padding: 0 !important;
    overflow: hidden;
  }

  :global(.hardware-button:hover .hardware-badge) {
    background: rgba(139, 92, 246, 0.25) !important;
    color: #c4b5fd !important;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.3) !important;
  }

  /* Sidebar Footer */
  .sidebar-footer {
    padding: 1rem;
    background: linear-gradient(135deg, #1a1f35 0%, #151929 100%);
    border-top: 1px solid rgba(139, 92, 246, 0.2);
  }

  :global([data-state="collapsed"]) .sidebar-footer {
    padding: 1rem 0.5rem;
    display: flex;
    justify-content: center;
  }

  .footer-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  :global([data-state="collapsed"]) .footer-content {
    align-items: center;
  }

  .status-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #8b5cf6;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    transition: opacity 0.2s ease;
  }

  :global([data-state="collapsed"]) .status-label {
    opacity: 0;
    height: 0;
    overflow: hidden;
  }

  .status-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: fit-content;
  }

  :global([data-state="collapsed"]) .status-badge {
    padding: 0.5rem;
    width: auto;
  }

  .status-text {
    white-space: nowrap;
    opacity: 1;
    transition: opacity 0.2s ease;
  }

  :global([data-state="collapsed"]) .status-text {
    opacity: 0;
    width: 0;
    overflow: hidden;
  }

  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    min-width: 0.5rem;
    border-radius: 9999px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Status Badge Variants */
  :global(.status-badge.status-connected) {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1)) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    color: #34d399 !important;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.2) !important;
  }

  :global(.status-badge.status-connected .status-dot) {
    background: #10b981;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
    animation: pulse-dot 2s ease-in-out infinite;
  }

  :global(.status-badge.status-disconnected) {
    background: rgba(71, 85, 105, 0.2) !important;
    border: 1px solid rgba(100, 116, 139, 0.3) !important;
    color: #94a3b8 !important;
  }

  :global(.status-badge.status-disconnected .status-dot) {
    background: #64748b;
  }

  :global(.status-badge.status-error) {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1)) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    color: #f87171 !important;
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.2) !important;
  }

  :global(.status-badge.status-error .status-dot) {
    background: #ef4444;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.6);
    animation: pulse-dot 1s ease-in-out infinite;
  }

  @keyframes pulse-dot {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.7;
      transform: scale(1.2);
    }
  }

  .status-text {
    text-transform: capitalize;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-header {
      padding: 0.875rem;
    }

    .icon-wrapper {
      width: 2rem;
      height: 2rem;
    }

    .icon {
      width: 1rem;
      height: 1rem;
    }

    .title {
      font-size: 0.875rem;
    }

    .subtitle {
      font-size: 0.625rem;
    }
  }
</style>