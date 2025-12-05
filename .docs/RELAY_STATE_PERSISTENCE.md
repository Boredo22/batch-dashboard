# Relay State Persistence Across Restarts

## Overview

The relay controller now **reads the current GPIO pin state** during initialization, preserving relay states across system restarts. This is especially useful during development when you need to restart the Flask backend frequently while growers continue using the system.

## How It Works

When the `RelayController` initializes (in `hardware/rpi_relays.py`):

1. **Read Current State**: For each relay pin, the controller:
   - Claims the pin as **input** temporarily
   - Reads the current GPIO pin state (HIGH or LOW)
   - Interprets the state based on your relay configuration (Active HIGH or Active LOW)

2. **Preserve State**:
   - Reclaims the pin as **output**
   - Writes back the **same state** that was read
   - Updates internal state tracking

3. **Track & Report**:
   - Logs each relay's state during initialization
   - Makes states available via API endpoints

## Example Log Output

```
INFO: Relay 1 (Tank 1 Fill) initialized to ON (GPIO 22 = 0)
INFO: Relay 2 (Tank 2 Fill) initialized to OFF (GPIO 26 = 1)
INFO: Relay 10 (Room 1) initialized to ON (GPIO 9 = 0)
INFO: Initialized 12 relay pins with ULN2803A - preserved existing states
```

## Benefits

1. **No Disruption During Development**: Restart your Flask backend without stopping active filling/mixing operations
2. **Frontend Sync**: When the frontend reloads, it fetches the actual relay states from the backend
3. **Recovery**: If the backend crashes and restarts, relays maintain their physical state
4. **Debugging**: Clear logging shows exactly what state each relay was in at startup

## Technical Details

### Active LOW Configuration (default)
- GPIO LOW (0) = Relay ON
- GPIO HIGH (1) = Relay OFF

### Active HIGH Configuration
- GPIO HIGH (1) = Relay ON
- GPIO LOW (0) = Relay OFF

The code automatically handles both configurations based on `RELAY_ACTIVE_HIGH` in `config.py`.

## API Endpoints

The frontend can query relay states via:
- `/api/hardware/status` - Full system status including relay states
- `/api/relay/states` - Relay states only

Both endpoints return the current tracked states which now match the physical GPIO states.

## Testing

Run this on your Pi to verify:

```bash
python -c "
from hardware.rpi_relays import RelayController
import logging
logging.basicConfig(level=logging.INFO)

controller = RelayController()
states = controller.get_all_relay_states()
print('Current relay states:', states)
"
```

You should see logs showing each relay being initialized with its current state.
