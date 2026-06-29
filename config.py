#!/usr/bin/env python3
"""
Feed Control System Configuration
Centralized configuration for all hardware mappings, constants, and settings
"""

# =============================================================================
# RELAY CONFIGURATION (ULN2803A Darlington Array)
# =============================================================================

# GPIO pin mappings for relays. THIS is the canonical source of truth for the
# live system. (hardware/utilities/relay_mapping.json is a snapshot produced by
# the interactive relayMap.py tool and is currently stale - it predates relay 1;
# do not treat it as authoritative. Re-export from here if you regenerate it.)
# Format: {relay_id: gpio_pin}
RELAY_GPIO_PINS = {
    1: 22,   # Tank 1 Fill,
    2: 26,   # Tank 2 Fill
    3: 20,   # Tank 3 Fill
    4: 21,   # Tank 1 Nute Dispense
    5: 16,   # Tank 2 Nute Dispense
    6: 19,   # Tank 3 Nute Dispense
    7: 12,   # Tank 1 Dispense Send
    8: 13,   # Tank 2 Dispense Send
    9: 10,   # Tank 3 Dispense Send
    10: 9,   # Room 1
    12: 0,   # Nursery
    13: 5    # Drain
}

# Descriptive names for each relay.
# Kept consistent with RELAY_GPIO_PINS above (previously this map was missing
# entries and mislabeled relay 6 as "Tank 2 Nute Dispense").
RELAY_NAMES = {
    1: "Tank 1 Fill",
    2: "Tank 2 Fill",
    3: "Tank 3 Fill",
    4: "Tank 1 Nute Dispense",
    5: "Tank 2 Nute Dispense",
    6: "Tank 3 Nute Dispense",
    7: "Tank 1 Dispense Send",
    8: "Tank 2 Dispense Send",
    9: "Tank 3 Dispense Send",
    10: "Room 1",
    # 11: intentionally absent - no GPIO pin is defined for relay 11, yet TANKS
    #     (tank 2 send_relay) and RELAY_COMBOS ("Send Tank 2") reference it. The
    #     startup check below warns about this so it fails loudly, not silently.
    12: "Nursery",
    13: "Drain",
}

RELAY_COMBOS = {
    "Mix Tank 1": [4, 7],
    "Send Tank 1": [4, 10],
    "Mix Tank 2": [5, 8],
    "Send Tank 2": [5, 11],
    "Mix Tank 3": [6, 9],
    "Send Tank 3": [6, 12],
}

# Relay logic settings (for ULN2803A)
RELAY_ACTIVE_HIGH = True  # GPIO HIGH = Relay ON (due to ULN2803A inversion)

# =============================================================================
# PUMP CONFIGURATION (Atlas Scientific EZO-PMP)
# =============================================================================

# EZO Pump I2C addresses
PUMP_ADDRESSES = {
    1: 11,    # Pump 1 at I2C address 11 (0x0B)
    2: 12,    # Pump 2 at I2C address 12 (0x0C)
    3: 13,    # Pump 3 at I2C address 13 (0x0D)
    4: 14,    # Pump 4 at I2C address 14 (0x0E)
    5: 15,    # Pump 5 at I2C address 15 (0x0F)
    6: 16,    # Pump 6 at I2C address 16 (0x10)
    7: 17,    # Pump 7 at I2C address 17 (0x11)
    8: 18,    # Pump 8 at I2C address 18 (0x12)
}

# Pump names/descriptions
PUMP_NAMES = {
    1: "Veg A",
    2: "Veg B", 
    3: "Bloom A",
    4: "Bloom B",
    5: "Cake",
    6: "Runclean",     # swapped onto the working pump (pump 7 / I2C 17 is dead)
    7: "PK Synergy",   # parked on the non-functional pump (unused in veg/bloom)
    8: "pH Down",
}

# I2C bus settings
I2C_BUS_NUMBER = 1  # Usually 1 on Raspberry Pi
I2C_DEFAULT_ADDRESS = 103  # Factory default for EZO pumps (0x67)

# EZO pump timing constants
EZO_COMMAND_DELAY = 0.3  # 300ms delay required by EZO pumps
EZO_MAX_RETRIES = 3
EZO_RETRY_DELAY = 0.1

# EZO response codes
EZO_RESPONSE_CODES = {
    1: "SUCCESS",
    2: "SYNTAX_ERROR", 
    254: "STILL_PROCESSING",
    255: "NO_DATA"
}

