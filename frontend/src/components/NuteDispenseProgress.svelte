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