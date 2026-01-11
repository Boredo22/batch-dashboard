<script>
  import { onMount } from "svelte";
  import { Zap, Layers, ChevronDown, ChevronUp } from "@lucide/svelte/icons";
  import { getApiUrl } from "$lib/websocket";

  let { relays = [], onRelayControl, onComboControl } = $props();

  // Ensure relays is always an array to prevent null reference errors
  let safeRelays = $derived(Array.isArray(relays) ? relays : []);

  // Relay combo presets
  let combos = $state([]);
  let showCombos = $state(false);
  let loadingCombo = $state(null);

  async function fetchCombos() {
    try {
      const response = await fetch(`${getApiUrl()}/api/relay/combos`);
      if (response.ok) {
        const data = await response.json();
        combos = data.combos || [];
      }
    } catch (error) {
      console.error('Error fetching relay combos:', error);
    }
  }

  async function activateCombo(comboName, action) {
    loadingCombo = comboName;
    try {
      const encodedName = encodeURIComponent(comboName);
      const response = await fetch(`${getApiUrl()}/api/relay/combo/${encodedName}/${action}`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        onComboControl?.(comboName, action, data);
      }
    } catch (error) {
      console.error('Error activating combo:', error);
    } finally {
      loadingCombo = null;
    }
  }

  function handleRelayControl(relayId, action) {
    console.log('[RelayCard] Button clicked:', relayId, action);
    onRelayControl?.(relayId, action);
  }

  // Check if a combo is currently active (all its relays are on)
  function isComboActive(combo) {
    return combo.relays.every(relayId => {
      const relay = safeRelays.find(r => r.id === relayId);
      return relay && relay.status === 'on';
    });
  }

  onMount(() => {
    fetchCombos();
  });
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Zap class="icon" />
        <span class="card-title">Relay Control</span>
      </div>
      <div class="header-actions">
        <button
          onclick={() => showCombos = !showCombos}
          class="btn-secondary btn-sm"
          title="Show/hide relay presets"
        >
          <Layers class="btn-icon" />
          Presets
          {#if showCombos}
            <ChevronUp class="btn-icon" />
          {:else}
            <ChevronDown class="btn-icon" />
          {/if}
        </button>
        <button
          onclick={() => handleRelayControl(0, 'off')}
          class="btn-secondary btn-sm btn-danger-hover"
        >
          All OFF
        </button>
      </div>
    </div>
  </div>
  <div class="card-content">
    <!-- Combo Presets Section (collapsible) -->
    {#if showCombos && combos.length > 0}
      <div class="combos-section">
        <div class="combos-label">Quick Presets</div>
        <div class="combos-grid">
          {#each combos as combo}
            {@const active = isComboActive(combo)}
            {@const loading = loadingCombo === combo.name}
            <div class="combo-item {active ? 'combo-active' : ''}">
              <div class="combo-header">
                <span class="combo-name">{combo.name}</span>
                <span class="combo-relays">R{combo.relays.join(', R')}</span>
              </div>
              <div class="combo-controls">
                <button
                  onclick={() => activateCombo(combo.name, 'on')}
                  class="btn-combo {active ? 'btn-combo-on-active' : ''}"
                  disabled={loading}
                >
                  {loading && !active ? '...' : 'ON'}
                </button>
                <button
                  onclick={() => activateCombo(combo.name, 'off')}
                  class="btn-combo {!active ? 'btn-combo-off-active' : ''}"
                  disabled={loading}
                >
                  {loading && active ? '...' : 'OFF'}
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Individual Relay Grid -->
    <div class="relay-grid">
      {#each safeRelays as relay}
        <div class="relay-item">
          <div class="relay-header">
            <span class="relay-label">R{relay.id}</span>
            <span class="status-badge {relay.status === 'on' ? 'status-active' : 'status-inactive'}">
              {relay.status === 'on' ? 'ON' : 'OFF'}
            </span>
          </div>
          <div class="relay-controls">
            <button
              onclick={() => handleRelayControl(relay.id, 'on')}
              class="btn-control {relay.status === 'on' ? 'btn-control-active' : ''}"
            >
              ON
            </button>
            <button
              onclick={() => handleRelayControl(relay.id, 'off')}
              class="btn-control {relay.status === 'off' ? 'btn-control-active' : ''}"
            >
              OFF
            </button>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;

    --accent-steel: #64748b;
    --accent-slate: #475569;
    --accent-cyan: #06b6d4;

    --status-success: #059669;
    --status-warning: #d97706;
    --status-error: #dc2626;

    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;

    --border-subtle: #334155;
    --border-emphasis: #475569;

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
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
  }

  .header-actions {
    display: flex;
    gap: var(--space-sm);
  }

  .btn-secondary {
    background: transparent;
    border: 1px solid var(--border-emphasis);
    color: var(--text-secondary);
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--bg-tertiary);
  }

  .btn-danger-hover:hover:not(:disabled) {
    background: rgba(220, 38, 38, 0.15);
    border-color: rgba(220, 38, 38, 0.3);
    color: var(--status-error);
  }

  .btn-sm {
    height: 1.75rem;
    padding: 0 0.625rem;
    font-size: var(--text-xs);
    font-weight: 500;
  }

  .btn-icon {
    width: 0.75rem;
    height: 0.75rem;
  }

  /* Combo Presets Section */
  .combos-section {
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-sm);
  }

  .combos-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-muted);
    margin-bottom: var(--space-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .combos-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
  }

  .combo-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    padding: var(--space-sm);
    transition: all 0.15s ease;
  }

  .combo-item.combo-active {
    border-color: rgba(5, 150, 105, 0.5);
    background: rgba(5, 150, 105, 0.08);
  }

  .combo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-xs);
  }

  .combo-name {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-primary);
  }

  .combo-relays {
    font-size: 0.625rem;
    color: var(--text-muted);
    font-family: ui-monospace, monospace;
  }

  .combo-controls {
    display: flex;
    gap: var(--space-xs);
  }

  .btn-combo {
    flex: 1;
    height: 1.75rem;
    background: transparent;
    border: 1px solid var(--border-emphasis);
    color: var(--text-secondary);
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-combo:hover:not(:disabled) {
    background: var(--bg-tertiary);
  }

  .btn-combo:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-combo-on-active {
    background: rgba(5, 150, 105, 0.15);
    border-color: rgba(5, 150, 105, 0.3);
    color: var(--status-success);
  }

  .btn-combo-off-active {
    background: var(--bg-tertiary);
    border-color: var(--accent-steel);
    color: var(--text-primary);
  }

  /* Individual Relays Grid */
  .relay-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-sm);
  }

  .relay-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .relay-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .relay-label {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--text-secondary);
  }

  .status-badge {
    height: 1rem;
    padding: 0 0.375rem;
    font-size: 0.625rem;
    font-weight: 500;
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
  }

  .status-active {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border: 1px solid rgba(5, 150, 105, 0.3);
  }

  .status-inactive {
    background: rgba(100, 116, 139, 0.15);
    color: var(--text-muted);
    border: 1px solid var(--border-subtle);
  }

  .relay-controls {
    display: flex;
    gap: var(--space-xs);
  }

  .btn-control {
    flex: 1;
    height: 2.5rem;
    background: transparent;
    border: 1px solid var(--border-emphasis);
    color: var(--text-secondary);
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-control:hover:not(:disabled) {
    background: var(--bg-tertiary);
    border-color: var(--accent-steel);
  }

  .btn-control-active {
    background: var(--bg-tertiary);
    border-color: var(--accent-steel);
    color: var(--text-primary);
  }

  .flex {
    display: flex;
  }

  .items-center {
    align-items: center;
  }

  .justify-between {
    justify-content: space-between;
  }

  .gap-2 {
    gap: 0.5rem;
  }

  /* Mobile responsive */
  @media (max-width: 640px) {
    .combos-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
