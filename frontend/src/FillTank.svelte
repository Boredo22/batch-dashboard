<script>
  import { onMount, onDestroy } from 'svelte';
  import { apiGet, apiPost } from '$lib/api.js';
  import { toast } from 'svelte-sonner';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';
  import ConfigPanel from './components/filltank/ConfigPanel.svelte';
  import DiagnosticsPanel from './components/filltank/DiagnosticsPanel.svelte';
  import SystemLog from './components/filltank/SystemLog.svelte';

  // This page now just STARTS and MONITORS the server-side batch dosing job
  // (dosing_job.py). The fill/dose/trim loop runs on the backend so it survives
  // a tablet sleep or tab close -- it no longer runs in this browser tab.

  const sseStatus = getSystemStatus();
  let unsubscribe = null;
  let lastJobState = '';

  // ============ CONFIGURATION ============
  let selectedTank = $state(1);
  let targetVolume = $state(80);
  let selectedRecipe = $state('veg_formula');
  // EC/pH entered as a range; mapped to setpoint +/- tolerance for the job.
  // Defaults match the veg target (2.2 EC, 6.2 pH) used by the closed loop.
  let ecTarget = $state({ min: 2.15, max: 2.25 });
  let phTarget = $state({ min: 6.1, max: 6.3 });
  let nutrientOverrides = $state({});

  // Kept only to satisfy ConfigPanel's props. Send is a separate manual
  // operation; the closed-loop batch is fill -> EC dose -> pH dose.
  let selectedRoom = $state(1);
  let sendVolume = $state(25);
  let enabledPhases = $state({ fill: true, mix: true, send: false });

  const tanks = [
    { id: 1, name: 'Tank 1 - Grow 1', capacity_gallons: 100, fill_relay: 1, mix_relays: [4, 7], send_relay: 10 },
    { id: 2, name: 'Tank 2 - Grow 2', capacity_gallons: 100, fill_relay: 2, mix_relays: [5, 8], send_relay: 11 },
    { id: 3, name: 'Tank 3 - Nursery', capacity_gallons: 35, fill_relay: 3, mix_relays: [6, 9], send_relay: 12 }
  ];
  const rooms = [{ id: 1, name: 'Grow Room 1', relay: 10 }];

  let recipes = $state({
    veg_formula: { 'Veg A': 30, 'Veg B': 30, 'pH Down': 0.5, 'Runclean': 0.2 },
    bloom_formula: { 'Bloom A': 30, 'Bloom B': 30, 'pH Down': 0.5, 'Runclean': 0.2 }
  });

  // ============ JOB STATE (from SSE batch_job) ============
  let job = $state(null);
  let starting = $state(false);
  let advisory = $state(false);
  let logs = $state([]);

  // ============ REAL-TIME DATA (from SSE, for DiagnosticsPanel) ============
  let ecValue = $state(0);
  let phValue = $state(0);
  let ecPhMonitoring = $state(false);
  let flowData = $state({ current: 0, target: 0, rate: 0 });
  let relays = $state([]);
  let pumps = $state([]);
  let flowMeters = $state([]);

  // ============ PHASE MODEL ============
  const PHASES = [
    { key: 'priming', label: 'Prime Fill (20 gal)', icon: 'fa-fill-drip' },
    { key: 'filling_dosing', label: 'Fill + Bulk EC Dose', icon: 'fa-flask' },
    { key: 'ec_trim', label: 'EC Trim', icon: 'fa-bolt' },
    { key: 'ph_dosing', label: 'pH Dose', icon: 'fa-tint' },
    { key: 'stabilizing', label: 'Stabilize', icon: 'fa-water' },
    { key: 'complete', label: 'Complete', icon: 'fa-circle-check' }
  ];
  const TERMINAL = ['complete', 'error', 'aborted'];

  let currentTank = $derived(tanks.find(t => t.id === selectedTank) || tanks[0]);
  let isConnected = $derived(sseStatus.isConnected);
  let jobState = $derived(job?.state ?? 'idle');
  let isRunning = $derived(!!job && !TERMINAL.includes(jobState) && jobState !== 'needs_operator');
  let needsOperator = $derived(jobState === 'needs_operator');
  let canStart = $derived(!job || TERMINAL.includes(jobState));
  let phaseIndex = $derived(PHASES.findIndex(p => p.key === jobState));

  function headerPhaseClass(state) {
    if (state === 'priming' || state === 'filling_dosing') return 'filling';
    if (state === 'ec_trim' || state === 'ph_dosing' || state === 'stabilizing') return 'mixing';
    if (state === 'complete') return 'complete';
    if (state === 'error' || state === 'aborted') return 'error';
    if (state === 'needs_operator') return 'paused';
    return 'idle';
  }

  // ============ SSE PROCESSING ============
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) return;

    ecValue = data.ec_value || 0;
    phValue = data.ph_value || 0;
    ecPhMonitoring = data.ec_ph_monitoring || false;
    relays = data.relays || [];
    pumps = data.pumps || [];
    flowMeters = data.flow_meters || [];

    const activeMeter = flowMeters.find(m => m.status === 'running');
    if (activeMeter) {
      flowData = {
        current: activeMeter.total_gallons || 0,
        target: activeMeter.target_gallons || targetVolume,
        rate: activeMeter.flow_rate || 0
      };
    }

    // Batch job snapshot
    job = data.batch_job || null;
    if (job && job.state !== lastJobState) {
      lastJobState = job.state;
      const t = TERMINAL.includes(job.state) ? 'success'
        : job.state === 'needs_operator' ? 'warn' : 'info';
      addLog(`[${job.state}] ${job.message || ''}`, t);
      if (job.state === 'complete') toast.success('Batch complete');
      if (job.state === 'needs_operator') toast.warning(job.message || 'Operator action needed');
      if (job.state === 'error') toast.error(job.message || 'Batch error');
    }
  });

  function addLog(message, type = 'info') {
    logs = [{ id: crypto.randomUUID(), timestamp: new Date(), type, message }, ...logs].slice(0, 200);
  }

  // ============ CONTROLS ============
  function rangeToSetpoint(range) {
    const lo = Number(range.min), hi = Number(range.max);
    const target = (lo + hi) / 2;
    const tol = Math.max(0, (hi - lo) / 2);
    return { target, tol };
  }

  async function startBatch() {
    if (!canStart || starting) return;
    const ec = rangeToSetpoint(ecTarget);
    const ph = rangeToSetpoint(phTarget);
    const body = {
      tank_id: selectedTank,
      target_gallons: Number(targetVolume),
      recipe: selectedRecipe,
      ec_target: ec.target, ec_tol: ec.tol,
      ph_target: ph.target, ph_tol: ph.tol,
      advisory
    };
    starting = true;
    addLog(`Starting batch: tank ${selectedTank}, ${targetVolume} gal ${selectedRecipe}, EC ${ec.target.toFixed(2)}±${ec.tol.toFixed(2)}, pH ${ph.target.toFixed(2)}±${ph.tol.toFixed(2)}`, 'info');
    try {
      const res = await apiPost('/api/job/batch/start', body);
      job = res.job;
      lastJobState = res.job?.state || '';
      toast.success('Batch job started');
    } catch (e) {
      addLog(`Start failed: ${e.message}`, 'err');
      toast.error(`Start failed: ${e.message}`);
    } finally {
      starting = false;
    }
  }

  async function ackAction() {
    try {
      await apiPost('/api/job/batch/ack');
    } catch (e) {
      toast.error(`Advance failed: ${e.message}`);
    }
  }

  // Convenience actuation for the current advisory step (operator still clicks).
  async function actuateValve(relay, on) {
    try {
      await apiPost(`/api/relay/${relay}/${on ? 'on' : 'off'}`);
      toast.success(`Relay ${relay} ${on ? 'ON' : 'OFF'}`);
    } catch (e) { toast.error(`Relay ${relay}: ${e.message}`); }
  }
  async function actuateCirc(relays, on) {
    for (const r of relays) await actuateValve(r, on);
  }
  async function actuateDose(name, pumpId, ml) {
    if (!pumpId) { toast.error(`No pump mapped for ${name}`); return; }
    try {
      await apiPost(`/api/pump/${pumpId}/dispense`, { amount: ml });
      toast.success(`${name}: dispensing ${ml}ml`);
    } catch (e) { toast.error(`${name}: ${e.message}`); }
  }

  async function abortBatch() {
    addLog('Aborting batch...', 'warn');
    try {
      await apiPost('/api/job/batch/abort');
      toast.message('Batch aborting — hardware shutting down');
    } catch (e) {
      toast.error(`Abort failed: ${e.message}`);
    }
  }

  async function emergencyStop() {
    addLog('EMERGENCY STOP', 'err');
    try {
      await apiPost('/api/job/batch/abort').catch(() => {});
      await apiPost('/api/emergency/stop');
      addLog('Emergency stop executed', 'err');
      toast.error('EMERGENCY STOP activated');
    } catch (e) {
      toast.error(`Emergency stop error: ${e.message}`);
    }
  }

  function fmt(v, d = 2) { return (v === null || v === undefined) ? '—' : Number(v).toFixed(d); }
  function inBand(v, target, tol) {
    if (v === null || v === undefined || target === null || target === undefined) return false;
    return Math.abs(v - target) <= (tol ?? 0.05) + 1e-9;
  }

  onMount(async () => {
    addLog('Fill Tank page initialized', 'info');
    unsubscribe = subscribe();
    try {
      const data = await apiGet('/api/nutrients');
      if (data.veg_formula) recipes.veg_formula = data.veg_formula;
      if (data.bloom_formula) recipes.bloom_formula = data.bloom_formula;
    } catch (error) {
      toast.error(`Failed to load recipes: ${error.message}`);
    }
  });

  onDestroy(() => { if (unsubscribe) unsubscribe(); });
