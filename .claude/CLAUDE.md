# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **Nutrient Mixing System** with a modern web-based architecture:
- **Backend**: Flask web server (`app.py`) that provides REST API endpoints for hardware control
- **Frontend**: Standalone Svelte 5 application with Vite build system in the `frontend/` directory

The system controls physical hardware (pumps, relays, flow meters, EC/pH sensors) through a comprehensive hardware abstraction layer.

### Key Components

**Backend (Python)**:
- `app.py` - Flask REST API server with comprehensive endpoints for all hardware control; route handlers use the `@api_endpoint` decorator (defined near the top of the file) for the standard try/except JSON error envelope
- `main.py` - Core feed control system (`FeedControlSystem`) with proven hardware communication patterns; owns the shared I2C lock
- `hardware/hardware_comms.py` - Hardware abstraction layer; the single public interface the API uses for all hardware control
- `hardware/rpi_pumps.py`, `hardware/rpi_relays.py`, `hardware/rpi_flow.py` - Hardware-specific controllers for Raspberry Pi (I2C pumps, GPIO relays, flow meters)
- `hardware/rpi_ezo_sensors.py` - EC/pH via direct I2C from Atlas Scientific EZO circuits (`EZOSensorController`, plus `MockEZOSensorController` for mock mode)
- `hardware/tank_monitor.py` - per-tank Arduino "tank monitors" over USB serial (separate from EC/pH)
- `hardware/soil_sensors.py` - ESP32 soil-moisture sensor nodes ingested over MQTT (`paho-mqtt`); firmware in `hardware/firmware/soil_sensor_esp32/`
- `dosing_job.py` - closed-loop batch dosing job engine (fill → dose → mix → send)
- `grow_cycles.py` - pure, testable grow-cycle report logic (stage detection, recipe selection, EC/pH targets, dose scaling); `build_reports()` backs `/api/grow-cycles/report`
- `config.py` - Centralized system configuration with all hardware mappings and settings; validates relay references at import and warns if a relay is referenced but has no GPIO pin

**Frontend (Svelte 5)**:
- `frontend/src/App.svelte` - Main application with client-side routing (via `globalThis.navigateTo`); mounts the svelte-sonner `Toaster`
- `frontend/src/Dashboard.svelte` - Stage 1 hardware testing interface
- `frontend/src/FillTank.svelte` - Stage 2 job process interface (fill/mix/send), with components under `frontend/src/components/filltank/`
- `frontend/src/Settings.svelte` - System configuration management
- `frontend/src/HeadGrower.svelte`, `Nutrients.svelte`, `GrowCycles.svelte`, `Knowledge.svelte` - additional operational pages
- `frontend/src/lib/api.js` - shared API client (`apiGet`, `apiPost`, `ApiError`, 15s timeout); all backend calls go through it
- `frontend/src/lib/stores/systemStatus.svelte.js` - SSE store (single EventSource + polling fallback) for live hardware status
- `frontend/src/lib/components/` - modern component library (`growers/`, `hardware/`, `layout/`, `ui/`)
- `frontend/src/main.js` - Single entry point for the Svelte application

**Hardware Control System**:
- `FeedControlSystem` class in `main.py` - Core system with proven command processing
- Direct hardware controllers for pumps, relays, flow meters; EC/pH via direct I2C EZO circuits; per-tank Arduino tank monitors over USB serial; ESP32 soil sensors over MQTT
- All controllers speak a consistent wire protocol (`Start;<Type>;<Id>;<Param>;end`), and every controller has a mock counterpart for hardware-free development

## Development Commands

### Frontend Development
```bash
cd frontend
npm run dev          # Start Vite dev server with hot reload on port 5173
npm run build        # Build for production (outputs to frontend/static/dist/)
npm run preview      # Preview production build
npm run watch        # Build and watch for changes
```

### Backend Development
```bash
python app.py        # Start Flask REST API server on port 5000
python main.py       # Start standalone feed control system with CLI
```

### Full Stack Development
1. Start Flask backend: `python app.py`
2. Start Vite dev server: `cd frontend && npm run dev`
3. Access frontend at `http://localhost:5173` (proxies API calls to Flask)

### Hardware Testing
The system supports both real hardware and mock mode for development without physical devices.

## Build System

**Vite Configuration**: 
- Single entry point in `frontend/src/main.js`
- Builds to `frontend/static/dist/` directory
- Proxy setup redirects `/api` calls to Flask backend on port 5000
- Uses Svelte 5 with runes enabled for reactive state management

**Flask Static Serving**: 
- Flask serves built Svelte files from `static/dist/` endpoints
- Main dashboard at `/` serves the built Svelte app
- All static assets served through Flask for production deployment

## Key Patterns

**State Management**: Uses Svelte 5 runes (`$state`, `$derived`, `$effect`) for reactive state management directly in components.

**API Communication**: 
- REST endpoints follow pattern `/api/{hardware_type}/{id}/{action}`
- Direct fetch calls from Svelte components to Flask API endpoints
- Real-time status updates through periodic polling

**Hardware Abstraction**: All hardware control goes through `hardware_comms.py` which provides a consistent interface to every hardware controller (each with a mock counterpart for development without a Pi).

**Multi-Stage Testing Architecture**:
- **Stage 1**: Individual hardware component testing (relays, pumps, flow meters, EC/pH)
- **Stage 2**: Complete job process testing (fill, mix, send operations)
- **Settings**: System configuration management with user and developer settings

**Error Handling**: Comprehensive error handling with user notifications and detailed logging throughout the system.

## Svelte 5 Development Rules

**CRITICAL**: Svelte components are single `.svelte` files that contain HTML, CSS, and JavaScript together. NEVER create separate HTML and JS files for Svelte components.

