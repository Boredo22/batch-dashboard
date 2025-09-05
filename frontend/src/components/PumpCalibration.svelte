<script>
  let selectedPumpNumber = $state(1);
  let targetML = $state(10);
  let actualML = $state('');
  let calibrationStatus = $state('idle'); // idle, dispensing, measuring, calibrating, complete
  let statusMessage = $state('');
  let calibrationStatusInfo = $state(null);
  let isCheckingStatus = $state(false);
  let currentVolumeInfo = $state(null);
  let volumeCheckInterval = $state(null);
  
  // Convert pump number (1-8) to i2c address (11-18)
  let selectedPump = $derived(() => {
    return (selectedPumpNumber + 10).toString();
  });
  
  // Get pump name for display
  let selectedPumpName = $derived(() => {
    return `Pump ${selectedPumpNumber}`;
  });
  
  async function startCalibration() {
    if (!selectedPumpNumber || selectedPumpNumber < 1 || selectedPumpNumber > 8 || !targetML) {
      statusMessage = 'Please select a pump (1-8) and target volume';
      return;
    }
    
    calibrationStatus = 'dispensing';
    statusMessage = `Dispensing ${targetML}ml from ${selectedPumpName}...`;
    startVolumeMonitoring();
    
    try {
      const response = await fetch(`/api/pumps/${selectedPumpNumber}/dispense`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: targetML
        })
      });
      
      if (response.ok) {
        calibrationStatus = 'measuring';
        statusMessage = `Dispensing complete. Please measure the actual amount dispensed and enter it below.`;
        stopVolumeMonitoring();
      } else {
        throw new Error('Failed to dispense');
      }
    } catch (error) {
      calibrationStatus = 'idle';
      statusMessage = `Error during dispensing: ${error.message}`;
      stopVolumeMonitoring();
    }
  }
  
  async function completeCalibration() {
    if (!actualML || actualML <= 0) {
      statusMessage = 'Please enter the actual measured volume';
      return;
    }
    
    calibrationStatus = 'calibrating';
    statusMessage = `Calibrating pump with actual volume: ${actualML}ml...`;
    
    try {
      const response = await fetch(`/api/pumps/${selectedPumpNumber}/calibrate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_volume: targetML,
          actual_volume: actualML
        })
      });
      
      if (response.ok) {
        calibrationStatus = 'complete';
        statusMessage = `Calibration complete! ${selectedPumpName} is now calibrated.`;
        setTimeout(resetCalibration, 3000);
      } else {
        throw new Error('Failed to calibrate');
      }
    } catch (error) {
      calibrationStatus = 'idle';
      statusMessage = `Error during calibration: ${error.message}`;
    }
  }
  
  function resetCalibration() {
    calibrationStatus = 'idle';
    statusMessage = '';
    actualML = '';
  }
  
  function cancelCalibration() {
    calibrationStatus = 'idle';
    statusMessage = '';
    actualML = '';
  }

  // Check calibration status
  async function checkCalibrationStatus() {
    isCheckingStatus = true;
    try {
      const response = await fetch(`/api/pumps/${selectedPumpNumber}/calibration/status`);
      const data = await response.json();
      calibrationStatusInfo = data;
    } catch (error) {
      statusMessage = `Error checking calibration status: ${error.message}`;
    }
    isCheckingStatus = false;
  }

  // Clear calibration
  async function clearCalibration() {
    try {
      const response = await fetch(`/api/pumps/${selectedPumpNumber}/calibration/clear`, {
        method: 'POST'
      });
      
      if (response.ok) {
        statusMessage = 'Calibration cleared successfully';
        await checkCalibrationStatus();
      } else {
        throw new Error('Failed to clear calibration');
      }
    } catch (error) {
      statusMessage = `Error clearing calibration: ${error.message}`;
    }
  }

  // Monitor current volume during dispensing
  function startVolumeMonitoring() {
    if (volumeCheckInterval) clearInterval(volumeCheckInterval);
    
    volumeCheckInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/pumps/${selectedPumpNumber}/volume`);
        const data = await response.json();
        currentVolumeInfo = data;
      } catch (error) {
        console.error('Error monitoring volume:', error);
      }
    }, 1000);
  }

  function stopVolumeMonitoring() {
    if (volumeCheckInterval) {
      clearInterval(volumeCheckInterval);
      volumeCheckInterval = null;
    }
  }

  // Pause pump
  async function pausePump() {
    try {
      const response = await fetch(`/api/pumps/${selectedPumpNumber}/pause`, {
        method: 'POST'
      });
      
      if (response.ok) {
        statusMessage = 'Pump paused - dispense same command again to resume';
      } else {
        throw new Error('Failed to pause pump');
      }
    } catch (error) {
      statusMessage = `Error pausing pump: ${error.message}`;
    }
  }

  // Call checkCalibrationStatus when component mounts or pump changes
  $effect(() => {
    if (selectedPumpNumber) {
      checkCalibrationStatus();
    }
  });

  // Clean up interval on component unmount
  $effect(() => {
    return () => {
      stopVolumeMonitoring();
    };
  });
