# Batch Dashboard - Project Refresher

**Last Updated**: December 5, 2025
**Current Branch**: main
**Status**: Production Ready - Shadcn UI Implementation Complete

---

## 🎯 Project Overview

This is a **Nutrient Mixing System** for commercial hydroponics/agriculture operations. It controls physical hardware (pumps, relays, flow meters, EC/pH sensors) through a modern web-based interface running on a Raspberry Pi.

### What It Does
- **Mixes nutrient solutions** by precisely dispensing liquid nutrients into water tanks
- **Controls tank operations**: fill with water, mix nutrients, send to grow rooms
- **Monitors water quality**: EC (electrical conductivity) and pH sensors via Arduino
- **Manages multiple tanks**: 3 tanks with different capacities (100, 100, 35 gallons)
- **Tracks flow**: 2 flow meters for water fill and send operations
- **8 peristaltic pumps**: Each pump dispenses a specific nutrient (Veg A/B, Bloom A/B, Cake, PK Synergy, Runclean, pH Down)

---

## 🏗️ Architecture

### Two-Tier System

**Backend (Python/Flask)**
- REST API server exposing hardware control endpoints
- Direct hardware communication (I2C for pumps, GPIO for relays/flow meters, Serial for Arduino)
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
├── app.py                      # Flask REST API server (MAIN BACKEND)
├── main.py                     # Core FeedControlSystem class
├── config.py                   # Centralized configuration (ALL hardware mappings)
├── hardware_safety.py          # Safety lockfile system
├── nutrients.json              # Nutrient formulas and recipes
├── simple_gui.py               # REFERENCE: Original working GUI (DON'T MODIFY)
│
├── hardware/                   # Hardware controllers
│   ├── hardware_comms.py       # Main hardware abstraction layer
│   ├── rpi_pumps.py           # EZO pump I2C controller
│   ├── rpi_relays.py          # ULN2803A relay GPIO controller
│   ├── rpi_flow.py            # Flow meter pulse counter
│   ├── rpi_unoComm.py         # Arduino serial communication
│   └── mock_controllers.py    # Mock hardware for development
│
└── frontend/                   # Svelte 5 application
    ├── src/
    │   ├── main.js            # Entry point
    │   ├── App.svelte         # Main app with page navigation
    │   ├── Dashboard.svelte   # Stage 1: Individual hardware testing
    │   ├── Stage2Testing.svelte # Stage 2: Job process testing
    │   ├── Settings.svelte    # System configuration
    │   ├── HeadGrower.svelte  # Main operations page (NEW REDESIGN)
    │   ├── Nutrients.svelte   # Manual nutrient dispensing
    │   │
    │   ├── components/        # OLD component library
    │   │   ├── PumpControl.svelte
    │   │   ├── RelayGrid.svelte
    │   │   ├── FlowMeterControl.svelte
    │   │   └── ...
    │   │
    │   └── lib/components/    # NEW component library
    │       ├── growers/       # Redesigned growers dashboard
    │       ├── hardware/      # Hardware control cards
    │       ├── layout/        # Layout components
    │       └── ui/            # Shadcn-style UI primitives
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

### EC/pH Sensors (Arduino Uno)
- Serial communication (115200 baud, /dev/ttyACM0)
- Commands: `Start;EcPh;ON;end`, `Start;EcPh;OFF;end`

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
    "arduino": True       # Use mock Arduino
}
```

---

## 🎨 Recent Major Changes (Last 3 Months)

### Shadcn-Svelte UI Implementation (Completed November 2025)
1. **Modern Component Library**
   - Migrated to shadcn-svelte component system
   - Professional UI components: Card, Button, Badge, Alert, Progress, etc.
   - Dark-first design with cyan/purple accents
   - Tailwind CSS utility-first styling
   - Lucide icons throughout the application

2. **Component Architecture**
   - **Layout Components**: `app-sidebar.svelte`, `site-header.svelte`, `dashboard-layout.svelte`
   - **Hardware Control Cards**: `pump-control-card.svelte`, `relay-control-card.svelte`, `flow-meter-card.svelte`, `ecph-monitor-card.svelte`, `system-log-card.svelte`
   - **Page Components**: HeadGrower (growers dashboard), Nutrients, Dashboard (Stage 1), Stage2Testing, Settings
   - All components use Svelte 5 runes (`$state`, `$derived`, `$effect`)

3. **Enhanced User Experience**
   - Sidebar navigation with collapsible sections
   - Breadcrumb navigation
   - Real-time system status monitoring
   - Improved responsive design (mobile/tablet/desktop)
   - Touch-optimized for 10" tablets
   - Professional loading and error states

4. **Technology Stack (Updated)**
   - **Svelte 5.38.6** - Latest Svelte with runes support
   - **Vite 5.4.19** - Lightning-fast build tool
   - **Tailwind CSS 3.4.17** - Utility-first CSS framework
   - **bits-ui 2.9.6** - Unstyled accessible UI primitives
   - **Lucide Svelte 0.543.0** - Professional icon library
   - **mode-watcher 1.1.0** - Dark/light mode management
   - **svelte-sonner 1.0.5** - Toast notifications
   - **tailwindcss-animate 1.0.7** - Animation utilities

### Safety & System Features
- Hardware safety lockfile (`/tmp/.nutrient_mixing_system.lock`)
- Prevents multiple instances from controlling hardware
- Relay state persistence across backend restarts
- Emergency stop functionality accessible via API and UI

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

### 4. Stage 2 Testing (Job Testing)
- **Path**: `currentPage = 'stage2'`
- **File**: `Stage2Testing.svelte`
- **Purpose**: Complete job process testing
- **Features**:
  - Fill job testing
  - Mix job testing
  - Send job testing
  - Multi-step process validation

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
- Check pin availability: `/hardware/gpio_monitor.py`

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

**Current Status**: Shadcn-svelte UI implementation complete and production-ready

**Optimization Opportunities**:
- Tablet responsiveness enhancements (10" tablet touch optimization)
- Component consolidation for reduced vertical scrolling
- Touch target size improvements (44x44px minimum)
- Slider control enhancements for touchscreen use

**Future Enhancements**:
- Database for recipe storage (currently JSON file)
- Job scheduling/automation system
- Multi-user access control and permissions
- Historical data logging with charts/visualization
- EC/pH auto-correction algorithms
- Real-time WebSocket updates (currently polling)

---

## 🔗 Quick Reference Links

- **Working GUI Reference**: `simple_gui.py` (DON'T MODIFY - reference only)
- **Hardware Commands**: See `.claude/CLAUDE.md` → Hardware Communication Protocols
- **Component Examples**: `frontend/src/lib/components/`
- **API Examples**: `app.py` (lines 100-800)
- **Svelte 5 Guide**: `.claude/SVELTE_REFERENCE.md`

---

## 🚨 Safety Rules

1. **NEVER modify `simple_gui.py`** - It's the working reference implementation
2. **NEVER change hardware command formats** - They're hardcoded in hardware controllers
3. **ALWAYS validate inputs** before sending commands
4. **ALWAYS check lockfile** before starting Flask app
5. **EMERGENCY STOP**: `POST /api/emergency_stop` or relay ID 0 OFF

---

**Welcome back! The system is operational and the UI redesign is looking great. The Head Grower page has been completely modernized with professional UI components and responsive design. Ready to continue development!**
