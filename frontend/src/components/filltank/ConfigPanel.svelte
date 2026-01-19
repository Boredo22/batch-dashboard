<script>
  let {
    // Tank & Volume
    selectedTank = $bindable(1),
    targetVolume = $bindable(25),
    tanks = [],

    // Recipe
    selectedRecipe = $bindable('veg_formula'),
    recipes = {},
    nutrientOverrides = $bindable({}),

    // EC/pH Targets
    ecTarget = $bindable({ min: 1.0, max: 2.0 }),
    phTarget = $bindable({ min: 5.5, max: 6.5 }),

    // Send Config
    selectedRoom = $bindable(1),
    sendVolume = $bindable(25),
    rooms = [],

    // Phase Enable
    enabledPhases = $bindable({ fill: true, mix: true, send: true }),

    // State
    isRunning = false,
    workflowPhase = 'idle'
  } = $props();

  // Get current tank config
  let currentTank = $derived(tanks.find(t => t.id === selectedTank) || {});

  // Get current recipe nutrients
  let currentRecipeNutrients = $derived(recipes[selectedRecipe] || {});

  // Calculate nutrient doses based on volume
  let calculatedDoses = $derived(() => {
    const doses = {};
    for (const [nutrient, mlPerGallon] of Object.entries(currentRecipeNutrients)) {
      const override = nutrientOverrides[nutrient];
      doses[nutrient] = {
        perGallon: override ?? mlPerGallon,
        total: (override ?? mlPerGallon) * targetVolume
      };
    }
    return doses;
  });

  // Show/hide overrides panel
  let showOverrides = $state(false);

  // Reset override for a nutrient
  function resetOverride(nutrient) {
    const newOverrides = { ...nutrientOverrides };
    delete newOverrides[nutrient];
    nutrientOverrides = newOverrides;
  }

  // Set override for a nutrient
  function setOverride(nutrient, value) {
    nutrientOverrides = { ...nutrientOverrides, [nutrient]: parseFloat(value) || 0 };
  }
</script>

