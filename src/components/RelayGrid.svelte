<script>
  let { relays = [], onRelayControl } = $props();

  async function handleRelayControl(relayId, state) {
    if (onRelayControl) {
      await onRelayControl(relayId, state);
    }
  }
</script>

<div class="relay-grid-container">
  <div class="section-header">
    <h3><i class="fas fa-toggle-on"></i> Relay Controls</h3>
    <button class="emergency-btn" onclick={() => handleRelayControl(0, false)}>
      <i class="fas fa-power-off"></i> ALL OFF
    </button>
  </div>
  
  <div class="relay-grid">
    {#each relays as relay}
      <div class="relay-card {relay.state ? 'active' : 'inactive'}">
        <div class="relay-header">
          <span class="relay-name">{relay.name}</span>
          <div class="status-dot {relay.state ? 'on' : 'off'}"></div>
        </div>
        <div class="relay-controls">
          <button 
            class="control-btn on-btn {relay.state ? 'active' : ''}" 
            onclick={() => handleRelayControl(relay.id, true)}
            disabled={relay.state}
          >
            ON {relay.state ? '(ON)' : '(OFF)'}
          </button>
          <button 
            class="control-btn off-btn {!relay.state ? 'active' : ''}" 
            onclick={() => handleRelayControl(relay.id, false)}
            disabled={!relay.state}
          >
            OFF {relay.state ? '(ON)' : '(OFF)'}
          </button>
        </div>
      </div>
    {/each}
  </div>
  
  <div class="log-info">
    <div class="log-info-header">
      <i class="fas fa-info-circle"></i>
      Log Messages
    </div>
    <div class="log-examples">
      <div class="log-example success">
        <span class="log-type">Success:</span> "Relay 5 ON" | "All relays OFF"
      </div>
      <div class="log-example error">
        <span class="log-type">Error:</span> "Invalid relay ID" | "Hardware communication failed"
      </div>
    </div>
  </div>
</div>

<style>
  .relay-grid-container {
    background: #2d3748;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    border: 1px solid #4a5568;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid #4a5568;
  }

  .section-header h3 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .section-header i {
    margin-right: 8px;
    color: #f59e0b;
  }

  .emergency-btn {
    background: #dc2626;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .emergency-btn:hover {
    background: #b91c1c;
    transform: translateY(-1px);
  }

  .relay-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .relay-card {
    background: #1a202c;
    border: 2px solid #4a5568;
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s;
  }

  .relay-card.active {
    background: #1a2e1a;
    border-color: #22c55e;
  }

  .relay-card.inactive {
    background: #2d1a1a;
    border-color: #ef4444;
  }

  .relay-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .relay-name {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 0.9rem;
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .status-dot.on {
    background: #22c55e;
  }

  .status-dot.off {
    background: #ef4444;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .relay-controls {
    display: flex;
    gap: 6px;
  }

  .control-btn {
    flex: 1;
    padding: 8px;
    border: none;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .on-btn {
    background: #1a2e1a;
    color: #4ade80;
    border: 1px solid #22c55e;
  }

  .on-btn.active {
    background: #22c55e;
    color: white;
  }

  .off-btn {
    background: #2d1a1a;
    color: #f87171;
    border: 1px solid #ef4444;
  }

  .off-btn.active {
    background: #ef4444;
    color: white;
  }

  .control-btn:hover:not(:disabled) {
    transform: translateY(-1px);
  }

  .log-info {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #4a5568;
  }

  .log-info-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #a0aec0;
  }

  .log-info-header i {
    color: #f59e0b;
  }

  .log-examples {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .log-example {
    font-size: 0.8rem;
    padding: 4px 0;
  }

  .log-type {
    font-weight: 600;
  }

  .log-example.success .log-type {
    color: #22c55e;
  }

  .log-example.error .log-type {
    color: #ef4444;
  }

  .log-example {
    color: #cbd5e0;
  }
</style>