</script>

<div class="fill-tank-page">
  <header class="header-bar">
    <div class="header-left">
      <h1><i class="fas fa-fill-drip"></i> Batch Fill &amp; Dose</h1>
      <div class="connection-badge" class:connected={isConnected}>
        <div class="status-dot"></div>
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>
    </div>

    <div class="header-center">
      <div class="phase-indicator {headerPhaseClass(jobState)}">
        <i class="fas fa-circle-notch {isRunning ? 'fa-spin' : ''}"></i>
        {job ? jobState.replace('_', ' ') : 'idle'}
      </div>
      {#if job}
        <div class="progress-indicator">
          {job.volume_gallons ?? 0}/{job.target_gallons ?? targetVolume} gal
        </div>
      {/if}
    </div>

    <div class="header-right">
      <button class="emergency-btn" onclick={emergencyStop} title="Emergency Stop">
        <i class="fas fa-power-off"></i> E-STOP
      </button>
    </div>
  </header>

  <main class="main-content">
    <aside class="config-panel-container">
      <ConfigPanel
        bind:selectedTank
        bind:targetVolume
        {tanks}
        bind:selectedRecipe
        {recipes}
        bind:nutrientOverrides
        bind:ecTarget
        bind:phTarget
        bind:selectedRoom
        bind:sendVolume
        {rooms}
        bind:enabledPhases
        isRunning={isRunning || needsOperator}
        workflowPhase={jobState}
      />
    </aside>

    <section class="status-container">
      <div class="batch-status">
        <div class="bs-header">
          <i class="fas fa-diagram-project"></i> Batch Progress
          {#if job?.advisory}<span class="advisory-tag">Advisory</span>{/if}
        </div>

        {#if job?.advisory && job.pending_action}
          <div class="advise-card">
            <div class="advise-head"><i class="fas fa-hand-point-right"></i> Your move — then press Advance</div>
            <div class="advise-summary">{job.pending_action.summary}</div>
            {#if job.pending_action.detail}
              <div class="advise-detail">{job.pending_action.detail}</div>
            {/if}

            <!-- One-click actuation for this step (you still decide & click) -->
            {#if job.pending_action.kind === 'valve'}
              <div class="act-row">
                <button class="act-btn" onclick={() => actuateValve(job.pending_action.payload.relay, job.pending_action.payload.on)}>
                  <i class="fas fa-toggle-{job.pending_action.payload.on ? 'on' : 'off'}"></i>
                  Relay {job.pending_action.payload.relay} {job.pending_action.payload.on ? 'ON' : 'OFF'}
                </button>
              </div>
            {:else if job.pending_action.kind === 'circulation'}
              <div class="act-row">
                <button class="act-btn" onclick={() => actuateCirc(job.pending_action.payload.relays || [], job.pending_action.payload.on)}>
                  <i class="fas fa-arrows-rotate"></i>
                  {job.pending_action.payload.on ? 'Open' : 'Close'} relays {(job.pending_action.payload.relays || []).join(' & ')}
                </button>
              </div>
            {:else if job.pending_action.kind === 'dose'}
              <div class="act-row">
                {#each Object.entries(job.pending_action.payload.doses || {}) as [name, ml]}
                  <button class="act-btn" onclick={() => actuateDose(name, job.pending_action.payload.pumps?.[name], ml)}>
                    <i class="fas fa-droplet"></i> {name} {ml}ml
                  </button>
                {/each}
              </div>
            {/if}

            <button class="advise-btn" onclick={ackAction}>
              <i class="fas fa-check"></i> Done — Advance
            </button>
          </div>
        {/if}

        {#if !job}
          <div class="bs-empty">
            <i class="fas fa-flask"></i>
            <p>No batch running. Configure on the left and press <strong>Start Batch</strong>.</p>
            <p class="bs-hint">Closed loop: fill &rarr; bulk EC dose &rarr; EC trim &rarr; pH dose to setpoint.</p>
          </div>
        {:else}
          <!-- phase tracker -->
          <div class="phase-track">
            {#each PHASES as phase, i}
              <div class="phase-row"
                   class:done={phaseIndex > i || jobState === 'complete'}
                   class:current={phaseIndex === i && jobState !== 'complete'}>
                <div class="phase-dot"><i class="fas {phase.icon}"></i></div>
                <div class="phase-label">{phase.label}</div>
                {#if phaseIndex === i && jobState !== 'complete'}
                  <i class="fas fa-spinner fa-spin phase-spin"></i>
                {:else if phaseIndex > i || jobState === 'complete'}
                  <i class="fas fa-check phase-check"></i>
                {/if}
              </div>
            {/each}
          </div>

          <!-- live metrics -->
          <div class="metrics">
            <div class="metric">
              <span class="m-label">Volume</span>
              <span class="m-value">{job.volume_gallons ?? 0} <small>/ {job.target_gallons} gal</small></span>
            </div>
            <div class="metric" class:good={inBand(job.ec, job.ec_target, job.ec_tol)}>
              <span class="m-label">EC</span>
              <span class="m-value">{fmt(job.ec)} <small>&rarr; {fmt(job.ec_target)}</small></span>
            </div>
            <div class="metric" class:good={inBand(job.ph, job.ph_target, job.ph_tol)}>
              <span class="m-label">pH</span>
              <span class="m-value">{fmt(job.ph)} <small>&rarr; {fmt(job.ph_target)}</small></span>
            </div>
            <div class="metric">
              <span class="m-label">EC trims</span>
              <span class="m-value">{job.ec_iterations ?? 0}</span>
            </div>
            <div class="metric">
              <span class="m-label">pH dosed</span>
              <span class="m-value">{fmt(job.ph_dosed_ml, 1)} <small>ml</small></span>
            </div>
            <div class="metric">
              <span class="m-label">Circ pump</span>
              <span class="m-value">{job.circ_running ? 'ON' : 'off'}</span>
            </div>
          </div>

          {#if job.message}
            <div class="bs-message">{job.message}</div>
          {/if}

          {#if needsOperator}
            <div class="operator-banner">
              <div class="ob-title"><i class="fas fa-triangle-exclamation"></i> Operator action needed</div>
              <div class="ob-text">{job.suggestion || job.message}</div>
              <div class="ob-hint">Circulation is still running so you can add water. Press <strong>Abort</strong> when done to shut down.</div>
            </div>
          {/if}
        {/if}
      </div>
    </section>

    <aside class="diagnostics-container">
      <DiagnosticsPanel
        {ecValue}
        {phValue}
        {ecTarget}
        {phTarget}
        {ecPhMonitoring}
        {flowData}
        {relays}
        {pumps}
        {flowMeters}
        {isConnected}
        timerRemaining={null}
      />
    </aside>
  </main>

  <div class="control-bar">
    <div class="control-buttons">
      {#if canStart}
        <label class="advisory-toggle" title="Program never actuates — it reads sensors and tells you what to do, you make every call">
          <input type="checkbox" bind:checked={advisory} />
          Advisory mode (I actuate; system coaches)
        </label>
        <button class="control-btn start" onclick={startBatch} disabled={!isConnected || starting}>
          <i class="fas fa-play"></i> {starting ? 'Starting...' : (advisory ? 'Start Advisory' : 'Start Batch')}
        </button>
      {:else}
        <button class="control-btn stop" onclick={abortBatch}>
          <i class="fas fa-stop"></i> Abort
        </button>
      {/if}
    </div>
  </div>

  <footer class="log-container">
    <SystemLog bind:logs isTestingMode={false} onToggleTestingMode={() => {}} />
  </footer>
</div>

<style>
  .fill-tank-page { display: flex; flex-direction: column; height: 100vh; background: #1a1a1a; color: #e2e8f0; }

  .header-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; background: #2d3748; border-bottom: 1px solid #4a5568; }
  .header-left { display: flex; align-items: center; gap: 16px; }
  .header-bar h1 { margin: 0; font-size: 1.25rem; color: #e2e8f0; display: flex; align-items: center; gap: 10px; }
  .header-bar h1 i { color: #3b82f6; }

  .connection-badge { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 16px; font-size: 0.8rem; font-weight: 500; background: #2d1a1a; color: #ef4444; }
  .connection-badge.connected { background: #1a2e1a; color: #22c55e; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.5;} }

  .header-center { display: flex; align-items: center; gap: 16px; }
  .phase-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 0.9rem; background: #374151; color: #a0aec0; text-transform: capitalize; }
  .phase-indicator.filling { background: #1e3a5f; color: #3b82f6; }
  .phase-indicator.mixing { background: #1a3a2a; color: #22c55e; }
  .phase-indicator.paused { background: #3a3a1a; color: #eab308; }
  .phase-indicator.complete { background: #1a2e1a; color: #22c55e; }
  .phase-indicator.error { background: #2d1a1a; color: #ef4444; }
  .progress-indicator { font-size: 0.85rem; color: #a0aec0; background: #374151; padding: 6px 12px; border-radius: 12px; }

  .emergency-btn { background: #dc2626; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; text-transform: uppercase; font-size: 0.85rem; }
  .emergency-btn:hover { background: #b91c1c; }

  .main-content { flex: 1; display: grid; grid-template-columns: 280px 1fr 280px; gap: 16px; padding: 16px; overflow: hidden; min-height: 0; }
  .config-panel-container, .diagnostics-container { overflow-y: auto; min-height: 0; }
  .status-container { background: #2d3748; border-radius: 12px; border: 1px solid #4a5568; overflow-y: auto; min-height: 0; }

  .batch-status { padding: 16px; }
  .bs-header { font-size: 1rem; font-weight: 600; color: #e2e8f0; display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
  .bs-header i { color: #3b82f6; }

  .advisory-tag { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; background: #1e3a5f; color: #60a5fa; padding: 2px 8px; border-radius: 10px; margin-left: 8px; }

  .advise-card { background: #11203a; border: 1px solid #3b82f6; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
  .advise-head { color: #60a5fa; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
  .advise-summary { color: #e2e8f0; font-size: 1.05rem; font-weight: 600; margin-bottom: 6px; }
  .advise-detail { color: #94a3b8; font-size: 0.85rem; margin-bottom: 12px; }
  .advise-btn { background: #2563eb; color: white; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }
  .advise-btn:hover { background: #1d4ed8; }

  .act-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .act-btn { background: #1a202c; color: #e2e8f0; border: 1px solid #4a5568; border-radius: 8px; padding: 8px 14px; font-weight: 600; font-size: 0.85rem; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }
  .act-btn:hover { border-color: #3b82f6; background: #222c3f; }

  .advisory-toggle { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #94a3b8; cursor: pointer; margin-right: 8px; }
  .advisory-toggle input { width: 16px; height: 16px; accent-color: #3b82f6; cursor: pointer; }

  .bs-empty { text-align: center; color: #6b7280; padding: 40px 16px; }
  .bs-empty i { font-size: 2rem; color: #4a5568; margin-bottom: 12px; }
  .bs-hint { font-size: 0.8rem; color: #4a5568; margin-top: 8px; }

  .phase-track { display: flex; flex-direction: column; gap: 4px; margin-bottom: 20px; }
  .phase-row { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 8px; background: #1a202c; opacity: 0.6; }
  .phase-row.current { opacity: 1; background: #1e3a5f; }
  .phase-row.done { opacity: 1; }
  .phase-dot { width: 28px; height: 28px; border-radius: 50%; background: #374151; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: #94a3b8; }
  .phase-row.current .phase-dot { background: #3b82f6; color: white; }
  .phase-row.done .phase-dot { background: #16a34a; color: white; }
  .phase-label { flex: 1; font-size: 0.9rem; }
  .phase-spin { color: #3b82f6; }
  .phase-check { color: #22c55e; }

  .metrics { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 12px; }
  .metric { background: #1a202c; border-radius: 8px; padding: 10px; border: 1px solid #374151; }
  .metric.good { border-color: #22c55e; }
  .m-label { display: block; font-size: 0.7rem; color: #6b7280; text-transform: uppercase; margin-bottom: 4px; }
  .m-value { font-size: 1.1rem; font-weight: 600; color: #e2e8f0; }
  .m-value small { font-size: 0.7rem; color: #6b7280; font-weight: 400; }

  .bs-message { font-size: 0.85rem; color: #94a3b8; padding: 10px 12px; background: #1a202c; border-radius: 8px; margin-bottom: 12px; }

  .operator-banner { background: #3a2e1a; border: 1px solid #eab308; border-radius: 8px; padding: 14px; }
  .ob-title { color: #eab308; font-weight: 700; display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
  .ob-text { color: #e2e8f0; font-size: 0.9rem; margin-bottom: 8px; }
  .ob-hint { color: #94a3b8; font-size: 0.8rem; }

  .control-bar { padding: 12px 24px; background: #2d3748; border-top: 1px solid #4a5568; border-bottom: 1px solid #4a5568; }
  .control-buttons { display: flex; gap: 12px; justify-content: center; }
  .control-btn { padding: 12px 24px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
  .control-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .control-btn.start { background: #22c55e; color: white; }
  .control-btn.start:hover:not(:disabled) { background: #16a34a; }
  .control-btn.stop { background: #ef4444; color: white; }
  .control-btn.stop:hover { background: #dc2626; }

  .log-container { height: 200px; padding: 0 16px 16px; }

  @media (max-width: 1200px) {
    .main-content { grid-template-columns: 1fr; grid-template-rows: auto auto auto; }
    .config-panel-container, .diagnostics-container { max-height: 320px; }
    .metrics { grid-template-columns: 1fr 1fr; }
  }
</style>