</script>

<div class="calibration-container">
  <div class="calibration-header">
    <h4><i class="fas fa-ruler"></i> Pump Calibration</h4>
    <p class="calibration-description">
      Calibrate pumps for accurate dispensing. Use water for calibration, not chemicals.
    </p>
  </div>
  
  <div class="calibration-form">
    <!-- Pump Selection -->
    <div class="form-row">
      <label for="pump-number">Select Pump (1-8):</label>
      <input
        id="pump-number"
        type="number"
        min="1"
        max="8"
        step="1"
        bind:value={selectedPumpNumber}
        disabled={calibrationStatus !== 'idle'}
        placeholder="Enter pump number"
      />
      <span class="pump-info">
        {#if selectedPumpNumber >= 1 && selectedPumpNumber <= 8}
          → {selectedPumpName} (I2C: {selectedPump})
        {/if}
      </span>
    </div>
    
    <!-- Target Volume -->
    <div class="form-row">
      <label for="target-ml">Target Volume (ml):</label>
      <input 
        id="target-ml"
        type="number" 
        min="1" 
        max="100" 
        step="0.1"
        bind:value={targetML}
        disabled={calibrationStatus !== 'idle'}
      />
    </div>
  </div>
  
  <!-- Calibration Status Info -->
  {#if calibrationStatusInfo}
    <div class="status-info">
      <div class="status-row">
        <span class="status-label">Calibration Status:</span>
        <span class="status-value status-{calibrationStatusInfo.calibration_status}">
          {calibrationStatusInfo.calibration_status || 'unknown'}
        </span>
      </div>
      {#if !isCheckingStatus}
        <div class="status-actions">
          <button class="btn btn-small btn-secondary" onclick={clearCalibration}>
            <i class="fas fa-trash" aria-hidden="true"></i>
            Clear Calibration
          </button>
        </div>
      {/if}
    </div>
  {/if}
  
  <!-- Real-time Volume Display -->
  {#if currentVolumeInfo && calibrationStatus === 'dispensing'}
    <div class="volume-monitor">
      <div class="volume-display">
        <span class="volume-label">Current Volume:</span>
        <span class="volume-value">
          {currentVolumeInfo.success ? `${currentVolumeInfo.current_volume}ml` : 'Error'}
        </span>
      </div>
      <button class="btn btn-small btn-warning" onclick={pausePump}>
        <i class="fas fa-pause" aria-hidden="true"></i>
        Pause
      </button>
    </div>
  {/if}
  
  <!-- Calibration Steps -->
  <div class="calibration-steps">
    <div class="step {calibrationStatus === 'dispensing' || calibrationStatus === 'measuring' || calibrationStatus === 'calibrating' || calibrationStatus === 'complete' ? 'active' : ''}">
      <div class="step-number">1</div>
      <div class="step-content">
        <h5>Dispense Water</h5>
        <p>Place a graduated cylinder or beaker on a scale and click "Start Calibration"</p>
      </div>
    </div>
    
    <div class="step {calibrationStatus === 'measuring' || calibrationStatus === 'calibrating' || calibrationStatus === 'complete' ? 'active' : ''}">
      <div class="step-number">2</div>
      <div class="step-content">
        <h5>Measure Actual Volume</h5>
        <p>Measure the actual amount dispensed and enter it below</p>
        {#if calibrationStatus === 'measuring'}
          <div class="measurement-input">
            <input
              type="number"
              step="0.1"
              min="0"
              bind:value={actualML}
              placeholder="Actual ml dispensed"
              aria-label="Enter actual volume dispensed in milliliters"
            />
            <span class="unit">ml</span>
          </div>
        {/if}
      </div>
    </div>
    
    <div class="step {calibrationStatus === 'calibrating' || calibrationStatus === 'complete' ? 'active' : ''}">
      <div class="step-number">3</div>
      <div class="step-content">
        <h5>Complete Calibration</h5>
        <p>The pump will be calibrated with the measured volume</p>
      </div>
    </div>
  </div>
  
  <!-- Status Message -->
  {#if statusMessage}
    <div class="status-message {calibrationStatus === 'complete' ? 'success' : calibrationStatus.includes('error') ? 'error' : 'info'}">
      <i class="fas fa-{calibrationStatus === 'complete' ? 'check-circle' : calibrationStatus === 'dispensing' || calibrationStatus === 'calibrating' ? 'spinner fa-spin' : 'info-circle'}"></i>
      {statusMessage}
    </div>
  {/if}
  
  <!-- Action Buttons -->
  <div class="calibration-actions">
    {#if calibrationStatus === 'idle'}
      <button
        class="btn btn-primary"
        onclick={startCalibration}
        disabled={!selectedPumpNumber || selectedPumpNumber < 1 || selectedPumpNumber > 8 || !targetML}
        aria-label="Start pump calibration process"
      >
        <i class="fas fa-play" aria-hidden="true"></i>
        Start Calibration
      </button>
    {:else if calibrationStatus === 'measuring'}
      <button
        class="btn btn-success"
        onclick={completeCalibration}
        disabled={!actualML}
        aria-label="Complete calibration with measured volume"
      >
        <i class="fas fa-check" aria-hidden="true"></i>
        Complete Calibration
      </button>
      <button
        class="btn btn-secondary"
        onclick={cancelCalibration}
        aria-label="Cancel calibration process"
      >
        <i class="fas fa-times" aria-hidden="true"></i>
        Cancel
      </button>
    {:else if calibrationStatus === 'dispensing' || calibrationStatus === 'calibrating'}
      <button class="btn btn-secondary" disabled aria-label="Calibration in progress">
        <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
        Processing...
      </button>
    {/if}
  </div>
  
  <!-- Calibration Tips -->
  <div class="calibration-tips">
    <h5><i class="fas fa-lightbulb"></i> Calibration Tips</h5>
    <ul>
      <li>Always use water for calibration, never chemicals</li>
      <li>Ensure tubing is full of water with no air bubbles</li>
      <li>Use a graduated cylinder or precise scale for measurement</li>
      <li>Recommended calibration volume: 10ml for accuracy</li>
      <li>Recalibrate periodically to maintain accuracy</li>
    </ul>
  </div>
</div>

<style>
  .calibration-container {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 0.5rem;
    padding: 1.5rem;
  }
  
  .calibration-header {
    margin-bottom: 1.5rem;
  }
  
  .calibration-header h4 {
    margin: 0 0 0.5rem 0;
    color: #06b6d4;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .calibration-description {
    color: #94a3b8;
    margin: 0;
    font-size: 0.9rem;
  }
  
  .calibration-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .form-row {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .form-row label {
    min-width: 140px;
    color: #cbd5e1;
    font-size: 0.9rem;
  }
  
  input[type="number"] {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #475569;
    border-radius: 0.25rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
  }
  
  input[type="number"]:focus {
    outline: none;
    border-color: #06b6d4;
  }
  
  input[type="number"]:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .pump-info {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-left: 0.5rem;
    white-space: nowrap;
  }
  
  .status-info {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .status-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }
  
  .status-label {
    color: #cbd5e1;
    font-size: 0.9rem;
    min-width: 140px;
  }
  
  .status-value {
    padding: 0.25rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: capitalize;
  }
  
  .status-uncalibrated {
    background: #2d0f0f;
    color: #ef4444;
  }
  
  .status-single_point, .status-volume_calibrated, .status-fully_calibrated {
    background: #0f2415;
    color: #10b981;
  }
  
  .status-unknown {
    background: #1f2937;
    color: #9ca3af;
  }
  
  .status-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .volume-monitor {
    background: #0f2419;
    border: 1px solid #06b6d4;
    border-radius: 0.375rem;
    padding: 1rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .volume-display {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .volume-label {
    color: #06b6d4;
    font-size: 0.9rem;
  }
  
  .volume-value {
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
  }
  
  .calibration-steps {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .step {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    opacity: 0.6;
    transition: all 0.3s;
  }
  
  .step.active {
    opacity: 1;
    border-color: #06b6d4;
    background: #0f2419;
  }
  
  .step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #334155;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    flex-shrink: 0;
  }
  
  .step.active .step-number {
    background: #06b6d4;
  }
  
  .step-content h5 {
    margin: 0 0 0.5rem 0;
    color: #e2e8f0;
    font-size: 0.95rem;
  }
  
  .step-content p {
    margin: 0;
    color: #94a3b8;
    font-size: 0.85rem;
  }
  
  .measurement-input {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }
  
  .measurement-input input {
    width: 120px;
    flex: none;
  }
  
  .unit {
    color: #94a3b8;
    font-size: 0.9rem;
  }
  
  .status-message {
    padding: 1rem;
    border-radius: 0.375rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }
  
  .status-message.info {
    background: #0f2419;
    color: #06b6d4;
    border: 1px solid #06b6d4;
  }
  
  .status-message.success {
    background: #0f2415;
    color: #10b981;
    border: 1px solid #10b981;
  }
  
  .status-message.error {
    background: #2d0f0f;
    color: #ef4444;
    border: 1px solid #ef4444;
  }
  
  .calibration-actions {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
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
  
  .btn-success {
    background: #10b981;
    color: white;
  }
  
  .btn-success:hover:not(:disabled) {
    background: #059669;
  }
  
  .btn-secondary {
    background: #475569;
    color: white;
  }
  
  .btn-secondary:hover:not(:disabled) {
    background: #64748b;
  }
  
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .btn-small {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }
  
  .btn-warning {
    background: #f59e0b;
    color: white;
  }
  
  .btn-warning:hover:not(:disabled) {
    background: #d97706;
  }
  
  .calibration-tips {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    padding: 1rem;
  }
  
  .calibration-tips h5 {
    margin: 0 0 0.75rem 0;
    color: #f59e0b;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }
  
  .calibration-tips ul {
    margin: 0;
    padding-left: 1.25rem;
  }
  
  .calibration-tips li {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
  }
  
  @media (max-width: 768px) {
    .form-row {
      flex-direction: column;
      align-items: stretch;
      gap: 0.5rem;
    }
    
    .form-row label {
      min-width: auto;
    }
    
    .pump-info {
      margin-left: 0;
      margin-top: 0.25rem;
    }
    
    .calibration-actions {
      flex-direction: column;
    }
    
    .measurement-input {
      justify-content: flex-start;
    }
  }
</style>