# =============================================================================
# FLOW METER CONFIGURATION
# =============================================================================
# Hardware: VFS1001 flow meter → 817 optocoupler module → Pi GPIO
#
# Wiring:
#   Flow meter signal (24V pulses) → Optocoupler IN1
#   Flow meter GND → Optocoupler input GND
#   Pi 3.3V → Optocoupler middle jumper (powers output pull-ups)
#   Optocoupler V1 → Pi GPIO 24 (flow meter 1)
#   Optocoupler output GND → Pi GND
#
# Signal behavior (INVERTED by optocoupler):
#   Flow pulse (24V HIGH) → Opto LED on → Output LOW → FALLING edge
#   No pulse (0V) → Opto LED off → Output HIGH (via pull-up)
#
# Edge detection: FALLING (detects start of each flow pulse)

# Flow meter GPIO pin mappings
FLOW_METER_GPIO_PINS = {
    1: 23,    # Flow meter 1 on GPIO 23 (Fill Tank)
    2: 24,    # Flow meter 2 on GPIO 24 (Send to Room)
}

# Flow meter names
FLOW_METER_NAMES = {
    1: "Tank Fill",
    2: "Tank Send",
}

# Flow meter calibration (pulses per gallon)
FLOW_METER_CALIBRATION = {
    1: 220,  # Pulses per gallon for meter 1
    2: 220,  # Pulses per gallon for meter 2
}

# Flow meter settings
FLOW_METER_INTERRUPT_EDGE = "FALLING"  # Interrupt on FALLING edge (optocoupler inverts signal: flow pulse HIGH → output LOW)

# Pulse debounce window (seconds). MUST be shorter than the real inter-pulse
# interval at max flow, or pulses get dropped — and dropping every other pulse
# halves BOTH the displayed rate AND the gallon count, so a fill silently
# overshoots. At 220 ppg, 6.6 gpm = ~24 pulses/s = ~41 ms spacing, so the old
# hardcoded 50 ms window dropped half the pulses (rate read ~3.3 instead of 6.6).
# 8 ms passes up to ~34 gpm @ 220 ppg while still rejecting sub-8 ms EMI/relay
# glitches. To tune: keep it below 60000 / (max_gpm * ppg) milliseconds with
# margin; raise it only if idle relay switching produces phantom pulses.
FLOW_PULSE_DEBOUNCE_SECONDS = 0.008

# =============================================================================
# EZO EC/pH SENSOR CONFIGURATION (Direct I2C on Raspberry Pi)
# =============================================================================

# EZO sensor I2C addresses
EZO_PH_ADDRESS = 0x63  # 99 decimal - pH sensor
EZO_EC_ADDRESS = 0x64  # 100 decimal - EC sensor

# EC/pH sensor calibration points
EC_CALIBRATION_SOLUTIONS = {
    "dry": 0,
    "single": 1413,  # 1413 μS/cm standard
    "low": 84,       # 84 μS/cm
    "high": 1413     # 1413 μS/cm
}

PH_CALIBRATION_SOLUTIONS = {
    "low": 4.0,      # pH 4.0 buffer
    "mid": 7.0,      # pH 7.0 buffer
    "high": 10.0     # pH 10.0 buffer
}

# =============================================================================
# TANK MONITOR CONFIGURATION (Per-tank Arduino pH/EC monitors)
# =============================================================================
# Each tank can have a dedicated Arduino with EZO pH/EC sensors connected
# via USB serial. The Arduino sends JSON: {"ph":X.XX,"ec":X.XX}

TANK_MONITOR_BAUDRATE = 9600

# Map tank_id -> serial port (None = auto-detect)
TANK_MONITOR_PORTS = {
    1: None,  # Tank 1 - auto-detect (first Arduino found)
    # 2: "/dev/ttyUSB1",  # Uncomment when adding Tank 2 monitor
    # 3: "/dev/ttyUSB2",  # Uncomment when adding Tank 3 monitor
}

# =============================================================================
# LEGACY ARDUINO UNO CONFIGURATION (DEAD on the live Pi system)
# =============================================================================
# EC/pH is now read by the Pi over direct I2C (see EZO_*_ADDRESS above and
# hardware/rpi_ezo_sensors.py). These constants are NOT used by app.py / main.py
# anymore; they are retained ONLY because the frozen reference GUI simple_gui.py
# still imports them. If/when simple_gui.py is retired, delete this whole block.
ARDUINO_UNO_PORTS = [
    "/dev/ttyACM0",
    "/dev/ttyACM1",

]

ARDUINO_UNO_BAUDRATE = 115200
ARDUINO_UNO_TIMEOUT = 1.0

# =============================================================================
# SYSTEM TIMING CONFIGURATION
# =============================================================================

# Status update intervals (in seconds)
STATUS_UPDATE_INTERVAL = 2.0      # General status updates
PUMP_CHECK_INTERVAL = 1.0         # Check pump status
VOLTAGE_CHECK_INTERVAL = 300.0    # Check pump voltages (5 minutes)
FLOW_UPDATE_INTERVAL = 0.5        # Flow meter updates

