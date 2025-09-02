<script>
  import { onMount } from 'svelte';
  
  let config = $state({});
  let loading = $state(true);
  let saving = $state(false);
  let activeSection = $state('user');
  
  // User settings - organized for easy editing
  let userSettings = $state({
    tanks: {},
    pumps: {
      names: {},
      addresses: {}
    },
    nutrients: {
      veg_formula: {},
      bloom_formula: {},
      pump_name_to_id: {}
    },
    formulas: {},
    timing: {
      status_update_interval: 2.0,
      pump_check_interval: 1.0,
      flow_update_interval: 0.5
    },
    limits: {
      max_pump_volume_ml: 2500.0,
      min_pump_volume_ml: 0.5,
      max_flow_gallons: 100
    }
  });

  // Available nutrients from pump names
  let availableNutrients = $derived(() => {
    return Object.keys(userSettings.pumps.names || {}).map(id => userSettings.pumps.names[id]);
  });

  // Available relays for mix relay selection
  let availableRelays = $derived(() => {
    return Object.keys(devSettings.gpio.relay_pins || {}).map(Number).sort((a, b) => a - b);
  });
  
  // Dev settings - technical configurations
  let devSettings = $state({
    gpio: {
      relay_pins: {},
      flow_meter_pins: {}
    },
    i2c: {
      bus_number: 1,
      pump_addresses: {},
      command_delay: 0.3
    },
    communication: {
      command_start: "Start",
      command_end: "end",
      arduino_baudrate: 115200
    },
    mock: {},
    debug: {
      debug_mode: false,
      verbose_logging: false,
      log_level: "INFO"
    }
  });

  onMount(async () => {
    try {
      await loadConfig();
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      loading = false;
    }
  });
  
  async function loadConfig() {
    const response = await fetch('/api/config');
    if (response.ok) {
      config = await response.json();
      organizeSettings();
    } else {
      throw new Error('Failed to load configuration');
    }
  }
  
  function organizeSettings() {
    // Organize user-friendly settings
    userSettings.tanks = config.TANKS || {};
    userSettings.pumps = {
      names: config.PUMP_NAMES || {},
      addresses: config.PUMP_ADDRESSES || {}
    };
    userSettings.nutrients = {
      veg_formula: config.VEG_FORMULA || {},
      bloom_formula: config.BLOOM_FORMULA || {},
      pump_name_to_id: config.PUMP_NAME_TO_ID || {}
    };
    userSettings.formulas = config.FORMULA_TARGETS || {};
    userSettings.timing = {
      status_update_interval: config.STATUS_UPDATE_INTERVAL || 2.0,
      pump_check_interval: config.PUMP_CHECK_INTERVAL || 1.0,
      flow_update_interval: config.FLOW_UPDATE_INTERVAL || 0.5
    };
    userSettings.limits = {
      max_pump_volume_ml: config.MAX_PUMP_VOLUME_ML || 2500.0,
      min_pump_volume_ml: config.MIN_PUMP_VOLUME_ML || 0.5,
      max_flow_gallons: config.MAX_FLOW_GALLONS || 100
    };
    
    // Organize development settings
    devSettings.gpio = {
      relay_pins: config.RELAY_GPIO_PINS || {},
      flow_meter_pins: config.FLOW_METER_GPIO_PINS || {}
    };
    devSettings.i2c = {
      bus_number: config.I2C_BUS_NUMBER || 1,
      pump_addresses: config.PUMP_ADDRESSES || {},
      command_delay: config.EZO_COMMAND_DELAY || 0.3
    };
    devSettings.communication = {
      command_start: config.COMMAND_START || "Start",
      command_end: config.COMMAND_END || "end",
      arduino_baudrate: config.ARDUINO_UNO_BAUDRATE || 115200
    };
    devSettings.mock = config.MOCK_SETTINGS || {};
    devSettings.debug = {
      debug_mode: config.DEBUG_MODE || false,
      verbose_logging: config.VERBOSE_LOGGING || false,
      log_level: config.LOG_LEVEL || "INFO"
    };
  }
  
  async function saveConfig() {
    if (saving) return;
    saving = true;
    
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userSettings,
          devSettings
        })
      });
      
      if (response.ok) {
        // Show success message
        console.log('Settings saved successfully');
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Error saving settings. Please try again.');
    } finally {
      saving = false;
    }
  }
  
  function addTank() {
    const newId = Math.max(...Object.keys(userSettings.tanks).map(Number), 0) + 1;
    userSettings.tanks[newId] = {
      name: `Tank ${newId}`,
      capacity_gallons: 100,
      fill_relay: 0,
      mix_relays: [],
      send_relay: 0
    };
  }
  
  function removeTank(tankId) {
    delete userSettings.tanks[tankId];
    userSettings.tanks = { ...userSettings.tanks };
  }
  
  function addNutrient(formulaType) {
    const formula = formulaType === 'veg' ? userSettings.nutrients.veg_formula : userSettings.nutrients.bloom_formula;
    // Find the first available nutrient that's not already in the formula
    const availableOptions = availableNutrients.filter(nutrient => !formula.hasOwnProperty(nutrient));
    if (availableOptions.length > 0) {
      formula[availableOptions[0]] = 0.0;
    }
  }
  
  function removeNutrient(formulaType, nutrientName) {
    const formula = formulaType === 'veg' ? userSettings.nutrients.veg_formula : userSettings.nutrients.bloom_formula;
    delete formula[nutrientName];
  }

  function addMixRelay(tankId) {
    const tank = userSettings.tanks[tankId];
    if (!tank.mix_relays) {
      tank.mix_relays = [];
    }
    // Find the first available relay that's not already used
    const usedRelays = tank.mix_relays;
    const availableOptions = availableRelays.filter(relay => !usedRelays.includes(relay));
    if (availableOptions.length > 0) {
      tank.mix_relays.push(availableOptions[0]);
    }
  }

  function removeMixRelay(tankId, index) {
    const tank = userSettings.tanks[tankId];
    if (tank.mix_relays) {
      tank.mix_relays.splice(index, 1);
      // Trigger reactivity
      userSettings.tanks = { ...userSettings.tanks };
    }
  }
