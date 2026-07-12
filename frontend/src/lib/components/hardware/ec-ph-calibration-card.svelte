<script>
  import { FlaskConical, Check, X, Trash2, Loader2 } from "@lucide/svelte/icons";
  import { apiGet, apiPost } from "$lib/api.js";
  import { toast } from "svelte-sonner";

  // Live readings (from the SSE store, passed down by the page) so the operator
  // can confirm the probe has stabilised before capturing each point.
  let { ecValue = 0, phValue = 0, ecPhMonitoring = false } = $props();

  // Calibration recipes. pH is 2-point (mid 7.00 first, then low 4.00 — Atlas
  // calibrates the midpoint first). EC is the Atlas 2-point recommendation,
  // which requires a dry calibration first, then 12,880 µS and 80,000 µS.
  const PH_STEPS = [
    { point: "mid", value: 7.0, label: "pH 7.00 buffer", hint: "Rinse the probe, place it in pH 7.00 buffer, and wait for the reading to settle." },
    { point: "low", value: 4.0, label: "pH 4.00 buffer", hint: "Rinse the probe, place it in pH 4.00 buffer, and wait for the reading to settle." },
  ];
  const EC_STEPS = [
    { point: "dry", value: null, label: "Dry calibration", hint: "The probe must be completely DRY and held in open air." },
    { point: "low", value: 12880, label: "12,880 µS solution", hint: "Rinse, place the probe in 12,880 µS solution, and wait for the reading to settle." },
    { point: "high", value: 80000, label: "80,000 µS solution", hint: "Rinse, place the probe in 80,000 µS solution, and wait for the reading to settle." },
  ];

  let status = $state(null);          // { ph: {...}, ec: {...} } from the backend
  let active = $state(null);          // 'ph' | 'ec' | null — only one wizard at a time
  let stepIndex = $state(0);
  let busy = $state(false);

  let steps = $derived(active === "ph" ? PH_STEPS : active === "ec" ? EC_STEPS : []);
  let currentStep = $derived(steps[stepIndex] ?? null);
  let liveReading = $derived(active === "ph" ? phValue : ecValue);
  let liveUnit = $derived(active === "ph" ? "" : "µS/cm");

  $effect(() => { loadStatus(); });

  async function loadStatus() {
    try {
      status = await apiGet("/api/sensors/calibration/status");
    } catch (error) {
      // Non-fatal: the wizard still works without the status summary.
      status = null;
    }
  }

  function start(sensor) {
    active = sensor;
    stepIndex = 0;
  }

  function cancel() {
    active = null;
    stepIndex = 0;
  }

  async function capture() {
    if (!currentStep || busy) return;
    busy = true;
    const sensor = active;
    const path = sensor === "ph" ? "/api/sensors/ph/calibrate" : "/api/sensors/ec/calibrate";
    const body = currentStep.value != null ? { point: currentStep.point, value: currentStep.value } : { point: currentStep.point };
    try {
      await apiPost(path, body);
      toast.success(`${sensor.toUpperCase()} — ${currentStep.label} captured`);
      if (stepIndex + 1 >= steps.length) {
        toast.success(`${sensor.toUpperCase()} calibration complete`);
        cancel();
        await loadStatus();
      } else {
        stepIndex += 1;
      }
    } catch (error) {
      toast.error(`${sensor.toUpperCase()} calibration: ${error.message}`);
    } finally {
      busy = false;
    }
  }

  async function clearCalibration(sensor) {
    if (!confirm(`Clear all ${sensor.toUpperCase()} calibration points? You'll need to recalibrate the sensor.`)) return;
    const path = sensor === "ph" ? "/api/sensors/ph/calibrate" : "/api/sensors/ec/calibrate";
    try {
      await apiPost(path, { point: "clear" });
      toast.success(`${sensor.toUpperCase()} calibration cleared`);
      if (active === sensor) cancel();
      await loadStatus();
    } catch (error) {
      toast.error(`Clear ${sensor.toUpperCase()} calibration: ${error.message}`);
    }
  }

  function pointsLabel(s) {
    if (!s) return "—";
    const n = s.calibration_points;
    const word = n === 1 ? "point" : "points";
    return `${s.status === "calibrated" ? "Calibrated" : "Uncalibrated"}${n != null ? ` · ${n} ${word}` : ""}`;
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center gap-2">
      <span class="icon"><FlaskConical size={16} /></span>
      <span class="card-title">Sensor Calibration</span>
    </div>
  </div>

  <div class="card-content">
    {#if active}
      <!-- Guided wizard -->
      <div class="wizard">
        <div class="wizard-head">
          <span class="wizard-title">{active === "ph" ? "pH" : "EC"} calibration</span>
          <span class="step-counter">Step {stepIndex + 1} of {steps.length}</span>
        </div>

        <div class="step-name">{currentStep?.label}</div>
        <p class="step-hint">{currentStep?.hint}</p>

        <div class="live-reading" class:warn={!ecPhMonitoring}>
          {#if ecPhMonitoring}
            <span class="live-label">Live</span>
            <span class="live-value">{liveReading?.toFixed(2)} <span class="live-unit">{liveUnit}</span></span>
          {:else}
            <span class="live-warn">Start EC/pH monitoring to see live readings before capturing.</span>
          {/if}
        </div>

        <div class="wizard-actions">
          <button class="btn-ghost" onclick={cancel} disabled={busy}>
            <X size={14} /> Cancel
          </button>
          <button class="btn-primary" onclick={capture} disabled={busy}>
            {#if busy}<span class="spin"><Loader2 size={14} /></span>{:else}<Check size={14} />{/if}
            Capture {currentStep?.point === "dry" ? "dry" : currentStep?.label?.split(" ")[0]}
          </button>
        </div>
      </div>
    {:else}
      <!-- Overview: status + entry points -->
      <div class="sensor-row">
        <div class="sensor-info">
          <span class="sensor-name">pH</span>
          <span class="sensor-status" class:ok={status?.ph?.status === "calibrated"}>{pointsLabel(status?.ph)}</span>
        </div>
        <div class="sensor-buttons">
          <button class="btn-primary" onclick={() => start("ph")}>Calibrate</button>
          <button class="btn-ghost" onclick={() => clearCalibration("ph")} title="Clear pH calibration">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div class="sensor-row">
        <div class="sensor-info">
          <span class="sensor-name">EC</span>
          <span class="sensor-status" class:ok={status?.ec?.status === "calibrated"}>{pointsLabel(status?.ec)}</span>
        </div>
        <div class="sensor-buttons">
          <button class="btn-primary" onclick={() => start("ec")}>Calibrate</button>
          <button class="btn-ghost" onclick={() => clearCalibration("ec")} title="Clear EC calibration">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <p class="recipe-note">pH: 2-point (7.00, 4.00) · EC: dry + 12,880 µS + 80,000 µS</p>
    {/if}
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;
    --accent-steel: #64748b;
    --accent-slate: #475569;
    --status-success: #059669;
    --status-warning: #d97706;
    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;
    --border-subtle: #334155;
    --border-emphasis: #475569;
    --space-sm: 0.5rem;
    --space-md: 0.75rem;
    --text-xs: 0.6875rem;
    --text-sm: 0.8125rem;
    --text-base: 0.9375rem;
  }

  .card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 0.375rem;
  }

  .card-header {
    padding: var(--space-md) var(--space-md) var(--space-sm);
    border-bottom: 1px solid var(--border-subtle);
  }

  .card-title {
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .card-content {
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .icon {
    display: inline-flex;
    color: var(--accent-steel);
  }

  .sensor-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-md);
  }

  .sensor-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .sensor-name {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
  }

  .sensor-status {
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .sensor-status.ok {
    color: var(--status-success);
  }

  .sensor-buttons {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
  }

  .recipe-note {
    margin: 0;
    font-size: var(--text-xs);
    color: var(--text-muted);
    border-top: 1px solid var(--border-subtle);
    padding-top: var(--space-sm);
  }

  /* Wizard */
  .wizard {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .wizard-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .wizard-title {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
  }

  .step-counter {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-family: ui-monospace, monospace;
  }

  .step-name {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-secondary);
  }

  .step-hint {
    margin: 0;
    font-size: var(--text-xs);
    color: var(--text-muted);
    line-height: 1.4;
  }

  .live-reading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-sm);
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-sm) var(--space-md);
    min-height: 2.25rem;
  }

  .live-reading.warn {
    border-color: rgba(217, 119, 6, 0.4);
  }

  .live-label {
    font-size: var(--text-xs);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .live-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    font-family: ui-monospace, monospace;
  }

  .live-unit {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-weight: 400;
  }

  .live-warn {
    font-size: var(--text-xs);
    color: var(--status-warning);
  }

  .wizard-actions {
    display: flex;
    gap: var(--space-sm);
    justify-content: flex-end;
  }

  .btn-primary,
  .btn-ghost {
    height: 2.25rem;
    padding: 0 0.75rem;
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    border: 1px solid transparent;
  }

  .btn-primary {
    background: var(--bg-tertiary);
    border-color: var(--border-emphasis);
    color: var(--text-primary);
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--accent-slate);
  }

  .btn-ghost {
    background: transparent;
    border-color: var(--border-emphasis);
    color: var(--text-muted);
  }

  .btn-ghost:hover:not(:disabled) {
    color: var(--text-primary);
    background: var(--bg-primary);
  }

  .btn-primary:disabled,
  .btn-ghost:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .spin {
    display: inline-flex;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .flex {
    display: flex;
  }

  .items-center {
    align-items: center;
  }

  .gap-2 {
    gap: 0.5rem;
  }
</style>