# Command processing
COMMAND_TIMEOUT = 1.0             # Command queue timeout
SERIAL_READ_TIMEOUT = 0.05        # Serial port read timeout

# Mock testing intervals (for development)
MOCK_FLOW_PULSE_INTERVAL = 0.02   # 20ms for mock flow pulses
MOCK_PULSES_PER_INTERVAL = 2      # Pulses to add per interval

# =============================================================================
# TANK CONFIGURATION
# =============================================================================

# Tank definitions  
TANKS = {
    1: {
        "name": "Tank 1 - Grow 1",
        "capacity_gallons": 100,
        "fill_relay": 1,        # Tank 1 Fill
        "mix_relays": [4, 7],   # Tank 1 Mix Relays
        "send_relay": 10,       # Tank 1 Dispense Send
    },
    2: {
        "name": "Tank 2 - Grow 2", 
        "capacity_gallons": 100,
        "fill_relay": 2,        # Tank 2 Fill
        "mix_relays": [5, 8],   # Tank 2 Mix Relays  
        "send_relay": 11,       # Tank 2 Dispense Send
    },
    3: {
        "name": "Tank 3 - Nursery",
        "capacity_gallons": 35,
        "fill_relay": 3,        # Tank 3 Fill
        "mix_relays": [6, 9],   # Tank 3 Mix Relays
        "send_relay": 12,       # Tank 3 Dispense Send
    }
}

# Room/zone definitions
ROOMS = {
    1: {
        "name": "Grow Room 1",
        "relay": 10,            # Room 1 relay
    }
}

# =============================================================================
# COMMUNICATION PROTOCOL CONSTANTS
# =============================================================================

# Serial command protocol
COMMAND_START = "Start"
COMMAND_END = "end"
COMMAND_SEPARATOR = ";"

# Command types
COMMAND_TYPES = [
    "Relay",
    "Dispense", 
    "Pump",
    "Cal",
    "StartFlow",
    "EcPh"
]

# Response message formats
MESSAGE_FORMATS = {
    "relay_response": "Start;RelayResponse;{relay_id};{state};end",
    "pump_response": "Start;PumpResponse;{pump_id};{response};end",
    "nute_status": "Start;Update;NuteStat;{pump_id};{status};{current};{target};end",
    "flow_status": "Start;Update;FlowStat;{flow_id};{gallons};{pulses};end",
    "flow_complete": "Start;Update;FlowComplete;{flow_id};end",
    "ec_reading": "Start;Update;Ec;{value};end",
    "ph_reading": "Start;Update;Ph;{value};end",
    "emergency_stop": "Start;Update;EmergencyStop;Complete;end"
}

# =============================================================================
# SAFETY AND LIMITS
# =============================================================================

# Pump safety limits
MAX_PUMP_VOLUME_ML = 2500.0       # Maximum single dispense volume
MIN_PUMP_VOLUME_ML = 0.5          # Minimum single dispense volume
PUMP_VOLTAGE_MIN = 5.0            # Minimum operating voltage
PUMP_VOLTAGE_MAX = 15.0           # Maximum operating voltage

# Flow meter limits
MAX_FLOW_GALLONS = 100            # Maximum flow target
FLOW_TIMEOUT_MINUTES = 60         # Flow operation timeout

