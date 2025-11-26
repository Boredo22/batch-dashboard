# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **Nutrient Mixing System** for commercial hydroponics/agriculture operations with a modern web-based architecture:
- **Backend**: Flask REST API server (`app.py`) providing comprehensive hardware control endpoints
- **Frontend**: Svelte 5 single-page application with Vite build system in the `frontend/` directory
- **Hardware**: Direct control of physical devices (pumps, relays, flow meters, EC/pH sensors) on Raspberry Pi 4B

The system controls physical hardware through a robust hardware abstraction layer, supporting both real hardware and mock mode for development without physical devices.

### Key Components

**Backend (Python)**:
- `app.py` - Flask REST API server with comprehensive endpoints for all hardware control
- `main.py` - Core `FeedControlSystem` class with proven hardware communication patterns
- `hardware/hardware_comms.py` - Hardware abstraction layer using exact patterns from working `simple_gui.py`
- `hardware/rpi_pumps.py` - EZO peristaltic pump I2C controller
- `hardware/rpi_relays.py` - ULN2803A relay GPIO controller with state persistence
- `hardware/rpi_flow.py` - Flow meter pulse counter (GPIO-based)
- `hardware/rpi_unoComm.py` - Arduino Uno serial communication for EC/pH sensors
- `hardware/rpi_ezo_sensors.py` - EZO EC/pH sensor I2C controller (background monitoring)
- `hardware/mock_controllers.py` - Mock hardware for development without physical devices
- `config.py` - Centralized system configuration with all hardware mappings and settings
- `hardware_safety.py` - Safety lockfile system to prevent multiple instances
- `ezo_ph_ec_controller.py` - Background monitoring service for EZO pH/EC sensors
- `simple_gui.py` - **REFERENCE ONLY** - Original working GUI (DO NOT MODIFY)

**Frontend (Svelte 5)**:
- `frontend/src/App.svelte` - Main application shell with page routing and navigation
- `frontend/src/HeadGrower.svelte` - Main operations interface (redesigned UI)
- `frontend/src/Nutrients.svelte` - Manual nutrient dispensing and recipe management
- `frontend/src/Dashboard.svelte` - Stage 1: Individual hardware testing interface
- `frontend/src/Stage2Testing.svelte` - Stage 2: Job process testing interface
- `frontend/src/Settings.svelte` - System configuration management
- `frontend/src/components/` - **LEGACY** component library (being migrated)
- `frontend/src/lib/components/` - **NEW** component library with modern architecture:
  - `growers/` - Redesigned growers dashboard components
  - `hardware/` - Hardware control card components
  - `layout/` - Sidebar, header, and layout components
  - `ui/` - Shadcn-style UI primitives (Button, Card, Input, etc.)
- `frontend/src/main.js` - Single entry point for the Svelte application

**Hardware Control System**:
- `FeedControlSystem` class in `main.py` - Core system with proven command processing
- Direct hardware controllers for pumps, relays, flow meters, and Arduino communication
- Uses exact same command protocols as the working `simple_gui.py` implementation
- **Relay state persistence** - Relays maintain state across backend restarts
- Background EC/pH monitoring with real-time sensor data

## Specialized Development Agents

This project includes two specialized AI agents defined in `.claude/agents/` for domain-specific development:

### backend-hardware-dev Agent
**Use for**: Python backend work, hardware communication (serial/GPIO), Flask APIs, hardware integration

**Expertise**:
- Python backend development with hardware integration focus
- Serial communication, GPIO control, embedded system interfaces
- Flask REST API design for hardware control systems
- Hardware abstraction layers and communication protocols
- Real-time data streaming and hardware status monitoring
- Error handling and recovery for hardware failures

**Philosophy**: Conservative development with emphasis on stability, proven patterns, and hardware safety. Always examines existing working code patterns before implementing changes.

### svelte5-ui-designer Agent
**Use for**: Frontend UI design, Svelte 5 components, dashboard layouts, visual design improvements

**Expertise**:
- Svelte 5 runes ($state, $derived, $effect, $props)
- Dark mode design with purple and green accent colors
- Component architecture for internal business dashboards
- Responsive design (mobile/tablet/desktop)
- Modern CSS (Grid, Flexbox, animations)
- Accessibility best practices (WCAG compliance)

**Philosophy**: Dark-first design with professional aesthetics, high information density while maintaining readability, reusable component patterns, optimized performance.

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
python simple_gui.py # Original working GUI (reference implementation)
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

## Recent Features & Improvements

