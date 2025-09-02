<script>
  import Dashboard from './Dashboard.svelte';
  import Stage2Testing from './Stage2Testing.svelte';
  import Settings from './Settings.svelte';
  
  let currentPage = $state('stage1');
  
  function navigateTo(page) {
    currentPage = page;
  }
</script>

<div class="app-container">
  <nav class="navigation">
    <div class="nav-brand">
      <h2>Nutrient System Dashboard</h2>
    </div>
    <div class="nav-tabs">
      <button 
        class="nav-tab {currentPage === 'stage1' ? 'active' : ''}"
        onclick={() => navigateTo('stage1')}
      >
        <i class="fas fa-tools"></i>
        Stage 1: Hardware Testing
      </button>
      <button 
        class="nav-tab {currentPage === 'stage2' ? 'active' : ''}"
        onclick={() => navigateTo('stage2')}
      >
        <i class="fas fa-cogs"></i>
        Stage 2: Job Testing
      </button>
      <button 
        class="nav-tab {currentPage === 'settings' ? 'active' : ''}"
        onclick={() => navigateTo('settings')}
      >
        <i class="fas fa-sliders-h"></i>
        Settings
      </button>
    </div>
  </nav>

  <div class="page-content">
    {#if currentPage === 'stage1'}
      <Dashboard />
    {:else if currentPage === 'stage2'}
      <Stage2Testing />
    {:else if currentPage === 'settings'}
      <Settings />
    {/if}
  </div>
</div>

<style>
  .app-container {
    width: 100vw;
    height: 100vh;
    background: #1a1a1a;
    color: white;
    display: flex;
    flex-direction: column;
  }

  .navigation {
    background: #0f172a;
    padding: 0.75rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #334155;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .nav-brand h2 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1.2rem;
    font-weight: 600;
  }

  .nav-tabs {
    display: flex;
    gap: 1rem;
  }

  .nav-tab {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    background: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
  }

  .nav-tab:hover {
    color: #e2e8f0;
    background: #1e293b;
    border-color: #475569;
  }

  .nav-tab.active {
    color: #06b6d4;
    background: #0f2419;
    border-color: #06b6d4;
  }

  .nav-tab i {
    font-size: 0.85rem;
  }

  .page-content {
    flex: 1;
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .navigation {
      flex-direction: column;
      gap: 1rem;
      padding: 1rem;
    }

    .nav-tabs {
      width: 100%;
      justify-content: center;
    }

    .nav-tab {
      flex: 1;
      justify-content: center;
      padding: 0.5rem 1rem;
      font-size: 0.8rem;
    }
  }

  @media (max-width: 480px) {
    .nav-tabs {
      flex-direction: column;
      gap: 0.5rem;
    }

    .nav-tab {
      width: 100%;
    }
  }
</style>