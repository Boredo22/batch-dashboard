# Nutrient Mixing System - Codebase Efficiency Refactoring Plan

## Executive Summary

Mike has consolidated his entire hydroponic control system onto a Raspberry Pi 4B with Atlas Scientific isolation shield. Previously, the system used:
- Arduino Mega for relays, pumps, and flow meters
- Arduino Uno for pH/EC sensors
- Serial communication between microcontrollers and a Windows box

**Now everything runs directly on the Pi via:**
- GPIO pins for 13 relays (via ULN2803A Darlington array)
- I2C bus 1 for 8 EZO-PMP pumps (addresses 11-18)
- I2C bus 1 for pH sensor (0x63) and EC sensor (0x64) via isolation shield
- GPIO pins for 2 flow meters with pulse counting

This refactoring removes Arduino-era dead code and simplifies the architecture now that no serial communication is needed.

---

## Current Architecture (Likely)

```
batch-dashboard/
├── app.py                    # Flask API server
├── main.py                   # FeedControlSystem coordinator
├── config.py                 # Hardware configuration
├── hardware_comms.py         # Abstraction layer (wraps FeedControlSystem)
├── simple_gui.py             # Tkinter reference GUI (KEEP)
├── hardware/
│   ├── __init__.py
│   ├── rpi_pumps.py          # EZO pump I2C controller
│   ├── rpi_relays.py         # GPIO relay controller
│   ├── rpi_flow.py           # Flow meter pulse counting
│   ├── rpi_unoComm.py        # Arduino Uno serial comm (DELETE)
│   ├── rpi_sensors.py        # pH/EC sensors (or ezo_sensors.py)
│   └── mock_hardware_libs.py # Mock hardware for dev
├── frontend/
│   └── src/                  # Svelte 5 frontend
└── templates/                # Flask templates (if any)
```

---

## PHASE 1: Remove Arduino Dead Code

### Files to DELETE entirely:

```bash
# Arduino Uno communication - no longer needed
rm hardware/rpi_unoComm.py
rm hardware/arduino_uno_comm.py  # if exists
rm arduino_uno_comm.py           # if exists at root
```

### Config entries to REMOVE from `config.py`:

```python
# DELETE these sections entirely:

# Arduino Uno serial communication (NO LONGER NEEDED)
ARDUINO_UNO_PORTS = [...]        # DELETE
ARDUINO_UNO_BAUDRATE = 115200    # DELETE  
ARDUINO_UNO_TIMEOUT = 1.0        # DELETE

# Also remove any Arduino Mega references if present
ARDUINO_MEGA_PORT = ...          # DELETE if exists
```

### Imports to REMOVE from `main.py`:

```python
# REMOVE this import:
from hardware.rpi_unoComm import ArduinoUnoController, find_arduino_uno_port

# REMOVE from FeedControlSystem.__init__():
# All code related to self.uno_controller, uno_port parameter
```

---

## PHASE 2: Simplify FeedControlSystem in `main.py`

The `FeedControlSystem` class was designed to coordinate Arduino serial communication. Now it can be drastically simplified.

### Current FeedControlSystem (BEFORE):

```python
class FeedControlSystem:
    def __init__(self, uno_port=None, use_mock_flow=None):
        # Initialize pump controller
        self.pump_controller = EZOPumpController()
        
        # Initialize relay controller
        self.relay_controller = RelayController()
        
        # Initialize flow controller
        self.flow_controller = FlowMeterController()
        
        # Initialize Arduino Uno controller  <-- REMOVE THIS
        if uno_port is None:
            uno_port = find_arduino_uno_port()
        if uno_port:
            self.uno_controller = ArduinoUnoController(port=uno_port)
        else:
            self.uno_controller = None
```

### Simplified FeedControlSystem (AFTER):