### Relay State Persistence (November 2024)
The relay controller now **preserves relay states across backend restarts** by reading the current GPIO pin state during initialization. This prevents disruption to active operations when restarting the Flask backend during development.

**How it works**:
1. On initialization, each relay pin is temporarily claimed as input
2. Current GPIO state is read and interpreted based on relay configuration (Active HIGH/LOW)
3. Pin is reclaimed as output and same state is written back
4. Internal state tracking is updated to match physical state

**Benefits**:
- No disruption to active filling/mixing operations during backend restarts
- Frontend automatically syncs with actual relay states on reload
- Clear logging shows exact state of each relay at startup
- Recovery from backend crashes maintains physical relay state

See `RELAY_STATE_PERSISTENCE.md` for detailed documentation.

### Background EC/pH Monitoring
EZO EC and pH sensors can be monitored in the background using a dedicated controller:
- Real-time sensor readings via I2C communication
- Automatic calibration support for both EC and pH sensors
- Integration test suite (`test_ecph_integration.py`, `test_ecph_realtime.py`)
- API endpoints for starting/stopping monitoring and reading current values

### UI Redesign (In Progress)
**Component Library Migration**:
- OLD: `frontend/src/components/` (legacy components)
- NEW: `frontend/src/lib/components/` (modern shadcn-svelte architecture)
- Tailwind CSS + custom design system
- Professional Lucide icons replacing emoji
- Responsive design optimized for mobile/tablet/desktop

**New Pages**:
- `HeadGrower.svelte` - Main operations interface with 3D tank visualizations
- Enhanced nutrient dosing interface with visual controls
- Activity log and real-time operations monitoring

**UI Components**:
- Card-based layout system
- Sidebar navigation with collapsible sections
- Progress indicators for dispensing operations
- Status badges and alerts for hardware state
- Form controls with validation

### Safety & Configuration
- Hardware safety lockfile (`/tmp/.nutrient_mixing_system.lock`) prevents multiple instances
- Emergency stop functionality accessible via API and hardware
- Comprehensive error handling with user notifications
- Mock hardware mode for development without physical devices
- Settings management (user preferences and developer settings)

## Key Patterns

**State Management**: Uses Svelte 5 runes (`$state`, `$derived`, `$effect`) for reactive state management directly in components.

**API Communication**: 
- REST endpoints follow pattern `/api/{hardware_type}/{id}/{action}`
- Direct fetch calls from Svelte components to Flask API endpoints
- Real-time status updates through periodic polling

**Hardware Abstraction**: All hardware control goes through `hardware_comms.py` which provides a consistent interface using proven working patterns from `simple_gui.py`.

**Multi-Stage Testing Architecture**:
- **Head Grower**: Main operations page with tank management and nutrient dispensing
- **Nutrients**: Manual nutrient dispensing with recipe save/load/delete functionality
- **Stage 1 (Dashboard)**: Individual hardware component testing (relays, pumps, flow meters, EC/pH)
- **Stage 2 (Stage2Testing)**: Complete job process testing (fill, mix, send operations)
- **Settings**: System configuration management with user and developer settings

**Error Handling**: Comprehensive error handling with user notifications and detailed logging throughout the system.

## Hardware Configuration

### Pumps (Atlas Scientific EZO-PMP)
- **8 peristaltic pumps** via I2C bus (addresses 11-18, or 0x0B-0x12 hex)
- Calibratable for precise dosing (volume range: 0.5ml - 2500ml per dispense)
- Status monitoring: dispensing, paused, stopped, voltage levels
- Commands: Dispense volume, stop, pause, calibrate, clear calibration

| ID | Name | I2C Address | Function |
|----|------|-------------|----------|
| 1 | Veg A | 11 (0x0B) | Vegetative nutrient A |
| 2 | Veg B | 12 (0x0C) | Vegetative nutrient B |
| 3 | Bloom A | 13 (0x0D) | Bloom nutrient A |
| 4 | Bloom B | 14 (0x0E) | Bloom nutrient B |
| 5 | Cake | 15 (0x0F) | Specialized additive |
| 6 | PK Synergy | 16 (0x10) | Phosphorus/Potassium booster |
| 7 | Runclean | 17 (0x11) | System cleaning solution |
| 8 | pH Down | 18 (0x12) | pH adjustment |

### Relays (ULN2803A Darlington Array)
- **13 relays** controlled via GPIO pins
- Control solenoid valves for tank operations
- Active HIGH logic (GPIO HIGH = Relay ON due to ULN2803A inversion)
- State persistence across restarts

