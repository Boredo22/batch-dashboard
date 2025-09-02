# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **Nutrient Mixing System** with dual architecture:
- **Backend**: Flask web server (`app.py`) that provides REST API endpoints and serves templates
- **Frontend**: Svelte 5 components with Vite build system for modern JavaScript UI

The system controls physical hardware (pumps, relays, flow meters) through a hardware abstraction layer in the `hardware/` directory.

### Key Components

**Backend (Python)**:
- `app.py` - Main Flask application with API endpoints and template routes
- `hardware/hardware_comms.py` - Hardware abstraction layer providing unified interface
- `hardware/rpi_*.py` - Hardware-specific modules for Raspberry Pi GPIO control
- `config.py` - System configuration including tank definitions and formulas

**Frontend (Svelte 5)**:
- `src/routes/Dashboard.svelte` - Main control interface
- `src/routes/Status.svelte` - System status monitoring
- `src/lib/stores/hardware.svelte.js` - Reactive state management using Svelte 5 runes
- Three separate entry points: `main.js`, `dashboard.js`, `status.js`

**Templates**: Flask Jinja2 templates in `templates/` provide the HTML structure with embedded Svelte mounting points.

## Development Commands

### Frontend Development
```bash
npm run dev          # Start Vite dev server with hot reload
npm run build        # Build for production (outputs to static/dist/)
npm run preview      # Preview production build
npm run watch        # Build and watch for changes
```

### Backend Development
```bash
python app.py        # Start Flask development server
python simple_gui.py # Alternative GUI interface
```

### Hardware Testing
The system supports both real hardware and mock mode for development without physical devices.

## Build System

**Vite Configuration**: 
- Multiple entry points for different pages (main, dashboard, status)
- Builds to `static/dist/` for Flask to serve
- Proxy setup redirects `/api` calls to Flask backend on port 5000
- Uses Svelte 5 with runes enabled

**Important**: The frontend builds JavaScript bundles that Flask serves via templates. Each page has its own entry point and Svelte component.

## Key Patterns

**State Management**: Uses Svelte 5 runes (`$state`, `$derived`) in `hardware.svelte.js` for reactive hardware state management.

**API Communication**: 
- REST endpoints follow pattern `/api/{hardware_type}/{id}/{action}`
- Hardware control methods in store handle both API calls and UI state updates
- Polling system updates hardware status every 10 seconds

**Hardware Abstraction**: All hardware control goes through `hardware_comms.py` which provides a consistent interface regardless of whether using real hardware or mocks.

**Error Handling**: Comprehensive error handling with user notifications through toast system and Flask flash messages.

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
1. Create a single `.svelte` file in appropriate directory (`src/routes/` or `src/lib/components/`)
2. Add corresponding entry point in root directory (e.g., `newpage.js`)
3. Update `vite.config.js` to include new entry point
4. Create Flask template in `templates/` directory to mount the component

See `SVELTE_REFERENCE.md` for complete syntax guide.

## Hardware Communication Protocols (PROVEN WORKING)

These protocols are extracted from `simple_gui.py` and are proven to work correctly with the Pi4B hardware. **All future hardware communication must follow these exact patterns.**

### Command Structure
All hardware commands use this exact format:
```
"Start;{COMMAND_TYPE};{ID};{PARAMETER};end"
```

### Relay Control
```python
# Single relay control (exact pattern from simple_gui.py:1063)
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
# Pump dispensing (exact pattern from simple_gui.py:1095)
command = f"Start;Dispense;{pump_id};{amount};end"
success = system.send_command(command)

# Pump stop (exact pattern from simple_gui.py:1113)
command = f"Start;Pump;{pump_id};X;end"
success = system.send_command(command)
```

**Validation Rules:**
- `pump_id` must be in `get_available_pumps()`
- `amount` must be between `MIN_PUMP_VOLUME_ML` and `MAX_PUMP_VOLUME_ML`
- Stop command uses "X" as parameter

### Flow Meter Control
```python
# Start flow monitoring (exact pattern from simple_gui.py:1139)
command = f"Start;StartFlow;{flow_id};{gallons};220;end"
success = system.send_command(command)

# Stop flow monitoring (exact pattern from simple_gui.py:1155)  
command = f"Start;StartFlow;{flow_id};0;end"
success = system.send_command(command)
```

**Validation Rules:**
- `flow_id` must be in `get_available_flow_meters()`
- `gallons` must be between 1 and `MAX_FLOW_GALLONS`
- Stop uses `gallons=0`
- Note: "220" is calibration parameter (pulses per gallon)

### EC/pH Control
```python
# Start EC/pH monitoring (exact pattern from simple_gui.py:1167)
command = "Start;EcPh;ON;end"
success = system.send_command(command)

# Stop EC/pH monitoring (exact pattern from simple_gui.py:1178)
command = "Start;EcPh;OFF;end"
success = system.send_command(command)
```

### System Initialization (CRITICAL)
```python
# Exact pattern from simple_gui.py:895-896
use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
system = FeedControlSystem(use_mock_flow=use_mock_flow)
system.start()
```

### Emergency Stop
```python
# Emergency stop all operations (exact pattern from simple_gui.py:1210)
system.emergency_stop()
```

**IMPORTANT NOTES:**
1. **Never modify these command formats** - they are hardcoded in the hardware controllers
2. **Always validate inputs** using the config functions before sending commands
3. **Use threading** for system initialization to avoid blocking the UI
4. **Commands are case-sensitive** - "ON"/"OFF" must be uppercase
5. **The hardware_comms.py module** implements these exact patterns and should be used for all hardware communication

## Complete Command Reference

See `HARDWARE_COMMANDS.md` for the comprehensive command reference including:
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