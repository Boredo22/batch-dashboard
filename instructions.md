# Nutrient Mixing System Enhancement Instructions

## Overview
Transform the existing Arduino-based nutrient mixing system into a Flask web application with proper hardware abstraction, job-based operations, and tank state management. The system currently uses Arduino Mega with ULN2803A relays, Atlas Scientific EZO pumps, and flow sensors.

## Existing System Context
- **Hardware**: Arduino Mega, ULN2803A Darlington Array, Atlas Scientific EZO-PMP pumps, flow sensors
- **Communication**: Serial protocol with specific command structure ("Start;Command;Parameters;end")
- **Current Files**: config.py, hardware files (relays/pumps/flow), web interface files

## File Organization Requirements
**CRITICAL**: Maintain separate hardware files as requested:
- `hardware/rpi_relay.py` - Relay control abstraction
- `hardware/rpi_pump.py` - EZO pump communication
- `hardware/rpi_flow.py` - Flow sensor monitoring
- `hardware/rpi_sensors.py` - pH/EC sensor handling
- Keep all hardware files atomic and focused on single responsibility

## Target Architecture

### Core Flask Application Structure
```
app/
├── app.py                 # Flask routes and main application
├── models.py              # Database models (SQLite)
├── jobs.py                # Job classes (FillJob, MixJob, SendJob)
├── scheduler.py           # Job execution and state management
├── hardware_manager.py    # Hardware abstraction coordinator
├── config.py              # System configuration (KEEP EXISTING)
├── database.db            # SQLite database
├── hardware/              # Hardware abstraction layer (KEEP SEPARATE)
│   ├── __init__.py
│   ├── rpi_relay.py       # Relay control
│   ├── rpi_pump.py        # Pump communication
│   ├── rpi_flow.py        # Flow sensors
│   └── rpi_sensors.py     # pH/EC sensors
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── settings.html
│   └── testing.html
└── static/
    └── style.css
```

## Implementation Tasks

### Task 1: Database Models (`models.py`)
Create SQLite models for:
```python
# Tank state enum
class TankState(Enum):
    IDLE = "idle"
    FILLING = "filling" 
    MIXING = "mixing"
    SENDING = "sending"

# Models needed:
- Tank: tank_id, name, capacity, current_volume, state
- Job: job_id, job_type, tank_id, parameters, status, created_at, updated_at
- SensorLog: timestamp, tank_id, ph_reading, ec_reading
- HardwareLog: timestamp, component, action, result
```

### Task 2: Hardware Abstraction Coordinator (`hardware_manager.py`)
Create a unified interface that coordinates the separate hardware files:
```python
class HardwareManager:
    def __init__(self):
        self.relay_controller = RelayController()  # from rpi_relay.py
        self.pump_controller = PumpController()    # from rpi_pump.py
        self.flow_controller = FlowController()    # from rpi_flow.py
        self.sensor_controller = SensorController() # from rpi_sensors.py
    
    # Unified tank operations
    def fill_tank(self, tank_id, gallons):
    def mix_tank(self, tank_id, formula):
    def send_from_tank(self, tank_id, gallons):
    
    # State queries
    def get_system_status(self):
    def is_tank_available(self, tank_id):
```

### Task 3: Job System (`jobs.py`)
Implement job classes using the existing hardware files:
```python
class BaseJob:
    def __init__(self, tank_id, hardware_manager):
        self.tank_id = tank_id
        self.hardware = hardware_manager
        self.status = JobStatus.PENDING
    
class FillJob(BaseJob):
    # Logic: Use relay + flow monitoring
    # Non-blocking: Can run with other operations
    
class MixJob(BaseJob):
    # Logic: Wait for water, circulate, add nutrients, test pH/EC
    # Blocking: Prevents other operations on tank
    
class SendJob(BaseJob):
    # Logic: Open outlet valve, monitor flow
    # Blocking: Prevents mix/send until complete
```

### Task 4: Enhanced Hardware Files
**Keep existing file separation** but enhance each:

#### `hardware/rpi_relay.py` - Enhance existing
- Add hardware abstraction layer over current relay control
- Support both real hardware and mock modes
- Integrate with existing RELAY_GPIO_PINS config
- Keep relay mapping logic intact