<div class="config-panel">
  <div class="panel-header">
    <h3><i class="fas fa-cog"></i> Configuration</h3>
  </div>

  <!-- Tank Selection -->
  <div class="config-section">
    <label class="section-label">Tank Selection</label>
    <select bind:value={selectedTank} disabled={isRunning} class="config-select">
      {#each tanks as tank}
        <option value={tank.id}>{tank.name} ({tank.capacity_gallons} gal)</option>
      {/each}
    </select>
    {#if currentTank.fill_relay}
      <div class="config-hint">
        Fill Relay: {currentTank.fill_relay} | Mix Relays: {currentTank.mix_relays?.join(', ')}
      </div>
    {/if}
  </div>

  <!-- Volume -->
  <div class="config-section">
    <label class="section-label">Fill Volume (gallons)</label>
    <input
      type="number"
      bind:value={targetVolume}
      min="1"
      max={currentTank.capacity_gallons || 100}
      step="1"
      disabled={isRunning}
      class="config-input"
    />
    <div class="config-hint">Max: {currentTank.capacity_gallons || 100} gallons</div>
  </div>

  <!-- Recipe Selection -->
  <div class="config-section">
    <label class="section-label">Nutrient Recipe</label>
    <select bind:value={selectedRecipe} disabled={isRunning} class="config-select">
      {#each Object.keys(recipes) as recipe}
        <option value={recipe}>{recipe.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
      {/each}
      <option value="custom">Custom (Manual Overrides)</option>
    </select>
  </div>

  <!-- EC Target -->
  <div class="config-section">
    <label class="section-label">EC Target Range (mS/cm)</label>
    <div class="range-inputs">
      <div class="range-input-group">
        <label>Min</label>
        <input
          type="number"
          bind:value={ecTarget.min}
          min="0"
          max="5"
          step="0.1"
          disabled={isRunning}
          class="config-input small"
        />
      </div>
      <span class="range-separator">-</span>
      <div class="range-input-group">
        <label>Max</label>
        <input
          type="number"
          bind:value={ecTarget.max}
          min="0"
          max="5"
          step="0.1"
          disabled={isRunning}
          class="config-input small"
        />
      </div>
    </div>
  </div>

  <!-- pH Target -->
  <div class="config-section">
    <label class="section-label">pH Target Range</label>
    <div class="range-inputs">
      <div class="range-input-group">
        <label>Min</label>
        <input
          type="number"
          bind:value={phTarget.min}
          min="0"
          max="14"
          step="0.1"
          disabled={isRunning}
          class="config-input small"
        />
      </div>
      <span class="range-separator">-</span>
      <div class="range-input-group">
        <label>Max</label>
        <input
          type="number"
          bind:value={phTarget.max}
          min="0"
          max="14"
          step="0.1"
          disabled={isRunning}
          class="config-input small"
        />
      </div>
    </div>
  </div>

  <!-- Nutrient Doses -->
  <div class="config-section">
    <button
      class="section-toggle"
      onclick={() => showOverrides = !showOverrides}
      disabled={isRunning}
    >
      <span class="section-label">Nutrient Doses</span>
      <i class="fas fa-chevron-{showOverrides ? 'up' : 'down'}"></i>
    </button>

    {#if showOverrides}
      <div class="nutrients-list">
        {#each Object.entries(calculatedDoses()) as [nutrient, dose]}
          <div class="nutrient-row">
            <span class="nutrient-name">{nutrient}</span>
            <div class="nutrient-input-group">
              <input
                type="number"
                value={dose.perGallon}
                min="0"
                step="0.1"
                disabled={isRunning}
                class="config-input tiny"
                onchange={(e) => setOverride(nutrient, e.target.value)}
              />
              <span class="unit">ml/gal</span>
            </div>
            <span class="nutrient-total">= {dose.total.toFixed(1)} ml</span>
            {#if nutrientOverrides[nutrient] !== undefined}
              <button
                class="reset-btn"
                onclick={() => resetOverride(nutrient)}
                disabled={isRunning}
                title="Reset to default"
              >
                <i class="fas fa-undo"></i>
              </button>
            {/if}
          </div>
        {/each}
      </div>
    {:else}
      <div class="nutrients-summary">
        {Object.keys(calculatedDoses()).length} nutrients configured
      </div>
    {/if}
  </div>

  <!-- Send Configuration -->
  <div class="config-section">
    <label class="section-label">Send to Room</label>
    <select bind:value={selectedRoom} disabled={isRunning || !enabledPhases.send} class="config-select">
      {#each rooms as room}
        <option value={room.id}>{room.name} (Relay {room.relay})</option>
      {/each}
    </select>
    <div class="send-volume-row">
      <label>Send Volume:</label>
      <input
        type="number"
        bind:value={sendVolume}
        min="1"
        max={targetVolume}
        step="1"
        disabled={isRunning || !enabledPhases.send}
        class="config-input small"
      />
      <span class="unit">gal</span>
    </div>
  </div>

  <!-- Phase Selection -->
  <div class="config-section phases-section">
    <label class="section-label">Enabled Phases</label>
    <div class="phases-grid">
      <label class="phase-checkbox">
        <input
          type="checkbox"
          bind:checked={enabledPhases.fill}
          disabled={isRunning}
        />
        <span class="checkbox-label">
          <i class="fas fa-fill-drip"></i> Fill
        </span>
      </label>
      <label class="phase-checkbox">
        <input
          type="checkbox"
          bind:checked={enabledPhases.mix}
          disabled={isRunning}
        />
        <span class="checkbox-label">
          <i class="fas fa-flask"></i> Mix
        </span>
      </label>
      <label class="phase-checkbox">
        <input
          type="checkbox"
          bind:checked={enabledPhases.send}
          disabled={isRunning}
        />
        <span class="checkbox-label">
          <i class="fas fa-share"></i> Send
        </span>
      </label>
    </div>
  </div>
</div>

<style>
  .config-panel {
    background: #2d3748;
    border-radius: 12px;
    border: 1px solid #4a5568;
    height: 100%;
    overflow-y: auto;
  }

  .panel-header {
    padding: 16px;
    border-bottom: 1px solid #4a5568;
    position: sticky;
    top: 0;
    background: #2d3748;
    z-index: 1;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 1rem;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .panel-header i {
    color: #3b82f6;
  }

  .config-section {
    padding: 12px 16px;
    border-bottom: 1px solid #374151;
  }

  .config-section:last-child {
    border-bottom: none;
  }

  .section-label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 8px;
  }

  .section-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    margin-bottom: 8px;
  }

  .section-toggle .section-label {
    margin-bottom: 0;
  }

  .section-toggle i {
    color: #6b7280;
    font-size: 0.75rem;
  }

  .config-select, .config-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #4a5568;
    border-radius: 6px;
    background: #1a202c;
    color: #e2e8f0;
    font-size: 0.9rem;
    transition: border-color 0.2s;
  }

  .config-select:focus, .config-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .config-select:disabled, .config-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .config-input.small {
    width: 80px;
    padding: 8px 10px;
  }

  .config-input.tiny {
    width: 60px;
    padding: 6px 8px;
    font-size: 0.85rem;
  }

  .config-hint {
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 4px;
  }

  .range-inputs {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .range-input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .range-input-group label {
    font-size: 0.7rem;
    color: #6b7280;
  }

  .range-separator {
    color: #6b7280;
    font-weight: bold;
    margin-top: 16px;
  }

  .nutrients-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
  }

  .nutrient-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: #1a202c;
    border-radius: 6px;
  }

  .nutrient-name {
    flex: 1;
    font-size: 0.85rem;
    color: #e2e8f0;
    min-width: 80px;
  }

  .nutrient-input-group {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .unit {
    font-size: 0.75rem;
    color: #6b7280;
  }

  .nutrient-total {
    font-size: 0.8rem;
    color: #22c55e;
    min-width: 70px;
    text-align: right;
  }

  .reset-btn {
    background: none;
    border: none;
    color: #6b7280;
    cursor: pointer;
    padding: 4px;
    font-size: 0.75rem;
  }

  .reset-btn:hover:not(:disabled) {
    color: #f59e0b;
  }

  .nutrients-summary {
    font-size: 0.8rem;
    color: #6b7280;
    padding: 8px;
    background: #1a202c;
    border-radius: 6px;
    text-align: center;
  }

  .send-volume-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    font-size: 0.85rem;
    color: #94a3b8;
  }

  .phases-section {
    padding-bottom: 16px;
  }

  .phases-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .phase-checkbox {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    padding: 8px 12px;
    background: #1a202c;
    border-radius: 6px;
    transition: background 0.2s;
  }

  .phase-checkbox:hover {
    background: #2d3748;
  }

  .phase-checkbox input {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: #3b82f6;
  }

  .phase-checkbox input:disabled {
    cursor: not-allowed;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    color: #e2e8f0;
  }

  .checkbox-label i {
    color: #3b82f6;
    width: 16px;
  }

  @media (max-width: 768px) {
    .config-panel {
      max-height: none;
    }

    .nutrient-row {
      flex-wrap: wrap;
    }

    .nutrient-name {
      width: 100%;
    }
  }
</style>
