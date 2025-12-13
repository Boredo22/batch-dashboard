<script>
  import { toast } from 'svelte-sonner';
  import { Settings, Play, CheckCircle, AlertCircle, RotateCcw, Beaker } from "@lucide/svelte/icons";

  let {
    pumps = [],
    onClose
  } = $props();

  // Wizard state
  let step = $state(1);
  let selectedPump = $state(null);
  let targetVolume = $state(100); // Default test volume in ml
  let actualVolume = $state(0);
  let isDispensing = $state(false);
  let dispensingComplete = $state(false);
  let calibrationResult = $state(null);
  let error = $state(null);

  // Derived values
  let safePumps = $derived(Array.isArray(pumps) ? pumps : []);
  let selectedPumpData = $derived(selectedPump ? safePumps.find(p => p.id === selectedPump) : null);
  let calibrationFactor = $derived(actualVolume > 0 && targetVolume > 0 ? actualVolume / targetVolume : 1);

  // Step labels
  const steps = [
    { num: 1, label: 'Select Pump' },
    { num: 2, label: 'Dispense Test' },
    { num: 3, label: 'Measure & Enter' },
    { num: 4, label: 'Apply Calibration' }
  ];

  async function startTestDispense() {
    if (!selectedPump || targetVolume <= 0) {
      error = 'Please select a pump and enter a valid test volume';
      return;
    }

    error = null;
    isDispensing = true;
    dispensingComplete = false;

    try {
      const response = await fetch(`/api/pump/${selectedPump}/dispense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: targetVolume })
      });

      if (response.ok) {
        toast.success(`Dispensing ${targetVolume}ml from pump ${selectedPump}`);
        // Poll for completion
        pollDispenseStatus();
      } else {
        const errorData = await response.json();
        error = errorData.error || 'Failed to start dispense';
        toast.error(error);
        isDispensing = false;
      }
    } catch (e) {
      error = `Network error: ${e.message}`;
      toast.error(error);
      isDispensing = false;
    }
  }

  async function pollDispenseStatus() {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/pumps/${selectedPump}/status`);
        if (response.ok) {
          const data = await response.json();
          if (!data.voltage?.is_dispensing) {
            clearInterval(pollInterval);
            isDispensing = false;
            dispensingComplete = true;
            toast.success('Test dispense complete! Measure the actual volume.');
            step = 3;
          }
        }
      } catch (e) {
        console.error('Error polling pump status:', e);
      }
    }, 1000);

    // Safety timeout after 2 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (isDispensing) {
        isDispensing = false;
        error = 'Dispense timeout - pump may have finished or encountered an error';
      }
    }, 120000);
  }

  async function applyCalibration() {
    if (!selectedPump || actualVolume <= 0) {
      error = 'Please enter the measured actual volume';
      return;
    }

    error = null;

    try {
      const response = await fetch(`/api/pumps/${selectedPump}/calibrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_volume: targetVolume,
          actual_volume: actualVolume
        })
      });

      if (response.ok) {
        const result = await response.json();
        calibrationResult = result;
        toast.success(`Pump ${selectedPump} calibrated successfully!`);
        step = 4;
      } else {
        const errorData = await response.json();
        error = errorData.error || 'Calibration failed';
        toast.error(error);
      }
    } catch (e) {
      error = `Network error: ${e.message}`;
      toast.error(error);
    }
  }

  async function clearCalibration() {
    if (!selectedPump) return;

    try {
      const response = await fetch(`/api/pumps/${selectedPump}/calibration/clear`, {
        method: 'POST'
      });

      if (response.ok) {
        toast.success(`Pump ${selectedPump} calibration cleared`);
        resetWizard();
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to clear calibration');
      }
    } catch (e) {
      toast.error(`Network error: ${e.message}`);
    }
  }

  function resetWizard() {
    step = 1;
    selectedPump = null;
    targetVolume = 100;
    actualVolume = 0;
    isDispensing = false;
    dispensingComplete = false;
    calibrationResult = null;
    error = null;
  }

  function nextStep() {
    if (step === 1 && !selectedPump) {
      error = 'Please select a pump';
      return;
    }
    error = null;
    step = Math.min(step + 1, 4);
  }

  function prevStep() {
    error = null;
    step = Math.max(step - 1, 1);
  }
</script>

<div class="wizard-overlay" onclick={() => onClose?.()}>
  <div class="wizard-container" onclick={(e) => e.stopPropagation()}>
    <!-- Header -->
    <div class="wizard-header">
      <div class="header-title">
        <Beaker class="header-icon" />
        <span>Pump Calibration Wizard</span>
      </div>
      <button class="close-btn" onclick={() => onClose?.()}>
        &times;
      </button>
    </div>

    <!-- Progress Steps -->
    <div class="progress-steps">
      {#each steps as s}
        <div class="step-item {step >= s.num ? 'active' : ''} {step > s.num ? 'complete' : ''}">
          <div class="step-num">{s.num}</div>
          <div class="step-label">{s.label}</div>
        </div>
      {/each}
    </div>

    <!-- Content -->
    <div class="wizard-content">
      {#if error}
        <div class="error-alert">
          <AlertCircle class="alert-icon" />
          <span>{error}</span>
        </div>
      {/if}

      {#if step === 1}
        <!-- Step 1: Select Pump -->
        <div class="step-content">
          <h3 class="step-title">Select Pump to Calibrate</h3>
          <p class="step-description">
            Choose the pump you want to calibrate. This process will dispense a test volume
            that you'll measure to determine the calibration factor.
          </p>

          <div class="pump-grid">
            {#each safePumps as pump}
              <button
                class="pump-card {selectedPump === pump.id ? 'selected' : ''}"
                onclick={() => selectedPump = pump.id}
              >
                <div class="pump-card-header">
                  <span class="pump-id">Pump {pump.id}</span>
                  {#if pump.calibrated}
                    <span class="calibrated-badge">Calibrated</span>
                  {/if}
                </div>
                <div class="pump-name">{pump.name || 'Unnamed'}</div>
              </button>
            {/each}
          </div>

          <div class="input-group">
            <label for="target-volume" class="label">Test Volume (ml)</label>
            <input
              id="target-volume"
              type="number"
              bind:value={targetVolume}
              min="10"
              max="500"
              class="number-input"
            />
            <p class="input-hint">Larger volumes give more accurate calibration (100ml recommended)</p>
          </div>
        </div>

      {:else if step === 2}
        <!-- Step 2: Dispense Test -->
        <div class="step-content">
          <h3 class="step-title">Dispense Test Volume</h3>
          <p class="step-description">
            Place a graduated cylinder or measuring container under
            <strong>Pump {selectedPump} ({selectedPumpData?.name})</strong>.
            Click "Start Dispense" to dispense <strong>{targetVolume}ml</strong>.
          </p>

          <div class="dispense-status">
            {#if isDispensing}
              <div class="status-indicator dispensing">
                <div class="spinner"></div>
                <span>Dispensing... Please wait</span>
              </div>
            {:else if dispensingComplete}
              <div class="status-indicator complete">
                <CheckCircle class="status-icon success" />
                <span>Dispense complete!</span>
              </div>
            {:else}
              <div class="status-indicator ready">
                <Play class="status-icon" />
                <span>Ready to dispense</span>
              </div>
            {/if}
          </div>

          <button
            class="btn-primary btn-large"
            onclick={startTestDispense}
            disabled={isDispensing}
          >
            {#if isDispensing}
              Dispensing...
            {:else}
              <Play class="btn-icon" />
              Start Dispense ({targetVolume}ml)
            {/if}
          </button>
        </div>

      {:else if step === 3}
        <!-- Step 3: Measure & Enter -->
        <div class="step-content">
          <h3 class="step-title">Enter Measured Volume</h3>
          <p class="step-description">
            Measure the actual volume dispensed using your graduated cylinder.
            Enter the measured value below.
          </p>

          <div class="measurement-display">
            <div class="measurement-row">
              <span class="measurement-label">Target Volume:</span>
              <span class="measurement-value">{targetVolume} ml</span>
            </div>
            <div class="measurement-row">
              <span class="measurement-label">Actual Volume:</span>
              <input
                type="number"
                bind:value={actualVolume}
                min="1"
                step="0.1"
                class="number-input measurement-input"
                placeholder="Enter measured ml"
              />
            </div>
            {#if actualVolume > 0}
              <div class="measurement-row result">
                <span class="measurement-label">Calibration Factor:</span>
                <span class="measurement-value factor">{calibrationFactor.toFixed(4)}</span>
              </div>
              <div class="calibration-preview">
                {#if calibrationFactor > 1.1}
                  <span class="preview-warning">Pump is under-dispensing by {((calibrationFactor - 1) * 100).toFixed(1)}%</span>
                {:else if calibrationFactor < 0.9}
                  <span class="preview-warning">Pump is over-dispensing by {((1 - calibrationFactor) * 100).toFixed(1)}%</span>
                {:else}
                  <span class="preview-good">Pump is within 10% accuracy</span>
                {/if}
              </div>
            {/if}
          </div>
        </div>

      {:else if step === 4}
        <!-- Step 4: Complete -->
        <div class="step-content">
          <div class="success-display">
            <CheckCircle class="success-icon" />
            <h3 class="success-title">Calibration Complete!</h3>
            <p class="success-message">
              Pump {selectedPump} ({selectedPumpData?.name}) has been calibrated successfully.
            </p>
            {#if calibrationResult}
              <div class="result-details">
                <div class="result-row">
                  <span>Target Volume:</span>
                  <span>{calibrationResult.target_volume} ml</span>
                </div>
                <div class="result-row">
                  <span>Actual Volume:</span>
                  <span>{calibrationResult.actual_volume} ml</span>
                </div>
                <div class="result-row highlight">
                  <span>Calibration Factor:</span>
                  <span>{calibrationResult.calibration_factor?.toFixed(4)}</span>
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="wizard-footer">
      <div class="footer-left">
        {#if selectedPump && step === 1}
          <button class="btn-ghost" onclick={clearCalibration}>
            <RotateCcw class="btn-icon" />
            Clear Calibration
          </button>
        {/if}
      </div>
      <div class="footer-right">
        {#if step > 1 && step < 4}
          <button class="btn-secondary" onclick={prevStep} disabled={isDispensing}>
            Back
          </button>
        {/if}
        {#if step === 1}
          <button class="btn-primary" onclick={nextStep} disabled={!selectedPump}>
            Next
          </button>
        {:else if step === 2 && dispensingComplete}
          <button class="btn-primary" onclick={nextStep}>
            Next
          </button>
        {:else if step === 3}
          <button class="btn-primary" onclick={applyCalibration} disabled={actualVolume <= 0}>
            Apply Calibration
          </button>
        {:else if step === 4}
          <button class="btn-secondary" onclick={resetWizard}>
            Calibrate Another
          </button>
          <button class="btn-primary" onclick={() => onClose?.()}>
            Done
          </button>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .wizard-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }

  .wizard-container {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 0.5rem;
    width: 100%;
    max-width: 600px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .wizard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #334155;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #f1f5f9;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .header-icon {
    width: 1.25rem;
    height: 1.25rem;
    color: #64748b;
  }

  .close-btn {
    width: 2rem;
    height: 2rem;
    border: none;
    background: transparent;
    color: #94a3b8;
    font-size: 1.5rem;
    cursor: pointer;
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .close-btn:hover {
    background: #334155;
    color: #f1f5f9;
  }

  .progress-steps {
    display: flex;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #334155;
    gap: 0.5rem;
  }

  .step-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .step-num {
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    background: #334155;
    color: #94a3b8;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .step-item.active .step-num {
    background: #64748b;
    color: #f1f5f9;
  }

  .step-item.complete .step-num {
    background: #059669;
    color: #f1f5f9;
  }

  .step-label {
    font-size: 0.625rem;
    color: #94a3b8;
    text-align: center;
  }

  .step-item.active .step-label {
    color: #f1f5f9;
  }

  .wizard-content {
    flex: 1;
    padding: 1.25rem;
    overflow-y: auto;
  }

  .error-alert {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(220, 38, 38, 0.15);
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: 0.375rem;
    margin-bottom: 1rem;
    color: #ef4444;
    font-size: 0.875rem;
  }

  .alert-icon {
    width: 1rem;
    height: 1rem;
    flex-shrink: 0;
  }

  .step-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .step-title {
    color: #f1f5f9;
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
  }

  .step-description {
    color: #94a3b8;
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
  }

  .pump-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.5rem;
  }

  .pump-card {
    padding: 0.75rem;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
  }

  .pump-card:hover {
    border-color: #475569;
  }

  .pump-card.selected {
    border-color: #64748b;
    background: #334155;
  }

  .pump-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.25rem;
  }

  .pump-id {
    color: #f1f5f9;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .calibrated-badge {
    font-size: 0.625rem;
    padding: 0.125rem 0.375rem;
    background: rgba(5, 150, 105, 0.15);
    color: #059669;
    border-radius: 0.25rem;
  }

  .pump-name {
    color: #94a3b8;
    font-size: 0.75rem;
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .label {
    color: #e2e8f0;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .number-input {
    height: 2.5rem;
    background: #0f172a;
    border: 1px solid #475569;
    border-radius: 0.25rem;
    color: #f1f5f9;
    font-size: 0.875rem;
    padding: 0 0.75rem;
    outline: none;
  }

  .number-input:focus {
    border-color: #64748b;
  }

  .input-hint {
    color: #64748b;
    font-size: 0.75rem;
    margin: 0;
  }

  .dispense-status {
    padding: 1.5rem;
    background: #0f172a;
    border-radius: 0.375rem;
    text-align: center;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: #94a3b8;
  }

  .status-indicator.dispensing {
    color: #f59e0b;
  }

  .status-indicator.complete {
    color: #059669;
  }

  .status-icon {
    width: 1.25rem;
    height: 1.25rem;
  }

  .status-icon.success {
    color: #059669;
  }

  .spinner {
    width: 1.25rem;
    height: 1.25rem;
    border: 2px solid #334155;
    border-top-color: #f59e0b;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .btn-primary, .btn-secondary, .btn-ghost {
    height: 2.5rem;
    padding: 0 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    border-radius: 0.375rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    transition: all 0.15s ease;
    border: 1px solid transparent;
  }

  .btn-primary {
    background: #475569;
    color: #f1f5f9;
  }

  .btn-primary:hover:not(:disabled) {
    background: #64748b;
  }

  .btn-secondary {
    background: transparent;
    border-color: #475569;
    color: #e2e8f0;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #334155;
  }

  .btn-ghost {
    background: transparent;
    color: #94a3b8;
  }

  .btn-ghost:hover:not(:disabled) {
    color: #f1f5f9;
    background: #334155;
  }

  .btn-primary:disabled, .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-large {
    width: 100%;
    height: 3rem;
    justify-content: center;
    font-size: 1rem;
  }

  .btn-icon {
    width: 1rem;
    height: 1rem;
  }

  .measurement-display {
    background: #0f172a;
    border-radius: 0.375rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .measurement-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .measurement-label {
    color: #94a3b8;
    font-size: 0.875rem;
  }

  .measurement-value {
    color: #f1f5f9;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .measurement-value.factor {
    font-family: ui-monospace, monospace;
    color: #0ea5e9;
  }

  .measurement-input {
    width: 120px;
    text-align: right;
  }

  .measurement-row.result {
    padding-top: 0.75rem;
    border-top: 1px solid #334155;
  }

  .calibration-preview {
    text-align: center;
    padding: 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
  }

  .preview-warning {
    color: #f59e0b;
  }

  .preview-good {
    color: #059669;
  }

  .success-display {
    text-align: center;
    padding: 1.5rem;
  }

  .success-icon {
    width: 3rem;
    height: 3rem;
    color: #059669;
    margin-bottom: 1rem;
  }

  .success-title {
    color: #f1f5f9;
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 0.5rem;
  }

  .success-message {
    color: #94a3b8;
    font-size: 0.875rem;
    margin: 0 0 1rem;
  }

  .result-details {
    background: #0f172a;
    border-radius: 0.375rem;
    padding: 1rem;
    text-align: left;
  }

  .result-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    font-size: 0.875rem;
    color: #94a3b8;
  }

  .result-row span:last-child {
    color: #f1f5f9;
    font-weight: 500;
  }

  .result-row.highlight {
    border-top: 1px solid #334155;
    margin-top: 0.5rem;
    padding-top: 0.75rem;
  }

  .result-row.highlight span:last-child {
    color: #0ea5e9;
    font-family: ui-monospace, monospace;
  }

  .wizard-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-top: 1px solid #334155;
  }

  .footer-left, .footer-right {
    display: flex;
    gap: 0.5rem;
  }
</style>
