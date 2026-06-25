<script>
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';

  let { relays = [], onToggleRelay } = $props();
</script>

<Card class="relay-control-card compact-card">
  <CardHeader>
    <CardTitle class="section-title-compact">Relay Controls</CardTitle>
  </CardHeader>
  <CardContent>
    <div class="relay-compact-grid">
      <!-- Tank 1 Relays -->
      <div class="relay-tank-section">
        <div class="tank-relay-header">Tank 1</div>
        <div class="tank-relays">
          {#each [1, 4, 7] as relayId}
            {@const relay = relays.find(r => r.id === relayId)}
            <Button
              class="relay-btn tank1-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
              onclick={() => onToggleRelay(relay.id)}
              variant="ghost"
            >
              <div class="relay-content">
                <div class="relay-id">{relay.id}</div>
                <div class="relay-name">{relay.name}</div>
                <div class="relay-status">{relay.status.toUpperCase()}</div>
              </div>
            </Button>
          {/each}
        </div>
      </div>

      <!-- Tank 2 Relays -->
      <div class="relay-tank-section">
        <div class="tank-relay-header">Tank 2</div>
        <div class="tank-relays">
          {#each [2, 5, 8] as relayId}
            {@const relay = relays.find(r => r.id === relayId)}
            <Button
              class="relay-btn tank2-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
              onclick={() => onToggleRelay(relay.id)}
              variant="ghost"
            >
              <div class="relay-content">
                <div class="relay-id">{relay.id}</div>
                <div class="relay-name">{relay.name}</div>
                <div class="relay-status">{relay.status.toUpperCase()}</div>
              </div>
            </Button>
          {/each}
        </div>
      </div>

      <!-- Tank 3 Relays -->
      <div class="relay-tank-section">
        <div class="tank-relay-header">Tank 3</div>
        <div class="tank-relays">
          {#each [3, 6, 9] as relayId}
            {@const relay = relays.find(r => r.id === relayId)}
            <Button
              class="relay-btn tank3-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
              onclick={() => onToggleRelay(relay.id)}
              variant="ghost"
            >
              <div class="relay-content">
                <div class="relay-id">{relay.id}</div>
                <div class="relay-name">{relay.name}</div>
                <div class="relay-status">{relay.status.toUpperCase()}</div>
              </div>
            </Button>
          {/each}
        </div>
      </div>

      <!-- Room & Drain Relays -->
      <div class="relay-tank-section">
        <div class="tank-relay-header">Rooms & Drain</div>
        <div class="tank-relays">
          {#each [10, 11, 12, 13] as relayId}
            {@const relay = relays.find(r => r.id === relayId)}
            <Button
              class="relay-btn rooms-relay {relay.status === 'on' ? 'relay-active' : 'relay-inactive'}"
              onclick={() => onToggleRelay(relay.id)}
              variant="ghost"
            >
              <div class="relay-content">
                <div class="relay-id">{relay.id}</div>
                <div class="relay-name">{relay.name}</div>
                <div class="relay-status">{relay.status.toUpperCase()}</div>
              </div>
            </Button>
          {/each}
        </div>
      </div>
    </div>
  </CardContent>
</Card>

<style>
  .compact-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    height: 100%;
  }

  .section-title-compact {
    font-size: var(--text-base) !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
  }

  /* Relay Control */
  .relay-control-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
  }

  /* Relay Compact Grid */
  .relay-compact-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
  }

  .relay-tank-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .tank-relay-header {
    font-weight: 600;
    color: var(--text-secondary);
    text-align: center;
    font-size: var(--text-xs);
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-sm);
    margin-bottom: var(--space-xs);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-subtle);
  }

  .tank-relays {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  :global(.relay-btn) {
    padding: var(--space-sm) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease !important;
    min-height: 56px !important;
    height: 56px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: var(--bg-secondary) !important;
    color: var(--text-muted) !important;
  }

  :global(.relay-btn:active) {
    opacity: 0.85;
  }

  /* Unified Relay Styling - No Color Coding */
  :global(.relay-btn.relay-active) {
    background: var(--accent-steel) !important;
    border-color: var(--border-emphasis) !important;
    color: var(--text-primary) !important;
  }

  :global(.relay-btn.relay-inactive) {
    background: var(--bg-secondary) !important;
    border-color: var(--border-subtle) !important;
    color: var(--text-muted) !important;
  }

  :global(.relay-btn.relay-inactive:hover) {
    background: var(--bg-tertiary) !important;
    border-color: var(--border-emphasis) !important;
  }

  .relay-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--space-xs);
    text-align: center;
    width: 100%;
    height: 100%;
  }

  .relay-id {
    font-weight: 500;
    font-size: 0.625rem;
    margin-bottom: 2px;
    opacity: 0.7;
  }

  .relay-name {
    font-size: var(--text-xs);
    line-height: 1.2;
    font-weight: 600;
    margin-bottom: 2px;
    color: inherit;
  }

  .relay-status {
    font-size: 0.625rem;
    font-weight: 500;
    padding: 1px 6px;
    border-radius: var(--radius-sm);
    background: rgba(0, 0, 0, 0.2);
    color: inherit;
    letter-spacing: 0.05em;
  }

  /* Touch Optimizations */
  @media (pointer: coarse) {
    :global(.relay-btn) {
      min-height: 44px !important;
      touch-action: manipulation !important;
    }
  }
</style>