**Key Relay Mappings**:
- Relays 1-3: Tank fill valves (Tank 1, 2, 3)
- Relays 4-6: Tank nutrient dispense valves
- Relays 7-9: Tank send valves (delivery to grow rooms)
- Relay 10: Room 1, Relay 12: Nursery, Relay 13: Drain
- Relay 0: Special ID for "all relays off" emergency command

### Flow Meters
- **2 pulse-based flow meters** (GPIO pins 24, 23)
- Measurement: 220 pulses per gallon
- Monitor water fill and send operations
- Range: 1-100 gallons per operation

### EC/pH Sensors
**Option 1: Arduino Uno (Serial Communication)**
- Serial port: /dev/ttyACM0 (115200 baud)
- Provides EC (electrical conductivity) and pH readings
- Commands: Start monitoring, stop monitoring

**Option 2: EZO EC/pH Sensors (I2C)**
- Direct I2C communication with EZO sensors
- Background monitoring capability
- Calibration support for both EC and pH
- Real-time readings for precise nutrient management

### Tank Configuration
- **Tank 1**: 100 gallons
- **Tank 2**: 100 gallons
- **Tank 3**: 35 gallons
- Each tank supports: Fill → Mix (with nutrient dosing) → Send operations

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
1. Create a single `.svelte` file in appropriate directory (`frontend/src/` for pages or `frontend/src/components/` for reusable components)
2. Import and use the component in the relevant parent component or page
3. No need to update build configuration - Vite handles imports automatically
4. Flask serves the built frontend as static files

See `SVELTE_REFERENCE.md` for complete syntax guide.

## REST API Endpoints

The Flask backend exposes comprehensive REST API endpoints for hardware control and system management.

### Hardware Control Endpoints

**Relay Control**:
```
POST /api/relay/{id}/on          # Turn relay on
POST /api/relay/{id}/off         # Turn relay off
POST /api/relay/{id}/toggle      # Toggle relay state
POST /api/relay/0/off            # Turn ALL relays off (emergency)
GET  /api/relay/states           # Get all relay states
```

**Pump Control**:
```
POST /api/pump/{id}/dispense     # Dispense volume (body: {amount_ml: number})
POST /api/pump/{id}/stop         # Stop pump immediately
POST /api/pump/{id}/pause        # Pause pump operation
POST /api/pump/{id}/calibrate    # Calibrate pump (body: {volume_ml: number})
POST /api/pump/{id}/clear_calibration  # Clear pump calibration
GET  /api/pump/{id}/status       # Get pump status and progress
GET  /api/pump/{id}/voltage      # Get pump voltage
GET  /api/pumps/refresh_calibrations  # Refresh all pump calibrations
```

**Flow Meter Control**:
```
POST /api/flow/{id}/start        # Start flow meter (body: {gallons: number})
POST /api/flow/{id}/stop         # Stop flow meter
GET  /api/flow/{id}/status       # Get current flow status
```

**EC/pH Sensor Control**:
```
POST /api/ecph/start             # Start EC/pH monitoring
POST /api/ecph/stop              # Stop EC/pH monitoring
GET  /api/ecph/read              # Read current EC/pH values
POST /api/ecph/calibrate_ph      # Calibrate pH sensor (body: {point: 4|7|10, temp: number})
POST /api/ecph/calibrate_ec      # Calibrate EC sensor (body: {point: 'dry'|number, temp: number})
GET  /api/ecph/calibration_status # Get calibration status
```

### System Management Endpoints

**Status and Hardware Info**:
```
GET  /api/hardware/status        # Get complete hardware status
GET  /api/system/status          # System health check
GET  /api/status                 # Complete system status (alias)
POST /api/emergency_stop         # Emergency stop all operations
```

**Settings Management**:
```
GET  /api/settings/user          # Get user settings
POST /api/settings/user          # Update user settings (body: JSON settings)
GET  /api/settings/developer     # Get developer settings
POST /api/settings/developer     # Update developer settings (body: JSON settings)
```

**Nutrient Management**:
```
GET  /api/nutrients              # Get nutrients configuration
GET  /api/nutrients/recipes      # Get all saved recipes
POST /api/nutrients/save_recipe  # Save new recipe (body: {name, pumps})
POST /api/nutrients/delete_recipe # Delete recipe (body: {name})
```

