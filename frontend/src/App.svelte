<script>
  import { onMount } from 'svelte';
  import DashboardLayout from '$lib/components/layout/dashboard-layout.svelte';
  import Dashboard from './Dashboard.svelte';
  import Stage2Testing from './Stage2Testing.svelte';
  import Settings from './Settings.svelte';
  import HeadGrower from './HeadGrower.svelte';
  import Nutrients from './Nutrients.svelte';

  let currentPage = $state('headgrower');
  let systemStatus = $state('disconnected');

  async function fetchSystemStatus() {
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const data = await response.json();
        systemStatus = data.status || 'connected';
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
      systemStatus = 'error';
    }
  }

  onMount(() => {
    fetchSystemStatus();
    // Poll system status every 5 seconds
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
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