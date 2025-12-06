# State Manager Implementation

## Overview

The State Manager is a local SQLite-based persistence layer for hardware state in the Nutrient Mixing System. It keeps hardware states (relay on/off, tank status, process progress) local for fast access and persistence across Flask restarts.

## Architecture

**Purpose**: Local hardware state persistence (fast, reliable)
**Technology**: SQLite (stdlib only, no external dependencies)
**Location**: `hardware_state.db` in project root
**Integration**: Automatic with relay controller, optional for other hardware

## Key Features

- **Thread-safe**: Uses `threading.RLock()` for concurrent access
- **Simple API**: Key-value interface with convenience methods
- **Automatic JSON**: Non-string values automatically serialized
- **Hardware-specific helpers**: Built-in methods for relays, tanks, processes
- **CLI access**: Debug-friendly command-line interface
- **No dependencies**: Standard library only

## Implementation

### Files Modified

1. **`state_manager.py`** (NEW/UPDATED)
   - Core StateManager class with SQLite backend
   - Convenience methods for relays, tanks, pumps, EC/pH sensors, and processes
   - Pump state tracking: active/inactive, job progress, calibration dates
   - EC/pH state tracking: monitoring status, current values, calibration dates
   - CLI for debugging and manual state management

2. **`hardware/rpi_relays.py`** (UPDATED)
   - Imports state manager
   - Syncs relay states to database on initialization
   - Updates database when relay states change

3. **`hardware/rpi_pumps.py`** (UPDATED)
   - Imports state manager
   - Tracks pump active state (dispensing/stopped)
   - Tracks job progress (total_ml, ml_dispensed, started_at)
   - Updates job progress during dispensing
   - Clears job on completion
   - Saves calibration dates when pumps are calibrated

4. **`hardware/rpi_ezo_sensors.py`** (UPDATED)
   - Imports state manager
   - Tracks EC/pH monitoring state (active/inactive)
   - Saves current EC/pH values with timestamps
   - Saves calibration dates for both EC and pH sensors
   - Updates values during monitoring loop

5. **`hardware/rpi_flow.py`** (UPDATED)
   - Imports state manager
   - Tracks flow meter active state (monitoring/stopped)
   - Tracks job progress (target_gallons, gallons_measured, operation_type, tank_id)
   - Updates job progress during flow monitoring
   - Clears job on completion
   - Tracks lifetime total gallons measured
   - Saves calibration (pulses per gallon)

6. **`app.py`** (UPDATED)
   - Imports state manager and snapshot function
   - New `/api/state` endpoint for complete state snapshot
   - Adds `persisted_relay_states` to `/api/hardware/status`

7. **`.gitignore`** (UPDATED)
   - Added `hardware_state.db` to prevent committing local state

## API Usage

### Python API

```python
from state_manager import state
from datetime import datetime

# Simple key-value
state.set("relay_1", "on")
current = state.get("relay_1", default="off")

# Bulk operations
state.set_many({"relay_1": "on", "relay_2": "off"})
all_relays = state.get_prefix("relay_")

# Relay convenience methods
state.set_relay(1, True)          # Set relay 1 ON
is_on = state.get_relay(1)        # Get relay 1 state
all_relays = state.get_all_relays()  # Get all relay states

# Tank states
state.set_tank_state(1, "filling")
current = state.get_tank_state(1)

# Pump state tracking
state.set_pump_state(1, True)     # Pump 1 is dispensing
state.set_pump_job(1, {
    "total_ml": 100,
    "ml_dispensed": 25,
    "job_id": "batch_123",
    "started_at": datetime.now().isoformat()
})
job = state.get_pump_job(1)       # Get current job
state.clear_pump_job(1)           # Clear when done
state.set_pump_calibration_date(1, datetime.now().isoformat())
cal_date = state.get_pump_calibration_date(1)
all_pumps = state.get_all_pumps() # Get all pump states

# EC/pH sensor tracking
state.set_ecph_monitoring(True)   # Start monitoring
state.set_ecph_values(1.5, 6.8)   # EC=1.5, pH=6.8
values = state.get_ecph_values()  # Get current values
state.set_ec_calibration_date(datetime.now().isoformat())
state.set_ph_calibration_date(datetime.now().isoformat())
ecph_status = state.get_ecph_status()  # Get complete status

# Flow meter tracking
state.set_flow_meter_state(1, True)  # Flow meter 1 active
state.set_flow_meter_job(1, {
    "target_gallons": 50,
    "gallons_measured": 12.5,
    "operation_type": "fill",  # 'fill' or 'send'
    "tank_id": 1,
    "started_at": datetime.now().isoformat()
})
job = state.get_flow_meter_job(1)  # Get current job
state.clear_flow_meter_job(1)      # Clear when done
state.set_flow_meter_calibration(1, 220)  # Pulses per gallon
state.set_flow_meter_total(1, 1500.0)  # Lifetime total
state.increment_flow_meter_total(1, 50.0)  # Add to total
total = state.get_flow_meter_total(1)
all_flows = state.get_all_flow_meters()  # Get all flow meter states

# Process tracking
state.set_process("fill_123", {
    "status": "running",
    "progress": 45.5,
    "target_gallons": 100
})
process = state.get_process("fill_123")
active_processes = state.get_active_processes()
```

### REST API

**Get State Snapshot**
```bash
GET /api/state
```