**File Structure**: Every Svelte component follows this pattern:
```svelte
<script>
  // All JavaScript logic goes here
</script>

<!-- HTML template -->
<div>Content here</div>

<style>
  /* CSS styles scoped to this component */
</style>
```

**Svelte 5 Runes** (required patterns):
- Use `$state()` for reactive variables instead of `let`
- Use `$derived()` for computed values instead of `$:`  
- Use `$effect()` for side effects instead of `$:`
- Use `$props()` for component props destructuring

**Component Creation**: When adding new Svelte pages/components:
1. Create a single `.svelte` file in appropriate directory (`frontend/src/` for pages or `frontend/src/lib/components/` for reusable components). Note: `frontend/src/components/` now only holds the `filltank/` subdir used by `FillTank.svelte`.
2. Import and use the component in the relevant parent component or page
3. No need to update build configuration - Vite handles imports automatically
4. Flask serves the built frontend as static files

## Conventions

- **Backend calls from the frontend**: use the shared client in `$lib/api.js` (`apiGet`/`apiPost`). Do not use raw `fetch()` in pages. Errors surface as svelte-sonner toasts.
- **Live hardware status**: subscribe to the SSE store in `$lib/stores/systemStatus.svelte.js`.
- **New Flask route handlers**: wrap them with the `@api_endpoint` decorator in `app.py` instead of repeating try/except.
- **Grow-cycle logic**: lives in `grow_cycles.py` (pure/testable); call `build_reports()` rather than embedding logic in handlers.

## Hardware Communication Protocols (PROVEN WORKING)

These are the proven command protocols hardcoded in the hardware controllers and known to work correctly with the Pi4B hardware. **All future hardware communication must follow these exact patterns.** (They originated in an earlier `simple_gui.py` reference implementation, since removed — the controllers under `hardware/` are now the source of truth.)

### Command Structure
All hardware commands use this exact format:
```
"Start;{COMMAND_TYPE};{ID};{PARAMETER};end"
```

### Relay Control
```python
# Single relay control (canonical relay protocol)
state_str = "ON" if state else "OFF"
command = f"Start;Relay;{relay_id};{state_str};end"
success = system.send_command(command)

# All relays off (relay_id = 0)
command = "Start;Relay;0;OFF;end"
```

**Validation Rules:**
- `relay_id` must be in `get_available_relays()` OR be `0` for all relays
- Only "ON"/"OFF" states allowed

### Pump Control
```python  
# Pump dispensing (canonical dispense protocol)
command = f"Start;Dispense;{pump_id};{amount};end"
success = system.send_command(command)

# Pump stop
command = f"Start;Pump;{pump_id};X;end"
success = system.send_command(command)
```

**Validation Rules:**
- `pump_id` must be in `get_available_pumps()`
- `amount` must be between `MIN_PUMP_VOLUME_ML` and `MAX_PUMP_VOLUME_ML`
- Stop command uses "X" as parameter

### Flow Meter Control
```python
# Start flow monitoring (canonical flow protocol)
command = f"Start;StartFlow;{flow_id};{gallons};220;end"
success = system.send_command(command)

# Stop flow monitoring
command = f"Start;StartFlow;{flow_id};0;end"
success = system.send_command(command)
```

**Validation Rules:**
- `flow_id` must be in `get_available_flow_meters()`
- `gallons` must be between 1 and `MAX_FLOW_GALLONS`
- Stop uses `gallons=0`
- Note: "220" is calibration parameter (pulses per gallon)

### EC/pH Control
EC/pH is read via **direct I2C** from Atlas Scientific EZO circuits (EZO pH at `0x63`, EZO EC at `0x64`), implemented in `hardware/rpi_ezo_sensors.py` (`EZOSensorController`; `MockEZOSensorController` for mock mode). This is NOT the legacy Arduino/serial path. The `Start;EcPh;ON/OFF;end` commands below remain only as the frozen legacy reference protocol.
```python
# Start EC/pH monitoring
command = "Start;EcPh;ON;end"
success = system.send_command(command)

# Stop EC/pH monitoring
command = "Start;EcPh;OFF;end"
success = system.send_command(command)
```

### System Initialization (CRITICAL)
```python
# Canonical system initialization
use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
system = FeedControlSystem(use_mock_flow=use_mock_flow)
system.start()
```

### Emergency Stop
```python
# Emergency stop all operations
system.emergency_stop()
```

**IMPORTANT NOTES:**
1. **Never modify these command formats** - they are hardcoded in the hardware controllers
2. **Always validate inputs** using the config functions before sending commands
3. **Use threading** for system initialization to avoid blocking the UI
4. **Commands are case-sensitive** - "ON"/"OFF" must be uppercase
5. **The hardware_comms.py module** implements these exact patterns and should be used for all hardware communication

## Complete Command Reference

See `docs/HARDWARE_COMMANDS.md` for the comprehensive command reference including:
- All Stage 1 individual hardware commands
- All Stage 2 job process command sequences  
- Hardware mapping and configuration
- Expected responses and error messages
- Emergency procedures and recovery steps

### Quick Command Summary

**Relay Control:**
```bash
"Start;Relay;{id};ON;end"    # Single relay on
"Start;Relay;{id};OFF;end"   # Single relay off  
"Start;Relay;0;OFF;end"      # All relays off (emergency)
```

**Pump Control:**
```bash
"Start;Dispense;{id};{ml};end"  # Dispense volume
"Start;Pump;{id};X;end"         # Stop pump
```

**Flow Meter Control:**
```bash
"Start;StartFlow;{id};{gal};220;end"  # Start flow
"Start;StartFlow;{id};0;end"          # Stop flow
```

**EC/pH Control:**
```bash
"Start;EcPh;ON;end"   # Start monitoring
"Start;EcPh;OFF;end"  # Stop monitoring
```