<script>
  let { logs = [] } = $props();

  function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
  }

  function getLogIcon(message) {
    const msg = message.toLowerCase();
    if (msg.includes('error') || msg.includes('failed')) return 'fas fa-exclamation-triangle';
    if (msg.includes('start') || msg.includes('on')) return 'fas fa-play';
    if (msg.includes('stop') || msg.includes('off')) return 'fas fa-stop';
    if (msg.includes('dispens')) return 'fas fa-tint';
    if (msg.includes('flow')) return 'fas fa-water';
    if (msg.includes('relay')) return 'fas fa-toggle-on';
    return 'fas fa-info-circle';
  }

  function getLogType(message) {
    const msg = message.toLowerCase();
    if (msg.includes('error') || msg.includes('failed')) return 'error';
    if (msg.includes('start') || msg.includes('dispens')) return 'success';
    if (msg.includes('stop') || msg.includes('off')) return 'warning';
    return 'info';
  }
</script>

<div class="system-log-container">
  <div class="log-header">
    <h3><i class="fas fa-list-ul"></i> System Log</h3>
    <div class="log-stats">
      <span class="log-count">{logs.length} entries</span>
    </div>
  </div>
  
  <div class="log-content" id="log-container">
    {#if logs.length === 0}
      <div class="empty-log">
        <i class="fas fa-clock"></i>
        <p>No system activity yet...</p>
      </div>
    {:else}
      {#each logs as log}
        <div class="log-entry {getLogType(log.message)}">
          <div class="log-icon">
            <i class="{getLogIcon(log.message)}"></i>
          </div>
          <div class="log-details">
            <div class="log-message">{log.message}</div>
            <div class="log-timestamp">{log.time}</div>
          </div>
        </div>
      {/each}
    {/if}
  </div>
  
  <div class="log-footer">
    <button class="clear-btn" onclick={() => logs.length = 0}>
      <i class="fas fa-trash"></i> Clear Log
    </button>
  </div>
</div>

<style>
  .system-log-container {
    background: #2d3748;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    border: 1px solid #4a5568;
    height: 100%;
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 140px);
  }

  .log-header {
    padding: 20px;
    border-bottom: 2px solid #4a5568;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }

  .log-header h3 {
    margin: 0;
    color: #e2e8f0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .log-header i {
    margin-right: 8px;
    color: #6366f1;
  }

  .log-stats {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .log-count {
    background: #1a202c;
    color: #a0aec0;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
  }

  .log-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .log-content::-webkit-scrollbar {
    width: 6px;
  }

  .log-content::-webkit-scrollbar-track {
    background: #1a202c;
    border-radius: 3px;
  }

  .log-content::-webkit-scrollbar-thumb {
    background: #4a5568;
    border-radius: 3px;
  }

  .log-content::-webkit-scrollbar-thumb:hover {
    background: #718096;
  }

  .empty-log {
    text-align: center;
    color: #718096;
    padding: 40px 20px;
  }

  .empty-log i {
    font-size: 2rem;
    margin-bottom: 12px;
    display: block;
  }

  .empty-log p {
    margin: 0;
    font-size: 0.9rem;
  }

  .log-entry {
    display: flex;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    border-left: 3px solid;
    transition: all 0.2s;
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(10px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .log-entry:hover {
    transform: translateX(4px);
  }

  .log-entry.info {
    background: #1a202c;
    border-left-color: #a0aec0;
  }

  .log-entry.success {
    background: #1a2e1a;
    border-left-color: #22c55e;
  }

  .log-entry.warning {
    background: #2e2a1a;
    border-left-color: #f59e0b;
  }

  .log-entry.error {
    background: #2d1a1a;
    border-left-color: #ef4444;
  }

  .log-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
  }

  .log-entry.info .log-icon {
    background: #2d3748;
    color: #a0aec0;
  }

  .log-entry.success .log-icon {
    background: #1a2e1a;
    color: #4ade80;
  }

  .log-entry.warning .log-icon {
    background: #2e2a1a;
    color: #fbbf24;
  }

  .log-entry.error .log-icon {
    background: #2d1a1a;
    color: #f87171;
  }

  .log-details {
    flex: 1;
    min-width: 0;
  }

  .log-message {
    color: #e2e8f0;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 4px;
    word-wrap: break-word;
  }

  .log-timestamp {
    color: #718096;
    font-size: 0.8rem;
    font-family: monospace;
  }

  .log-footer {
    padding: 16px 20px;
    border-top: 1px solid #4a5568;
    flex-shrink: 0;
  }

  .clear-btn {
    background: #1a202c;
    color: #a0aec0;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .clear-btn:hover {
    background: #2d3748;
    color: #e2e8f0;
  }
</style>