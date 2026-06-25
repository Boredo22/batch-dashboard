# Batch Dashboard - Project Refresher

**Last Updated**: June 24, 2026
**Current Branch**: newTablet
**Status**: Active Development - post dead-code cleanup, tablet UI phase

---

## 🎯 Project Overview

This is a **Nutrient Mixing System** for commercial hydroponics/agriculture operations. It controls physical hardware (pumps, relays, flow meters, EC/pH sensors) through a modern web-based interface running on a Raspberry Pi.

### What It Does
- **Mixes nutrient solutions** by precisely dispensing liquid nutrients into water tanks
- **Controls tank operations**: fill with water, mix nutrients, send to grow rooms
- **Monitors water quality**: EC (electrical conductivity) and pH via direct-I2C Atlas Scientific EZO circuits
- **Manages multiple tanks**: 3 tanks with different capacities (100, 100, 35 gallons)
- **Tracks flow**: 2 flow meters for water fill and send operations
- **8 peristaltic pumps**: Each pump dispenses a specific nutrient (Veg A/B, Bloom A/B, Cake, PK Synergy, Runclean, pH Down)

---

## 🏗️ Architecture

### Two-Tier System

**Backend (Python/Flask)**
- REST API server exposing hardware control endpoints
- Direct hardware communication (I2C for pumps and EC/pH EZO sensors, GPIO for relays/flow meters, USB serial for per-tank Arduino tank monitors)
- Route handlers wrapped with the `@api_endpoint` decorator (standard JSON error envelope)
- Runs on Raspberry Pi 4B
- Port: 5000

**Frontend (Svelte 5/Vite)**
- Modern single-page application
- Real-time hardware status monitoring
- Responsive design (mobile/tablet/desktop)
- Dev server: Port 5173 (proxies to Flask)
- Production: Served as static files by Flask

---

## 📂 File Structure

```
/home/pi/batch-dashboard/
├── app.py                      # Flask REST API server (MAIN BACKEND); @api_endpoint decorator
├── main.py                     # Core FeedControlSystem class; owns shared I2C lock
├── config.py                   # Centralized configuration (ALL hardware mappings); validates relay refs at import
├── grow_cycles.py              # Pure grow-cycle report logic (build_reports)
├── hardware_safety.py          # Safety lockfile system (atomic O_CREAT|O_EXCL)
├── nutrients.json              # Nutrient formulas and recipes
├── simple_gui.py               # REFERENCE: Original working GUI (DON'T MODIFY)
│
├── hardware/                   # Hardware controllers
│   ├── hardware_comms.py       # Main hardware abstraction layer
│   ├── rpi_pumps.py           # EZO pump I2C controller
│   ├── rpi_relays.py          # ULN2803A relay GPIO controller
│   ├── rpi_flow.py            # Flow meter pulse counter
│   ├── rpi_ezo_sensors.py     # EC/pH via direct I2C EZO circuits (EZOSensorController, MockEZOSensorController)
│   ├── tank_monitor.py        # Per-tank Arduino tank monitors (USB serial)
│   └── mock_controllers.py    # Mock hardware for development
│
└── frontend/                   # Svelte 5 application
    ├── src/
    │   ├── main.js            # Entry point
    │   ├── App.svelte         # Router (globalThis.navigateTo) + svelte-sonner Toaster
    │   ├── Dashboard.svelte   # Stage 1: Individual hardware testing
    │   ├── FillTank.svelte    # Stage 2: Job process (fill/mix/send)
    │   ├── Settings.svelte    # System configuration
    │   ├── HeadGrower.svelte  # Main operations page (-> lib/components/growers/growers-dashboard.svelte)
    │   ├── Nutrients.svelte   # Manual nutrient dispensing
    │   ├── GrowCycles.svelte  # Grow-cycle reports
    │   ├── Knowledge.svelte   # Knowledge / reference page
    │   │
    │   ├── lib/
    │   │   ├── api.js                        # Shared API client (apiGet, apiPost, ApiError, 15s timeout)
    │   │   ├── stores/systemStatus.svelte.js # SSE store (EventSource + polling fallback)
    │   │   └── components/                   # Modern component library
    │   │       ├── growers/                  # Redesigned growers dashboard
    │   │       ├── hardware/                 # Hardware control cards
    │   │       ├── layout/                   # Layout components
    │   │       └── ui/                       # Shadcn-style UI primitives
    │   │
    │   └── components/filltank/  # Components used by FillTank.svelte
    │       ├── ConfigPanel.svelte
    │       ├── DiagnosticsPanel.svelte
    │       ├── SystemLog.svelte
    │       └── WorkflowFlowchart.svelte
    │
    ├── package.json
    └── vite.config.js
```

