// src/lib/stores/hardware.svelte.js - FIXED VERSION
class HardwareStore {
  // Initialize state with runes
  hardware = $state({
    pumps: {},
    relays: {},
    flow_meters: {},
    limits: {}
  });
  
  status = $state({
    pumps: {},
    relays: {},
    flow_meters: {},
    ec_ph: {},
    running: false
  });
  
  systemStatus = $state({
    connected: false,
    lastUpdate: null,
    error: null
  });
  
  ui = $state({
    loading: false,
    activeModal: null,
    notifications: []
  });
  
  // Derived computed values
  isOnline = $derived(this.systemStatus.connected && !this.systemStatus.error);
  totalPumps = $derived(Object.keys(this.hardware.pumps).length);
  activePumps = $derived(Object.values(this.status.pumps).filter(p => p.active).length);
  totalRelays = $derived(Object.keys(this.hardware.relays).length);
  activeRelays = $derived(Object.values(this.status.relays).filter(r => r.state).length);

  constructor() {
    // Initialize with Flask data if available
    if (typeof window !== 'undefined' && window.flaskData) {
      this.hardware = { ...this.hardware, ...window.flaskData.hardware };
      this.status = { ...this.status, ...window.flaskData.status };
      this.systemStatus.connected = true;
      this.systemStatus.lastUpdate = Date.now();
    }
  }

  // FIXED: Remove $effect from class method - use regular polling
  startStatusPolling() {
    // Initial load
    this.updateSystemStatus();
    
    // Set up regular polling
    const interval = setInterval(() => {
      this.updateSystemStatus();
    }, 10000); // Every 10 seconds

    // Return cleanup function that components can call
    return () => {
      clearInterval(interval);
    };
  }

  async updateSystemStatus() {
    try {
      this.ui.loading = true;
      
      const response = await fetch('/api/status');
      const data = await response.json();
      
      if (data.success) {
        this.status = { ...this.status, ...data.status };
        this.hardware = { ...this.hardware, ...data.hardware };
        this.systemStatus.connected = true;
        this.systemStatus.lastUpdate = Date.now();
        this.systemStatus.error = null;
      } else {
        throw new Error(data.error || 'Failed to get status');
      }
    } catch (error) {
      console.error('Status update failed:', error);
      this.systemStatus.connected = false;
      this.systemStatus.error = error.message;
    } finally {
      this.ui.loading = false;
    }
  }

  async controlRelay(relayId, state) {
    const action = state ? 'on' : 'off';
    const response = await fetch(`/api/relay/${relayId}/${action}`, { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      this.showNotification(`Relay ${relayId} turned ${action}`, 'success');
      await this.updateSystemStatus();
    } else {
      this.showNotification(`Relay ${relayId} failed: ${data.error}`, 'danger');
    }
    
    return data;
  }

  async dispense(pumpId, volume) {
    const response = await fetch(`/api/pump/${pumpId}/dispense`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ volume })
    });
    
    const data = await response.json();
    
    if (data.success) {
      this.showNotification(`Pump ${pumpId} dispensing ${volume}ml`, 'success');
      await this.updateSystemStatus();
    } else {
      this.showNotification(`Pump ${pumpId} failed: ${data.error}`, 'danger');
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
}

// Create singleton instance
export const hardwareStore = new HardwareStore();