<script>
  import PumpCalibration from './components/PumpCalibration.svelte';
  import Nutrients from './components/Nutrients.svelte';
  import NuteDispenseProgress from './components/NuteDispenseProgress.svelte';
  
  // Pump configuration from config.py
  const pumpNames = {
    1: "Veg A", 2: "Veg B", 3: "Bloom A", 4: "Bloom B",
    5: "Cake", 6: "PK Synergy", 7: "Runclean", 8: "pH Down"
  };
  
  // State management
  let systemStatus = $state({});
  let pumps = $state([]);
  let statusInterval = $state(null);
  let isConnected = $state(false);
  let lastUpdate = $state(new Date());
  
  // Manual dispense state
  let dispenseAmounts = $state({
    1: 2000, 2: 2000, 3: 0, 4: 0, 5: 0, 6: 0, 7: 15, 8: 30
  });
  let isDispensing = $state(false);
  let totalMixTime = $state(0);
  let dispensingPumps = $state(new Set());
  
  // Recipe management state
  let recipes = $state([]);
  let selectedRecipe = $state('');
  let newRecipeName = $state('');
  let isAddingRecipe = $state(false);
  let editingRecipe = $state(null);
  
  // Nutrients configuration
  let nutrientsConfig = $state({
    available_nutrients: [],
    veg_formula: {},
    bloom_formula: {},
    pump_name_to_id: {}
  });
  
  // UI state
  let activeSection = $state('dispense');
  
  // Computed values
  let totalVolume = $derived(Object.values(dispenseAmounts).reduce((sum, vol) => sum + vol, 0));
  
  let dispensingSummary = $derived(Object.entries(dispenseAmounts)
    .filter(([id, amount]) => amount > 0)
    .map(([id, amount]) => `${amount}ml ${pumpNames[id]}`)
    .join(', '));
  
  let overallProgress = $derived(() => {
    if (!isDispensing || dispensingPumps.size === 0) return 0;
    
    const totalTargetVolume = Object.entries(dispenseAmounts)
      .filter(([id, amount]) => amount > 0)
      .reduce((sum, [id, amount]) => sum + amount, 0);
      
    const totalCurrentVolume = pumps
      .filter(pump => dispenseAmounts[pump.id] > 0)
      .reduce((sum, pump) => sum + (pump.current_volume || 0), 0);
      
    return totalTargetVolume > 0 ? Math.min((totalCurrentVolume / totalTargetVolume) * 100, 100) : 0;
  });
  
  // Status fetching
  async function fetchSystemStatus() {
    try {
      const response = await fetch('/api/status');
      if (response.ok) {
        const data = await response.json();
        systemStatus = data;
        
        // API already returns pumps in the correct array format
        pumps = data.pumps || [];
        
        // Ensure all pumps have required fields
        pumps = pumps.map(pump => ({
          ...pump,
          is_dispensing: pump.is_dispensing || pump.status === 'running',
          current_volume: pump.current_volume || 0,
          target_volume: pump.target_volume || 0,
          voltage: pump.voltage || 0,
          calibrated: pump.calibrated || false
        }));
        
        isConnected = true;
        lastUpdate = new Date();
      } else {
        isConnected = false;
      }
    } catch (error) {
      console.error('Failed to fetch status:', error);
      isConnected = false;
    }
  }
  
  // Load nutrients configuration
  async function loadNutrientsConfig() {
    try {
      const response = await fetch('/api/nutrients');
      if (response.ok) {
        const data = await response.json();
        nutrientsConfig = data;
        
        // Initialize recipes from formulas
        recipes = [
          {
            name: 'VEG Formula',
            description: 'Vegetative growth formula',
            pumps: data.veg_formula || {},
            type: 'veg'
          },
          {
            name: 'BLOOM Formula', 
            description: 'Flowering/blooming formula',
            pumps: data.bloom_formula || {},
            type: 'bloom'
          }
        ];
      }
    } catch (error) {
      console.error('Failed to load nutrients config:', error);
    }
  }
  
  // Manual dispensing functions
  async function startManualDispense() {
    if (isDispensing || totalVolume === 0) return;
    
    isDispensing = true;
    totalMixTime = Date.now();
    dispensingPumps.clear();
    
    // Start dispensing for all pumps with amounts > 0
    for (const [pumpId, amount] of Object.entries(dispenseAmounts)) {
      if (amount > 0) {
        dispensingPumps.add(parseInt(pumpId));
        try {
          const response = await fetch(`/api/pumps/${pumpId}/dispense`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount })
          });
          
          if (!response.ok) {
            console.error(`Failed to start pump ${pumpId}`);
            dispensingPumps.delete(parseInt(pumpId));
          }
        } catch (error) {
          console.error(`Error starting pump ${pumpId}:`, error);
          dispensingPumps.delete(parseInt(pumpId));
        }
      }
    }
  }
  
  async function stopAllPumps() {
    for (const pumpId of dispensingPumps) {
      try {
        await fetch(`/api/pumps/${pumpId}/stop`, { method: 'POST' });
      } catch (error) {
        console.error(`Error stopping pump ${pumpId}:`, error);
      }
    }
    isDispensing = false;
    dispensingPumps.clear();
  }
  
  async function emergencyStop() {
    try {
      await fetch('/api/emergency/stop', { method: 'POST' });
      isDispensing = false;
      dispensingPumps.clear();
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  }
  
  // Recipe functions
  function loadRecipe(recipe) {
    // Convert recipe pumps to dispense amounts using pump name to ID mapping
    const newAmounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0 };
    
    for (const [nutrientName, amount] of Object.entries(recipe.pumps)) {
      const pumpId = nutrientsConfig.pump_name_to_id?.[nutrientName];
      if (pumpId && newAmounts.hasOwnProperty(pumpId)) {
        newAmounts[pumpId] = amount * 50; // Convert ml/gal to ml for 50 gallon mix
      }
    }
    
    dispenseAmounts = newAmounts;
    selectedRecipe = recipe.name;
  }
  
  function saveNewRecipe() {
    if (!newRecipeName.trim()) return;
    
    // Convert current dispense amounts to recipe format
    const recipePumps = {};
    for (const [pumpId, amount] of Object.entries(dispenseAmounts)) {
      if (amount > 0) {
        const nutrientName = pumpNames[pumpId];
        recipePumps[nutrientName] = amount / 50; // Convert back to ml/gal
      }
    }
    
    const newRecipe = {
      name: newRecipeName,
      description: 'Custom recipe',
      pumps: recipePumps,
      type: 'custom'
    };
    
    recipes = [...recipes, newRecipe];
    newRecipeName = '';
    isAddingRecipe = false;
  }
  
  function deleteRecipe(index) {
    if (recipes[index].type !== 'custom') return; // Don't delete system recipes
    recipes = recipes.filter((_, i) => i !== index);
  }
  
  // Lifecycle
  async function initializeComponent() {
    await loadNutrientsConfig();
    await fetchSystemStatus();
    
    // Set up status polling
    statusInterval = setInterval(fetchSystemStatus, 2000);
  }
  
  // Check if dispensing is complete
  $effect(() => {
    if (isDispensing && dispensingPumps.size > 0) {
      let allComplete = true;
      for (const pumpId of dispensingPumps) {
        const pump = pumps.find(p => p.id === pumpId);
        if (pump && pump.status === 'running') {
          allComplete = false;
          break;
        }
      }
      
      if (allComplete) {
        isDispensing = false;
        dispensingPumps.clear();
        totalMixTime = Date.now() - totalMixTime;
      }
    }
  });
  
  // Initialize on mount
  $effect(() => {
    initializeComponent();
    
    // Cleanup on unmount
    return () => {
      if (statusInterval) {
        clearInterval(statusInterval);
      }
    };
  });