**Response Format**:
All endpoints return JSON with consistent format:
```json
{
  "success": true|false,
  "message": "Human-readable message",
  "data": { /* Response data */ },
  "error": "Error details (if success: false)"
}
```

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

## Project File Structure

```
/home/pi/batch-dashboard/
├── .claude/                        # Claude AI guidance files
│   ├── CLAUDE.md                  # This file
│   ├── agents/
│   │   ├── backend-hardware-dev.md    # Backend development agent
│   │   └── svelte5-ui-designer.md     # Frontend UI design agent
│
├── .docs/                          # Project documentation
│   ├── HARDWARE_COMMANDS.md       # Complete hardware command reference
│   └── shadcn_redesign.md         # UI redesign migration guide
│
├── hardware/                       # Hardware control modules
│   ├── hardware_comms.py          # Main hardware abstraction layer
│   ├── rpi_pumps.py              # EZO pump I2C controller
│   ├── rpi_relays.py             # Relay GPIO controller
│   ├── rpi_flow.py               # Flow meter controller
│   ├── rpi_unoComm.py            # Arduino serial communication
│   ├── rpi_ezo_sensors.py        # EZO sensor I2C controller
│   ├── mock_controllers.py       # Mock hardware for testing
│   └── utilities/                # Utility modules
│       ├── relay_control.py
│       └── relayMap.py
│
├── frontend/                       # Svelte 5 application
│   ├── src/
│   │   ├── main.js               # Application entry point
│   │   ├── App.svelte            # Main app shell with routing
│   │   ├── HeadGrower.svelte     # Main operations page
│   │   ├── Nutrients.svelte      # Manual nutrient dispensing
│   │   ├── Dashboard.svelte      # Stage 1 hardware testing
│   │   ├── Stage2Testing.svelte  # Stage 2 job testing
│   │   ├── Settings.svelte       # System configuration
│   │   │
│   │   ├── components/           # LEGACY component library
│   │   │   ├── PumpControl.svelte
│   │   │   ├── RelayGrid.svelte
│   │   │   ├── FlowMeterControl.svelte
│   │   │   ├── ECPHMonitor.svelte
│   │   │   └── ...
│   │   │
│   │   └── lib/                  # NEW component library
│   │       ├── components/
│   │       │   ├── growers/      # Growers dashboard
│   │       │   ├── hardware/     # Hardware control cards
│   │       │   ├── layout/       # Sidebar, header, layout
│   │       │   └── ui/           # Shadcn UI primitives
│   │       ├── transitions.js    # Svelte transitions
│   │       └── utils.js          # Utility functions
│   │
│   ├── static/dist/              # Build output directory
│   ├── package.json              # Frontend dependencies
│   ├── vite.config.js            # Vite build configuration
│   └── tailwind.config.js        # Tailwind CSS configuration
│
├── app.py                         # Flask REST API server (MAIN BACKEND)
├── main.py                        # FeedControlSystem core class
├── config.py                      # Hardware configuration
├── hardware_safety.py             # Safety lockfile system
├── ezo_ph_ec_controller.py       # Background EC/pH monitoring
├── simple_gui.py                  # REFERENCE ONLY - Original working GUI
├── nutrients.json                 # Nutrient recipes and formulas
├── requirements.txt               # Python dependencies
├── PROJECT_REFRESHER.md           # Project overview and recent changes
├── RELAY_STATE_PERSISTENCE.md    # Relay state persistence documentation
├── ToDo.md                        # Project todo list
│
└── test_ecph_*.py                # EC/pH integration tests
```

## Development Best Practices

### Backend Development

**1. Hardware Safety First**
- Always check the safety lockfile before starting the Flask app
- Use `hardware_safety.py` to prevent multiple instances
- Implement proper error handling for all hardware operations
- Test with mock hardware first before using real devices

**2. Follow Proven Patterns**
- Study `simple_gui.py` before modifying hardware communication
- Use exact command formats from working implementation
- Never modify command protocols without testing extensively
- Preserve backward compatibility with frontend interfaces

**3. Configuration Management**
- All hardware mappings in `config.py` (single source of truth)
- Use mock settings for development: `MOCK_SETTINGS = {'pumps': True, ...}`
- Validate all inputs against config constants before sending commands
- Log all hardware commands and responses for debugging

**4. Error Handling**
- Implement comprehensive try-catch blocks for hardware operations
- Return consistent JSON responses with success/error status
- Log errors with sufficient context for troubleshooting
- Provide meaningful error messages to frontend users

### Frontend Development