# System limits
MAX_CONCURRENT_PUMPS = 4          # Maximum pumps running simultaneously
EMERGENCY_STOP_TIMEOUT = 5.0      # Emergency stop timeout

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# Component-specific log levels
LOG_LEVELS = {
    "main": "INFO",
    "pumps": "INFO", 
    "relays": "INFO",
    "flow": "INFO",
    "arduino": "INFO"
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_relay_name(relay_id):
    """Get descriptive name for relay"""
    return RELAY_NAMES.get(relay_id, f"Relay {relay_id}")

def get_pump_name(pump_id):
    """Get descriptive name for pump"""
    return PUMP_NAMES.get(pump_id, f"Pump {pump_id}")

def get_flow_meter_name(meter_id):
    """Get descriptive name for flow meter"""
    return FLOW_METER_NAMES.get(meter_id, f"Flow Meter {meter_id}")

def get_tank_info(tank_id):
    """Get tank configuration"""
    return TANKS.get(tank_id, {})

def get_available_relays():
    """Get list of available relay IDs"""
    return list(RELAY_GPIO_PINS.keys())

def get_available_pumps():
    """Get list of available pump IDs"""
    return list(PUMP_ADDRESSES.keys())

def get_available_flow_meters():
    """Get list of available flow meter IDs"""
    return list(FLOW_METER_GPIO_PINS.keys())

def validate_relay_id(relay_id):
    """Check if relay ID is valid"""
    return relay_id in RELAY_GPIO_PINS

def validate_pump_id(pump_id):
    """Check if pump ID is valid"""
    return pump_id in PUMP_ADDRESSES

def validate_flow_meter_id(meter_id):
    """Check if flow meter ID is valid"""
    return meter_id in FLOW_METER_GPIO_PINS


def _validate_relay_references():
    """Fail loudly on relay-config drift.

    Every relay referenced by TANKS and RELAY_COMBOS must have a GPIO pin in
    RELAY_GPIO_PINS, otherwise control_relay() silently rejects it and the
    corresponding tank operation (e.g. "Send Tank 2", which references relay 11)
    just does nothing. This surfaces that as a startup warning instead of a
    silent no-op. Returns the list of missing relay IDs.
    """
    import logging
    log = logging.getLogger(__name__)

    referenced = set()
    for tank in TANKS.values():
        if "fill_relay" in tank:
            referenced.add(tank["fill_relay"])
        if "send_relay" in tank:
            referenced.add(tank["send_relay"])
        referenced.update(tank.get("mix_relays", []))
    for combo in RELAY_COMBOS.values():
        referenced.update(combo)

    missing = sorted(r for r in referenced if r not in RELAY_GPIO_PINS)
    if missing:
        log.warning(
            "Relay config drift: relay(s) %s are referenced by TANKS/RELAY_COMBOS "
            "but have no GPIO pin in RELAY_GPIO_PINS. Operations using them will "
            "silently fail validation. Add the pin(s) or fix the references.",
            missing,
        )
    return missing


# Run the check at import so the warning shows up wherever config is loaded.
_validate_relay_references()

# =============================================================================
# NUTRIENT FORMULAS - MOVED TO nutrients.json
# =============================================================================
# Note: Nutrient formulas, available nutrients, and pump mappings are now 
# stored in nutrients.json and managed via the /api/nutrients endpoints.
# This provides better separation of concerns and easier management.

# Job configuration
JOB_SETTINGS = {
    "fill_timeout_minutes": 60,
    "mix_duration_minutes": 5,
    "send_timeout_minutes": 30,
    "ph_tolerance": 0.1,
    "ec_tolerance": 0.1,
    "min_water_gallons": 20  # Minimum water before mixing
}

# =============================================================================
# DEVELOPMENT/DEBUG SETTINGS
# =============================================================================

# Debug flags
DEBUG_MODE = False
USE_MOCK_HARDWARE = False
VERBOSE_LOGGING = False

# Mock hardware settings (for testing without real hardware)
MOCK_SETTINGS = {
    "pumps": False,         # Use mock pumps
    "relays": False,        # Use real relays
    "flow_meters": False,   # Use mock flow meters
    "arduino": False,       # Use mock EC/pH sensors (legacy key name; now the EZO I2C sensor)
    "tank_monitors": False  # Use mock per-tank pH/EC monitors
}

# Test configuration
TEST_PUMP_ID = 1
TEST_RELAY_ID = 2
TEST_FLOW_METER_ID = 1
TEST_VOLUME_ML = 10.0
TEST_FLOW_GALLONS = 5

if __name__ == "__main__":
    """Print configuration summary when run directly"""
    print("Feed Control System Configuration")
    print("=" * 50)
    
    print(f"\nRelays: {len(RELAY_GPIO_PINS)} available")
    for relay_id, gpio in RELAY_GPIO_PINS.items():
        print(f"  Relay {relay_id:2d} (GPIO {gpio:2d}): {get_relay_name(relay_id)}")
    
    print(f"\nPumps: {len(PUMP_ADDRESSES)} available")
    for pump_id, addr in PUMP_ADDRESSES.items():
        print(f"  Pump {pump_id} (I2C {addr:3d}): {get_pump_name(pump_id)}")
    
    print(f"\nFlow Meters: {len(FLOW_METER_GPIO_PINS)} available")
    for meter_id, gpio in FLOW_METER_GPIO_PINS.items():
        print(f"  Flow {meter_id} (GPIO {gpio}): {get_flow_meter_name(meter_id)}")
    
    print(f"\nTanks: {len(TANKS)} configured")
    for tank_id, info in TANKS.items():
        print(f"  Tank {tank_id}: {info['name']} ({info['capacity_gallons']} gal)")
    
    print(f"\nSystem Settings:")
    print(f"  I2C Bus: {I2C_BUS_NUMBER}")
    print(f"  EZO pH/EC I2C: 0x{EZO_PH_ADDRESS:02X} / 0x{EZO_EC_ADDRESS:02X}")
    print(f"  Tank Monitor Baudrate: {TANK_MONITOR_BAUDRATE}")
    print(f"  Status Interval: {STATUS_UPDATE_INTERVAL}s")
    print(f"  Debug Mode: {DEBUG_MODE}")