```python
class FeedControlSystem:
    def __init__(self, use_mock_flow=False):
        """Initialize the feed control system - pure Pi, no Arduino"""
        self.running = False
        self.command_queue = queue.Queue()
        self.worker_thread = None
        self.message_callback = None
        
        # Initialize controllers - all on Pi now
        logger.info("Initializing Pi-native feed control system...")
        
        try:
            self.pump_controller = EZOPumpController()
            logger.info("✓ EZO pump controller initialized (I2C addresses 11-18)")
        except Exception as e:
            logger.error(f"✗ Pump controller failed: {e}")
            self.pump_controller = None
        
        try:
            self.relay_controller = RelayController()
            logger.info("✓ Relay controller initialized (GPIO)")
        except Exception as e:
            logger.error(f"✗ Relay controller failed: {e}")
            self.relay_controller = None
        
        try:
            if use_mock_flow:
                self.flow_controller = MockFlowMeterController()
                logger.info("✓ Mock flow controller initialized")
            else:
                self.flow_controller = FlowMeterController()
                logger.info("✓ Flow controller initialized (GPIO)")
        except Exception as e:
            logger.error(f"✗ Flow controller failed: {e}")
            self.flow_controller = None
        
        try:
            self.sensor_controller = EZOSensorController()
            logger.info("✓ pH/EC sensor controller initialized (I2C 0x63/0x64)")
        except Exception as e:
            logger.error(f"✗ Sensor controller failed: {e}")
            self.sensor_controller = None
        
        # Timing for status updates
        self.last_status_update = 0
        self.last_pump_check = 0
```

**Key changes:**
1. Remove `uno_port` parameter entirely
2. Remove `self.uno_controller` and all references
3. Add `self.sensor_controller` for pH/EC (was on Arduino Uno before)
4. Simplify logging messages

---

## PHASE 3: Consolidate I2C Bus Management

Currently, pumps and sensors might each open their own I2C bus. Create a shared I2C manager:

### Create `hardware/i2c_manager.py`:

```python
#!/usr/bin/env python3
"""
Shared I2C Bus Manager
Single bus instance for all I2C devices (pumps at 11-18, pH at 0x63, EC at 0x64)
"""

import threading
import smbus2
import logging

logger = logging.getLogger(__name__)

class I2CManager:
    """Thread-safe singleton for I2C bus access"""
    _instance = None
    _lock = threading.Lock()
    _bus_lock = threading.Lock()
    
    def __new__(cls, bus_number=1):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._bus = None
                    cls._instance._bus_number = bus_number
                    cls._instance._initialize_bus()
        return cls._instance
    
    def _initialize_bus(self):
        """Initialize the I2C bus"""
        try:
            self._bus = smbus2.SMBus(self._bus_number)
            logger.info(f"I2C bus {self._bus_number} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus: {e}")
            self._bus = None
    
    @property
    def bus(self):
        """Get the bus instance"""
        return self._bus
    
    def send_command(self, address, command, delay=0.3):
        """
        Send command to EZO device with proper locking
        Returns: (success, response_code, data_string)
        """
        if self._bus is None:
            return False, 0, "Bus not initialized"
        
        with self._bus_lock:
            try:
                # Use raw I2C messages (required for EZO devices)
                write_msg = smbus2.i2c_msg.write(address, list(command.encode('utf-8')))
                self._bus.i2c_rdwr(write_msg)
                
                # Wait for processing
                import time
                time.sleep(delay)
                
                # Read response
                read_msg = smbus2.i2c_msg.read(address, 32)
                self._bus.i2c_rdwr(read_msg)
                
                data = list(read_msg)
                response_code = data[0]
                
                if response_code == 1:  # Success
                    response_str = ''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip()
                    return True, response_code, response_str
                else:
                    return False, response_code, ""
                    
            except Exception as e:
                logger.error(f"I2C error at address {address}: {e}")
                return False, 0, str(e)
    
    def close(self):
        """Close the I2C bus"""
        with self._bus_lock:
            if self._bus:
                self._bus.close()
                self._bus = None


def get_i2c_manager():
    """Get the shared I2C manager instance"""
    return I2CManager()
```

### Update `hardware/rpi_pumps.py` to use shared manager:

```python
# CHANGE FROM:
self.bus = smbus2.SMBus(self.bus_number)

# CHANGE TO:
from hardware.i2c_manager import get_i2c_manager
self.i2c = get_i2c_manager()

# Then use:
success, code, response = self.i2c.send_command(pump_address, command)
```

### Update `hardware/ezo_sensors.py` similarly:

```python
from hardware.i2c_manager import get_i2c_manager

class EZOSensorController:
    def __init__(self):
        self.i2c = get_i2c_manager()
        self.ph_address = 0x63
        self.ec_address = 0x64
```

