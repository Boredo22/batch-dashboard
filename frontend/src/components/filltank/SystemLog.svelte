<script>
  let {
    logs = $bindable([]),
    isTestingMode = false,
    onToggleTestingMode = null
  } = $props();

  // Filter state
  let activeFilters = $state(['info', 'cmd', 'rsp', 'warn', 'err', 'success']);
  let searchQuery = $state('');

  // Filter definitions
  const filterTypes = [
    { id: 'info', label: 'Info', color: '#3b82f6' },
    { id: 'cmd', label: 'CMD', color: '#f59e0b' },
    { id: 'rsp', label: 'RSP', color: '#22c55e' },
    { id: 'warn', label: 'Warn', color: '#eab308' },
    { id: 'err', label: 'Error', color: '#ef4444' },
    { id: 'success', label: 'OK', color: '#10b981' }
  ];

  // Toggle filter
  function toggleFilter(filterId) {
    if (activeFilters.includes(filterId)) {
      activeFilters = activeFilters.filter(f => f !== filterId);
    } else {
      activeFilters = [...activeFilters, filterId];
    }
  }

  // Filtered logs
  let filteredLogs = $derived(() => {
    return logs.filter(log => {
      // Filter by type
      if (!activeFilters.includes(log.type)) return false;
      // Filter by search
      if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  });

  // Auto-scroll ref
  let logContainer = $state(null);
  let autoScroll = $state(true);

  // Scroll to bottom when new logs arrive
  $effect(() => {
    if (autoScroll && logContainer && logs.length > 0) {
      logContainer.scrollTop = 0;
    }
  });

  // Clear logs
  function clearLogs() {
    logs = [];
  }

  // Export logs
  function exportLogs() {
    const exportData = {
      exported: new Date().toISOString(),
      totalEntries: logs.length,
      logs: logs.map(log => ({
        timestamp: log.timestamp,
        type: log.type,
        message: log.message,
        step: log.step || null
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fill-tank-log-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Format timestamp
  function formatTime(timestamp) {
    if (!timestamp) return '--:--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
  }

  // Get type label
  function getTypeLabel(type) {
    const filter = filterTypes.find(f => f.id === type);
    return filter ? filter.label : type.toUpperCase();
  }

  // Get type color
  function getTypeColor(type) {
    const filter = filterTypes.find(f => f.id === type);
    return filter ? filter.color : '#6b7280';
  }
</script>

<div class="system-log">
  <div class="log-header">
    <div class="header-left">
      <h4><i class="fas fa-terminal"></i> System Log</h4>
      <span class="log-count">{filteredLogs().length} entries</span>
    </div>
    <div class="header-actions">
      <button class="action-btn" onclick={clearLogs} title="Clear logs" aria-label="Clear logs">
        <i class="fas fa-trash"></i>
      </button>
      <button class="action-btn" onclick={exportLogs} title="Export logs" aria-label="Export logs">
        <i class="fas fa-download"></i>
      </button>
      <label class="testing-toggle" title="Toggle testing mode">
        <input
          type="checkbox"
          checked={isTestingMode}
          onchange={() => onToggleTestingMode?.(!isTestingMode)}
        />
        <span class="toggle-label">
          <i class="fas fa-flask"></i> Testing
        </span>
      </label>
    </div>
  </div>

  <div class="log-filters">
    <div class="filter-buttons">
      {#each filterTypes as filter}
        <button
          class="filter-btn"
          class:active={activeFilters.includes(filter.id)}
          style="--filter-color: {filter.color}"
          onclick={() => toggleFilter(filter.id)}
        >
          {filter.label}
        </button>
      {/each}
    </div>
    <div class="search-box">
      <i class="fas fa-search"></i>
      <input
        type="text"
        placeholder="Search logs..."
        bind:value={searchQuery}
      />
    </div>
  </div>

  <div class="log-container" bind:this={logContainer}>
    {#if filteredLogs().length === 0}
      <div class="empty-log">
        <i class="fas fa-clipboard-list"></i>
        <span>No log entries</span>
      </div>
    {:else}
      {#each filteredLogs() as log}
        <div class="log-entry" style="--type-color: {getTypeColor(log.type)}">
          <span class="log-time">{formatTime(log.timestamp)}</span>
          <span class="log-type">[{getTypeLabel(log.type)}]</span>
          <span class="log-message">{log.message}</span>
          {#if log.step}
            <span class="log-step">{log.step}</span>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .system-log {
    background: #1a202c;
    border-radius: 12px;
    border: 1px solid #4a5568;
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 200px;
  }

  .log-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #2d3748;
    border-bottom: 1px solid #4a5568;
    border-radius: 12px 12px 0 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .log-header h4 {
    margin: 0;
    font-size: 0.9rem;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .log-header i {
    color: #3b82f6;
  }

  .log-count {
    font-size: 0.75rem;
    color: #6b7280;
    background: #374151;
    padding: 2px 8px;
    border-radius: 10px;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .action-btn {
    background: #374151;
    border: none;
    color: #a0aec0;
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.85rem;
  }

  .action-btn:hover {
    background: #4a5568;
    color: #e2e8f0;
  }

  .testing-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 6px;
    background: #374151;
    transition: all 0.2s;
  }

  .testing-toggle:hover {
    background: #4a5568;
  }

  .testing-toggle input {
    display: none;
  }

  .testing-toggle:has(input:checked) {
    background: #1e3a5f;
    color: #3b82f6;
  }

  .toggle-label {
    font-size: 0.8rem;
    color: #a0aec0;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .testing-toggle:has(input:checked) .toggle-label {
    color: #3b82f6;
  }

  .log-filters {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid #374151;
    gap: 12px;
    flex-wrap: wrap;
  }

  .filter-buttons {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .filter-btn {
    background: #374151;
    border: 1px solid #4a5568;
    color: #6b7280;
    padding: 4px 10px;
    border-radius: 12px;
    cursor: pointer;
    font-size: 0.7rem;
    font-weight: 600;
    transition: all 0.2s;
  }

  .filter-btn:hover {
    background: #4a5568;
  }

  .filter-btn.active {
    background: color-mix(in srgb, var(--filter-color) 20%, transparent);
    border-color: var(--filter-color);
    color: var(--filter-color);
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #374151;
    border-radius: 6px;
    padding: 4px 10px;
    flex: 1;
    max-width: 200px;
  }

  .search-box i {
    color: #6b7280;
    font-size: 0.75rem;
  }

  .search-box input {
    background: none;
    border: none;
    color: #e2e8f0;
    font-size: 0.8rem;
    width: 100%;
  }

  .search-box input:focus {
    outline: none;
  }

  .search-box input::placeholder {
    color: #6b7280;
  }

  .log-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .empty-log {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #6b7280;
    gap: 8px;
  }

  .empty-log i {
    font-size: 2rem;
    opacity: 0.5;
  }

  .log-entry {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 6px 10px;
    background: #2d3748;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.8rem;
    border-left: 3px solid var(--type-color);
  }

  .log-time {
    color: #6b7280;
    min-width: 65px;
    font-size: 0.75rem;
  }

  .log-type {
    color: var(--type-color);
    font-weight: 600;
    min-width: 50px;
    font-size: 0.75rem;
  }

  .log-message {
    color: #e2e8f0;
    flex: 1;
    word-break: break-word;
  }

  .log-step {
    font-size: 0.7rem;
    color: #6b7280;
    background: #374151;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .log-filters {
      flex-direction: column;
      align-items: stretch;
    }

    .search-box {
      max-width: none;
    }

    .log-entry {
      flex-wrap: wrap;
    }

    .log-message {
      width: 100%;
      order: 3;
      margin-top: 4px;
    }
  }
</style>
