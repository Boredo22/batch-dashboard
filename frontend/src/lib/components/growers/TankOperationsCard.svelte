<script>
  import { Card, CardContent, CardHeader } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Select } from '$lib/components/ui/select';

  // Props
  let {
    tankId = 1,
    tankConfig = {},
    relays = [],
    recipes = [],
    onStartOperation = () => {},
    onStopOperation = () => {},
    isProcessing = false
  } = $props();

  // Local state
  let selectedOperation = $state('fill');
  let waterAmount = $state(tankConfig.maxGallons ? Math.min(50, tankConfig.maxGallons) : 50);
  let selectedRecipe = $state(null);
  let isExpanded = $state(true);

  // Derived max gallons
  let maxGallons = $derived(tankConfig.maxGallons || 100);

  // Derived values
  let fillActive = $derived(
    relays.some(r => r.id === tankConfig.fillRelay && r.status === 'on')
  );

  let mixActive = $derived(
    tankConfig.mixRelays?.every(id =>
      relays.find(r => r.id === id)?.status === 'on'
    ) || false
  );

  let sendActive = $derived(
    relays.some(r => r.id === tankConfig.sendRelay && r.status === 'on')
  );

  let currentStatus = $derived(() => {
    if (fillActive) return 'filling';
    if (mixActive) return 'mixing';
    if (sendActive) return 'sending';
    return 'idle';
  });

  let canStart = $derived(() => {
    if (selectedOperation === 'fill') return waterAmount > 0 && waterAmount <= maxGallons;
    if (selectedOperation === 'mix') return selectedRecipe !== null;
    if (selectedOperation === 'send') return waterAmount > 0 && waterAmount <= maxGallons;
    return false;
  });

  // Methods
  function handleStartOperation() {
    const operationData = {
      tankId,
      operation: selectedOperation,
      waterAmount: selectedOperation !== 'mix' ? waterAmount : null,
      recipe: selectedOperation === 'mix' ? selectedRecipe : null
    };
    onStartOperation(operationData);
  }

  function handleStopOperation() {
    onStopOperation(tankId);
  }

  function setWaterPreset(amount) {
    waterAmount = amount;
  }
</script>

