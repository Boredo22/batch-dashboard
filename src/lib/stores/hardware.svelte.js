// src/lib/stores/hardware.svelte.js
// Hardware state management using Svelte 5 runes

export class HardwareStore {
  // System status state
  systemStatus = $state({
    connected: false,
    timestamp: null,
    lastUpdate: Date.now()
  });

  // Hardware configuration
  hardware = $state({
    pumps: { ids: [] },
    flow_meters: { ids: [] },
    mock_settings: {}
  });

  // Real-time status data
  status = $state({
    tanks: {},
    pumps: {},
    flows: {},
    jobs: {}
  });

  // UI state
  ui = $state({
    loading: false,
    activeModal: null,
    notifications: []
  });

  constructor() {
    // Initialize from Flask data if available
    if (typeof window !== 'undefined' && window.flaskData) {
      this.hardware = { ...this.hardware, ...window.flaskData.hardware };
      this.status = { ...this.status, ...window.flaskData.status };
    }

    // Start status polling
    this.startStatusPolling();
  }

  // Derived values using $derived
  isOnline = $derived(this.systemStatus.connected);

  statusText = $derived(
    this.systemStatus.connected ? 'Online' :
    this.ui.loading ? 'Checking...' : 'Offline'
  );

  activePumps = $derived(
    Object.entries(this.status.pumps || {})
      .filter(([id, pump]) => pump.active)
      .length
  );

  activeFlows = $derived(
    Object.entries(this.status.flows || {})
      .filter(([id, flow]) => flow.active)
      .length
  );

  // API methods
  async updateSystemStatus() {
    this.ui.loading = true;
    
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      
      if (data.success) {
        this.status = { ...this.status, ...data.status };
        this.systemStatus.connected = true;
        this.systemStatus.timestamp = new Date().toLocaleString();
        this.systemStatus.lastUpdate = Date.now();
      } else {
        this.systemStatus.connected = false;
        this.showNotification(`Status update failed: ${data.error}`, 'danger');
      }
    } catch (error) {
      this.systemStatus.connected = false;
      this.showNotification(`Status error: ${error.message}`, 'danger');
    } finally {
      this.ui.loading = false;
    }
  }

  async dispensePump(pumpId, amount) {
    const response = await fetch(`/api/pump/${pumpId}/dispense`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount })
    });
    
    const data = await response.json();
    
    if (data.success) {
      this.showNotification(`Pump ${pumpId} dispensing ${amount}ml`, 'success');
      await this.updateSystemStatus(); // Refresh status
    } else {
      this.showNotification(`Pump ${pumpId} failed: ${data.error}`, 'danger');
    }
    
    return data;
  }

  async startFlow(flowId, gallons) {
    const response = await fetch(`/api/flow/${flowId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gallons })
    });
    
    const data = await response.json();
    
    if (data.success) {
      this.showNotification(`Flow meter ${flowId} started for ${gallons} gallons`, 'success');
      await this.updateSystemStatus();
    } else {
      this.showNotification(`Flow meter ${flowId} failed: ${data.error}`, 'danger');
    }
    
    return data;
  }

  async emergencyStop() {
    const response = await fetch('/api/emergency/stop', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      this.showNotification('🚨 EMERGENCY STOP ACTIVATED 🚨', 'warning');
      await this.updateSystemStatus();
    } else {
      this.showNotification(`Emergency stop failed: ${data.error}`, 'danger');
    }
    
    return data;
  }

  async stopAllOperations() {
    const response = await fetch('/api/operations/stop-all', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      this.showNotification('All operations stopped', 'warning');
      await this.updateSystemStatus();
    } else {
      this.showNotification(`Failed to stop operations: ${data.error}`, 'danger');
    }
    
    return data;
  }

  // Notification system
  showNotification(message, type = 'info') {
    const id = Date.now();
    const notification = { id, message, type, timestamp: Date.now() };
    
    this.ui.notifications.push(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      this.removeNotification(id);
    }, 5000);
  }

  removeNotification(id) {
    const index = this.ui.notifications.findIndex(n => n.id === id);
    if (index > -1) {
      this.ui.notifications.splice(index, 1);
    }
  }

  // Modal management
  openModal(modalId, data = null) {
    this.ui.activeModal = { id: modalId, data };
  }

  closeModal() {
    this.ui.activeModal = null;
  }

  // Status polling with $effect
  startStatusPolling() {
    $effect(() => {
      const interval = setInterval(() => {
        this.updateSystemStatus();
      }, 10000); // Every 10 seconds

      // Initial load
      this.updateSystemStatus();

      // Cleanup function
      return () => {
        clearInterval(interval);
      };
    });
  }

  // WebSocket connection (optional enhancement)
  connectWebSocket() {
    if (typeof window === 'undefined') return;
    
    const ws = new WebSocket(`ws://${window.location.host}/api/status/stream`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.status = { ...this.status, ...data };
      this.systemStatus.connected = true;
      this.systemStatus.lastUpdate = Date.now();
    };
    
    ws.onclose = () => {
      this.systemStatus.connected = false;
      // Try to reconnect after 5 seconds
      setTimeout(() => this.connectWebSocket(), 5000);
    };
    
    ws.onerror = () => {
      this.systemStatus.connected = false;
    };
  }
}

// Create singleton instance
export const hardwareStore = new HardwareStore();