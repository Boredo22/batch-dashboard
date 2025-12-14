<script>
  import { onMount, onDestroy } from 'svelte';
  import { Toaster, toast } from 'svelte-sonner';
  import DashboardLayout from '$lib/components/layout/dashboard-layout.svelte';
  import Dashboard from './Dashboard.svelte';
  import Stage2Testing from './Stage2Testing.svelte';
  import Settings from './Settings.svelte';
  import HeadGrower from './HeadGrower.svelte';
  import Nutrients from './Nutrients.svelte';
  import FlowMeters from './FlowMeters.svelte';

  let currentPage = $state('headgrower');
  let systemStatus = $state('disconnected');
  let showShortcutsHelp = $state(false);

  // Keyboard shortcut definitions
  const shortcuts = {
    'e': { action: 'emergency', description: 'Emergency Stop' },
    '1': { action: 'tank1', description: 'Select Tank 1' },
    '2': { action: 'tank2', description: 'Select Tank 2' },
    '3': { action: 'tank3', description: 'Select Tank 3' },
    'g': { action: 'grower', description: 'Go to Grower Dashboard' },
    'n': { action: 'nutrients', description: 'Go to Nutrients' },
    'd': { action: 'dashboard', description: 'Go to Hardware Testing' },
    's': { action: 'settings', description: 'Go to Settings' },
    '?': { action: 'help', description: 'Show Shortcuts Help' }
  };

  async function fetchSystemStatus() {
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const data = await response.json();
        // The API returns success: true/false, not a status string
        // Use success to determine connection status
        systemStatus = data.success ? 'connected' : 'error';
      } else {
        systemStatus = 'error';
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
      systemStatus = 'disconnected';
    }
  }

  async function emergencyStop() {
    try {
      const response = await fetch('/api/emergency/stop', { method: 'POST' });
      if (response.ok) {
        toast.warning('EMERGENCY STOP ACTIVATED', {
          description: 'All operations halted',
          duration: 5000
        });
      } else {
        toast.error('Emergency stop failed!');
      }
    } catch (error) {
      toast.error(`Emergency stop error: ${error.message}`);
    }
  }

  function handleKeydown(event) {
    // Ignore shortcuts when typing in input fields
    if (event.target.tagName === 'INPUT' ||
        event.target.tagName === 'TEXTAREA' ||
        event.target.tagName === 'SELECT') {
      return;
    }

    const key = event.key.toLowerCase();
    const shortcut = shortcuts[key];

    if (!shortcut) return;

    // Prevent default for our shortcuts
    event.preventDefault();

    switch (shortcut.action) {
      case 'emergency':
        emergencyStop();
        break;
      case 'tank1':
        globalThis.selectTank?.(1) || toast.info('Tank 1 selected (shortcut)');
        break;
      case 'tank2':
        globalThis.selectTank?.(2) || toast.info('Tank 2 selected (shortcut)');
        break;
      case 'tank3':
        globalThis.selectTank?.(3) || toast.info('Tank 3 selected (shortcut)');
        break;
      case 'grower':
        currentPage = 'headgrower';
        toast.info('Navigated to Grower Dashboard');
        break;
      case 'nutrients':
        currentPage = 'nutrients';
        toast.info('Navigated to Nutrients');
        break;
      case 'dashboard':
        currentPage = 'stage1';
        toast.info('Navigated to Hardware Testing');
        break;
      case 'settings':
        currentPage = 'settings';
        toast.info('Navigated to Settings');
        break;
      case 'help':
        showShortcutsHelp = !showShortcutsHelp;
        break;
    }
  }

  onMount(() => {
    fetchSystemStatus();
    // Poll system status every 5 seconds
    const interval = setInterval(fetchSystemStatus, 5000);

    // Add keyboard shortcut listener
    window.addEventListener('keydown', handleKeydown);

    return () => {
      clearInterval(interval);
      window.removeEventListener('keydown', handleKeydown);
    };
  });

  function getPageConfig() {
    switch (currentPage) {
      case 'headgrower':
        return {
          title: 'Grower Dashboard',
          subtitle: 'Complete growing operations and job management',
          breadcrumbs: [{ title: 'Grower Dashboard' }]
        };
      case 'nutrients':
        return {
          title: 'Nutrient Management',
          subtitle: 'Manual dispensing and recipe management',
          breadcrumbs: [{ title: 'Nutrients' }]
        };
      case 'stage1':
        return {
          title: 'Hardware Testing Dashboard',
          subtitle: 'Individual component testing and control',
          breadcrumbs: [{ title: 'Stage 1', href: '#' }, { title: 'Hardware Testing' }]
        };
      case 'stage2':
        return {
          title: 'Stage 2 Testing',
          subtitle: 'Complete job process testing',
          breadcrumbs: [{ title: 'Stage 2', href: '#' }, { title: 'Job Testing' }]
        };
      case 'settings':
        return {
          title: 'System Settings',
          subtitle: 'Configuration and preferences',
          breadcrumbs: [{ title: 'Settings' }]
        };
      case 'flowmeters':
        return {
          title: 'Flow Meter Diagnostics',
          subtitle: 'Real-time GPIO monitoring and pulse detection troubleshooting',
          breadcrumbs: [{ title: 'Diagnostics', href: '#' }, { title: 'Flow Meters' }]
        };
      default:
        return {
          title: 'Nutrient Mixing System',
          subtitle: '',
          breadcrumbs: []
        };
    }
  }

  let pageConfig = $derived(getPageConfig());

  // Navigation function for when we implement proper routing later
  function navigateTo(page) {
    currentPage = page;
  }

  // Expose navigation globally for now (until we implement proper routing)
  globalThis.navigateTo = navigateTo;
