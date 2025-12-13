# Real-Time Development Agent

Use this agent for implementing real-time features using Flask-SocketIO and Svelte WebSocket clients.

## Expertise

- **Flask-SocketIO** server implementation
- **Svelte WebSocket** client patterns with $state runes
- **Event-driven architecture** for hardware status updates
- **Replacing polling** with push-based updates
- **Reconnection handling** and error recovery
- **Room-based broadcasting** for multi-client scenarios

## When to Use

- Implementing WebSocket connections for real-time status
- Replacing polling-based status updates
- Adding live hardware event streaming
- Building real-time job progress updates
- Implementing multi-client synchronization

## Architecture Pattern

```
Hardware Event → Flask Backend → SocketIO → Svelte Client → UI Update
                     ↑
              Background Thread
              (monitors hardware)
```

## Backend Implementation

### Flask-SocketIO Setup
```python
# app.py additions
from flask_socketio import SocketIO, emit, join_room, leave_room

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Replace: app.run(...)
# With: socketio.run(app, host='0.0.0.0', port=5000)
```

### Event Emitters
```python
# Emit hardware status changes
def emit_relay_change(relay_id: int, state: bool):
    socketio.emit('relay_update', {
        'relay_id': relay_id,
        'state': state,
        'timestamp': datetime.now().isoformat()
    })

def emit_pump_progress(pump_id: int, current: float, target: float):
    socketio.emit('pump_progress', {
        'pump_id': pump_id,
        'current_ml': current,
        'target_ml': target,
        'percent': (current / target * 100) if target > 0 else 0
    })

def emit_flow_update(flow_id: int, gallons: float, target: float):
    socketio.emit('flow_update', {
        'flow_id': flow_id,
        'current_gallons': gallons,
        'target_gallons': target,
        'percent': (gallons / target * 100) if target > 0 else 0
    })

def emit_job_update(job_type: str, job_state: dict):
    socketio.emit('job_update', {
        'job_type': job_type,
        'state': job_state
    })
```

### Client Connection Handling
```python
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    # Send current state on connect
    emit('initial_state', get_system_status())

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_tank')
def handle_subscribe_tank(data):
    tank_id = data.get('tank_id')
    join_room(f'tank_{tank_id}')
    emit('subscribed', {'tank_id': tank_id})
```

### Background Status Broadcaster
```python
import threading
import time

def status_broadcaster():
    """Background thread that emits status updates"""
    while True:
        try:
            status = get_system_status()
            socketio.emit('status_update', status)
        except Exception as e:
            print(f"Broadcast error: {e}")
        time.sleep(1)  # Emit every second

# Start broadcaster thread
broadcaster_thread = threading.Thread(target=status_broadcaster, daemon=True)
broadcaster_thread.start()
```

## Frontend Implementation

### WebSocket Store (Svelte 5)
```svelte
<!-- frontend/src/lib/stores/websocket.svelte.js -->
<script context="module">
import { io } from 'socket.io-client';

// Reactive state using Svelte 5 runes
let socket = $state(null);
let connected = $state(false);
let hardwareStatus = $state({});
let activeJobs = $state({});

export function initWebSocket() {
    socket = io('http://localhost:5000');

    socket.on('connect', () => {
        connected = true;
        console.log('WebSocket connected');
    });

    socket.on('disconnect', () => {
        connected = false;
        console.log('WebSocket disconnected');
    });

    socket.on('status_update', (data) => {
        hardwareStatus = data;
    });

    socket.on('relay_update', (data) => {
        // Update specific relay in state
        if (hardwareStatus.relays) {
            const relay = hardwareStatus.relays.find(r => r.id === data.relay_id);
            if (relay) relay.state = data.state;
        }
    });

    socket.on('job_update', (data) => {
        activeJobs[data.job_type] = data.state;
    });

    return socket;
}

export function getStatus() {
    return { connected, hardwareStatus, activeJobs };
}
</script>
```

### Component Usage
```svelte
<!-- Example component using WebSocket -->
<script>
    import { onMount, onDestroy } from 'svelte';
    import { initWebSocket, getStatus } from '$lib/stores/websocket.svelte.js';

    let socket;
    let { connected, hardwareStatus } = $derived(getStatus());

    onMount(() => {
        socket = initWebSocket();
    });

    onDestroy(() => {
        if (socket) socket.disconnect();
    });
</script>

{#if connected}
    <span class="text-green-500">Live</span>
{:else}
    <span class="text-red-500">Disconnected</span>
{/if}
```

### Reconnection Handling
```javascript
socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    // Implement exponential backoff
    setTimeout(() => {
        socket.connect();
    }, Math.min(1000 * Math.pow(2, retryCount), 30000));
});
```

## Migration from Polling

### Before (Polling)
```svelte
<script>
    let status = $state({});

    async function fetchStatus() {
        const res = await fetch('/api/status');
        status = await res.json();
    }

    // Poll every 2 seconds
    setInterval(fetchStatus, 2000);
</script>
```

### After (WebSocket)
```svelte
<script>
    import { getStatus } from '$lib/stores/websocket.svelte.js';
    let { hardwareStatus: status } = $derived(getStatus());
    // No polling needed - updates push automatically
</script>
```

## Dependencies

### Backend
```
# requirements.txt
flask-socketio>=5.3.0
python-socketio>=5.8.0
eventlet>=0.33.0  # or gevent
```

### Frontend
```json
// package.json
{
    "dependencies": {
        "socket.io-client": "^4.6.0"
    }
}
```

## Event Reference

| Event | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `status_update` | Server→Client | Full status object | Periodic full status |
| `relay_update` | Server→Client | `{relay_id, state}` | Single relay change |
| `pump_progress` | Server→Client | `{pump_id, current, target}` | Pump dispense progress |
| `flow_update` | Server→Client | `{flow_id, gallons, target}` | Flow meter progress |
| `job_update` | Server→Client | `{job_type, state}` | Job state change |
| `ecph_reading` | Server→Client | `{ec, ph, timestamp}` | EC/pH sensor reading |
| `error` | Server→Client | `{message, code}` | Error notification |
| `subscribe_tank` | Client→Server | `{tank_id}` | Subscribe to tank events |

## Testing WebSocket

```python
# tests/test_websocket.py
import pytest
from flask_socketio import SocketIOTestClient

def test_status_broadcast(app, socketio):
    client = SocketIOTestClient(app, socketio)
    received = client.get_received()

    assert any(msg['name'] == 'initial_state' for msg in received)
```