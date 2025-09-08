# Nutrient Pump Progress Bar Fixes

## Problem Analysis

The progress bars for nutrient pump dispensing are not showing up properly due to several issues:

1. **Data Structure Mismatch**: API response format doesn't match component expectations
2. **Scattered Progress Bar Code**: Multiple implementations instead of reusable component  
3. **Broken Real-time Updates**: Progress updates from `NuteStat` messages not being processed correctly
4. **Conditional Rendering Issues**: Progress bars not appearing when they should

## Required Changes

### 1. Create Reusable Progress Bar Component

**File: `frontend/src/components/NuteDispenseProgress.svelte`**

```svelte
<script>
  // Props with default values
  let {
    pumpId = 0,
    pumpName = 'Unknown Pump',
    currentVolume = 0,
    targetVolume = 0,
    isDispensing = false,
    voltage = 0,
    showVoltage = true,
    size = 'normal', // 'compact', 'normal', 'large'
    theme = 'default' // 'default', 'success', 'warning'
  } = $props();

  // Computed values
  let progress = $derived(() => {
    if (!targetVolume || targetVolume === 0) return 0;
    return Math.min((currentVolume / targetVolume) * 100, 100);
  });

  let progressText = $derived(() => {
    return `${currentVolume.toFixed(1)}ml / ${targetVolume.toFixed(1)}ml`;
  });

  let voltageStatus = $derived(() => {
    if (voltage >= 5.0 && voltage <= 12.0) return 'normal';
    return 'warning';
  });

  let statusText = $derived(() => {
    if (!isDispensing) return 'Ready';
    if (progress >= 100) return 'Complete';
    return 'Dispensing';
  });
</script>

<div class="nute-progress {size} {theme}" class:dispensing={isDispensing}>
  <div class="progress-header">
    <div class="pump-info">
      <span class="pump-name">{pumpName}</span>
      <span class="pump-id">Pump {pumpId}</span>
    </div>
    
    <div class="status-area">
      {#if showVoltage}
        <div class="voltage {voltageStatus}">
          {voltage.toFixed(1)}V
        </div>
      {/if}
      <div class="status-indicator {isDispensing ? 'active' : 'idle'}">
        {statusText}
      </div>
    </div>
  </div>

  {#if isDispensing || progress > 0}
    <div class="progress-section">
      <div class="progress-info">
        <span class="volume-text">{progressText}</span>
        <span class="percentage">{progress.toFixed(1)}%</span>
      </div>
      
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          style="width: {progress}%"
        ></div>
      </div>
      
      {#if isDispensing}
        <div class="pulse-indicator">
          <i class="fas fa-circle"></i>
          <span>Dispensing...</span>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .nute-progress {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s ease;
    position: relative;
  }

  .nute-progress.dispensing {
    border-color: #22c55e;
    background: #0f1f0f;
    box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
    animation: pulse-border 2s infinite;
  }

  @keyframes pulse-border {
    0%, 100% { border-color: #22c55e; }
    50% { border-color: #4ade80; }
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .pump-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
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

  .status-area {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .voltage {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 6px;
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
    font-size: 0.8rem;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 6px;
    transition: all 0.2s;
  }

  .status-indicator.active {
    color: #22c55e;
    background: rgba(34, 197, 94, 0.15);
    animation: pulse-text 2s infinite;
  }

  .status-indicator.idle {
    color: #94a3b8;
    background: rgba(148, 163, 184, 0.1);
  }

  @keyframes pulse-text {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .progress-section {
    margin-top: 12px;
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .volume-text {
    color: #e2e8f0;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .percentage {
    color: #22c55e;
    font-size: 0.85rem;
    font-weight: 700;
  }

  .progress-bar {
    height: 8px;
    background: #0f172a;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #334155;
    position: relative;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #22c55e, #4ade80);
    border-radius: 3px;
    transition: width 0.5s ease;
    position: relative;
  }

  .dispensing .progress-fill {
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
    animation: progress-glow 2s infinite;
  }

  @keyframes progress-glow {
    0%, 100% { 
      box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
    }
    50% { 
      box-shadow: 0 0 20px rgba(34, 197, 94, 0.8);
    }
  }

  .pulse-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
    color: #22c55e;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .pulse-indicator i {
    animation: pulse-dot 1.5s infinite;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
  }
</style>
```

### 2. Fix Main Nutrients.svelte Component

**File: `frontend/src/Nutrients.svelte`**

**Key Changes Needed:**

1. **Import the new progress component:**
```javascript
import NuteDispenseProgress from './components/NuteDispenseProgress.svelte';
```

2. **Fix data structure mapping in fetchSystemStatus():**
```javascript
async function fetchSystemStatus() {
  try {
    const response = await fetch('/api/status');
    if (response.ok) {
      const data = await response.json();
      systemStatus = data;
      
      // Map API response to expected pump structure
      pumps = (data.pumps || []).map(pump => ({
        id: pump.id,
        name: pumpNames[pump.id] || `Pump ${pump.id}`,
        status: pump.is_dispensing ? 'running' : 'stopped',
        voltage: pump.voltage || 0,
        is_dispensing: pump.is_dispensing || false,
        current_volume: pump.current_volume || 0,
        target_volume: pump.target_volume || 0,
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
```

