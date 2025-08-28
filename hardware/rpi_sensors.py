#!/usr/bin/env python3
"""
pH/EC Sensor Controller for Raspberry Pi
Atlas Scientific EZO sensor communication and mock sensor support
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
from config import (
    PH_CALIBRATION_SOLUTIONS,
    EC_CALIBRATION_SOLUTIONS,
    I2C_BUS_NUMBER,
    EZO_COMMAND_DELAY,
    EZO_MAX_RETRIES,
    EZO_RETRY_DELAY,
    EZO_RESPONSE_CODES
)

try:
    import smbus2
except ImportError:
    print("smbus2 not installed. Install with: pip install smbus2")
    smbus2 = None

logger = logging.getLogger(__name__)

class SensorController:
    """Atlas Scientific EZO pH/EC sensor controller"""
    
    def __init__(self, ph_address: int = 99, ec_address: int = 100, bus_number: int = None):
        """Initialize sensor controller"""
        self.ph_address = ph_address
        self.ec_address = ec_address
        self.bus_number = bus_number or I2C_BUS_NUMBER
        self.bus = None
        
        # Sensor information
        self.sensor_info = {
            'ph': {
                'address': ph_address,
                'calibrated': False,
                'last_reading': None,
                'last_reading_time': 0,
                'connected': False,
                'temperature_compensation': 25.0  # Default temp
            },
            'ec': {
                'address': ec_address,
                'calibrated': False,
                'last_reading': None,
                'last_reading_time': 0,
                'connected': False,
                'temperature_compensation': 25.0  # Default temp
            }
        }
        
        # Target ranges for validation
        self.target_ranges = {
            'ph': {'min': 5.5, 'max': 6.5, 'tolerance': 0.1},
            'ec': {'min': 1.0, 'max': 2.0, 'tolerance': 0.1}
        }
        
        # Initialize I2C bus
        self.initialize_bus()
        
        # Initialize sensors
        self.initialize_sensors()
    
    def initialize_bus(self):
        """Initialize I2C bus connection"""
        if not smbus2:
            logger.error("smbus2 not available - cannot initialize I2C bus")
            return False
        
        try:
            self.bus = smbus2.SMBus(self.bus_number)
            logger.info(f"Initialized I2C bus {self.bus_number} for sensors")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus {self.bus_number}: {e}")
            return False
    
    def send_command(self, sensor_type: str, command: str, delay: float = None) -> Optional[str]:
        """Send command to EZO sensor using proper I2C method"""
        if sensor_type not in self.sensor_info:
            logger.error(f"Invalid sensor type: {sensor_type}")
            return None
        
        if not self.bus:
            logger.error("I2C bus not initialized")
            return None
        
        address = self.sensor_info[sensor_type]['address']
        delay = delay or EZO_COMMAND_DELAY
        
        retries = 0
        while retries < EZO_MAX_RETRIES:
            try:
                # Send command using raw I2C
                msg = smbus2.i2c_msg.write(address, list(command.encode()))
                self.bus.i2c_rdwr(msg)
                
                # Wait for processing
                time.sleep(delay)
                
                # Read response
                msg = smbus2.i2c_msg.read(address, 32)
                self.bus.i2c_rdwr(msg)
                
                data = list(msg)
                
                # Parse response
                if len(data) > 0:
                    response_code = data[0]
                    
                    if response_code == 1:  # Success
                        response_text = ''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip()
                        logger.debug(f"{sensor_type.upper()} sensor ({command}): {response_text}")
                        self.sensor_info[sensor_type]['connected'] = True
                        return response_text
                    elif response_code == 254:  # Still processing
                        retries += 1
                        time.sleep(EZO_RETRY_DELAY)
                        continue
                    else:
                        error_msg = EZO_RESPONSE_CODES.get(response_code, f"Unknown error: {response_code}")
                        logger.warning(f"{sensor_type.upper()} sensor error: {error_msg}")
                        return None
                else:
                    logger.warning(f"{sensor_type.upper()} sensor: No response data")
                    return None
                
            except Exception as e:
                retries += 1
                logger.debug(f"{sensor_type.upper()} sensor retry {retries}/{EZO_MAX_RETRIES}: {e}")
                if retries < EZO_MAX_RETRIES:
                    time.sleep(EZO_RETRY_DELAY * retries)
                else:
                    logger.error(f"{sensor_type.upper()} sensor failed after {EZO_MAX_RETRIES} retries: {e}")
                    self.sensor_info[sensor_type]['connected'] = False
        
        return None
    
    def initialize_sensors(self):
        """Initialize pH and EC sensors"""
        logger.info("Initializing pH/EC sensors...")
        
        for sensor_type in ['ph', 'ec']:
            logger.debug(f"Initializing {sensor_type.upper()} sensor...")
            
            # Get device info
            info = self.send_command(sensor_type, "i")
            if info:
                logger.info(f"{sensor_type.upper()} sensor: {info}")
                self.sensor_info[sensor_type]['connected'] = True
                
                # Get calibration status
                cal_status = self.send_command(sensor_type, "Cal,?")
                if cal_status and cal_status.startswith("?Cal,"):
                    cal_value = cal_status.split(",")[1] if "," in cal_status else "0"
                    self.sensor_info[sensor_type]['calibrated'] = int(cal_value) > 0
                    logger.info(f"{sensor_type.upper()} calibration status: {self.sensor_info[sensor_type]['calibrated']}")
                
                # Set temperature compensation
                temp_cmd = f"T,{self.sensor_info[sensor_type]['temperature_compensation']}"
                self.send_command(sensor_type, temp_cmd)
                
            else:
                logger.warning(f"{sensor_type.upper()} sensor not responding")
                self.sensor_info[sensor_type]['connected'] = False
        
        connected_sensors = sum(1 for info in self.sensor_info.values() if info['connected'])
        logger.info(f"Initialized {connected_sensors}/2 sensors")
    
    def read_ph(self) -> Optional[float]:
        """Read pH value"""
        response = self.send_command('ph', "R")
        if response:
            try:
                ph_value = float(response)
                self.sensor_info['ph']['last_reading'] = ph_value
                self.sensor_info['ph']['last_reading_time'] = time.time()
                logger.debug(f"pH reading: {ph_value}")
                return ph_value
            except ValueError:
                logger.warning(f"Invalid pH response: {response}")
        return None
    
    def read_ec(self) -> Optional[float]:
        """Read EC value in mS/cm"""
        response = self.send_command('ec', "R")
        if response:
            try:
                # EC response format: "EC,TDS,SAL,SG"
                if "," in response:
                    ec_value = float(response.split(",")[0])
                else:
                    ec_value = float(response)
                
                # Convert to mS/cm if needed
                if ec_value > 100:  # Likely in µS/cm
                    ec_value = ec_value / 1000.0
                
                self.sensor_info['ec']['last_reading'] = ec_value
                self.sensor_info['ec']['last_reading_time'] = time.time()
                logger.debug(f"EC reading: {ec_value} mS/cm")
                return ec_value
            except ValueError:
                logger.warning(f"Invalid EC response: {response}")
        return None
    
    def read_both_sensors(self) -> Dict[str, Optional[float]]:
        """Read both pH and EC sensors"""
        return {
            'ph': self.read_ph(),
            'ec': self.read_ec(),
            'timestamp': time.time()
        }
    
    def set_temperature_compensation(self, temperature: float):
        """Set temperature compensation for both sensors"""
        for sensor_type in ['ph', 'ec']:
            if self.sensor_info[sensor_type]['connected']:
                temp_cmd = f"T,{temperature:.1f}"
                response = self.send_command(sensor_type, temp_cmd)
                if response:
                    self.sensor_info[sensor_type]['temperature_compensation'] = temperature
                    logger.info(f"{sensor_type.upper()} temperature compensation set to {temperature}°C")
    
    def calibrate_ph(self, solution_type: str, actual_ph: float = None) -> bool:
        """Calibrate pH sensor"""
        if solution_type not in PH_CALIBRATION_SOLUTIONS:
            logger.error(f"Invalid pH calibration solution: {solution_type}")
            return False
        
        if not self.sensor_info['ph']['connected']:
            logger.error("pH sensor not connected")
            return False
        
        # Use config value or provided value
        ph_value = actual_ph or PH_CALIBRATION_SOLUTIONS[solution_type]
        
        # Send calibration command
        cal_cmd = f"Cal,{solution_type},{ph_value}"
        response = self.send_command('ph', cal_cmd)
        
        if response:
            logger.info(f"pH sensor calibrated with {solution_type} solution (pH {ph_value})")
            self.sensor_info['ph']['calibrated'] = True
            return True
        else:
            logger.error(f"pH calibration failed for {solution_type}")
            return False
    
    def calibrate_ec(self, solution_type: str, actual_ec: float = None) -> bool:
        """Calibrate EC sensor"""
        if solution_type not in EC_CALIBRATION_SOLUTIONS:
            logger.error(f"Invalid EC calibration solution: {solution_type}")
            return False
        
        if not self.sensor_info['ec']['connected']:
            logger.error("EC sensor not connected")
            return False
        
        # Use config value or provided value
        ec_value = actual_ec or EC_CALIBRATION_SOLUTIONS[solution_type]
        
        # Send calibration command
        cal_cmd = f"Cal,{solution_type},{ec_value}"
        response = self.send_command('ec', cal_cmd)
        
        if response:
            logger.info(f"EC sensor calibrated with {solution_type} solution ({ec_value} µS/cm)")
            self.sensor_info['ec']['calibrated'] = True
            return True
        else:
            logger.error(f"EC calibration failed for {solution_type}")
            return False
    
    def validate_readings(self, ph_target: float = None, ec_target: float = None) -> Dict[str, bool]:
        """Validate current readings against targets"""
        readings = self.read_both_sensors()
        validation = {'ph': False, 'ec': False}
        
        # Validate pH
        if readings['ph'] is not None:
            if ph_target is not None:
                ph_tolerance = self.target_ranges['ph']['tolerance']
                validation['ph'] = abs(readings['ph'] - ph_target) <= ph_tolerance
            else:
                # Check if within general acceptable range
                ph_range = self.target_ranges['ph']
                validation['ph'] = ph_range['min'] <= readings['ph'] <= ph_range['max']
        
        # Validate EC
        if readings['ec'] is not None:
            if ec_target is not None:
                ec_tolerance = self.target_ranges['ec']['tolerance']
                validation['ec'] = abs(readings['ec'] - ec_target) <= ec_tolerance
            else:
                # Check if within general acceptable range
                ec_range = self.target_ranges['ec']
                validation['ec'] = ec_range['min'] <= readings['ec'] <= ec_range['max']
        
        return validation
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """Get comprehensive sensor status"""
        return {
            'ph': {
                'connected': self.sensor_info['ph']['connected'],
                'calibrated': self.sensor_info['ph']['calibrated'],
                'last_reading': self.sensor_info['ph']['last_reading'],
                'last_reading_time': self.sensor_info['ph']['last_reading_time'],
                'temperature_compensation': self.sensor_info['ph']['temperature_compensation']
            },
            'ec': {
                'connected': self.sensor_info['ec']['connected'],
                'calibrated': self.sensor_info['ec']['calibrated'],
                'last_reading': self.sensor_info['ec']['last_reading'],
                'last_reading_time': self.sensor_info['ec']['last_reading_time'],
                'temperature_compensation': self.sensor_info['ec']['temperature_compensation']
            },
            'target_ranges': self.target_ranges
        }
    
    def close(self):
        """Close I2C bus connection"""
        if self.bus:
            try:
                self.bus.close()
                self.bus = None
                logger.info("Sensor I2C bus closed")
            except Exception as e:
                logger.error(f"Error closing sensor I2C bus: {e}")


class MockSensorController(SensorController):
    """Mock sensor controller for testing without hardware"""
    
    def __init__(self, ph_address: int = 99, ec_address: int = 100, bus_number: int = None):
        """Initialize mock sensor controller"""
        # Don't call parent __init__ to avoid I2C initialization
        self.ph_address = ph_address
        self.ec_address = ec_address
        self.bus_number = bus_number or I2C_BUS_NUMBER
        self.bus = None
        
        # Mock sensor information
        self.sensor_info = {
            'ph': {
                'address': ph_address,
                'calibrated': True,  # Mock as calibrated
                'last_reading': 6.2,
                'last_reading_time': time.time(),
                'connected': True,
                'temperature_compensation': 25.0
            },
            'ec': {
                'address': ec_address,
                'calibrated': True,  # Mock as calibrated
                'last_reading': 1.4,
                'last_reading_time': time.time(),
                'connected': True,
                'temperature_compensation': 25.0
            }
        }
        
        # Target ranges for validation
        self.target_ranges = {
            'ph': {'min': 5.5, 'max': 6.5, 'tolerance': 0.1},
            'ec': {'min': 1.0, 'max': 2.0, 'tolerance': 0.1}
        }
        
        logger.info("Mock sensor controller initialized")
    
    def initialize_bus(self):
        """Mock bus initialization"""
        return True
    
    def initialize_sensors(self):
        """Mock sensor initialization"""
        logger.info("Mock sensors initialized (pH: 6.2, EC: 1.4 mS/cm)")
    
    def send_command(self, sensor_type: str, command: str, delay: float = None) -> Optional[str]:
        """Mock command sending"""
        if sensor_type not in self.sensor_info:
            return None
        
        # Simulate some common responses
        if command == "i":
            return f"?I,{sensor_type.upper()},1.0"
        elif command == "Cal,?":
            return "?Cal,3"  # Mock as 3-point calibrated
        elif command == "R":
            # Return mock reading
            if sensor_type == 'ph':
                return str(self.sensor_info['ph']['last_reading'])
            elif sensor_type == 'ec':
                return f"{self.sensor_info['ec']['last_reading']:.2f}"
        elif command.startswith("T,"):
            return "OK"
        elif command.startswith("Cal,"):
            return "OK"
        
        return "OK"
    
    def read_ph(self) -> Optional[float]:
        """Mock pH reading with slight variation"""
        import random
        base_ph = 6.2
        variation = random.uniform(-0.1, 0.1)
        ph_value = base_ph + variation
        
        self.sensor_info['ph']['last_reading'] = ph_value
        self.sensor_info['ph']['last_reading_time'] = time.time()
        logger.debug(f"Mock pH reading: {ph_value}")
        return ph_value
    
    def read_ec(self) -> Optional[float]:
        """Mock EC reading with slight variation"""
        import random
        base_ec = 1.4
        variation = random.uniform(-0.1, 0.1)
        ec_value = base_ec + variation
        
        self.sensor_info['ec']['last_reading'] = ec_value
        self.sensor_info['ec']['last_reading_time'] = time.time()
        logger.debug(f"Mock EC reading: {ec_value} mS/cm")
        return ec_value
    
    def close(self):
        """Mock cleanup"""
        logger.info("Mock sensor controller closed")


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("pH/EC Sensor Controller Test")
    print("=" * 40)
    
    # Use mock controller for testing
    controller = MockSensorController()
    
    # Test sensor status
    status = controller.get_sensor_status()
    print(f"pH sensor connected: {status['ph']['connected']}")
    print(f"EC sensor connected: {status['ec']['connected']}")
    
    # Test readings
    print("\nTesting sensor readings...")
    for i in range(5):
        readings = controller.read_both_sensors()
        print(f"Reading {i+1}: pH={readings['ph']:.2f}, EC={readings['ec']:.2f} mS/cm")
        
        # Test validation
        validation = controller.validate_readings(ph_target=6.0, ec_target=1.5)
        print(f"  Validation: pH={'✓' if validation['ph'] else '✗'}, EC={'✓' if validation['ec'] else '✗'}")
        
        time.sleep(1)
    
    # Test calibration
    print("\nTesting calibration...")
    ph_cal = controller.calibrate_ph('mid', 7.0)
    ec_cal = controller.calibrate_ec('single', 1413)
    print(f"pH calibration: {'✓' if ph_cal else '✗'}")
    print(f"EC calibration: {'✓' if ec_cal else '✗'}")
    
    controller.close()
    print("Test completed")