<Card class="tank-operation-card">
  <CardHeader class="pb-3">
    <button
      class="header-toggle"
      onclick={() => isExpanded = !isExpanded}
    >
      <div class="tank-header tank-theme-{tankConfig.color}">
        <div class="tank-icon-sm">
          <span class="text-lg font-bold">{tankId}</span>
        </div>
        <div class="flex flex-col flex-1">
          <span class="tank-title">{tankConfig.label}</span>
          <div class="flex items-center gap-2 mt-0.5">
            <Badge
              variant="secondary"
              class="status-badge status-{currentStatus()}"
            >
              {currentStatus().toUpperCase()}
            </Badge>
            {#if currentStatus() !== 'idle'}
              <span class="text-xs text-slate-400">
                {currentStatus() === 'filling' ? `${waterAmount} gal` :
                 currentStatus() === 'mixing' ? selectedRecipe?.name || 'Mix' :
                 `${waterAmount} gal`}
              </span>
            {/if}
          </div>
        </div>
        <svg
          class="chevron {isExpanded ? 'expanded' : ''}"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
    </button>
  </CardHeader>

  {#if isExpanded}
  <CardContent>
    <!-- Operation Type Selector -->
    <div class="operation-selector">
      <button
        class="op-btn {selectedOperation === 'fill' ? 'active' : ''}"
        onclick={() => selectedOperation = 'fill'}
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v20M12 2l-4 4M12 2l4 4M17 8v13a2 2 0 01-2 2H9a2 2 0 01-2-2V8"/>
        </svg>
        <span>Fill</span>
      </button>

      <button
        class="op-btn {selectedOperation === 'mix' ? 'active' : ''}"
        onclick={() => selectedOperation = 'mix'}
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M8 12h8M12 8v8M20 12c0 4.418-3.582 8-8 8s-8-3.582-8-8 3.582-8 8-8 8 3.582 8 8z"/>
        </svg>
        <span>Mix</span>
      </button>

      <button
        class="op-btn {selectedOperation === 'send' ? 'active' : ''}"
        onclick={() => selectedOperation = 'send'}
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
        </svg>
        <span>Send</span>
      </button>
    </div>

    <!-- Fill Operation Controls -->
    {#if selectedOperation === 'fill'}
      <div class="operation-config">
        <div class="config-header">
          <span class="config-label">Water Amount</span>
          <div class="amount-display">
            {waterAmount}<span class="unit">gal</span>
          </div>
        </div>

        <input
          type="range"
          class="water-slider"
          min="1"
          max={maxGallons}
          bind:value={waterAmount}
        />

        <div class="preset-row">
          {#if maxGallons >= 100}
            {#each [10, 25, 50, 75, 100] as amount}
              <button
                class="preset-chip {waterAmount === amount ? 'active' : ''}"
                onclick={() => setWaterPreset(amount)}
              >
                {amount}
              </button>
            {/each}
          {:else if maxGallons >= 30}
            {#each [5, 10, 15, 20, 30] as amount}
              {#if amount <= maxGallons}
                <button
                  class="preset-chip {waterAmount === amount ? 'active' : ''}"
                  onclick={() => setWaterPreset(amount)}
                >
                  {amount}
                </button>
              {/if}
            {/each}
          {:else}
            {#each [5, 10, 15, 20] as amount}
              {#if amount <= maxGallons}
                <button
                  class="preset-chip {waterAmount === amount ? 'active' : ''}"
                  onclick={() => setWaterPreset(amount)}
                >
                  {amount}
                </button>
              {/if}
            {/each}
          {/if}
        </div>
      </div>
    {/if}

    <!-- Mix Operation Controls -->
    {#if selectedOperation === 'mix'}
      <div class="operation-config">
        <div class="config-header">
          <span class="config-label">Nutrient Recipe</span>
        </div>

        <div class="recipe-grid">
          {#each recipes as recipe}
            <button
              class="recipe-card {selectedRecipe?.name === recipe.name ? 'active' : ''}"
              onclick={() => selectedRecipe = recipe}
            >
              <div class="recipe-icon">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 2v6m6-6v6M4 8h16M4 8v10a2 2 0 002 2h12a2 2 0 002-2V8"/>
                </svg>
              </div>
              <span class="recipe-name">{recipe.name}</span>
              <span class="recipe-count">{Object.keys(recipe.pumps || {}).length} nutrients</span>
            </button>
          {/each}

          {#if recipes.length === 0}
            <div class="empty-state">
              <span class="text-sm text-slate-500">No recipes available</span>
              <span class="text-xs text-slate-600">Create recipes in Nutrients page</span>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Send Operation Controls -->
    {#if selectedOperation === 'send'}
      <div class="operation-config">
        <div class="config-header">
          <span class="config-label">Send Amount</span>
          <div class="amount-display">
            {waterAmount}<span class="unit">gal</span>
          </div>
        </div>

        <input
          type="range"
          class="water-slider"
          min="1"
          max={maxGallons}
          bind:value={waterAmount}
        />

        <div class="preset-row">
          {#if maxGallons >= 100}
            {#each [10, 25, 50, 75, 100] as amount}
              <button
                class="preset-chip {waterAmount === amount ? 'active' : ''}"
                onclick={() => setWaterPreset(amount)}
              >
                {amount}
              </button>
            {/each}
          {:else if maxGallons >= 30}
            {#each [5, 10, 15, 20, 30] as amount}
              {#if amount <= maxGallons}
                <button
                  class="preset-chip {waterAmount === amount ? 'active' : ''}"
                  onclick={() => setWaterPreset(amount)}
                >
                  {amount}
                </button>
              {/if}
            {/each}
          {:else}
            {#each [5, 10, 15, 20] as amount}
              {#if amount <= maxGallons}
                <button
                  class="preset-chip {waterAmount === amount ? 'active' : ''}"
                  onclick={() => setWaterPreset(amount)}
                >
                  {amount}
                </button>
              {/if}
            {/each}
          {/if}
        </div>
      </div>
    {/if}

    <!-- Action Buttons -->
    <div class="action-buttons">
      {#if currentStatus() === 'idle'}
        <Button
          class="start-btn tank-theme-{tankConfig.color}"
          disabled={!canStart() || isProcessing}
          onclick={handleStartOperation}
        >
          <svg class="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          Start {selectedOperation.charAt(0).toUpperCase() + selectedOperation.slice(1)}
        </Button>
      {:else}
        <Button
          variant="destructive"
          class="stop-btn"
          disabled={isProcessing}
          onclick={handleStopOperation}
        >
          <svg class="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="6" y="6" width="12" height="12" fill="currentColor"></rect>
          </svg>
          Stop {currentStatus().charAt(0).toUpperCase() + currentStatus().slice(1)}
        </Button>
      {/if}
    </div>
  </CardContent>
  {/if}
</Card>

<style>
  :global(.tank-operation-card) {
    background: linear-gradient(135deg, #1a1f35 0%, #151929 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
  }

  .header-toggle {
    width: 100%;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
  }

  .tank-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
    border-radius: 0.5rem;
    transition: background 0.2s;
  }

  .tank-header:hover {
    background: rgba(139, 92, 246, 0.05);
  }

  .tank-icon-sm {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1e293b;
    color: #94a3b8;
    font-weight: 800;
    border: 2px solid;
    transition: all 0.3s;
  }

  .tank-theme-blue .tank-icon-sm {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(168, 85, 247, 0.1));
    color: #a78bfa;
    border-color: rgba(139, 92, 246, 0.3);
  }

  .tank-theme-green .tank-icon-sm {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(52, 211, 153, 0.1));
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.3);
  }

  .tank-theme-yellow .tank-icon-sm {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(16, 185, 129, 0.1));
    color: #10b981;
    border-color: rgba(16, 185, 129, 0.3);
  }

  .tank-title {
    font-size: 1rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.025em;
  }

  .chevron {
    color: #6b7280;
    transition: transform 0.3s;
    flex-shrink: 0;
  }

  .chevron.expanded {
    transform: rotate(180deg);
    color: #8b5cf6;
  }

  :global(.status-badge) {
    font-size: 0.625rem;
    font-weight: 800;
    letter-spacing: 0.05em;
  }

  :global(.status-idle) {
    background: rgba(71, 85, 105, 0.3) !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(100, 116, 139, 0.3) !important;
  }

  :global(.status-filling) {
    background: rgba(59, 130, 246, 0.2) !important;
    color: #60a5fa !important;
    border: 1px solid rgba(59, 130, 246, 0.4) !important;
  }

  :global(.status-mixing) {
    background: rgba(139, 92, 246, 0.2) !important;
    color: #a78bfa !important;
    border: 1px solid rgba(139, 92, 246, 0.4) !important;
  }

  :global(.status-sending) {
    background: rgba(16, 185, 129, 0.2) !important;
    color: #34d399 !important;
    border: 1px solid rgba(16, 185, 129, 0.4) !important;
  }

  /* Operation Selector */
  .operation-selector {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .op-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.375rem;
    padding: 0.625rem 0.5rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1.5px solid rgba(51, 65, 85, 0.8);
    border-radius: 0.5rem;
    color: #94a3b8;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
  }

  .op-btn:hover {
    border-color: rgba(139, 92, 246, 0.5);
    background: rgba(30, 41, 59, 0.8);
    transform: translateY(-2px);
  }

  .op-btn.active {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border-color: #a78bfa;
    color: white;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
  }

  /* Operation Config */
  .operation-config {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(10, 15, 30, 0.9));
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 0.5rem;
    padding: 0.875rem;
    margin-bottom: 0.75rem;
  }

  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.625rem;
  }

  .config-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #8b5cf6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .amount-display {
    font-size: 1.5rem;
    font-weight: 700;
    color: #a78bfa;
    font-family: monospace;
  }

  .amount-display .unit {
    font-size: 0.75rem;
    color: #64748b;
    margin-left: 0.25rem;
  }

  /* Water Slider */
  .water-slider {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 0.375rem;
    background: linear-gradient(to right, rgba(139, 92, 246, 0.3), rgba(139, 92, 246, 0.1));
    border-radius: 9999px;
    outline: none;
    cursor: pointer;
    border: 1px solid rgba(139, 92, 246, 0.2);
    margin-bottom: 0.625rem;
  }

  .water-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1.5rem;
    height: 1.5rem;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2);
  }

  .water-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 0 0 6px rgba(139, 92, 246, 0.3);
  }

  .water-slider::-moz-range-thumb {
    width: 1.5rem;
    height: 1.5rem;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2);
  }

  /* Preset Row */
  .preset-row {
    display: flex;
    gap: 0.5rem;
    justify-content: space-between;
  }

  .preset-chip {
    flex: 1;
    padding: 0.5rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 0.5rem;
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .preset-chip:hover {
    border-color: rgba(139, 92, 246, 0.4);
    color: #e2e8f0;
  }

  .preset-chip.active {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    border-color: #a78bfa;
    color: white;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
  }

  /* Recipe Grid */
  .recipe-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .recipe-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.375rem;
    padding: 0.75rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1.5px solid rgba(51, 65, 85, 0.8);
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.3s;
  }

  .recipe-card:hover {
    border-color: rgba(139, 92, 246, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
  }

  .recipe-card.active {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.15));
    border-color: #a78bfa;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
  }

  .recipe-icon {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(139, 92, 246, 0.15);
    border-radius: 0.5rem;
    color: #a78bfa;
  }

  .recipe-card.active .recipe-icon {
    background: rgba(139, 92, 246, 0.3);
    color: #c4b5fd;
  }

  .recipe-name {
    font-size: 0.875rem;
    font-weight: 700;
    color: #f1f5f9;
    text-align: center;
  }

  .recipe-count {
    font-size: 0.625rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .empty-state {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem;
    text-align: center;
  }

  /* Action Buttons */
  .action-buttons {
    display: flex;
    gap: 0.75rem;
  }

  :global(.start-btn) {
    flex: 1;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.4) !important;
    transition: all 0.3s !important;
  }

  :global(.start-btn:hover:not(:disabled)) {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.6) !important;
  }

  :global(.start-btn:disabled) {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
  }

  :global(.tank-theme-green .start-btn) {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.4) !important;
  }

  :global(.tank-theme-green .start-btn:hover:not(:disabled)) {
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.6) !important;
  }

  :global(.stop-btn) {
    flex: 1;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.5rem !important;
  }
</style>