</script>

<div class="min-h-screen bg-background text-foreground">
  <!-- Global toast notifications -->
  <Toaster
    richColors
    position="top-right"
    toastOptions={{
      style: 'background: hsl(var(--card)); border: 1px solid hsl(var(--border)); color: hsl(var(--foreground));'
    }}
  />

  <DashboardLayout
    title={pageConfig.title}
    subtitle={pageConfig.subtitle}
    {systemStatus}
    breadcrumbs={pageConfig.breadcrumbs}
  >
    {#snippet children()}
      {#if currentPage === 'headgrower'}
        <HeadGrower />
      {:else if currentPage === 'nutrients'}
        <Nutrients />
      {:else if currentPage === 'stage1'}
        <Dashboard />
      {:else if currentPage === 'stage2'}
        <Stage2Testing />
      {:else if currentPage === 'flowmeters'}
        <FlowMeters />
      {:else if currentPage === 'settings'}
        <Settings />
      {/if}
    {/snippet}
  </DashboardLayout>

  <!-- Keyboard Shortcuts Help Modal -->
  {#if showShortcutsHelp}
    <div class="shortcuts-overlay" onclick={() => showShortcutsHelp = false} role="dialog" aria-modal="true">
      <div class="shortcuts-modal" onclick={(e) => e.stopPropagation()}>
        <div class="shortcuts-header">
          <h3>Keyboard Shortcuts</h3>
          <button class="close-btn" onclick={() => showShortcutsHelp = false} aria-label="Close">
            &times;
          </button>
        </div>
        <div class="shortcuts-content">
          <div class="shortcuts-section">
            <h4>Emergency</h4>
            <div class="shortcut-row">
              <kbd>E</kbd>
              <span>Emergency Stop</span>
            </div>
          </div>
          <div class="shortcuts-section">
            <h4>Navigation</h4>
            <div class="shortcut-row">
              <kbd>G</kbd>
              <span>Grower Dashboard</span>
            </div>
            <div class="shortcut-row">
              <kbd>N</kbd>
              <span>Nutrients</span>
            </div>
            <div class="shortcut-row">
              <kbd>D</kbd>
              <span>Hardware Testing</span>
            </div>
            <div class="shortcut-row">
              <kbd>S</kbd>
              <span>Settings</span>
            </div>
          </div>
          <div class="shortcuts-section">
            <h4>Tank Selection</h4>
            <div class="shortcut-row">
              <kbd>1</kbd>
              <span>Select Tank 1</span>
            </div>
            <div class="shortcut-row">
              <kbd>2</kbd>
              <span>Select Tank 2</span>
            </div>
            <div class="shortcut-row">
              <kbd>3</kbd>
              <span>Select Tank 3</span>
            </div>
          </div>
          <div class="shortcuts-section">
            <h4>Help</h4>
            <div class="shortcut-row">
              <kbd>?</kbd>
              <span>Show this help</span>
            </div>
          </div>
        </div>
        <div class="shortcuts-footer">
          <span class="hint">Press <kbd>?</kbd> anytime to toggle this help</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .shortcuts-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }

  .shortcuts-modal {
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: 0.75rem;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  }

  .shortcuts-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid hsl(var(--border));
  }

  .shortcuts-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .close-btn {
    background: none;
    border: none;
    color: hsl(var(--muted-foreground));
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    transition: color 0.15s;
  }

  .close-btn:hover {
    color: hsl(var(--foreground));
  }

  .shortcuts-content {
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .shortcuts-section h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.75rem;
    font-weight: 600;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .shortcut-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.375rem 0;
  }

  kbd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.75rem;
    height: 1.75rem;
    padding: 0 0.5rem;
    background: hsl(var(--muted));
    border: 1px solid hsl(var(--border));
    border-radius: 0.25rem;
    font-family: ui-monospace, monospace;
    font-size: 0.8rem;
    font-weight: 500;
    color: hsl(var(--foreground));
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .shortcut-row span {
    color: hsl(var(--muted-foreground));
    font-size: 0.875rem;
  }

  .shortcuts-footer {
    padding: 0.75rem 1.25rem;
    border-top: 1px solid hsl(var(--border));
    background: hsl(var(--muted) / 0.3);
    border-radius: 0 0 0.75rem 0.75rem;
  }

  .hint {
    font-size: 0.75rem;
    color: hsl(var(--muted-foreground));
  }

  .hint kbd {
    height: 1.25rem;
    min-width: 1.25rem;
    font-size: 0.7rem;
  }
</style>