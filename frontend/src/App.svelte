<script>
  import { onMount } from 'svelte';
  import DashboardLayout from '$lib/components/layout/dashboard-layout.svelte';
  import Dashboard from './Dashboard.svelte';
  import Stage2Testing from './Stage2Testing.svelte';
  import Settings from './Settings.svelte';
  import HeadGrower from './HeadGrower.svelte';
  import Nutrients from './Nutrients.svelte';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';

  let currentPage = $state('headgrower');

  // Get reactive system status from SSE store
  const status = getSystemStatus();

  // Derive connection status for the layout
  let systemStatus = $derived(status.isConnected ? 'connected' : status.connectionStatus);

  onMount(() => {
    // Subscribe to SSE updates - returns unsubscribe function for cleanup
    const unsubscribe = subscribe();
    return unsubscribe;
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
      {:else if currentPage === 'settings'}
        <Settings />
      {/if}
    {/snippet}
  </DashboardLayout>
</div>