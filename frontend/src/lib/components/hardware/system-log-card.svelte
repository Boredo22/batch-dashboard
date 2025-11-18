<script>
  import { ScrollText, Download, Trash2 } from "@lucide/svelte/icons";

  let { logs = [], onClearLogs } = $props();

  function getLogLevel(message) {
    if (message.toLowerCase().includes('error')) return 'error';
    if (message.toLowerCase().includes('warning')) return 'warning';
    if (message.toLowerCase().includes('success')) return 'success';
    return 'info';
  }

  function exportLogs() {
    const logText = logs.map(log => `[${log.time}] ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="card">
  <div class="card-header">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <ScrollText class="icon" />
        <span class="card-title">System Log</span>
        <span class="log-count">{logs.length}</span>
      </div>
      <div class="flex gap-1">
        <button
          onclick={exportLogs}
          disabled={logs.length === 0}
          class="icon-btn"
          title="Export logs"
        >
          <Download class="icon-btn-icon" />
        </button>
        <button
          onclick={onClearLogs}
          disabled={logs.length === 0}
          class="icon-btn"
          title="Clear logs"
        >
          <Trash2 class="icon-btn-icon" />
        </button>
      </div>
    </div>
  </div>
  <div class="card-content">
    <div class="log-container">
      {#each logs as log}
        <div class="log-entry log-level-{getLogLevel(log.message)}">
          <span class="log-time">{log.time}</span>
          <span class="log-message">{log.message}</span>
        </div>
      {:else}
        <div class="empty-state">
          No log entries yet
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;

    --accent-steel: #64748b;
    --accent-slate: #475569;

    --status-success: #059669;
    --status-warning: #d97706;
    --status-error: #dc2626;

    --text-primary: #f1f5f9;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;

    --border-subtle: #334155;
    --border-emphasis: #475569;

    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 0.75rem;

    --text-xs: 0.6875rem;
    --text-sm: 0.8125rem;
    --text-base: 0.9375rem;
  }

  .card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 0.375rem;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .card-header {
    padding: var(--space-md) var(--space-md) var(--space-sm);
    border-bottom: 1px solid var(--border-subtle);
  }

  .card-title {
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .card-content {
    padding: var(--space-md);
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .icon {
    width: 1rem;
    height: 1rem;
    color: var(--accent-steel);
  }

  .log-count {
    height: 1.25rem;
    padding: 0 0.5rem;
    font-size: var(--text-xs);
    font-weight: 500;
    background: rgba(100, 116, 139, 0.15);
    color: var(--text-muted);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
  }

  .icon-btn {
    width: 1.75rem;
    height: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: 1px solid var(--border-emphasis);
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .icon-btn:hover:not(:disabled) {
    background: var(--bg-tertiary);
  }

  .icon-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .icon-btn-icon {
    width: 0.875rem;
    height: 0.875rem;
    color: var(--text-secondary);
  }

  .log-container {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
    padding-right: var(--space-sm);
    min-height: 0;
  }

  .log-container::-webkit-scrollbar {
    width: 0.375rem;
  }

  .log-container::-webkit-scrollbar-track {
    background: var(--bg-primary);
    border-radius: 0.25rem;
  }

  .log-container::-webkit-scrollbar-thumb {
    background: var(--border-emphasis);
    border-radius: 0.25rem;
  }

  .log-container::-webkit-scrollbar-thumb:hover {
    background: var(--accent-steel);
  }

  .log-entry {
    display: flex;
    align-items: flex-start;
    gap: var(--space-sm);
    padding: var(--space-sm);
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    font-size: 0.6875rem;
    line-height: 1.3;
  }

  .log-time {
    flex-shrink: 0;
    font-family: ui-monospace, monospace;
    color: var(--text-muted);
    font-weight: 500;
    padding: 0.125rem 0.375rem;
    background: rgba(100, 116, 139, 0.15);
    border: 1px solid var(--border-subtle);
    border-radius: 0.25rem;
    font-size: 0.625rem;
  }

  .log-message {
    flex: 1;
    font-family: ui-monospace, monospace;
    color: var(--text-secondary);
    word-break: break-all;
  }

  .log-level-error .log-time {
    background: rgba(220, 38, 38, 0.15);
    color: var(--status-error);
    border-color: rgba(220, 38, 38, 0.3);
  }

  .log-level-warning .log-time {
    background: rgba(217, 119, 6, 0.15);
    color: var(--status-warning);
    border-color: rgba(217, 119, 6, 0.3);
  }

  .log-level-success .log-time {
    background: rgba(5, 150, 105, 0.15);
    color: var(--status-success);
    border-color: rgba(5, 150, 105, 0.3);
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-muted);
    font-size: var(--text-sm);
  }

  .flex {
    display: flex;
  }

  .items-center {
    align-items: center;
  }

  .justify-between {
    justify-content: space-between;
  }

  .gap-1 {
    gap: 0.25rem;
  }

  .gap-2 {
    gap: 0.5rem;
  }
</style>
