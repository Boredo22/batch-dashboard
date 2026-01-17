<script>
  import { onMount, onDestroy } from 'svelte';
  import FillJobTesting from './components/FillJobTesting.svelte';
  import SendJobTesting from './components/SendJobTesting.svelte';
  import MixJobTesting from './components/MixJobTesting.svelte';
  import SystemLog from './components/SystemLog.svelte';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';

  // Get reactive system status from SSE store
  const sseStatus = getSystemStatus();

  // State variables using Svelte 5 runes
  let logs = $state([]);
  let errorMessage = $state('');

  // Derive system status from SSE connection
  let systemStatus = $derived(sseStatus.isConnected ? 'Connected' : 'Disconnected');

  // Job states
  let activeFillJob = $state(null);
  let activeSendJob = $state(null);
  let activeMixJob = $state(null);

  // SSE unsubscribe function
  let unsubscribe = null;

  // Track last processed timestamp to avoid reprocessing same data
  let lastProcessedTimestamp = '';

  // React to SSE status updates
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) {
      errorMessage = sseStatus.lastError;
      return;
    }

    // Skip if we've already processed this update (prevents infinite loops)
    if (data.timestamp === lastProcessedTimestamp) return;
    lastProcessedTimestamp = data.timestamp;

    errorMessage = '';

    // Update active job states from backend
    activeFillJob = data.active_fill_job || null;
    activeSendJob = data.active_send_job || null;
    activeMixJob = data.active_mix_job || null;
  });

  // Job control functions
  async function startFillJob(tankId, gallons) {
    try {
      const response = await fetch('/api/jobs/fill/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tank_id: tankId, gallons: gallons })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(`Fill job started: Tank ${tankId}, ${gallons} gallons`);
        await fetchSystemStatus();
        return result;
      } else {
        const error = await response.json();
        addLog(`Fill job error: ${error.error}`);
        return null;
      }
    } catch (error) {
      addLog(`Fill job error: ${error.message}`);
      return null;
    }
  }

  async function startSendJob(roomId, gallons) {
    try {
      const response = await fetch('/api/jobs/send/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: roomId, gallons: gallons })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(`Send job started: Room ${roomId}, ${gallons} gallons`);
        await fetchSystemStatus();
        return result;
      } else {
        const error = await response.json();
        addLog(`Send job error: ${error.error}`);
        return null;
      }
    } catch (error) {
      addLog(`Send job error: ${error.message}`);
      return null;
    }
  }

  async function startMixJob(tankId) {
    try {
      const response = await fetch('/api/jobs/mix/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tank_id: tankId })
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(`Mix job started: Tank ${tankId}`);
        await fetchSystemStatus();
        return result;
      } else {
        const error = await response.json();
        addLog(`Mix job error: ${error.error}`);
        return null;
      }
    } catch (error) {
      addLog(`Mix job error: ${error.message}`);
      return null;
    }
  }

  async function stopJob(jobType) {
    try {
      const response = await fetch(`/api/jobs/${jobType}/stop`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        addLog(`${jobType} job stopped`);
        await fetchSystemStatus();
        return result;
      } else {
        const error = await response.json();
        addLog(`Stop job error: ${error.error}`);
        return null;
      }
    } catch (error) {
      addLog(`Stop job error: ${error.message}`);
      return null;
    }
  }

  function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    logs = [{ time: timestamp, message }, ...logs].slice(0, 100);
  }

  onMount(async () => {
    addLog('Stage 2 Testing initialized...');

    // Subscribe to SSE updates
    unsubscribe = subscribe();
  });

  onDestroy(() => {
    // Unsubscribe from SSE when component unmounts
    if (unsubscribe) {
      unsubscribe();
    }
  });
</script>

<div class="app">
  <div class="top-bar">
    <h1>Stage 2: Job Testing Dashboard</h1>
    <div class="status-info">
      <div class="status-badge {systemStatus.toLowerCase()}">
        {systemStatus}
      </div>
      <div class="active-jobs">
        {#if activeFillJob || activeSendJob || activeMixJob}
          <span class="jobs-indicator">
            <i class="fas fa-cogs"></i>
            {[activeFillJob, activeSendJob, activeMixJob].filter(Boolean).length} Active
          </span>
        {:else}
          <span class="jobs-indicator idle">
            <i class="fas fa-pause"></i>
            Idle
          </span>
        {/if}
      </div>
    </div>
  </div>

  <div class="main-grid">
    <div class="left-panel">
      <FillJobTesting 
        activeJob={activeFillJob}
        onStartJob={startFillJob}
        onStopJob={() => stopJob('fill')}
      />
      <SendJobTesting 
        activeJob={activeSendJob}
        onStartJob={startSendJob}
        onStopJob={() => stopJob('send')}
      />
      <MixJobTesting 
        activeJob={activeMixJob}
        onStartJob={startMixJob}
        onStopJob={() => stopJob('mix')}
      />
    </div>

    <div class="right-panel">
      <SystemLog {logs} />
    </div>
  </div>
</div>

<style>
  .app {
    width: 100vw;
    height: 100vh;
    background: #1a1a1a;
    color: white;
    display: flex;
    flex-direction: column;
  }

  .top-bar {
    background: #2d3748;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #4a5568;
  }

  .top-bar h1 {
    margin: 0;
    color: white;
    font-size: 1.5rem;
  }

  .status-info {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .status-badge {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.875rem;
  }

  .status-badge.connected {
    background: #22c55e;
    color: white;
  }

  .status-badge.disconnected {
    background: #ef4444;
    color: white;
  }

  .status-badge.error {
    background: #f97316;
    color: white;
  }

  .jobs-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .jobs-indicator:not(.idle) {
    background: #1a2e1a;
    color: #4ade80;
    border: 1px solid #22c55e;
  }

  .jobs-indicator.idle {
    background: #2d2d2d;
    color: #a0aec0;
    border: 1px solid #4a5568;
  }

  .main-grid {
    flex: 1;
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
    padding: 1.5rem;
    overflow: hidden;
    max-width: 100%;
  }

  .left-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    overflow-y: auto;
    padding-right: 0.5rem;
  }

  .right-panel {
    background: #2d3748;
    border-radius: 0.5rem;
    border: 1px solid #4a5568;
    min-height: 0;
  }

  @media (max-width: 1400px) {
    .main-grid {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr auto;
      gap: 1rem;
    }
    
    .right-panel {
      height: 350px;
    }
  }

  @media (max-width: 768px) {
    .top-bar {
      flex-direction: column;
      gap: 0.5rem;
      padding: 1rem;
    }
    
    .status-info {
      flex-direction: column;
      gap: 8px;
    }
    
    .main-grid {
      padding: 1rem;
    }
    
    .right-panel {
      height: 300px;
    }
  }
</style>