Response:
```json
{
  "success": true,
  "state": {
    "relays": {
      "1": true,
      "2": false,
      "3": true
    },
    "tanks": {
      "1": "filling",
      "2": "idle"
    },
    "pumps": {
      "1": {
        "active": true,
        "job": {
          "total_ml": 100,
          "ml_dispensed": 25,
          "started_at": "2025-12-05T14:25:19.304387"
        },
        "calibration_date": "2025-11-15T10:30:00.000000"
      }
    },
    "ecph": {
      "monitoring_active": true,
      "ec": 1.5,
      "ph": 6.8,
      "last_reading": "2025-12-05T14:25:19.304387",
      "ec_calibration_date": "2025-11-10T09:00:00.000000",
      "ph_calibration_date": "2025-11-10T09:15:00.000000"
    },
    "flow_meters": {
      "1": {
        "active": true,
        "job": {
          "target_gallons": 50,
          "gallons_measured": 12.5,
          "operation_type": "fill",
          "tank_id": 1,
          "started_at": "2025-12-05T14:25:19.304387"
        },
        "calibration": 220,
        "total_gallons": 1500.0
      }
    },
    "processes": {
      "fill_123": {
        "status": "running",
        "progress": 45.5
      }
    },
    "timestamp": "2025-12-05T14:25:19.304387"
  }
}
```

**Hardware Status (includes persisted states)**
```bash
GET /api/hardware/status
```

Response includes new field:
```json
{
  "success": true,
  "status": { ... },
  "hardware": { ... },
  "persisted_relay_states": {
    "1": true,
    "2": false,
    "3": true
  }
}
```

### CLI Usage

```bash
# View all state
python state_manager.py

# Get specific key
python state_manager.py get relay_1

# Set a value
python state_manager.py set relay_1 on

# Delete a key
python state_manager.py delete relay_1

# Clear all state (requires confirmation)
python state_manager.py clear
```

## Integration Details

### Relay Controller Integration

The relay controller automatically syncs state in two places:

1. **On initialization** (`setup_gpio()`):
   - Reads current GPIO pin states
   - Initializes `self.relay_states` dict
   - Calls `init_state_from_hardware(self.relay_states)` to sync to database

2. **On state change** (`set_relay()`):
   - Updates GPIO pin
   - Updates internal `self.relay_states` dict
   - Calls `state.set_relay(relay_id, state)` to persist

This ensures the database always reflects actual hardware state.

### Flask Integration

**Startup**:
- Imports state manager globally
- State manager auto-initializes database on import

**During operation**:
- Relay changes automatically persist via relay controller
- State snapshot available via `/api/state` endpoint
- Hardware status includes persisted relay states

## Database Schema

```sql
CREATE TABLE state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_state_updated ON state(updated_at);
```

**Example Data**:
```
key                        | value                                                  | updated_at
---------------------------|--------------------------------------------------------|---------------------------
relay_1                    | "on"                                                   | 2025-12-05T14:25:19.304
relay_2                    | "off"                                                  | 2025-12-05T14:25:19.304
tank_1_state               | "filling"                                              | 2025-12-05T14:25:19.304
pump_1_active              | true                                                   | 2025-12-05T14:25:19.304
pump_1_job                 | {"total_ml":100,"ml_dispensed":25,"started_at":"..."} | 2025-12-05T14:25:19.304
pump_1_calibration_date    | "2025-11-15T10:30:00.000000"                          | 2025-11-15T10:30:00.000
ecph_monitoring_active     | true                                                   | 2025-12-05T14:25:19.304
ecph_current_values        | {"ec":1.5,"ph":6.8,"timestamp":"..."}                 | 2025-12-05T14:25:19.304
ec_calibration_date        | "2025-11-10T09:00:00.000000"                          | 2025-11-10T09:00:00.000
ph_calibration_date        | "2025-11-10T09:15:00.000000"                          | 2025-11-10T09:15:00.000
flow_1_active              | true                                                   | 2025-12-05T14:25:19.304
flow_1_job                 | {"target_gallons":50,"gallons_measured":12.5,"..."}  | 2025-12-05T14:25:19.304
flow_1_calibration         | 220                                                    | 2025-11-01T08:00:00.000
flow_1_total_gallons       | 1500.0                                                 | 2025-12-05T14:25:19.304
process_fill_123           | {"status":"running","progress":45.5}                   | 2025-12-05T14:25:19.304
```

## Benefits

1. **Persistence**: Hardware states survive Flask restarts
2. **Fast**: Local SQLite is extremely fast for key-value operations
3. **Simple**: No external dependencies, easy to understand
4. **Safe**: Thread-safe for concurrent access
5. **Debuggable**: CLI provides easy inspection and manipulation
6. **Separation**: Local state (fast) separate from analytics (Supabase)

## Future Enhancements

Potential future improvements:

1. **Pump state tracking**: Add convenience methods for pump status
2. **Flow meter tracking**: Track flow meter progress and history
3. **Process orchestration**: Enhanced process tracking with state machine
4. **State history**: Optional history table for state changes
5. **Automatic cleanup**: Prune old process data automatically
6. **State validation**: Validate state transitions (e.g., tank can't go from idle to mixing)

## Testing

The implementation includes:

- ✅ State manager module with full functionality
- ✅ Relay controller integration
- ✅ Flask API endpoints
- ✅ CLI for debugging
- ✅ Thread safety
- ✅ Database persistence

**Manual testing**:
```bash
# Test CLI
python state_manager.py

# Test Python API
python -c "from state_manager import state; \
  state.set_relay(1, True); \
  print('Relay 1:', state.get_relay(1)); \
  print('All relays:', state.get_all_relays())"

# Test Flask endpoint (requires Flask running)
curl http://localhost:5000/api/state
```

## Notes

- Database file `hardware_state.db` is in `.gitignore`
- State manager gracefully handles missing database (auto-creates)
- Fallback behavior if state manager import fails (for testing)
- Compatible with both real hardware and mock mode

---

**Implementation completed**: December 5, 2025
**Status**: ✅ Ready for production use