#### `hardware/rpi_pump.py` - Enhance existing  
- Maintain EZO pump I2C communication
- Add job-based dispensing with progress tracking
- Preserve existing Atlas Scientific protocol
- Support formula-based dispensing (ml/gallon calculations)

#### `hardware/rpi_flow.py` - Enhance existing
- Keep current pulse counting and calibration
- Add gallon-based target monitoring
- Integrate with job completion detection
- Maintain mock testing capabilities

#### `hardware/rpi_sensors.py` - Create new
- pH/EC sensor communication (Atlas Scientific EZO)
- Target validation (±0.1 tolerance)
- Calibration management
- Mock sensor data for testing

### Task 5: Flask Application (`app.py`)
Create 3-page mobile-friendly interface:

#### Homepage - Operations
- Tank status display (IDLE/FILLING/MIXING/SENDING states)
- Fill Jobs: Tank dropdown + gallon input + START FILL
- Mix Jobs: Tank dropdown + formula (Veg/Bloom) + pH/EC targets + START MIX  
- Send Jobs: Tank dropdown + gallon input + START SEND
- Real-time status updates via AJAX

#### Settings Page
- Hardware configuration editor
- Formula management (ml/gallon for each pump)
- pH/EC target ranges and tolerances
- System parameters

#### Testing Page
- Individual hardware component testing
- Manual controls for debugging
- Operation logs and system health
- Mock hardware toggle

### Task 6: Job Scheduler (`scheduler.py`)
- Single-threaded operation initially
- Tank state management and conflict prevention
- Job queue processing
- State transition logic:
  - IDLE → FILLING/MIXING allowed
  - FILLING → MIXING allowed after 20 gallons
  - MIXING → blocks all other operations
  - SENDING → blocks mix/send, allows fill

## Key Integration Points

### Configuration Preservation
- **Maintain existing config.py structure**
- Preserve RELAY_GPIO_PINS, PUMP_ADDRESSES, TANKS configuration
- Keep formulas: VEG_FORMULA, BLOOM_FORMULA
- Add new settings for job parameters, timeouts, tolerances

### Hardware Communication
- **Preserve Arduino communication protocol** for transition period
- Support both direct hardware control AND Arduino fallback
- Use existing serial command structure: "Start;Command;Parameters;end"
- Gradual migration from Arduino to direct Raspberry Pi control

### Safety Features
- Flow sensor failure detection
- pH/EC sensor validation  
- Emergency stop functionality
- Volume limit enforcement
- Mixing timeout safeguards

## Development Phases

### Phase 1: Foundation (Priority)
1. Database models and basic Flask app
2. Hardware manager coordinating existing hardware files
3. Manual job triggering via UI
4. Tank state tracking
**Validation**: UI can trigger operations, states update correctly

### Phase 2: Job Automation
1. Automated job execution
2. Basic job queue/scheduler
3. State conflict prevention
**Validation**: Jobs run automatically, no state conflicts

### Phase 3: Enhanced Features
1. pH/EC monitoring and validation
2. Formula-based nutrient dispensing
3. Advanced mixing algorithms
**Validation**: Consistent nutrient quality

## Code Quality Requirements

### File Size Limits
- Target 100-200 lines per file (split if larger)
- Each hardware file should be atomic and focused
- Clean separation of concerns

### Error Handling
- Comprehensive exception handling in all hardware interactions
- Graceful degradation if hardware unavailable
- Detailed logging for troubleshooting

### Testing Support
- Mock hardware implementations in each hardware file
- Easy toggle between real/mock hardware
- Comprehensive testing interface

### Mobile-First UI
- Responsive design for head grower mobile access
- Clear tank status indicators
- Simple, reliable operation controls
- Real-time status updates

## Success Criteria
- Head grower can reliably fill/mix/send via mobile UI
- No tank state conflicts or unsafe operations
- Clear operation logging and troubleshooting
- Easy hardware maintenance and upgrades
- Scalable foundation for future features

## Migration Strategy
1. Keep Arduino system running during development
2. Test Python system in parallel with mock hardware
3. Gradual hardware migration (relay → pump → sensors)
4. Full cutover only after thorough validation

## Important Notes
- **Preserve existing hardware file organization** - do not consolidate
- Keep config.py structure intact
- Maintain Arduino protocol compatibility during transition
- Focus on reliability and simplicity over complexity
- Prioritize mobile usability for growers