</script>

<div class="settings-container">
  <header class="settings-header">
    <h1>System Settings</h1>
    <p>Configure your nutrient mixing system parameters</p>
  </header>
  
  {#if loading}
    <div class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      Loading configuration...
    </div>
  {:else}
    <!-- Section Navigation -->
    <div class="section-nav">
      <button 
        class="section-tab {activeSection === 'user' ? 'active' : ''}"
        onclick={() => activeSection = 'user'}
      >
        <i class="fas fa-user-cog"></i>
        User Settings
      </button>
      <button 
        class="section-tab {activeSection === 'dev' ? 'active' : ''}"
        onclick={() => activeSection = 'dev'}
      >
        <i class="fas fa-code"></i>
        Development Settings
      </button>
    </div>

    <!-- User Settings Section -->
    {#if activeSection === 'user'}
      <div class="settings-section">
        
        <!-- Tank Configuration -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-water"></i> Tank Configuration</h3>
            <button class="btn btn-secondary" onclick={addTank}>
              <i class="fas fa-plus"></i> Add Tank
            </button>
          </div>
          <div class="tanks-grid">
            {#each Object.entries(userSettings.tanks) as [tankId, tank]}
              <div class="tank-card">
                <div class="tank-header">
                  <h4>Tank {tankId}</h4>
                  <button class="btn-remove" onclick={() => removeTank(tankId)} aria-label="Remove Tank {tankId}">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
                <div class="form-row">
                  <label for="tank-{tankId}-name">Name:</label>
                  <input id="tank-{tankId}-name" type="text" bind:value={tank.name} />
                </div>
                <div class="form-row">
                  <label for="tank-{tankId}-capacity">Capacity (gallons):</label>
                  <input id="tank-{tankId}-capacity" type="number" bind:value={tank.capacity_gallons} />
                </div>
                <div class="form-row">
                  <label for="tank-{tankId}-fill-relay">Fill Relay:</label>
                  <input id="tank-{tankId}-fill-relay" type="number" bind:value={tank.fill_relay} />
                </div>
                <div class="form-row">
                  <label for="tank-{tankId}-send-relay">Send Relay:</label>
                  <input id="tank-{tankId}-send-relay" type="number" bind:value={tank.send_relay} />
                </div>
                <div class="form-row">
                  <label>Mix Relays:</label>
                  <div class="mix-relays-container">
                    {#if tank.mix_relays && tank.mix_relays.length > 0}
                      {#each tank.mix_relays as relay, index}
                        <div class="mix-relay-item">
                          <select bind:value={tank.mix_relays[index]}>
                            {#each availableRelays as relayOption}
                              <option value={relayOption}>{relayOption}</option>
                            {/each}
                          </select>
                          <button class="btn-remove" onclick={() => removeMixRelay(tankId, index)} aria-label="Remove mix relay">
                            <i class="fas fa-times"></i>
                          </button>
                        </div>
                      {/each}
                    {:else}
                      <div class="no-mix-relays">No mix relays configured</div>
                    {/if}
                    <button class="btn btn-secondary btn-sm" onclick={() => addMixRelay(tankId)}>
                      <i class="fas fa-plus"></i> Add Mix Relay
                    </button>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
        
        <!-- Pump Configuration -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-tint"></i> Pump Configuration</h3>
          </div>
          <div class="pumps-grid">
            {#each Object.entries(userSettings.pumps.names) as [pumpId, name]}
              <div class="pump-card">
                <div class="form-row">
                  <label for="pump-{pumpId}-name">Pump {pumpId}:</label>
                  <input id="pump-{pumpId}-name" type="text" bind:value={userSettings.pumps.names[pumpId]} />
                </div>
              </div>
            {/each}
          </div>
        </div>
        
        <!-- Nutrient Formulas -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-flask"></i> Nutrient Formulas</h3>
          </div>
          <div class="formulas-container">
            <!-- VEG Formula -->
            <div class="formula-section">
              <div class="formula-header">
                <h4>VEG Formula (ml/gallon)</h4>
                <button class="btn btn-secondary" onclick={() => addNutrient('veg')}>
                  <i class="fas fa-plus"></i> Add Nutrient
                </button>
              </div>
              {#each Object.entries(userSettings.nutrients.veg_formula) as [nutrient, amount]}
                <div class="nutrient-row">
                  <select bind:value={userSettings.nutrients.veg_formula[nutrient]} style="display: none;">
                    {#each availableNutrients as nutrientOption}
                      <option value={nutrientOption}>{nutrientOption}</option>
                    {/each}
                  </select>
                  <span class="nutrient-name">{nutrient}</span>
                  <input type="number" step="0.1" bind:value={userSettings.nutrients.veg_formula[nutrient]} />
                  <span class="nutrient-unit">ml/gal</span>
                  <button class="btn-remove" onclick={() => removeNutrient('veg', nutrient)} aria-label="Remove {nutrient} from VEG formula">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              {/each}
            </div>
            
            <!-- BLOOM Formula -->
            <div class="formula-section">
              <div class="formula-header">
                <h4>BLOOM Formula (ml/gallon)</h4>
                <button class="btn btn-secondary" onclick={() => addNutrient('bloom')}>
                  <i class="fas fa-plus"></i> Add Nutrient
                </button>
              </div>
              {#each Object.entries(userSettings.nutrients.bloom_formula) as [nutrient, amount]}
                <div class="nutrient-row">
                  <select bind:value={userSettings.nutrients.bloom_formula[nutrient]} style="display: none;">
                    {#each availableNutrients as nutrientOption}
                      <option value={nutrientOption}>{nutrientOption}</option>
                    {/each}
                  </select>
                  <span class="nutrient-name">{nutrient}</span>
                  <input type="number" step="0.1" bind:value={userSettings.nutrients.bloom_formula[nutrient]} />
                  <span class="nutrient-unit">ml/gal</span>
                  <button class="btn-remove" onclick={() => removeNutrient('bloom', nutrient)} aria-label="Remove {nutrient} from BLOOM formula">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              {/each}
            </div>
          </div>
        </div>
        
        <!-- System Timing -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-clock"></i> System Timing</h3>
          </div>
          <div class="timing-grid">
            <div class="form-row">
              <label for="status-update-interval">Status Update Interval (seconds):</label>
              <input id="status-update-interval" type="number" step="0.1" bind:value={userSettings.timing.status_update_interval} />
            </div>
            <div class="form-row">
              <label for="pump-check-interval">Pump Check Interval (seconds):</label>
              <input id="pump-check-interval" type="number" step="0.1" bind:value={userSettings.timing.pump_check_interval} />
            </div>
            <div class="form-row">
              <label for="flow-update-interval">Flow Update Interval (seconds):</label>
              <input id="flow-update-interval" type="number" step="0.1" bind:value={userSettings.timing.flow_update_interval} />
            </div>
          </div>
        </div>
        
        <!-- Safety Limits -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-shield-alt"></i> Safety Limits</h3>
          </div>
          <div class="limits-grid">
            <div class="form-row">
              <label for="max-pump-volume">Max Pump Volume (ml):</label>
              <input id="max-pump-volume" type="number" step="0.1" bind:value={userSettings.limits.max_pump_volume_ml} />
            </div>
            <div class="form-row">
              <label for="min-pump-volume">Min Pump Volume (ml):</label>
              <input id="min-pump-volume" type="number" step="0.1" bind:value={userSettings.limits.min_pump_volume_ml} />
            </div>
            <div class="form-row">
              <label for="max-flow-gallons">Max Flow (gallons):</label>
              <input id="max-flow-gallons" type="number" bind:value={userSettings.limits.max_flow_gallons} />
            </div>
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Development Settings Section -->
    {#if activeSection === 'dev'}
      <div class="settings-section">
        
        <!-- GPIO Configuration -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-microchip"></i> GPIO Configuration</h3>
          </div>
          <div class="gpio-container">
            <div class="gpio-section">
              <h4>Relay GPIO Pins</h4>
              {#each Object.entries(devSettings.gpio.relay_pins) as [relayId, pin]}
                <div class="gpio-row">
                  <label for="relay-{relayId}-pin">Relay {relayId}:</label>
                  <input id="relay-{relayId}-pin" type="number" bind:value={devSettings.gpio.relay_pins[relayId]} />
                </div>
              {/each}
            </div>
            
            <div class="gpio-section">
              <h4>Flow Meter GPIO Pins</h4>
              {#each Object.entries(devSettings.gpio.flow_meter_pins) as [meterId, pin]}
                <div class="gpio-row">
                  <label for="flow-meter-{meterId}-pin">Flow Meter {meterId}:</label>
                  <input id="flow-meter-{meterId}-pin" type="number" bind:value={devSettings.gpio.flow_meter_pins[meterId]} />
                </div>
              {/each}
            </div>
          </div>
        </div>
        
        <!-- I2C Configuration -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-ethernet"></i> I2C Configuration</h3>
          </div>
          <div class="i2c-grid">
            <div class="form-row">
              <label for="i2c-bus-number">I2C Bus Number:</label>
              <input id="i2c-bus-number" type="number" bind:value={devSettings.i2c.bus_number} />
            </div>
            <div class="form-row">
              <label for="ezo-command-delay">EZO Command Delay (seconds):</label>
              <input id="ezo-command-delay" type="number" step="0.01" bind:value={devSettings.i2c.command_delay} />
            </div>
          </div>
        </div>
        
        <!-- Mock Settings -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-test-tube"></i> Mock Hardware Settings</h3>
          </div>
          <div class="mock-grid">
            {#each Object.entries(devSettings.mock) as [component, enabled]}
              <div class="checkbox-row">
                <label>
                  <input type="checkbox" bind:checked={devSettings.mock[component]} />
                  Mock {component}
                </label>
              </div>
            {/each}
          </div>
        </div>
        
        <!-- Debug Settings -->
        <div class="settings-group">
          <div class="group-header">
            <h3><i class="fas fa-bug"></i> Debug Settings</h3>
          </div>
          <div class="debug-grid">
            <div class="checkbox-row">
              <label>
                <input type="checkbox" bind:checked={devSettings.debug.debug_mode} />
                Debug Mode
              </label>
            </div>
            <div class="checkbox-row">
              <label>
                <input type="checkbox" bind:checked={devSettings.debug.verbose_logging} />
                Verbose Logging
              </label>
            </div>
            <div class="form-row">
              <label for="log-level">Log Level:</label>
              <select id="log-level" bind:value={devSettings.debug.log_level}>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Save Button -->
    <div class="save-section">
      <button 
        class="btn btn-primary save-btn {saving ? 'saving' : ''}" 
        onclick={saveConfig}
        disabled={saving}
      >
        {#if saving}
          <i class="fas fa-spinner fa-spin"></i>
          Saving...
        {:else}
          <i class="fas fa-save"></i>
          Save Settings
        {/if}
      </button>
    </div>
  {/if}
</div>

<style>
  .settings-container {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    background: #1a1a1a;
    color: white;
    min-height: calc(100vh - 4rem);
    overflow-y: auto;
    position: relative;
  }
  
  .settings-header {
    text-align: center;
    margin-bottom: 2rem;
  }
  
  .settings-header h1 {
    color: #06b6d4;
    margin: 0 0 0.5rem 0;
  }
  
  .settings-header p {
    color: #94a3b8;
    margin: 0;
  }
  
  .loading {
    text-align: center;
    padding: 4rem;
    color: #94a3b8;
  }
  
  .section-nav {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    justify-content: center;
  }
  
  .section-tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 2rem;
    border: none;
    border-radius: 0.5rem;
    background: #0f172a;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #334155;
  }
  
  .section-tab:hover {
    background: #1e293b;
    color: #e2e8f0;
  }
  
  .section-tab.active {
    background: #0f2419;
    color: #06b6d4;
    border-color: #06b6d4;
  }
  
  .settings-section {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .settings-group {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 1.5rem;
  }
  
  .group-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }
  
  .group-header h3 {
    color: #e2e8f0;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .tanks-grid, .pumps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
  }
  
  .tank-card, .pump-card {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 0.375rem;
    padding: 1rem;
  }
  
  .tank-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .tank-header h4 {
    margin: 0;
    color: #06b6d4;
  }
  
  .form-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }
  
  .form-row label {
    min-width: 120px;
    color: #cbd5e1;
    font-size: 0.9rem;
  }
  
  input[type="text"], input[type="number"], select {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #475569;
    border-radius: 0.25rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
  }
  
  input:focus, select:focus {
    outline: none;
    border-color: #06b6d4;
  }
  
  .formulas-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  
  .formula-section {
    background: #1e293b;
    border-radius: 0.375rem;
    padding: 1rem;
  }
  
  .formula-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .formula-header h4 {
    margin: 0;
    color: #06b6d4;
  }
  
  .nutrient-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .nutrient-row .nutrient-name {
    flex: 1;
    color: #e2e8f0;
    font-weight: 500;
    padding: 0.5rem;
    background: #475569;
    border-radius: 0.25rem;
    border: 1px solid #64748b;
  }
  
  .nutrient-row input[type="number"] {
    width: 80px;
  }

  .nutrient-row .nutrient-unit {
    color: #94a3b8;
    font-size: 0.85rem;
    min-width: 40px;
  }

  .mix-relays-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  .mix-relay-item {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .mix-relay-item select {
    flex: 1;
  }

  .no-mix-relays {
    color: #94a3b8;
    font-style: italic;
    padding: 0.5rem;
  }

  .btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
  }
  
  .timing-grid, .limits-grid, .i2c-grid, .debug-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  
  .gpio-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  
  .gpio-section {
    background: #1e293b;
    border-radius: 0.375rem;
    padding: 1rem;
  }
  
  .gpio-section h4 {
    margin: 0 0 1rem 0;
    color: #06b6d4;
  }
  
  .gpio-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }
  
  .gpio-row label {
    min-width: 100px;
    color: #cbd5e1;
    font-size: 0.9rem;
  }
  
  .gpio-row input {
    width: 80px;
  }
  
  .mock-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .checkbox-row {
    display: flex;
    align-items: center;
  }
  
  .checkbox-row label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #cbd5e1;
    cursor: pointer;
  }
  
  input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: #06b6d4;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .btn-primary {
    background: #06b6d4;
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #0891b2;
  }
  
  .btn-secondary {
    background: #475569;
    color: white;
  }
  
  .btn-secondary:hover {
    background: #64748b;
  }
  
  .btn-remove {
    background: #dc2626;
    color: white;
    padding: 0.25rem 0.5rem;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    font-size: 0.8rem;
  }
  
  .btn-remove:hover {
    background: #b91c1c;
  }
  
  .save-section {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
  }
  
  .save-btn {
    padding: 1rem 3rem;
    font-size: 1rem;
    font-weight: 600;
  }
  
  .save-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  @media (max-width: 768px) {
    .settings-container {
      padding: 1rem;
    }
    
    .section-nav {
      flex-direction: column;
      align-items: center;
    }
    
    .section-tab {
      width: 200px;
      justify-content: center;
    }
    
    .formulas-container,
    .timing-grid,
    .limits-grid,
    .i2c-grid,
    .debug-grid,
    .gpio-container {
      grid-template-columns: 1fr;
    }
    
    .tanks-grid,
    .pumps-grid {
      grid-template-columns: 1fr;
    }
    
    .form-row {
      flex-direction: column;
      align-items: stretch;
      gap: 0.5rem;
    }
    
    .form-row label {
      min-width: auto;
    }
  }
</style>