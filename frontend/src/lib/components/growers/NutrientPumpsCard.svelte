<script>
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';

  let { pumps = [], dosingAmount = 50, onDispense, onSliderInput } = $props();
</script>

<Card class="nute-pumps-card compact-card card-elevated h-full">
  <CardHeader>
    <CardTitle class="section-title-compact">Nutrient Pumps</CardTitle>
  </CardHeader>
  <CardContent>
    <div class="nute-pumps-compact-grid">
      {#each pumps as pump}
        <Button
          class="pump-btn-compact {pump.status === 'dispensing' ? 'pump-active' : 'pump-idle'}"
          onclick={() => onDispense(pump.id, dosingAmount)}
          disabled={pump.status === 'dispensing'}
        >
          <div class="pump-content-compact">
            <div class="pump-id-compact">P{pump.id}</div>
            <div class="pump-name-compact">{pump.name}</div>
            {#if pump.status === 'dispensing'}
              <div class="pump-status-compact">{pump.progress}%</div>
            {:else}
              <div class="pump-status-compact">{dosingAmount}ml</div>
            {/if}
          </div>
        </Button>
      {/each}
    </div>
    <div class="dosing-amount-selector">
      <input
        type="range"
        class="dosing-slider-compact"
        min="1"
        max="2000"
        value={dosingAmount}
        step="1"
        oninput={onSliderInput}
      />
      <div class="dosing-value-compact">{dosingAmount}ml</div>
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

  /* Nutrient Pumps - Compact Grid */
  .nute-pumps-compact-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
    margin-bottom: var(--space-md);
  }

  :global(.pump-btn-compact) {
    padding: var(--space-xs) !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.2s ease !important;
    min-height: 60px !important;
    height: 60px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .pump-content-compact {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    width: 100%;
  }

  .pump-id-compact {
    font-size: 0.625rem;
    font-weight: 500;
    color: var(--text-muted);
  }

  .pump-name-compact {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-primary);
    text-align: center;
  }

  .pump-status-compact {
    font-size: 0.625rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .dosing-amount-selector {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding-top: var(--space-sm);
    border-top: 1px solid var(--border-subtle);
  }

  .dosing-slider-compact {
    flex: 1;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .dosing-slider-compact::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: hsl(var(--brand));
    border: 2px solid hsl(var(--brand) / 0.4);
    box-shadow: 0 0 8px hsl(var(--brand) / 0.5);
    border-radius: 50%;
    cursor: pointer;
  }

  .dosing-slider-compact::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: hsl(var(--brand));
    border: 2px solid hsl(var(--brand) / 0.4);
    box-shadow: 0 0 8px hsl(var(--brand) / 0.5);
    border-radius: 50%;
    cursor: pointer;
  }

  .dosing-value-compact {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    min-width: 60px;
    text-align: right;
  }

  /* Unified Pump Styling - No Nutrient Color Coding */
  :global(.pump-idle) {
    background: var(--bg-secondary) !important;
    border-color: var(--border-subtle) !important;
    color: var(--text-primary) !important;
  }

  :global(.pump-idle:hover) {
    background: var(--bg-tertiary) !important;
    border-color: var(--border-emphasis) !important;
  }

  :global(.pump-active) {
    background: var(--status-warning) !important;
    border-color: var(--status-warning) !important;
    color: var(--bg-primary) !important;
  }
</style>