</script>

<div class="nutrients-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-info">
      <h2><i class="fas fa-tint"></i> Nutrient Management</h2>
      <div class="connection-status {isConnected ? 'connected' : 'disconnected'}">
        <i class="fas fa-{isConnected ? 'check-circle' : 'exclamation-triangle'}"></i>
        {isConnected ? 'Connected' : 'Disconnected'}
        <span class="last-update">· Updated {lastUpdate.toLocaleTimeString()}</span>
      </div>
    </div>
    
    <!-- Emergency Stop -->
    <button class="emergency-btn" onclick={emergencyStop} aria-label="Emergency stop all operations">
      <i class="fas fa-exclamation-triangle"></i>
      EMERGENCY STOP
    </button>
  </div>
  
  <!-- Section Navigation -->
  <div class="section-nav">
    <button 
      class="nav-btn {activeSection === 'dispense' ? 'active' : ''}"
      onclick={() => activeSection = 'dispense'}
    >
      <i class="fas fa-play-circle"></i>
      Manual Dispense
    </button>
    <button 
      class="nav-btn {activeSection === 'recipes' ? 'active' : ''}"
      onclick={() => activeSection = 'recipes'}
    >
      <i class="fas fa-book"></i>
      Recipes
    </button>
    <button 
      class="nav-btn {activeSection === 'calibration' ? 'active' : ''}"
      onclick={() => activeSection = 'calibration'}
    >
      <i class="fas fa-ruler"></i>
      Calibration
    </button>
    <button 
      class="nav-btn {activeSection === 'config' ? 'active' : ''}"
      onclick={() => activeSection = 'config'}
    >
      <i class="fas fa-cog"></i>
      Configuration
    </button>
  </div>
  
  <!-- Manual Dispense Section -->
  {#if activeSection === 'dispense'}
    <div class="section">
      <!-- Mix Summary -->
      <div class="mix-summary">
        <div class="summary-header">
          <h3><i class="fas fa-flask"></i> Current Mix</h3>
          <div class="total-volume">
            Total: <span class="volume-value">{totalVolume.toLocaleString()}ml</span>
          </div>
        </div>
        
        {#if dispensingSummary}
          <div class="dispense-summary">{dispensingSummary}</div>
        {:else}
          <div class="no-mix">No nutrients selected for dispensing</div>
        {/if}
        
        <!-- Overall Progress -->
        {#if isDispensing}
          <div class="overall-progress">
            <div class="progress-header">
              <span class="progress-label">Overall Progress</span>
              <span class="progress-percent">{overallProgress().toFixed(1)}%</span>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar-fill" style="width: {overallProgress()}%"></div>
            </div>
          </div>
        {/if}
      </div>
      
      <!-- Pump Grid -->
      <div class="pump-grid">
        {#each Object.entries(pumpNames) as [pumpId, pumpName]}
          {@const pump = pumps.find(p => p.id == pumpId)}
          {@const isActive = dispensingPumps.has(parseInt(pumpId))}
          {@const amount = dispenseAmounts[pumpId] || 0}
          
          <div class="pump-card {isActive ? 'dispensing' : ''} {amount > 0 ? 'selected' : ''}">
            <div class="pump-header">
              <div class="pump-info">
                <span class="pump-name">{pumpName}</span>
                <span class="pump-id">Pump {pumpId}</span>
              </div>
              <div class="pump-status">
                <div class="voltage {pump?.voltage >= 5.0 && pump?.voltage <= 12.0 ? 'normal' : 'warning'}">
                  {pump?.voltage?.toFixed(1) || '0.0'}V
                </div>
                <div class="status-indicator {pump?.status === 'running' ? 'running' : 'stopped'}"></div>
              </div>
            </div>
            
            <!-- Volume Input -->
            <div class="volume-control">
              <label for="pump-{pumpId}-amount">Amount (ml)</label>
              <input
                id="pump-{pumpId}-amount"
                type="number"
                min="0"
                max="5000"
                step="0.1"
                bind:value={dispenseAmounts[pumpId]}
                disabled={isDispensing}
              />
            </div>
            
            <!-- Progress Bar -->
            {#if (isActive && pump) || (pump && (pump.current_volume > 0 || pump.is_dispensing))}
              <NuteDispenseProgress
                pumpId={parseInt(pumpId)}
                pumpName={pumpName}
                currentVolume={pump?.current_volume || 0}
                targetVolume={pump?.target_volume || amount}
                isDispensing={pump?.is_dispensing || false}
                voltage={pump?.voltage || 0}
                size="normal"
              />
            {/if}
            
            <!-- Calibration Status -->
            {#if pump?.calibrated !== undefined}
              <div class="calibration-status {pump.calibrated ? 'calibrated' : 'uncalibrated'}">
                <i class="fas fa-{pump.calibrated ? 'check-circle' : 'exclamation-circle'}"></i>
                {pump.calibrated ? 'Calibrated' : 'Needs Calibration'}
              </div>
            {/if}
          </div>
        {/each}
      </div>
      
      <!-- Control Buttons -->
      <div class="dispense-controls">
        <button 
          class="control-btn start-btn" 
          onclick={startManualDispense}
          disabled={isDispensing || totalVolume === 0}
        >
          <i class="fas fa-play"></i>
          Start Dispensing
        </button>
        
        <button 
          class="control-btn stop-btn" 
          onclick={stopAllPumps}
          disabled={!isDispensing}
        >
          <i class="fas fa-stop"></i>
          Stop All
        </button>
        
        <button 
          class="control-btn clear-btn"
          onclick={() => dispenseAmounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0 }}
          disabled={isDispensing}
        >
          <i class="fas fa-eraser"></i>
          Clear All
        </button>
      </div>
    </div>
  {/if}
  
  <!-- Recipes Section -->
  {#if activeSection === 'recipes'}
    <div class="section">
      <div class="recipes-header">
        <h3><i class="fas fa-book"></i> Nutrient Recipes</h3>
        <button 
          class="add-recipe-btn {isAddingRecipe ? 'active' : ''}"
          onclick={() => isAddingRecipe = !isAddingRecipe}
        >
          <i class="fas fa-{isAddingRecipe ? 'times' : 'plus'}"></i>
          {isAddingRecipe ? 'Cancel' : 'Add Recipe'}
        </button>
      </div>
      
      <!-- Add New Recipe -->
      {#if isAddingRecipe}
        <div class="add-recipe-form">
          <div class="form-row">
            <input 
              type="text" 
              placeholder="Recipe name..." 
              bind:value={newRecipeName}
              class="recipe-name-input"
            />
            <button 
              class="save-recipe-btn"
              onclick={saveNewRecipe}
              disabled={!newRecipeName.trim()}
            >
              <i class="fas fa-save"></i>
              Save Recipe
            </button>
          </div>
          <div class="recipe-help">
            Set your desired amounts above, then save as a recipe for quick loading later.
          </div>
        </div>
      {/if}
      
      <!-- Recipe List -->
      <div class="recipes-grid">
        {#each recipes as recipe, index}
          <div class="recipe-card {selectedRecipe === recipe.name ? 'selected' : ''}">
            <div class="recipe-header">
              <div class="recipe-info">
                <h4>{recipe.name}</h4>
                <p>{recipe.description}</p>
              </div>
              <div class="recipe-type type-{recipe.type}">
                {recipe.type.toUpperCase()}
              </div>
            </div>
            
            <div class="recipe-ingredients">
              {#each Object.entries(recipe.pumps) as [nutrient, amount]}
                <div class="ingredient">
                  <span class="nutrient-name">{nutrient}</span>
                  <span class="nutrient-amount">{amount} ml/gal</span>
                </div>
              {/each}
            </div>
            
            <div class="recipe-actions">
              <button 
                class="recipe-btn load-btn"
                onclick={() => loadRecipe(recipe)}
                disabled={isDispensing}
              >
                <i class="fas fa-download"></i>
                Load Recipe
              </button>
              
              {#if recipe.type === 'custom'}
                <button 
                  class="recipe-btn delete-btn"
                  onclick={() => deleteRecipe(index)}
                  disabled={isDispensing}
                  aria-label="Delete {recipe.name} recipe"
                >
                  <i class="fas fa-trash"></i>
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Calibration Section -->
  {#if activeSection === 'calibration'}
    <div class="section">
      <PumpCalibration />
    </div>
  {/if}
  
  <!-- Configuration Section -->
  {#if activeSection === 'config'}
    <div class="section">
      <Nutrients nutrients={nutrientsConfig.available_nutrients} />
    </div>
  {/if}
</div>

<style>
  .nutrients-page {
    padding: 1.5rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #334155;
  }

  .header-info h2 {
    margin: 0 0 0.5rem 0;
    color: #e2e8f0;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .header-info i {
    color: #06b6d4;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .connection-status.connected {
    color: #22c55e;
  }

  .connection-status.disconnected {
    color: #ef4444;
  }

  .last-update {
    color: #94a3b8;
    font-size: 0.8rem;
    font-weight: normal;
  }

  .emergency-btn {
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    animation: pulse-red 2s infinite;
  }

  .emergency-btn:hover {
    background: #b91c1c;
    transform: scale(1.05);
  }

  @keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }
  }

  .section-nav {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    background: #0f172a;
    padding: 0.5rem;
    border-radius: 0.75rem;
    border: 1px solid #334155;
  }

  .nav-btn {
    flex: 1;
    background: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .nav-btn:hover {
    color: #e2e8f0;
    background: #1e293b;
  }

  .nav-btn.active {
    background: #06b6d4;
    color: white;
  }

  .section {
    animation: fade-in 0.3s ease-in-out;
  }

  @keyframes fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .mix-summary {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .summary-header h3 {
    margin: 0;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .summary-header i {
    color: #06b6d4;
  }

  .total-volume {
    color: #94a3b8;
    font-size: 0.9rem;
  }

  .volume-value {
    color: #06b6d4;
    font-weight: 600;
    font-size: 1.1rem;
  }

  .dispense-summary {
    color: #e2e8f0;
    font-size: 0.95rem;
    line-height: 1.5;
  }

  .no-mix {
    color: #6b7280;
    font-style: italic;
    text-align: center;
    padding: 1rem;
  }

  .overall-progress {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #334155;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .progress-label {
    color: #e2e8f0;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .progress-percent {
    color: #22c55e;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .progress-bar-container {
    height: 12px;
    background: #0f172a;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid #334155;
  }

  .progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #22c55e, #4ade80);
    border-radius: 5px;
    transition: width 0.5s ease;
    animation: pulse-progress 2s infinite;
  }

  @keyframes pulse-progress {
    0%, 100% { box-shadow: 0 0 8px rgba(34, 197, 94, 0.3); }
    50% { box-shadow: 0 0 16px rgba(34, 197, 94, 0.6); }
  }

  .pump-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .pump-card {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 0.75rem;
    padding: 1rem;
    transition: all 0.2s;
  }

  .pump-card.selected {
    border-color: #06b6d4;
    background: #0f2419;
  }

  .pump-card.dispensing {
    border-color: #22c55e;
    background: #0f1f0f;
    animation: pulse-border 2s infinite;
  }

  @keyframes pulse-border {
    0%, 100% { border-color: #22c55e; }
    50% { border-color: #4ade80; }
  }

  .pump-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .pump-name {
    color: #e2e8f0;
    font-weight: 600;
    font-size: 1rem;
  }

  .pump-id {
    color: #94a3b8;
    font-size: 0.8rem;
  }

  .pump-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .voltage {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid;
  }

  .voltage.normal {
    color: #22c55e;
    border-color: #22c55e;
    background: rgba(34, 197, 94, 0.1);
  }

  .voltage.warning {
    color: #f59e0b;
    border-color: #f59e0b;
    background: rgba(245, 158, 11, 0.1);
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .status-indicator.running {
    background: #22c55e;
    animation: pulse 2s infinite;
  }

  .status-indicator.stopped {
    background: #6b7280;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .volume-control {
    margin-bottom: 1rem;
  }

  .volume-control label {
    display: block;
    color: #cbd5e1;
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
  }

  .volume-control input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #475569;
    border-radius: 0.375rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
  }

  .volume-control input:focus {
    outline: none;
    border-color: #06b6d4;
  }

  .pump-progress {
    margin-bottom: 1rem;
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
    font-size: 0.8rem;
    color: #e2e8f0;
  }

  .progress-bar {
    height: 6px;
    background: #0f172a;
    border-radius: 3px;
    overflow: hidden;
    border: 1px solid #334155;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #22c55e, #4ade80);
    border-radius: 2px;
    transition: width 0.3s ease;
  }

  .calibration-status {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .calibration-status.calibrated {
    color: #22c55e;
  }

  .calibration-status.uncalibrated {
    color: #f59e0b;
  }

  .dispense-controls {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  .control-btn {
    padding: 1rem 2rem;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 140px;
    justify-content: center;
  }

  .start-btn {
    background: #22c55e;
    color: white;
  }

  .start-btn:hover:not(:disabled) {
    background: #16a34a;
    transform: translateY(-1px);
  }

  .stop-btn {
    background: #ef4444;
    color: white;
  }

  .stop-btn:hover:not(:disabled) {
    background: #dc2626;
    transform: translateY(-1px);
  }

  .clear-btn {
    background: #6b7280;
    color: white;
  }

  .clear-btn:hover:not(:disabled) {
    background: #4b5563;
    transform: translateY(-1px);
  }

  .control-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  /* Recipe Styles */
  .recipes-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .recipes-header h3 {
    margin: 0;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .add-recipe-btn {
    background: #06b6d4;
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .add-recipe-btn:hover {
    background: #0891b2;
  }

  .add-recipe-btn.active {
    background: #ef4444;
  }

  .add-recipe-form {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .form-row {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .recipe-name-input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #475569;
    border-radius: 0.375rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
  }

  .recipe-name-input:focus {
    outline: none;
    border-color: #06b6d4;
  }

  .save-recipe-btn {
    background: #22c55e;
    color: white;
    border: none;
    border-radius: 0.375rem;
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .save-recipe-btn:hover:not(:disabled) {
    background: #16a34a;
  }

  .save-recipe-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .recipe-help {
    color: #94a3b8;
    font-size: 0.85rem;
    font-style: italic;
  }

  .recipes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1rem;
  }

  .recipe-card {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 0.75rem;
    padding: 1.5rem;
    transition: all 0.2s;
  }

  .recipe-card.selected {
    border-color: #06b6d4;
    background: #0f2419;
  }

  .recipe-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .recipe-info h4 {
    margin: 0 0 0.25rem 0;
    color: #e2e8f0;
    font-size: 1rem;
  }

  .recipe-info p {
    margin: 0;
    color: #94a3b8;
    font-size: 0.85rem;
  }

  .recipe-type {
    padding: 0.25rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .type-veg {
    background: #0f2415;
    color: #22c55e;
    border: 1px solid #22c55e;
  }

  .type-bloom {
    background: #2d0f2d;
    color: #a855f7;
    border: 1px solid #a855f7;
  }

  .type-custom {
    background: #1e3a8a;
    color: #3b82f6;
    border: 1px solid #3b82f6;
  }

  .recipe-ingredients {
    margin-bottom: 1.5rem;
  }

  .ingredient {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.25rem 0;
    border-bottom: 1px solid #334155;
    font-size: 0.85rem;
  }

  .nutrient-name {
    color: #e2e8f0;
  }

  .nutrient-amount {
    color: #06b6d4;
    font-weight: 500;
  }

  .recipe-actions {
    display: flex;
    gap: 0.5rem;
  }

  .recipe-btn {
    flex: 1;
    padding: 0.75rem;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .load-btn {
    background: #06b6d4;
    color: white;
  }

  .load-btn:hover:not(:disabled) {
    background: #0891b2;
  }

  .delete-btn {
    background: #ef4444;
    color: white;
    flex: none;
    width: 40px;
  }

  .delete-btn:hover:not(:disabled) {
    background: #dc2626;
  }

  .recipe-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Mobile Responsiveness */
  @media (max-width: 768px) {
    .nutrients-page {
      padding: 1rem;
    }

    .page-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }

    .section-nav {
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .nav-btn {
      min-width: calc(50% - 0.25rem);
      font-size: 0.8rem;
    }

    .pump-grid {
      grid-template-columns: 1fr;
    }

    .dispense-controls {
      flex-direction: column;
    }

    .control-btn {
      width: 100%;
    }

    .summary-header {
      flex-direction: column;
      gap: 0.5rem;
      align-items: flex-start;
    }

    .form-row {
      flex-direction: column;
    }

    .recipe-name-input {
      width: 100%;
    }
  }
</style>