3. **Replace existing progress bar implementation in pump grid:**
```svelte
<!-- In the pump grid section, replace the existing progress bar with: -->
{#each Object.entries(pumpNames) as [pumpId, pumpName]}
  {@const pump = pumps.find(p => p.id == pumpId)}
  {@const isActive = dispensingPumps.has(parseInt(pumpId))}
  {@const amount = dispenseAmounts[pumpId] || 0}
  
  <div class="pump-card {isActive ? 'dispensing' : ''} {amount > 0 ? 'selected' : ''}">
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
    
    <!-- Replace existing progress bar section with the new component -->
    <NuteDispenseProgress
      pumpId={parseInt(pumpId)}
      pumpName={pumpName}
      currentVolume={pump?.current_volume || 0}
      targetVolume={pump?.target_volume || amount}
      isDispensing={pump?.is_dispensing || false}
      voltage={pump?.voltage || 0}
      size="normal"
    />
    
    <!-- Rest of pump card content -->
  </div>
{/each}
```

### 3. Fix PumpControl.svelte Component

**File: `frontend/src/components/PumpControl.svelte`**

**Changes:**
1. Import the new progress component
2. Replace existing progress bar implementation with:

```svelte
<!-- Replace existing progress container with: -->
{#if pump.is_dispensing && pump.current_volume !== undefined && pump.target_volume !== undefined}
  <NuteDispenseProgress
    pumpId={pump.id}
    pumpName={pump.name}
    currentVolume={pump.current_volume}
    targetVolume={pump.target_volume}
    isDispensing={pump.is_dispensing}
    voltage={pump.voltage}
    size="compact"
  />
{/if}
```

### 4. Fix Real-time Data Updates

**In multiple files that fetch system status, ensure this pattern:**

```javascript
// Make sure API endpoint returns proper structure
async function fetchSystemStatus() {
  try {
    const response = await fetch('/api/status');
    if (response.ok) {
      const data = await response.json();
      
      // Ensure pumps array has correct structure for progress bars
      if (data.pumps) {
        // Convert API response to standardized pump objects
        const updatedPumps = Object.entries(data.pumps).map(([pumpId, pumpData]) => ({
          id: parseInt(pumpId),
          name: pumpNames[pumpId] || `Pump ${pumpId}`,
          status: pumpData.is_dispensing ? 'running' : 'stopped',
          voltage: pumpData.voltage || 0,
          is_dispensing: pumpData.is_dispensing || false,
          current_volume: pumpData.current_volume || 0,
          target_volume: pumpData.target_volume || 0,
          calibrated: pumpData.calibrated || false
        }));
        
        pumps = updatedPumps;
      }
    }
  } catch (error) {
    console.error('Failed to fetch status:', error);
  }
}
```

### 5. Backend API Verification

**Ensure the Flask API (`app.py`) returns the correct structure:**

```python
# In the /api/status endpoint, ensure pump data includes:
pump_status = {
    "pumps": {
        str(pump_id): {
            "id": pump_id,
            "is_dispensing": pump_info.get('is_dispensing', False),
            "current_volume": pump_info.get('current_volume', 0),
            "target_volume": pump_info.get('target_volume', 0),
            "voltage": pump_info.get('voltage', 0),
            "calibrated": pump_info.get('calibrated', False)
        }
        for pump_id, pump_info in all_pump_status.items()
    }
}
```

### 6. Handle NuteStat Updates

**Ensure the main.py properly sends NuteStat updates:**

```python
# In hardware_comms.py or main.py, when processing NuteStat messages:
def _handle_nute_stat_update(self, parts):
    """Handle: Start;Update;NuteStat;5;ON;281.67;500.00;end"""
    if len(parts) >= 7:
        pump_id = int(parts[3])
        status = parts[4]  # "ON" or "OFF"
        current_volume = float(parts[5])
        target_volume = float(parts[6])
        
        # Update pump info that will be returned by /api/status
        if pump_id in self.pump_status:
            self.pump_status[pump_id].update({
                'current_volume': current_volume,
                'target_volume': target_volume,
                'is_dispensing': status == "ON"
            })
```

## Testing the Fixes

1. **Start a nutrient dispense operation**
2. **Verify progress bars appear** in both Nutrients.svelte and any other components
3. **Check real-time updates** - progress should update every second based on NuteStat messages
4. **Test multiple pumps** dispensing simultaneously
5. **Verify completion** - progress bars should show 100% and stop animating when done

## Expected Behavior After Fixes

- Progress bars will show up immediately when dispensing starts
- Real-time updates every second showing current/target volume and percentage
- Smooth animations and visual feedback during dispensing
- Consistent progress bar appearance across all components
- Proper completion state when target volume is reached

## Key Files to Modify

1. `frontend/src/components/NuteDispenseProgress.svelte` (new file)
2. `frontend/src/Nutrients.svelte` (import and use new component)
3. `frontend/src/components/PumpControl.svelte` (replace progress bar)
4. `frontend/src/Dashboard.svelte` (update status mapping)
5. `app.py` (verify API response structure)
6. `hardware_comms.py` or `main.py` (ensure proper NuteStat handling)

The main issue was the mismatch between what the progress bar components expected (`current_volume`, `target_volume`, `is_dispensing`) and what the API was actually providing. This comprehensive fix ensures consistent data structures throughout the application.