**1. Svelte 5 Conventions**
- Always use Svelte 5 runes: `$state()`, `$derived()`, `$effect()`, `$props()`
- Never use legacy reactive syntax (`$:`)
- Single `.svelte` files containing script, template, and styles
- Component props using `$props()` destructuring

**2. Component Organization**
- NEW components go in `src/lib/components/` (modern architecture)
- Reusable UI primitives in `src/lib/components/ui/`
- Domain-specific components in appropriate subdirectories
- Legacy components in `src/components/` (being migrated)

**3. API Communication**
- Use consistent fetch patterns with error handling
- Poll for status updates at appropriate intervals
- Handle loading states and errors in UI
- Display user-friendly error messages

**4. Responsive Design**
- Test on mobile, tablet, and desktop viewports
- Use Tailwind responsive utilities (`sm:`, `md:`, `lg:`)
- Optimize for 10" tablet as primary grower interface
- Dark mode as default theme

### Testing Workflow

**1. Development Cycle**
```bash
# Terminal 1: Backend with mock hardware
python app.py

# Terminal 2: Frontend dev server
cd frontend && npm run dev

# Browser: http://localhost:5173
```

**2. Hardware Testing Sequence**
- Start with Stage 1 (individual component testing)
- Verify each hardware type works correctly
- Move to Stage 2 (job process testing)
- Test complete workflows (fill → mix → send)
- Use Settings page to toggle mock/real hardware

**3. Production Deployment**
```bash
# Build frontend
cd frontend && npm run build

# Verify build output
ls -la frontend/static/dist/

# Start Flask (serves built frontend)
python app.py

# Access: http://<raspberry-pi-ip>:5000
```

## Troubleshooting

### Common Issues

**1. Hardware Not Responding**
```bash
# Check safety lockfile
ls -la /tmp/.nutrient_mixing_system.lock

# Remove if stale (ensure no other instance running)
rm /tmp/.nutrient_mixing_system.lock

# Check I2C devices (pumps should be at 0x0B-0x12)
i2cdetect -y 1

# Check GPIO pins availability
python hardware/gpio_monitor.py
```

**2. I2C Communication Errors**
```bash
# Enable I2C interface
sudo raspi-config
# Interface Options → I2C → Enable

# Check I2C bus
ls -la /dev/i2c-*

# Verify pump addresses
i2cdetect -y 1
```

**3. Port Already in Use**
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

**4. Frontend Build Issues**
```bash
cd frontend

# Clean install
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build
```

**5. GPIO Permission Errors**
```bash
# Run with sudo if needed
sudo python app.py

# Or add user to gpio group
sudo usermod -a -G gpio $USER
```

**6. Serial Port Access (Arduino)**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Check port exists
ls -la /dev/ttyACM0

# Verify permissions
sudo chmod 666 /dev/ttyACM0
```

### Debug Mode

Enable verbose logging in `config.py`:
```python
DEBUG_MODE = True
VERBOSE_LOGGING = True
LOG_LEVEL = "DEBUG"
```

### Mock Hardware Development

Configure mock devices in `config.py`:
```python
MOCK_SETTINGS = {
    'pumps': True,        # Use mock pumps (no I2C required)
    'relays': False,      # Use real relays
    'flow_meters': True,  # Use mock flow meters
    'arduino': True       # Use mock Arduino (no serial required)
}
```

## Additional Documentation

- **`PROJECT_REFRESHER.md`** - Comprehensive project overview and recent changes
- **`RELAY_STATE_PERSISTENCE.md`** - Relay state persistence implementation details
- **`.docs/HARDWARE_COMMANDS.md`** - Complete hardware command reference
- **`.docs/shadcn_redesign.md`** - UI redesign migration guide
- **`ToDo.md`** - Project roadmap and implementation notes

## Safety Rules & Reminders

1. **NEVER modify `simple_gui.py`** - It's the proven reference implementation
2. **NEVER change hardware command formats** - They're hardcoded in controllers
3. **ALWAYS validate inputs** before sending hardware commands
4. **ALWAYS check lockfile** before starting Flask app
5. **EMERGENCY STOP**: `POST /api/emergency_stop` or relay ID 0 OFF
6. **Test with mock hardware** before using real devices
7. **Study existing code** before implementing hardware changes
8. **Preserve proven patterns** from working implementations
9. **Log all hardware operations** for debugging and auditing
10. **Handle errors gracefully** with user-friendly messages

---

**This system is production-ready and actively used in commercial agriculture operations. Maintain stability and reliability as top priorities in all development work.**