---

## PHASE 4: Clean Up Config.py

### REMOVE these sections:

```python
# =============================================================================
# ARDUINO UNO CONFIGURATION (EC/pH Sensors) - DELETE ENTIRE SECTION
# =============================================================================

# Arduino Uno serial communication - DELETE
ARDUINO_UNO_PORTS = [
    "/dev/ttyACM0",
    "/dev/ttyACM1", 
]
ARDUINO_UNO_BAUDRATE = 115200
ARDUINO_UNO_TIMEOUT = 1.0

# EC/pH sensor calibration points - MOVE TO SENSOR SECTION
EC_CALIBRATION_SOLUTIONS = {...}  # Keep but move
PH_CALIBRATION_SOLUTIONS = {...}  # Keep but move
```

### ADD/UPDATE these sections:

```python
# =============================================================================
# I2C DEVICE CONFIGURATION (All on bus 1)
# =============================================================================

I2C_BUS_NUMBER = 1

# EZO Pump addresses (moved from addresses 5,8,9,10,11,12,13,103 to 11-18)
PUMP_ADDRESSES = {
    1: 11,   # Veg A
    2: 12,   # Veg B
    3: 13,   # Bloom A
    4: 14,   # Bloom B
    5: 15,   # Cake
    6: 16,   # PK Synergy
    7: 17,   # Runclean
    8: 18,   # pH Down
}

# pH/EC Sensor addresses (on Atlas isolation shield)
PH_SENSOR_ADDRESS = 0x63   # 99 decimal
EC_SENSOR_ADDRESS = 0x64   # 100 decimal

# EZO Command timing
EZO_COMMAND_DELAY = 0.3    # 300ms standard delay
EZO_CAL_DELAY = 1.0        # 1s for calibration commands
EZO_READ_DELAY = 0.6       # 600ms for read commands
```

---

## PHASE 5: Simplify hardware_comms.py

The `hardware_comms.py` abstraction layer can be simplified since we no longer need to coordinate Arduino communication.

### OPTION A: Keep as thin wrapper (recommended)

```python
#!/usr/bin/env python3
"""
Hardware Communications - Simplified for Pi-only operation
"""

import threading
from typing import Dict, Any
from main import FeedControlSystem
from config import (
    get_available_pumps, get_available_relays, get_available_flow_meters,
    MOCK_SETTINGS
)

# Singleton system instance
_system = None
_lock = threading.Lock()

def get_system():
    """Get or create the feed control system"""
    global _system
    with _lock:
        if _system is None:
            use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
            _system = FeedControlSystem(use_mock_flow=use_mock_flow)
            _system.start()
        return _system

# Direct hardware functions
def control_relay(relay_id: int, state: bool) -> bool:
    sys = get_system()
    if sys and sys.relay_controller:
        return sys.relay_controller.set_relay(relay_id, state)
    return False

def dispense_pump(pump_id: int, amount_ml: float) -> bool:
    sys = get_system()
    if sys and sys.pump_controller:
        return sys.pump_controller.dispense(pump_id, amount_ml)
    return False

def stop_pump(pump_id: int) -> bool:
    sys = get_system()
    if sys and sys.pump_controller:
        return sys.pump_controller.stop(pump_id)
    return False

def read_ph() -> float:
    sys = get_system()
    if sys and sys.sensor_controller:
        return sys.sensor_controller.read_ph()
    return None

def read_ec() -> float:
    sys = get_system()
    if sys and sys.sensor_controller:
        return sys.sensor_controller.read_ec()
    return None

def get_system_status() -> Dict[str, Any]:
    sys = get_system()
    if sys:
        return sys.get_status()
    return {'error': 'System not available'}

def emergency_stop() -> bool:
    sys = get_system()
    if sys:
        if sys.relay_controller:
            sys.relay_controller.all_off()
        if sys.pump_controller:
            sys.pump_controller.stop_all()
        return True
    return False

def cleanup():
    global _system
    with _lock:
        if _system:
            _system.stop()
            _system = None
```

### OPTION B: Eliminate entirely and call controllers directly from app.py

If `hardware_comms.py` is just passing through to `FeedControlSystem`, consider eliminating it and having `app.py` use the controllers directly.