---

## 🔧 Hardware Configuration

### Pumps (Atlas Scientific EZO-PMP)
- **8 pumps** via I2C (addresses 11-18)
- Calibratable peristaltic pumps
- Volume range: 0.5ml - 2500ml per dispense
- Commands: `Start;Dispense;{id};{ml};end`, `Start;Pump;{id};X;end` (stop)

| ID | Name | Address |
|----|------|---------|
| 1 | Veg A | 11 |
| 2 | Veg B | 12 |
| 3 | Bloom A | 13 |
| 4 | Bloom B | 14 |
| 5 | Cake | 15 |
| 6 | PK Synergy | 16 |
| 7 | Runclean | 17 |
| 8 | pH Down | 18 |

### Relays (ULN2803A Darlington Array)
- **13 relays** via GPIO pins
- Control water valves for tank operations
- Commands: `Start;Relay;{id};ON;end`, `Start;Relay;{id};OFF;end`
- Emergency: `Start;Relay;0;OFF;end` (all off)

Key relays:
- 1-3: Tank fill valves
- 4-6: Tank nute dispense valves
- 7-9: Tank send valves
- 10: Room 1, 12: Nursery, 13: Drain

### Flow Meters
- **2 flow meters** (GPIO 24, 23)
- Pulse-based measurement (220 pulses/gallon)
- Commands: `Start;StartFlow;{id};{gallons};220;end`
- Stop: `Start;StartFlow;{id};0;end`

### EC/pH Sensors (Atlas Scientific EZO, direct I2C)
- EZO pH at I2C `0x63`, EZO EC at I2C `0x64`
- Read directly over I2C via `hardware/rpi_ezo_sensors.py` (`EZOSensorController`; `MockEZOSensorController` for mock mode)
- NOT Arduino/serial. The `Start;EcPh;ON/OFF;end` strings remain only as the frozen `simple_gui.py` reference protocol.

### Tank Monitors (per-tank Arduino, USB serial)
- Separate from EC/pH: per-tank Arduino "tank monitors" over USB serial via `hardware/tank_monitor.py`

---

## 🚀 Development Workflow

### Starting the System

**Backend Only:**
```bash
python app.py
# Flask API runs on http://localhost:5000
```

**Frontend Development:**
```bash
cd frontend
npm run dev
# Vite dev server on http://localhost:5173 (with HMR)
# API calls auto-proxy to Flask on :5000
```

**Full Stack:**
1. Terminal 1: `python app.py`
2. Terminal 2: `cd frontend && npm run dev`
3. Open http://localhost:5173

**Production Build:**
```bash
cd frontend
npm run build  # Outputs to frontend/static/dist/
# Flask serves built files from /static/dist
```

### Key Commands
```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install

# Mock hardware mode (edit config.py)
MOCK_SETTINGS = {
    "pumps": True,        # Use mock pumps
    "relays": False,      # Use real relays
    "flow_meters": True,  # Use mock flow meters
    "ezo_sensors": True   # Use mock EC/pH (MockEZOSensorController)
}
```

---

## 🎨 Recent Major Changes (Last 2 Months)

