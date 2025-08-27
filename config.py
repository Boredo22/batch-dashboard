#!/usr/bin/env python3
"""
Feed Control System Configuration
Centralized configuration for all hardware mappings, constants, and settings
"""

# =============================================================================
# RELAY CONFIGURATION (ULN2803A Darlington Array)
# =============================================================================

# GPIO pin mappings for relays (from relay_mapping.json)
# Format: {relay_id: gpio_pin}
RELAY_GPIO_PINS = {
    1: 22,   # Relay 1 on GPIO 22,
    2: 26,   # Tank 2 Fill
    3: 20,   # Tank 3 Fill
    4: 21,   # Tank 1 Nute Dispense
    5: 16,   # Tank 2 Nute Dispense
    6: 19,   # Tank 3 Nute Dispense
    7: 12,   # Tank 1 Dispense Send
    8: 13,   # Tank 2 Dispense Send
    9: 10,   # Tank 3 Dispense Send
    10: 9,   # Room 1
    12: 0,
    13: 5
}

# Descriptive names for each relay
RELAY_NAMES = {
    2: "Tank 2 Fill",
    3: "Tank 3 Fill", 
    4: "Tank 1 Nute Dispense",
    6: "Tank 2 Nute Dispense",
    7: "Tank 1 Dispense Send",
    8: "Tank 2 Dispense Send",
    9: "Tank 3 Dispense Send",
    10: "Room 1",
}

# Relay logic settings (for ULN2803A)
RELAY_ACTIVE_HIGH = True  # GPIO HIGH = Relay ON (due to ULN2803A inversion)

# =============================================================================
# PUMP CONFIGURATION (Atlas Scientific EZO-PMP)
# =============================================================================

# EZO Pump I2C addresses
PUMP_ADDRESSES = {
    1: 1,    # Pump 1 at I2C address 1
    2: 2,    # Pump 2 at I2C address 2
    3: 3,    # Pump 3 at I2C address 3
    4: 4,    # Pump 4 at I2C address 4
    5: 5,    # Pump 5 at I2C address 5
    6: 6,    # Pump 6 at I2C address 6
    7: 7,    # Pump 7 at I2C address 7
    8: 8,    # Pump 8 at I2C address 8
}

# Pump names/descriptions
PUMP_NAMES = {
    1: "Nitrogen A",
    2: "Nitrogen B", 
    3: "Phosphorus A",
    4: "Phosphorus B",
    5: "Potassium A",
    6: "Potassium B",
    7: "Micronutrients",
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

# Flow meter GPIO pin mappings
FLOW_METER_GPIO_PINS = {
    1: 3,    # Flow meter 1 on GPIO 3
    2: 2,    # Flow meter 2 on GPIO 2
}

# Flow meter names
FLOW_METER_NAMES = {
    1: "Tank 1 Fill Flow",
    2: "Tank 2 Fill Flow",
}

# Flow meter calibration (pulses per gallon)
FLOW_METER_CALIBRATION = {
    1: 220,  # Pulses per gallon for meter 1
    2: 220,  # Pulses per gallon for meter 2
}

# Flow meter settings
FLOW_METER_INTERRUPT_EDGE = "FALLING"  # Interrupt on falling edge

# =============================================================================
# ARDUINO UNO CONFIGURATION (EC/pH Sensors)
# =============================================================================

# Arduino Uno serial communication
ARDUINO_UNO_PORTS = [
    "/dev/ttyACM0",
    "/dev/ttyACM1", 
    "/dev/ttyUSB0",
    "/dev/ttyUSB1"
]

ARDUINO_UNO_BAUDRATE = 115200
ARDUINO_UNO_TIMEOUT = 1.0

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
        "name": "Nutrient Tank 1",
        "capacity_gallons": 55,
        "fill_relay": 4,        # Tank 1 Nute Dispense
        "send_relay": 7,        # Tank 1 Dispense Send
        "flow_meter": 1,
        "pumps": [1, 3, 5, 7]   # Associated nutrient pumps
    },
    2: {
        "name": "Nutrient Tank 2", 
        "capacity_gallons": 55,
        "fill_relay": 2,        # Tank 2 Fill
        "send_relay": 8,        # Tank 2 Dispense Send
        "flow_meter": 2,
        "pumps": [2, 4, 6, 8]   # Associated nutrient pumps
    },
    3: {
        "name": "Nutrient Tank 3",
        "capacity_gallons": 55,
        "fill_relay": 3,        # Tank 3 Fill
        "send_relay": 9,        # Tank 3 Dispense Send
        "flow_meter": None,     # No flow meter assigned
        "pumps": []             # No pumps assigned yet
    }
}

# Room/zone definitions
ROOMS = {
    1: {
        "name": "Grow Room 1",
        "relay": 10,            # Room 1 relay
        "tanks": [1, 2],        # Can receive from these tanks
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

# =============================================================================
# DEVELOPMENT/DEBUG SETTINGS
# =============================================================================

# Debug flags
DEBUG_MODE = False
USE_MOCK_HARDWARE = False
VERBOSE_LOGGING = False

# Mock hardware settings (for testing without real hardware)
MOCK_SETTINGS = {
    "pumps": True,      # Use mock pumps
    "relays": False,    # Use real relays
    "flow_meters": True, # Use mock flow meters
    "arduino": True     # Use mock Arduino
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
    print(f"  Arduino Baudrate: {ARDUINO_UNO_BAUDRATE}")
    print(f"  Status Interval: {STATUS_UPDATE_INTERVAL}s")
    print(f"  Debug Mode: {DEBUG_MODE}")