---

## PHASE 6: Remove Legacy Command Protocol (Optional)

The old Arduino system used string commands like `"Start;Relay;1;ON;end"`. Now that we're calling Python directly, this protocol is unnecessary overhead.

### BEFORE (command string parsing):

```python
# In main.py
def _process_relay_command(self, parts):
    relay_no = int(parts[2])
    state = parts[3]
    new_state = (state == "ON")
    # ... GPIO operation
```

### AFTER (direct method calls):

```python
# In hardware_comms.py or app.py
def control_relay(relay_id: int, state: bool) -> bool:
    return relay_controller.set_relay(relay_id, state)
```

**However**, if you want to keep the command protocol for logging/debugging purposes, that's fine. Just know it's optional complexity now.

---

## PHASE 7: Files to Delete/Archive

### DELETE (no longer needed):
```bash
rm hardware/rpi_unoComm.py
rm hardware/arduino_uno_comm.py  # if exists
rm arduino_uno_comm.py           # if at root
```

### ARCHIVE (optional, for reference):
```bash
mkdir archive/
mv old_arduino_mega_file archive/
# Keep simple_gui.py - it's your reference implementation
```

### KEEP INTACT:
- `simple_gui.py` - Working reference implementation
- `config.py` - After cleanup
- `hardware/rpi_pumps.py` - EZO pump controller
- `hardware/rpi_relays.py` - GPIO relay controller
- `hardware/rpi_flow.py` - Flow meter controller
- `hardware/ezo_sensors.py` - pH/EC sensor controller
- `app.py` - Flask API
- `frontend/` - Svelte frontend

---

## Summary of Changes

| Action | File | Description |
|--------|------|-------------|
| DELETE | `hardware/rpi_unoComm.py` | Arduino Uno serial comm |
| DELETE | Config entries | `ARDUINO_UNO_*` settings |
| CREATE | `hardware/i2c_manager.py` | Shared I2C bus singleton |
| UPDATE | `main.py` | Remove uno_controller, add sensor_controller |
| UPDATE | `hardware/rpi_pumps.py` | Use shared I2C manager |
| UPDATE | `hardware/ezo_sensors.py` | Use shared I2C manager |
| UPDATE | `config.py` | Remove Arduino config, add sensor addresses |
| SIMPLIFY | `hardware_comms.py` | Remove command string parsing if desired |

---

## Testing Checklist After Refactoring

1. **I2C devices respond:**
   ```bash
   # Scan for devices (EZO devices may not show in i2cdetect)
   i2cdetect -y 1
   
   # Test pump communication
   python3 -c "
   from hardware.rpi_pumps import EZOPumpController
   p = EZOPumpController()
   print(p.get_pump_info(1))
   "
   
   # Test sensor communication
   python3 -c "
   from hardware.ezo_sensors import EZOSensorController
   s = EZOSensorController()
   print(f'pH: {s.read_ph()}')
   print(f'EC: {s.read_ec()}')
   "
   ```

2. **GPIO relays work:**
   ```bash
   python3 -c "
   from hardware.rpi_relays import RelayController
   r = RelayController()
   r.set_relay(1, True)
   import time; time.sleep(1)
   r.set_relay(1, False)
   "
   ```

3. **Flow meters respond:**
   ```bash
   python3 -c "
   from hardware.rpi_flow import FlowMeterController
   f = FlowMeterController()
   print(f.get_status())
   "
   ```

4. **Flask API starts:**
   ```bash
   python3 app.py
   # Test endpoints in browser or curl
   ```

5. **Frontend connects:**
   ```bash
   cd frontend && npm run dev
   # Check browser console for API errors
   ```

---

## Notes for Claude Code

1. **Run on Pi:** All changes should be tested on the actual Raspberry Pi 4B
2. **Backup first:** `cp -r batch-dashboard batch-dashboard-backup`
3. **Incremental changes:** Do one phase at a time and test
4. **Keep simple_gui.py:** It's the working reference - don't modify it
5. **I2C addresses:** Pumps are at 11-18, pH at 0x63 (99), EC at 0x64 (100)
6. **GPIO library:** Using `lgpio` not `RPi.GPIO` (Pi 4B compatible)
7. **Flow meters:** GPIO 23 and 24 with RISING edge detection