### Recent cleanup (June 2026)
1. **Dead-code purge (~8k lines)** - removed the legacy single-component set under `frontend/src/components/` (ECPHMonitor, FlowMeterControl, RelayGrid, PumpControl, NuteDispenseProgress, Nutrients, PumpCalibration, FillJobTesting, SendJobTesting, MixJobTesting, SystemLog), `Stage2Testing.svelte` (replaced by `FillTank.svelte`), and three dead backend EC/pH modules (`hardware/rpi_unoComm.py`, `hardware/rpi_sensors.py`, `ezo_ph_ec_controller.py`).
2. **Shared frontend API client** - `frontend/src/lib/api.js` (`apiGet`/`apiPost`/`ApiError`, 15s timeout); all backend calls go through it (no raw `fetch()` in pages); errors surface as svelte-sonner toasts. Live status via the SSE store `lib/stores/systemStatus.svelte.js`.
3. **`@api_endpoint` decorator** - in `app.py`, wraps handlers with the standard try/except JSON error envelope; new handlers should use it.
4. **`grow_cycles.py` extraction** - pure/testable grow-cycle logic (stage detection, recipe selection, EC/pH targets, dose scaling); `/api/grow-cycles/report` calls `build_reports()`.
5. **Hardware safety** - pump + sensor controllers share one I2C lock (created in `main.py`'s `FeedControlSystem`) to serialize the bus; the instance lockfile in `hardware_safety.py` is now atomic (`O_CREAT|O_EXCL`); `config.py` validates relay references at import.
6. **Mock EC/pH** - `MockEZOSensorController` in `hardware/rpi_ezo_sensors.py` for mock-mode EC/pH.

### UI Redesign (Branch: newTablet)
1. **New Head Grower Page** - Complete redesign with modern dashboard
   - `HeadGrower.svelte` - Main operations interface
   - Uses `growers-dashboard.svelte` component (comprehensive redesign)
   - Professional icons (replaced emojis)
   - 3D tank visualizations with fill levels
   - Enhanced nutrient dosing interface
   - Responsive design (mobile/tablet/desktop)

2. **Component Library Migration** (now complete)
   - Modern library lives in `frontend/src/lib/components/` (`growers/`, `hardware/`, `layout/`, `ui/`)
   - Legacy single-component set under `frontend/src/components/` has been deleted; only the `filltank/` subdir remains
   - Using Tailwind CSS + custom design system
   - Lucide icons for professional UI

3. **Settings System**
   - User settings: Mix times, flow rates, preferences
   - Developer settings: Mock hardware, debug modes
   - API endpoints: GET/POST `/api/settings/user`, `/api/settings/developer`

4. **Pump Calibration Improvements**
   - Caching system to reduce I2C checks
   - Real-time calibration status
   - Voltage monitoring (every 5 minutes)

### Safety Features
- Hardware safety lockfile (`/tmp/.nutrient_mixing_system.lock`)
- Prevents multiple instances from controlling hardware
- Emergency stop functionality

---

## 📋 Application Pages

### 1. Head Grower (Main Operations)
- **Path**: `currentPage = 'headgrower'`
- **File**: `HeadGrower.svelte` → uses `growers-dashboard.svelte`
- **Purpose**: Complete growing operations
- **Features**:
  - Tank status visualization
  - Fill/Mix/Send operations per tank
  - Nutrient dosing with visual controls
  - Active operations monitoring
  - Flow meter status
  - Activity log

### 2. Nutrients (Manual Dispensing)
- **Path**: `currentPage = 'nutrients'`
- **File**: `Nutrients.svelte`
- **Purpose**: Manual nutrient dispensing and recipe management
- **Features**:
  - Individual pump control with amount sliders
  - Recipe save/load/delete
  - Pump calibration interface
  - Real-time dispense progress
  - Total volume calculation

### 3. Stage 1 Testing (Hardware Testing)
- **Path**: `currentPage = 'stage1'`
- **File**: `Dashboard.svelte`
- **Purpose**: Individual component testing
- **Features**:
  - Relay on/off controls
  - Pump dispense controls
  - Flow meter start/stop
  - EC/pH monitoring toggle
  - System logs

### 4. Stage 2 (Job Process)
- **Path**: `currentPage = 'stage2'`
- **File**: `FillTank.svelte` (components under `frontend/src/components/filltank/`)
- **Purpose**: Complete job process (fill/mix/send)
- **Features**:
  - Fill job
  - Mix job
  - Send job
  - Multi-step process validation

> Note: additional pages exist — `GrowCycles.svelte` (grow-cycle reports) and `Knowledge.svelte` (reference).

### 5. Settings
- **Path**: `currentPage = 'settings'`
- **File**: `Settings.svelte`
- **Purpose**: System configuration
- **Features**:
  - User preferences
  - Developer settings
  - Mock hardware toggles
  - System parameters

---

## 🔌 API Endpoints Reference

### Hardware Control
```
GET    /api/hardware/status              # Get all hardware status
POST   /api/relay/{id}/toggle            # Toggle relay on/off
POST   /api/relay/{id}/on                # Turn relay on
POST   /api/relay/{id}/off               # Turn relay off
POST   /api/relay/0/off                  # ALL RELAYS OFF (emergency)

POST   /api/pump/{id}/dispense           # Dispense {amount_ml}
POST   /api/pump/{id}/stop               # Stop pump
POST   /api/pump/{id}/calibrate          # Calibrate pump {volume_ml}
POST   /api/pump/{id}/clear_calibration  # Clear calibration
POST   /api/pump/{id}/pause              # Pause pump
GET    /api/pump/{id}/voltage            # Get pump voltage
GET    /api/pump/{id}/status             # Get pump status

POST   /api/flow/{id}/start              # Start flow {gallons}
POST   /api/flow/{id}/stop               # Stop flow

POST   /api/ecph/start                   # Start EC/pH monitoring
POST   /api/ecph/stop                    # Stop EC/pH monitoring

POST   /api/emergency_stop               # EMERGENCY STOP ALL
```

### System Management
```
GET    /api/status                       # Complete system status
GET    /api/system/status                # System health check
GET    /api/settings/user                # Get user settings
POST   /api/settings/user                # Update user settings
GET    /api/settings/developer           # Get dev settings
POST   /api/settings/developer           # Update dev settings
```

### Nutrients
```
GET    /api/nutrients                    # Get all nutrients config
POST   /api/nutrients/save_recipe        # Save new recipe
POST   /api/nutrients/delete_recipe      # Delete recipe
GET    /api/nutrients/recipes            # Get all recipes
```

---

## ⚠️ Important Patterns

### Hardware Command Protocol (DO NOT CHANGE)
All hardware commands follow this exact format from `simple_gui.py`:
```
"Start;{COMMAND_TYPE};{ID};{PARAMETER};end"
```

Examples:
```python
# Relay control
"Start;Relay;1;ON;end"      # Turn relay 1 on
"Start;Relay;1;OFF;end"     # Turn relay 1 off
"Start;Relay;0;OFF;end"     # All relays off

# Pump control
"Start;Dispense;1;100;end"  # Pump 1 dispense 100ml
"Start;Pump;1;X;end"        # Pump 1 stop

# Flow meter
"Start;StartFlow;1;10;220;end"  # Flow meter 1, 10 gallons
"Start;StartFlow;1;0;end"       # Flow meter 1 stop

# EC/pH
"Start;EcPh;ON;end"         # Start monitoring
"Start;EcPh;OFF;end"        # Stop monitoring
```

### Svelte 5 Runes (REQUIRED)
```svelte
<script>
  // Use $state() for reactive variables
  let count = $state(0);

  // Use $derived() for computed values
  let doubled = $derived(count * 2);

  // Use $effect() for side effects
  $effect(() => {
    console.log('Count changed:', count);
  });

  // Use $props() for component props
  let { title, subtitle } = $props();
</script>
```

### File Structure Pattern
Every Svelte component is a SINGLE `.svelte` file:
```svelte
<script>
  // All JavaScript here
</script>

<!-- HTML template -->
<div>Content</div>

<style>
  /* Scoped CSS */
</style>
```

---

## 🐛 Common Issues & Solutions

### 1. Hardware Not Responding
- Check safety lockfile: `ls /tmp/.nutrient_mixing_system.lock`
- Only one instance can run at a time
- Kill other instances or delete lockfile (if safe)

### 2. I2C Errors (Pumps)
- Check I2C bus: `i2cdetect -y 1`
- Should see addresses 11-18 (0x0B-0x12)
- Enable I2C: `sudo raspi-config` → Interface Options

### 3. GPIO Errors (Relays/Flow Meters)
- Run with sudo if permission errors
- Check pin availability: `tools/gpio_monitor.py`

### 4. Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 5. Port Already in Use
```bash
# Find process on port 5000
lsof -i :5000
# Kill it
kill -9 <PID>
```

---

## 📊 System State Flow

### Tank Operation Sequence
1. **FILL**: Open fill relay → Start flow meter → Monitor gallons → Close relay when target reached
2. **MIX**: Open mix relays → Dispense nutrients from pumps → Mix for X minutes → Close relays
3. **SEND**: Open send relay → Start flow meter → Monitor delivery → Close relay

### Pump State Machine
```
IDLE → DISPENSING → PAUSED → DISPENSING → COMPLETE → IDLE
                  ↓
                STOPPED (emergency or user stop)
```

---

## 🔐 Configuration Files

### config.py
- Hardware pin mappings
- I2C addresses
- Timing constants
- Safety limits
- Mock hardware settings

### nutrients.json
- Available nutrients list
- Veg formula (default recipe)
- Bloom formula (default recipe)
- Pump name to ID mapping
- User-saved custom recipes

---

## 🎯 Next Steps / TODO

See [ToDo.md](ToDo.md) for detailed implementation notes.

**Current Focus**: tablet UI phase (newTablet branch)
- Head Grower page complete
- Settings integration in progress
- Mobile/tablet responsiveness improvements

**Known Open Items**:
- Relay 11 has no GPIO pin but is referenced by Tank 2 send (startup logs a warning)
- No dispense watchdog yet
- The frontend SSE-sync `$effect` is still duplicated across pages
- `growers-dashboard.svelte` and `Settings.svelte` are very large

**Future Enhancements**:
- Database for recipe storage (currently JSON file)
- Job scheduling/automation
- Multi-user access control
- Historical data logging/charts
- EC/pH auto-correction algorithms

---

## 🔗 Quick Reference Links

- **Working GUI Reference**: `simple_gui.py` (DON'T MODIFY - reference only)
- **Hardware Commands**: `.docs/HARDWARE_COMMANDS.md` (also `.claude/CLAUDE.md` → Hardware Communication Protocols)
- **Component Examples**: `frontend/src/lib/components/`
- **Frontend API client**: `frontend/src/lib/api.js`
- **API Examples**: `app.py`

---

## 🚨 Safety Rules

1. **NEVER modify `simple_gui.py`** - It's the working reference implementation
2. **NEVER change hardware command formats** - They're hardcoded in hardware controllers
3. **ALWAYS validate inputs** before sending commands
4. **ALWAYS check lockfile** before starting Flask app
5. **EMERGENCY STOP**: `POST /api/emergency_stop` or relay ID 0 OFF

---

**Welcome back! The system is operational. A big dead-code cleanup just landed (shared `api.js` client, `@api_endpoint` decorator, `grow_cycles.py`, direct-I2C EC/pH, shared I2C lock + atomic lockfile), and the tablet UI work continues on the `newTablet` branch. Ready to continue development!**
