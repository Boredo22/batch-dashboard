<script>
  import { onMount, onDestroy } from 'svelte';
  import { apiGet, apiPost } from '$lib/api.js';
  import { toast } from 'svelte-sonner';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';

  // Hands-on hardware verification checklist. Actuate each item, confirm the
  // correct physical device responds, and record Pass/Fail + notes. Verdicts
  // persist to localStorage so a multi-step manual tank fill can be checked off
  // over time, and can be exported as a JSON report.

  const sseStatus = getSystemStatus();
  let unsubscribe = null;

  // ============ VERDICT STORE (localStorage) ============
  const STORAGE_KEY = 'hwVerifyResults.v1';
  let results = $state({});   // { key: { status: 'pass'|'fail', notes: '' } }

  function loadResults() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) results = JSON.parse(raw);
    } catch (e) { /* ignore corrupt storage */ }
  }
  function saveResults() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(results)); } catch (e) { /* ignore */ }
  }
  function verdict(key) { return results[key]?.status ?? 'untested'; }
  function setVerdict(key, status) {
    const cur = results[key] || { status: 'untested', notes: '' };
    // toggle off if clicking the same verdict again
    const next = cur.status === status ? 'untested' : status;
    results = { ...results, [key]: { ...cur, status: next, ts: new Date().toISOString() } };
    saveResults();
  }
  function setNotes(key, notes) {
    const cur = results[key] || { status: 'untested', notes: '' };
    results = { ...results, [key]: { ...cur, notes } };
    saveResults();
  }
  function resetAll() {
    if (!confirm('Clear all verification results?')) return;
    results = {};
    saveResults();
    toast.message('Verification results cleared');
  }

  // ============ LIVE HARDWARE (from SSE) ============
  let relays = $derived(sseStatus.relays);
  let pumps = $derived(sseStatus.pumps);
  let flowMeters = $derived(sseStatus.flowMeters);
  let ecValue = $derived(sseStatus.ecValue);
  let phValue = $derived(sseStatus.phValue);
  let tankMonitors = $derived(sseStatus.tankMonitors);
  let isConnected = $derived(sseStatus.isConnected);

  // ============ TEST INPUTS ============
  let flowTestGallons = $state({});   // {flowId: gallons}
  let pumpTestMl = $state({});        // {pumpId: ml}
  let ecphReading = $state(null);

  function flowGal(id) { return flowTestGallons[id] ?? 5; }
  function pumpMl(id) { return pumpTestMl[id] ?? 10; }

  // ============ SUMMARY ============
  // Build the list of all expected item keys so "untested" is counted correctly.
  let allKeys = $derived.by(() => {
    const keys = [];
    for (const r of relays) keys.push(`relay:${r.id}`);
    for (const f of flowMeters) keys.push(`flow:${f.id}`);
    for (const p of pumps) keys.push(`pump:${p.id}`);
    keys.push('sensor:ec', 'sensor:ph');
    return keys;
  });
  let summary = $derived.by(() => {
    let pass = 0, fail = 0;
    for (const k of allKeys) {
      const s = results[k]?.status;
      if (s === 'pass') pass++;
      else if (s === 'fail') fail++;
    }
    return { pass, fail, untested: allKeys.length - pass - fail, total: allKeys.length };
  });

  // ============ HARDWARE ACTIONS ============
  async function relayOn(id) {
    try { await apiPost(`/api/relay/${id}/on`); toast.success(`Relay ${id} ON`); }
    catch (e) { toast.error(`Relay ${id}: ${e.message}`); }
  }
  async function relayOff(id) {
    try { await apiPost(`/api/relay/${id}/off`); toast.message(`Relay ${id} OFF`); }
    catch (e) { toast.error(`Relay ${id}: ${e.message}`); }
  }
  async function allRelaysOff() {
    try { await apiPost('/api/relay/all/off'); toast.message('All relays OFF'); }
    catch (e) { toast.error(e.message); }
  }
  async function flowStart(id) {
    try { await apiPost(`/api/flow/${id}/start`, { gallons: Number(flowGal(id)) }); toast.success(`Flow ${id} started (${flowGal(id)} gal)`); }
    catch (e) { toast.error(`Flow ${id}: ${e.message}`); }
  }
  async function flowStop(id) {
    try { await apiPost(`/api/flow/${id}/stop`); toast.message(`Flow ${id} stopped`); }
    catch (e) { toast.error(`Flow ${id}: ${e.message}`); }
  }
  async function flowReset(id) {
    try { await apiPost(`/api/flow/${id}/diagnostics/reset`); toast.message(`Flow ${id} counter reset`); }
    catch (e) { toast.error(`Flow ${id}: ${e.message}`); }
  }
  async function pumpDispense(id) {
    try { await apiPost(`/api/pump/${id}/dispense`, { amount: Number(pumpMl(id)) }); toast.success(`Pump ${id} dispensing ${pumpMl(id)}ml`); }
    catch (e) { toast.error(`Pump ${id}: ${e.message}`); }
  }
  async function pumpStop(id) {
    try { await apiPost(`/api/pump/${id}/stop`); toast.message(`Pump ${id} stopped`); }
    catch (e) { toast.error(`Pump ${id}: ${e.message}`); }
  }
  async function readEcPh() {
    try {
      const res = await apiGet('/api/sensors/ecph/read');
      ecphReading = res.data || null;
      toast.success(`EC ${res.data?.ec ?? '—'}, pH ${res.data?.ph ?? '—'}`);
    } catch (e) { toast.error(`Sensor read: ${e.message}`); }
  }
  async function emergencyStop() {
    try { await apiPost('/api/emergency/stop'); toast.error('EMERGENCY STOP activated'); }
    catch (e) { toast.error(`E-stop: ${e.message}`); }
  }

  // ============ EXPORT ============
  function exportReport() {
    const report = {
      generated_at: new Date().toISOString(),
      summary: summary,
      items: allKeys.map(k => ({ item: k, ...(results[k] || { status: 'untested', notes: '' }) }))
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hardware-verification-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Report downloaded');
  }

  onMount(() => {
    loadResults();
    unsubscribe = subscribe();
  });
  onDestroy(() => { if (unsubscribe) unsubscribe(); });
</script>

<div class="hwv">
  <!-- Header / summary bar -->
  <header class="hwv-header">
    <div class="hdr-left">
      <h2><i class="fas fa-clipboard-check"></i> Hardware Verification</h2>
      <span class="conn" class:on={isConnected}>{isConnected ? 'Live' : 'Disconnected'}</span>
    </div>
    <div class="hdr-summary">
      <span class="chip pass">{summary.pass} pass</span>
      <span class="chip fail">{summary.fail} fail</span>
      <span class="chip untested">{summary.untested} untested</span>
    </div>
    <div class="hdr-actions">
      <button class="btn ghost" onclick={allRelaysOff}><i class="fas fa-ban"></i> All Relays Off</button>
      <button class="btn ghost" onclick={exportReport}><i class="fas fa-download"></i> Export</button>
      <button class="btn ghost danger" onclick={resetAll}><i class="fas fa-trash"></i> Reset</button>
      <button class="btn estop" onclick={emergencyStop}><i class="fas fa-power-off"></i> E-STOP</button>
    </div>
  </header>

  <p class="howto">
    Use during a manual tank fill: actuate each item, confirm the <strong>correct</strong> physical
    device responds, then mark <span class="t pass">Pass</span> or <span class="t fail">Fail</span>.
    Results auto-save to this browser; use Export for a report.
  </p>

  <!-- RELAYS -->
  <section class="card">
    <h3><i class="fas fa-toggle-on"></i> Relays / Valves</h3>
    <div class="rows">
      {#each relays as relay}
        {@const key = `relay:${relay.id}`}
        <div class="row" class:live={relay.state}>
          <div class="row-id">
            <span class="badge" class:on={relay.state}>{relay.state ? 'ON' : 'OFF'}</span>
            <div class="row-name">
              <strong>#{relay.id}</strong> {relay.name}
            </div>
          </div>
          <div class="row-controls">
            <button class="btn sm on" onclick={() => relayOn(relay.id)}>On</button>
            <button class="btn sm off" onclick={() => relayOff(relay.id)}>Off</button>
          </div>
          <div class="verdict">
            <button class="v pass" aria-label="Pass" class:active={verdict(key) === 'pass'} onclick={() => setVerdict(key, 'pass')}><i class="fas fa-check"></i></button>
            <button class="v fail" aria-label="Fail" class:active={verdict(key) === 'fail'} onclick={() => setVerdict(key, 'fail')}><i class="fas fa-xmark"></i></button>
          </div>
          <input class="notes" placeholder="notes…" value={results[key]?.notes ?? ''} oninput={(e) => setNotes(key, e.target.value)} />
        </div>
      {/each}
      {#if relays.length === 0}<div class="empty">No relays reported.</div>{/if}
    </div>
  </section>

  <!-- FLOW METERS -->
  <section class="card">
    <h3><i class="fas fa-water"></i> Flow Meters</h3>
    <div class="rows">
      {#each flowMeters as meter}
        {@const key = `flow:${meter.id}`}
        <div class="row" class:live={meter.status === 'running'}>
          <div class="row-id">
            <span class="badge" class:on={meter.status === 'running'}>{meter.status}</span>
            <div class="row-name">
              <strong>#{meter.id}</strong> {meter.name}
              <div class="live-read">
                {meter.total_gallons ?? 0}/{meter.target_gallons ?? 0} gal · {meter.pulse_count ?? 0} pulses · {meter.flow_rate ?? 0} gpm
              </div>
            </div>
          </div>
          <div class="row-controls">
            <input class="num" type="number" min="1" value={flowGal(meter.id)}
                   oninput={(e) => flowTestGallons = { ...flowTestGallons, [meter.id]: e.target.value }} />
            <button class="btn sm on" onclick={() => flowStart(meter.id)}>Start</button>
            <button class="btn sm off" onclick={() => flowStop(meter.id)}>Stop</button>
            <button class="btn sm ghost" onclick={() => flowReset(meter.id)}>Reset</button>
          </div>
          <div class="verdict">
            <button class="v pass" aria-label="Pass" class:active={verdict(key) === 'pass'} onclick={() => setVerdict(key, 'pass')}><i class="fas fa-check"></i></button>
            <button class="v fail" aria-label="Fail" class:active={verdict(key) === 'fail'} onclick={() => setVerdict(key, 'fail')}><i class="fas fa-xmark"></i></button>
          </div>
          <input class="notes" placeholder="notes…" value={results[key]?.notes ?? ''} oninput={(e) => setNotes(key, e.target.value)} />
        </div>
      {/each}
      {#if flowMeters.length === 0}<div class="empty">No flow meters reported.</div>{/if}
    </div>
  </section>

  <!-- PUMPS -->
  <section class="card">
    <h3><i class="fas fa-pump-medical"></i> Nutrient Pumps</h3>
    <div class="rows">
      {#each pumps as pump}
        {@const key = `pump:${pump.id}`}
        <div class="row" class:live={pump.is_dispensing}>
          <div class="row-id">
            <span class="badge" class:on={pump.is_dispensing}>{pump.is_dispensing ? 'RUN' : 'idle'}</span>
            <div class="row-name">
              <strong>#{pump.id}</strong> {pump.name}
              <div class="live-read">
                {pump.voltage ?? 0}V · {pump.calibrated ? 'calibrated' : 'uncalibrated'}{pump.connected ? '' : ' · disconnected'}
              </div>
            </div>
          </div>
          <div class="row-controls">
            <input class="num" type="number" min="0.5" step="0.5" value={pumpMl(pump.id)}
                   oninput={(e) => pumpTestMl = { ...pumpTestMl, [pump.id]: e.target.value }} />
            <span class="unit">ml</span>
            <button class="btn sm on" onclick={() => pumpDispense(pump.id)}>Dispense</button>
            <button class="btn sm off" onclick={() => pumpStop(pump.id)}>Stop</button>
          </div>
          <div class="verdict">
            <button class="v pass" aria-label="Pass" class:active={verdict(key) === 'pass'} onclick={() => setVerdict(key, 'pass')}><i class="fas fa-check"></i></button>
            <button class="v fail" aria-label="Fail" class:active={verdict(key) === 'fail'} onclick={() => setVerdict(key, 'fail')}><i class="fas fa-xmark"></i></button>
          </div>
          <input class="notes" placeholder="notes…" value={results[key]?.notes ?? ''} oninput={(e) => setNotes(key, e.target.value)} />
        </div>
      {/each}
      {#if pumps.length === 0}<div class="empty">No pumps reported.</div>{/if}
    </div>
  </section>

  <!-- SENSORS -->
  <section class="card">
    <h3><i class="fas fa-vial"></i> EC / pH Sensors</h3>
    <div class="sensor-live">
      <div class="sensor-box">
        <span class="s-label">EC (live)</span>
        <span class="s-value">{ecValue || '—'} <small>mS/cm</small></span>
      </div>
      <div class="sensor-box">
        <span class="s-label">pH (live)</span>
        <span class="s-value">{phValue || '—'}</span>
      </div>
      <button class="btn sm on" onclick={readEcPh}><i class="fas fa-rotate"></i> Read Now</button>
      {#if ecphReading}
        <div class="sensor-box read">
          <span class="s-label">Last read</span>
          <span class="s-value">EC {ecphReading.ec ?? '—'} · pH {ecphReading.ph ?? '—'}</span>
        </div>
      {/if}
    </div>
    <div class="rows">
      {#each [{ key: 'sensor:ec', name: 'EC sensor (dip in known standard, e.g. 1413 µS)' }, { key: 'sensor:ph', name: 'pH sensor (dip in pH 7.0 / 4.0 buffer)' }] as item}
        <div class="row">
          <div class="row-id"><div class="row-name">{item.name}</div></div>
          <div class="verdict">
            <button class="v pass" aria-label="Pass" class:active={verdict(item.key) === 'pass'} onclick={() => setVerdict(item.key, 'pass')}><i class="fas fa-check"></i></button>
            <button class="v fail" aria-label="Fail" class:active={verdict(item.key) === 'fail'} onclick={() => setVerdict(item.key, 'fail')}><i class="fas fa-xmark"></i></button>
          </div>
          <input class="notes" placeholder="expected vs measured…" value={results[item.key]?.notes ?? ''} oninput={(e) => setNotes(item.key, e.target.value)} />
        </div>
      {/each}
    </div>
  </section>

  <!-- TANK MONITORS (informational) -->
  {#if tankMonitors && Object.keys(tankMonitors).length > 0}
    <section class="card">
      <h3><i class="fas fa-temperature-half"></i> Tank Monitors</h3>
      <div class="rows">
        {#each Object.entries(tankMonitors) as [tid, reading]}
          <div class="row">
            <div class="row-id"><div class="row-name"><strong>Tank {tid}</strong>
              <div class="live-read">pH {reading?.ph ?? '—'} · EC {reading?.ec ?? '—'}</div>
            </div></div>
          </div>
        {/each}
      </div>
    </section>
  {/if}
</div>

<style>
  .hwv { padding: 16px; max-width: 1100px; margin: 0 auto; color: #e2e8f0; }

  .hwv-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
  .hdr-left { display: flex; align-items: center; gap: 12px; }
  .hwv-header h2 { margin: 0; font-size: 1.15rem; display: flex; align-items: center; gap: 8px; }
  .hwv-header h2 i { color: #3b82f6; }
  .conn { font-size: 0.75rem; padding: 3px 10px; border-radius: 12px; background: #2d1a1a; color: #ef4444; }
  .conn.on { background: #1a2e1a; color: #22c55e; }

  .hdr-summary { display: flex; gap: 6px; }
  .chip { font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; font-weight: 600; }
  .chip.pass { background: #14321f; color: #22c55e; }
  .chip.fail { background: #321414; color: #ef4444; }
  .chip.untested { background: #2a2f3a; color: #94a3b8; }

  .hdr-actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .howto { font-size: 0.82rem; color: #94a3b8; background: #1a202c; border: 1px solid #2d3748; border-radius: 8px; padding: 10px 12px; margin: 8px 0 16px; }
  .howto .t { padding: 1px 6px; border-radius: 6px; font-weight: 600; }
  .t.pass { background: #14321f; color: #22c55e; }
  .t.fail { background: #321414; color: #ef4444; }

  .card { background: #2d3748; border: 1px solid #4a5568; border-radius: 12px; padding: 14px 16px; margin-bottom: 16px; }
  .card h3 { margin: 0 0 12px; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; color: #e2e8f0; }
  .card h3 i { color: #3b82f6; }

  .rows { display: flex; flex-direction: column; gap: 8px; }
  .row { display: grid; grid-template-columns: minmax(180px, 1.4fr) auto auto minmax(120px, 1fr); gap: 10px; align-items: center; padding: 8px 10px; background: #1a202c; border: 1px solid #232b3a; border-radius: 8px; }
  .row.live { border-color: #3b82f6; box-shadow: 0 0 0 1px #3b82f6 inset; }

  .row-id { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .badge { font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: #374151; color: #94a3b8; min-width: 38px; text-align: center; text-transform: uppercase; }
  .badge.on { background: #16a34a; color: white; }
  .row-name { font-size: 0.85rem; min-width: 0; }
  .live-read { font-size: 0.72rem; color: #6b7280; margin-top: 2px; }

  .row-controls { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .num { width: 64px; padding: 6px 8px; background: #0f1420; border: 1px solid #374151; border-radius: 6px; color: #e2e8f0; font-size: 0.85rem; }
  .unit { font-size: 0.72rem; color: #6b7280; }

  .verdict { display: flex; gap: 6px; }
  .v { width: 34px; height: 34px; border-radius: 8px; border: 1px solid #374151; background: #0f1420; color: #6b7280; cursor: pointer; font-size: 0.9rem; }
  .v.pass.active { background: #16a34a; border-color: #16a34a; color: white; }
  .v.fail.active { background: #dc2626; border-color: #dc2626; color: white; }
  .v:hover { border-color: #4a5568; }

  .notes { padding: 7px 9px; background: #0f1420; border: 1px solid #374151; border-radius: 6px; color: #e2e8f0; font-size: 0.8rem; }
  .notes:focus, .num:focus { outline: none; border-color: #3b82f6; }

  .empty { color: #6b7280; font-size: 0.85rem; padding: 8px; }

  .sensor-live { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
  .sensor-box { background: #1a202c; border: 1px solid #232b3a; border-radius: 8px; padding: 8px 14px; }
  .sensor-box.read { border-color: #3b82f6; }
  .s-label { display: block; font-size: 0.68rem; color: #6b7280; text-transform: uppercase; }
  .s-value { font-size: 1.05rem; font-weight: 600; }
  .s-value small { font-size: 0.7rem; color: #6b7280; font-weight: 400; }

  .btn { padding: 8px 12px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 6px; background: #374151; color: #e2e8f0; }
  .btn.sm { padding: 6px 10px; font-size: 0.78rem; }
  .btn.on { background: #2563eb; color: white; }
  .btn.off { background: #4b5563; color: white; }
  .btn.ghost { background: transparent; border: 1px solid #4a5568; }
  .btn.ghost.danger { border-color: #7f1d1d; color: #fca5a5; }
  .btn.estop { background: #dc2626; color: white; text-transform: uppercase; }
  .btn:hover { filter: brightness(1.1); }

  @media (max-width: 720px) {
    .row { grid-template-columns: 1fr; }
    .verdict { justify-content: flex-start; }
  }
</style>
