<script>
  import { Sprout, Battery, Wifi, Thermometer } from "@lucide/svelte/icons";

  let {
    soilSensors = {}
  } = $props();

  // Convert the keyed object payload into a sorted array.
  let sensorList = $derived(
    Object.values(soilSensors)
      .filter(s => s && s.sensor_id != null)
      .sort((a, b) => a.sensor_id - b.sensor_id)
  );

  // Group sensors by room, preserving insertion order so room sections render
  // in the order they first appear in the payload.
  let rooms = $derived(() => {
    const out = new Map();
    for (const s of sensorList) {
      const key = s.room || 'Unassigned';
      if (!out.has(key)) out.set(key, []);
      out.get(key).push(s);
    }
    return Array.from(out, ([name, sensors]) => ({ name, sensors }));
  });

  let onlineCount = $derived(sensorList.filter(s => s.status === 'online').length);

  function ageLabel(iso) {
    if (!iso) return 'never';
    const d = new Date(iso);
    const secs = Math.max(0, Math.round((Date.now() - d.getTime()) / 1000));
    if (secs < 60) return `${secs}s ago`;
    const mins = Math.round(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.round(mins / 60);
    return `${hours}h ago`;
  }

  function fmt(v, digits = 1, unit = '') {
    if (v == null || isNaN(v)) return '—';
    return `${Number(v).toFixed(digits)}${unit}`;
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="header-row">
      <div class="header-left">
        <Sprout class="icon" />
        <span class="card-title">Soil Sensors</span>
      </div>
      <span class="count">
        {onlineCount}/{sensorList.length} online
      </span>
    </div>
  </div>

  <div class="card-content">
    {#if sensorList.length === 0}
      <div class="empty-state">No soil sensors registered</div>
    {:else}
      {#each rooms() as room (room.name)}
        <section class="room">
          <header class="room-header">
            <span class="room-name">{room.name}</span>
            <span class="room-count">{room.sensors.length}</span>
          </header>
          <div class="sensor-grid">
            {#each room.sensors as s (s.sensor_id)}
              <article class="sensor-card status-{s.status || 'offline'}">
                <header class="sensor-head">
                  <span class="sensor-name" title={s.name}>{s.name}</span>
                  <span class="status-dot" aria-label={s.status}></span>
                </header>

                <div class="moisture">
                  <span class="moisture-value">{fmt(s.moisture, 1)}</span>
                  <span class="moisture-unit">%</span>
                </div>

                <div class="aux">
                  <span class="aux-item">
                    <Thermometer class="aux-icon" />
                    {fmt(s.temp, 1, '°C')}
                  </span>
                  {#if s.ec != null}
                    <span class="aux-item">
                      EC {fmt(s.ec, 2)}
                    </span>
                  {/if}
                </div>

                <footer class="sensor-foot">
                  <span class="foot-item" title="Battery">
                    <Battery class="foot-icon" />
                    {fmt(s.batt, 2, 'V')}
                  </span>
                  <span class="foot-item" title="Signal (RSSI)">
                    <Wifi class="foot-icon" />
                    {s.rssi != null ? `${s.rssi} dBm` : '—'}
                  </span>
                  <span class="foot-item age">{ageLabel(s.last_update)}</span>
                </footer>
              </article>
            {/each}
          </div>
        </section>
      {/each}
    {/if}
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-card: #1e293b;
    --accent-steel: #64748b;
    --status-success: #059669;
    --status-warning: #d97706;
    --status-error: #dc2626;
    --text-primary: #f1f5f9;
    --text-muted: #94a3b8;
    --border-subtle: #334155;

    --space-xs: 0.25rem;
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

  .header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .card-title {
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .icon {
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
  }

  .count {
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .card-content {
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .empty-state {
    text-align: center;
    color: var(--text-muted);
    font-size: var(--text-sm);
    padding: var(--space-md);
  }

  .room {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .room-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--space-xs);
  }

  .room-name {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .room-count {
    font-size: var(--text-xs);
    color: var(--text-muted);
  }

  .sensor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--space-sm);
  }

  .sensor-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.375rem;
    padding: var(--space-sm);
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .sensor-card.status-stale {
    border-color: rgba(217, 119, 6, 0.4);
  }

  .sensor-card.status-offline {
    border-color: rgba(220, 38, 38, 0.4);
    opacity: 0.7;
  }

  .sensor-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-xs);
  }

  .sensor-name {
    font-size: var(--text-xs);
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background: var(--status-error);
    flex-shrink: 0;
  }

  .status-online .status-dot {
    background: var(--status-success);
    box-shadow: 0 0 6px rgba(5, 150, 105, 0.5);
  }

  .status-stale .status-dot {
    background: var(--status-warning);
  }

  .moisture {
    display: flex;
    align-items: baseline;
    gap: 0.125rem;
    justify-content: center;
    padding: var(--space-xs) 0;
  }

  .moisture-value {
    font-size: 1.625rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
    line-height: 1;
  }

  .status-stale .moisture-value,
  .status-offline .moisture-value {
    color: var(--text-muted);
  }

  .moisture-unit {
    font-size: 0.875rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .aux {
    display: flex;
    justify-content: center;
    gap: var(--space-sm);
    font-size: var(--text-xs);
    color: var(--text-muted);
    flex-wrap: wrap;
  }

  .aux-item {
    display: inline-flex;
    align-items: center;
    gap: 0.1875rem;
  }

  .aux-icon {
    width: 0.75rem;
    height: 0.75rem;
  }

  .sensor-foot {
    display: flex;
    justify-content: space-between;
    gap: var(--space-xs);
    font-size: 0.625rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border-subtle);
    padding-top: var(--space-xs);
  }

  .foot-item {
    display: inline-flex;
    align-items: center;
    gap: 0.125rem;
    white-space: nowrap;
  }

  .foot-icon {
    width: 0.6875rem;
    height: 0.6875rem;
  }

  .foot-item.age {
    margin-left: auto;
    font-style: italic;
  }
</style>
