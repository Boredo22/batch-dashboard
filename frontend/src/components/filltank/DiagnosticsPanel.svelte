<script>
  let {
    // EC/pH values
    ecValue = 0,
    phValue = 0,
    ecTarget = { min: 1.0, max: 2.0 },
    phTarget = { min: 5.5, max: 6.5 },
    ecPhMonitoring = false,

    // Flow data
    flowData = { current: 0, target: 0, rate: 0 },

    // Hardware status
    relays = [],
    pumps = [],
    flowMeters = [],

    // Connection status
    isConnected = false,

    // Timer
    timerRemaining = null
  } = $props();

  // Check if EC is in range
  let ecInRange = $derived(ecValue >= ecTarget.min && ecValue <= ecTarget.max);

  // Check if pH is in range
  let phInRange = $derived(phValue >= phTarget.min && phValue <= phTarget.max);

  // Active relays
  let activeRelays = $derived(relays.filter(r => r.state));

  // Active pumps
  let activePumps = $derived(pumps.filter(p => p.is_dispensing));

  // Flow progress percentage
  let flowProgress = $derived(flowData.target > 0 ? (flowData.current / flowData.target) * 100 : 0);

  // Format timer
  function formatTimer(seconds) {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<div class="diagnostics-panel">
  <div class="panel-header">
    <h3><i class="fas fa-chart-line"></i> Diagnostics</h3>
    <div class="connection-status" class:connected={isConnected}>
      <div class="status-dot"></div>
      {isConnected ? 'Connected' : 'Disconnected'}
    </div>
  </div>

  <!-- Timer Display -->
  {#if timerRemaining !== null}
    <div class="timer-display">
      <i class="fas fa-clock"></i>
      <span class="timer-value">{formatTimer(timerRemaining)}</span>
    </div>
  {/if}

  <!-- EC/pH Section -->
  <div class="diag-section sensors-section">
    <div class="section-title">
      <i class="fas fa-heartbeat"></i> Sensors
      {#if ecPhMonitoring}
        <span class="monitoring-badge">Monitoring</span>
      {/if}
    </div>

    <div class="sensor-grid">
      <div class="sensor-card" class:in-range={ecInRange} class:out-of-range={!ecInRange && ecValue > 0}>
        <div class="sensor-label">EC</div>
        <div class="sensor-value">{ecValue.toFixed(2)}</div>
        <div class="sensor-unit">mS/cm</div>
        <div class="sensor-range">Target: {ecTarget.min}-{ecTarget.max}</div>
      </div>

      <div class="sensor-card" class:in-range={phInRange} class:out-of-range={!phInRange && phValue > 0}>
        <div class="sensor-label">pH</div>
        <div class="sensor-value">{phValue.toFixed(2)}</div>
        <div class="sensor-unit"></div>
        <div class="sensor-range">Target: {phTarget.min}-{phTarget.max}</div>
      </div>
    </div>
  </div>

  <!-- Flow Section -->
  <div class="diag-section flow-section">
    <div class="section-title">
      <i class="fas fa-water"></i> Flow Status
    </div>

    <div class="flow-stats">
      <div class="flow-stat">
        <span class="stat-label">Rate</span>
        <span class="stat-value">{flowData.rate?.toFixed(1) || '0.0'}</span>
        <span class="stat-unit">GPM</span>
      </div>
      <div class="flow-stat">
        <span class="stat-label">Current</span>
        <span class="stat-value">{flowData.current?.toFixed(1) || '0.0'}</span>
        <span class="stat-unit">gal</span>
      </div>
      <div class="flow-stat">
        <span class="stat-label">Target</span>
        <span class="stat-value">{flowData.target?.toFixed(1) || '0.0'}</span>
        <span class="stat-unit">gal</span>
      </div>
    </div>

    {#if flowData.target > 0}
      <div class="flow-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: {flowProgress}%"></div>
        </div>
        <span class="progress-text">{flowProgress.toFixed(0)}%</span>
      </div>
    {/if}
  </div>

  <!-- Relays Section -->
  <div class="diag-section relays-section">
    <div class="section-title">
      <i class="fas fa-toggle-on"></i> Relays
      <span class="count-badge">{activeRelays.length} active</span>
    </div>

    <div class="hardware-list">
      {#if activeRelays.length > 0}
        {#each activeRelays as relay}
          <div class="hardware-item active">
            <span class="hw-id">R{relay.id}</span>
            <span class="hw-name">{relay.name || `Relay ${relay.id}`}</span>
            <span class="hw-status on">ON</span>
          </div>
        {/each}
      {:else}
        <div class="empty-state">All relays off</div>
      {/if}
    </div>
  </div>

  <!-- Pumps Section -->
  <div class="diag-section pumps-section">
    <div class="section-title">
      <i class="fas fa-pump-medical"></i> Pumps
      <span class="count-badge">{activePumps.length} active</span>
    </div>

    <div class="hardware-list">
      {#if activePumps.length > 0}
        {#each activePumps as pump}
          <div class="hardware-item active">
            <span class="hw-id">P{pump.id}</span>
            <span class="hw-name">{pump.name || `Pump ${pump.id}`}</span>
            <div class="pump-progress">
              <div class="mini-progress-bar">
                <div
                  class="mini-progress-fill"
                  style="width: {pump.target_volume > 0 ? (pump.current_volume / pump.target_volume * 100) : 0}%"
                ></div>
              </div>
              <span class="pump-volume">{pump.current_volume?.toFixed(1)}/{pump.target_volume?.toFixed(1)} ml</span>
            </div>
          </div>
        {/each}
      {:else}
        <div class="empty-state">All pumps idle</div>
      {/if}
    </div>
  </div>

  <!-- Flow Meters Section -->
  <div class="diag-section flowmeters-section">
    <div class="section-title">
      <i class="fas fa-tachometer-alt"></i> Flow Meters
    </div>

    <div class="hardware-list">
      {#each flowMeters as meter}
        <div class="hardware-item" class:active={meter.status === 'running'}>
          <span class="hw-id">F{meter.id}</span>
          <span class="hw-name">{meter.name || `Flow ${meter.id}`}</span>
          <span class="hw-status" class:on={meter.status === 'running'}>
            {meter.status === 'running' ? 'Running' : 'Stopped'}
          </span>
        </div>
      {/each}
      {#if flowMeters.length === 0}
        <div class="empty-state">No flow meters</div>
      {/if}
    </div>
  </div>
</div>

<style>
  .diagnostics-panel {
    background: #2d3748;
    border-radius: 12px;
    border: 1px solid #4a5568;
    height: 100%;
    overflow-y: auto;
  }

  .panel-header {
    padding: 16px;
    border-bottom: 1px solid #4a5568;
    display: flex;
    align-items: center;
    justify-content: space-between;
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
    color: #22c55e;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: #ef4444;
    padding: 4px 8px;
    background: #2d1a1a;
    border-radius: 12px;
  }

  .connection-status.connected {
    color: #22c55e;
    background: #1a2e1a;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .timer-display {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 16px;
    background: #1e3a5f;
    border-bottom: 1px solid #3b82f6;
  }

  .timer-display i {
    color: #3b82f6;
    font-size: 1.2rem;
  }

  .timer-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #e2e8f0;
    font-family: 'Consolas', monospace;
  }

  .diag-section {
    padding: 12px 16px;
    border-bottom: 1px solid #374151;
  }

  .diag-section:last-child {
    border-bottom: none;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 12px;
  }

  .section-title i {
    color: #3b82f6;
    width: 16px;
  }

  .monitoring-badge {
    font-size: 0.7rem;
    background: #22c55e;
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    margin-left: auto;
  }

  .count-badge {
    font-size: 0.7rem;
    background: #4a5568;
    color: #e2e8f0;
    padding: 2px 8px;
    border-radius: 10px;
    margin-left: auto;
  }

  .sensor-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .sensor-card {
    background: #1a202c;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    border: 2px solid transparent;
    transition: all 0.3s;
  }

  .sensor-card.in-range {
    border-color: #22c55e;
    background: #1a2e1a;
  }

  .sensor-card.out-of-range {
    border-color: #f59e0b;
    background: #2d2a1a;
    animation: pulse-warning 1s infinite;
  }

  @keyframes pulse-warning {
    0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
    50% { box-shadow: 0 0 12px 4px rgba(245, 158, 11, 0.4); }
  }

  .sensor-label {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 4px;
  }

  .sensor-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #e2e8f0;
  }

  .sensor-card.in-range .sensor-value {
    color: #22c55e;
  }

  .sensor-card.out-of-range .sensor-value {
    color: #f59e0b;
  }

  .sensor-unit {
    font-size: 0.7rem;
    color: #6b7280;
    min-height: 14px;
  }

  .sensor-range {
    font-size: 0.7rem;
    color: #4a5568;
    margin-top: 4px;
  }

  .flow-stats {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
  }

  .flow-stat {
    flex: 1;
    background: #1a202c;
    border-radius: 6px;
    padding: 8px;
    text-align: center;
  }

  .stat-label {
    display: block;
    font-size: 0.7rem;
    color: #6b7280;
    margin-bottom: 4px;
  }

  .stat-value {
    display: block;
    font-size: 1.1rem;
    font-weight: bold;
    color: #e2e8f0;
  }

  .stat-unit {
    display: block;
    font-size: 0.65rem;
    color: #6b7280;
  }

  .flow-progress {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: #1a202c;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #06b6d4);
    transition: width 0.3s;
  }

  .progress-text {
    font-size: 0.85rem;
    font-weight: 600;
    color: #3b82f6;
    min-width: 40px;
    text-align: right;
  }

  .hardware-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .hardware-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    background: #1a202c;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .hardware-item.active {
    background: #1e3a5f;
    border-left: 3px solid #3b82f6;
  }

  .hw-id {
    font-weight: 600;
    color: #6b7280;
    min-width: 28px;
  }

  .hw-name {
    flex: 1;
    color: #e2e8f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .hw-status {
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: #374151;
    color: #6b7280;
  }

  .hw-status.on {
    background: #1a2e1a;
    color: #22c55e;
  }

  .pump-progress {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 100px;
  }

  .mini-progress-bar {
    height: 4px;
    background: #374151;
    border-radius: 2px;
    overflow: hidden;
  }

  .mini-progress-fill {
    height: 100%;
    background: #3b82f6;
    transition: width 0.3s;
  }

  .pump-volume {
    font-size: 0.7rem;
    color: #6b7280;
    text-align: right;
  }

  .empty-state {
    font-size: 0.8rem;
    color: #6b7280;
    text-align: center;
    padding: 12px;
    background: #1a202c;
    border-radius: 6px;
  }

  @media (max-width: 768px) {
    .sensor-grid {
      grid-template-columns: 1fr;
    }

    .flow-stats {
      flex-direction: column;
    }
  }
</style>
