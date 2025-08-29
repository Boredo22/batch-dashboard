#!/usr/bin/env python3
"""
Atlas Scientific EZO Pump Controller for Raspberry Pi
Uses centralized configuration from config.py
Implements the correct I2C communication method for EZO pumps
Works independently without hardware manager - compatible with simple_gui.py pattern
"""

import time
import logging
from config import (
    PUMP_ADDRESSES,
    PUMP_NAMES,
    I2C_BUS_NUMBER,
    I2C_DEFAULT_ADDRESS,
    EZO_COMMAND_DELAY,
    EZO_MAX_RETRIES,
    EZO_RETRY_DELAY,
    EZO_RESPONSE_CODES,
    MAX_PUMP_VOLUME_ML,
    MIN_PUMP_VOLUME_ML,
    PUMP_VOLTAGE_MIN,
    PUMP_VOLTAGE_MAX,
    get_pump_name,
    get_available_pumps,
    validate_pump_id
)

try:
    import smbus2
except ImportError:
    print("smbus2 not installed. Install with: pip install smbus2")
    exit(1)

logger = logging.getLogger(__name__)

class EZOPumpController:
    def __init__(self, bus_number=None):
        """Initialize EZO Pump Controller"""
        self.bus_number = bus_number or I2C_BUS_NUMBER
        self.bus = None
        
        # Pump information storage
        self.pump_info = {}
        for pump_id in PUMP_ADDRESSES.keys():
            self.pump_info[pump_id] = {
                'name': get_pump_name(pump_id),
                'address': PUMP_ADDRESSES[pump_id],
                'calibrated': False,
                'voltage': 0.0,
                'total_volume': 0.0,
                'current_volume': 0.0,
                'target_volume': 0.0,
                'is_dispensing': False,
                'last_check': 0,
                'last_error': '',
                'connected': False
            }
        
        # Initialize I2C bus
        self.initialize_bus()
        
        # Initialize pumps
        self.initialize_pumps()
    
    def initialize_bus(self):
        """Initialize I2C bus connection"""
        try:
            self.bus = smbus2.SMBus(self.bus_number)
            logger.info(f"Initialized I2C bus {self.bus_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus {self.bus_number}: {e}")
            return False
    
    def send_command(self, pump_id, command, delay=None):
        """Send command to EZO pump using proper I2C method"""
        if not validate_pump_id(pump_id):
            logger.error(f"Invalid pump ID: {pump_id}")
            return None
        
        if not self.bus:
            logger.error("I2C bus not initialized")
            return None
        
        address = PUMP_ADDRESSES[pump_id]
        delay = delay or EZO_COMMAND_DELAY
        
        retries = 0
        while retries < EZO_MAX_RETRIES:
            try:
                # Send command using raw I2C (equivalent to Arduino Wire library)
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
                        logger.debug(f"Pump {pump_id} ({command}): {response_text}")
                        self.pump_info[pump_id]['connected'] = True
                        self.pump_info[pump_id]['last_error'] = ''
                        return response_text
                    elif response_code == 254:  # Still processing
                        retries += 1
                        time.sleep(EZO_RETRY_DELAY)
                        continue
                    else:
                        error_msg = EZO_RESPONSE_CODES.get(response_code, f"Unknown error: {response_code}")
                        logger.warning(f"Pump {pump_id} error: {error_msg}")
                        self.pump_info[pump_id]['last_error'] = error_msg
                        return None
                else:
                    logger.warning(f"Pump {pump_id}: No response data")
                    return None
                
            except Exception as e:
                retries += 1
                logger.debug(f"Pump {pump_id} retry {retries}/{EZO_MAX_RETRIES}: {e}")
                if retries < EZO_MAX_RETRIES:
                    time.sleep(EZO_RETRY_DELAY * retries)
                else:
                    logger.error(f"Pump {pump_id} failed after {EZO_MAX_RETRIES} retries: {e}")
                    self.pump_info[pump_id]['connected'] = False
                    self.pump_info[pump_id]['last_error'] = str(e)
        
        return None
    
    def initialize_pumps(self):
        """Initialize all pumps and get their status"""
        logger.info("Initializing EZO pumps...")
        
        for pump_id in PUMP_ADDRESSES.keys():
            logger.debug(f"Initializing pump {pump_id}...")
            
            # Get device info
            info = self.send_command(pump_id, "i")
            if info:
                logger.info(f"Pump {pump_id}: {info}")
                self.pump_info[pump_id]['connected'] = True
                
                # Get calibration status
                cal_status = self.send_command(pump_id, "Cal,?")
                if cal_status and cal_status.startswith("?Cal,"):
                    cal_value = cal_status.split(",")[1] if "," in cal_status else "0"
                    self.pump_info[pump_id]['calibrated'] = int(cal_value) > 0
                
                # Get voltage
                voltage = self.send_command(pump_id, "PV,?")
                if voltage and voltage.startswith("?PV,"):
                    voltage_value = voltage.split(",")[1] if "," in voltage else "0"
                    try:
                        self.pump_info[pump_id]['voltage'] = float(voltage_value)
                    except ValueError:
                        pass
                
                # Get pump name
                name = self.send_command(pump_id, "Name,?")
                if name and name.startswith("?Name,"):
                    pump_name = name.split(",")[1] if "," in name else ""
                    if pump_name:
                        # Don't override config names unless pump has a custom name
                        pass
            else:
                logger.warning(f"Pump {pump_id} not responding")
                self.pump_info[pump_id]['connected'] = False
        
        connected_pumps = sum(1 for info in self.pump_info.values() if info['connected'])
        logger.info(f"Initialized {connected_pumps}/{len(PUMP_ADDRESSES)} pumps")
    
    def start_dispense(self, pump_id, volume_ml):
        """Start dispensing specified volume"""
        if not validate_pump_id(pump_id):
            return False
        
        if not (MIN_PUMP_VOLUME_ML <= volume_ml <= MAX_PUMP_VOLUME_ML):
            logger.error(f"Volume {volume_ml}ml outside valid range ({MIN_PUMP_VOLUME_ML}-{MAX_PUMP_VOLUME_ML}ml)")
            return False
        
        if not self.pump_info[pump_id]['connected']:
            logger.error(f"Pump {pump_id} not connected")
            return False
        
        # Check if pump is already dispensing
        if self.pump_info[pump_id]['is_dispensing']:
            logger.warning(f"Pump {pump_id} is already dispensing")
            return False
        
        # Send dispense command
        command = f"D,{volume_ml:.2f}"
        response = self.send_command(pump_id, command)
        
        if response is not None:
            # Update pump state
            self.pump_info[pump_id]['target_volume'] = volume_ml
            self.pump_info[pump_id]['current_volume'] = 0.0
            self.pump_info[pump_id]['is_dispensing'] = True
            self.pump_info[pump_id]['last_check'] = time.time()
            
            pump_name = get_pump_name(pump_id)
            logger.info(f"Started dispensing {volume_ml}ml from {pump_name}")
            return True
        
        return False
    
    def stop_dispense(self, pump_id):
        """Stop dispensing"""
        if not validate_pump_id(pump_id):
            return None
        
        response = self.send_command(pump_id, "X")
        
        if response and response.startswith("*DONE,"):
            try:
                # Parse dispensed volume
                volume_str = response.split(",")[1]
                dispensed_volume = float(volume_str)
                
                # Update pump state
                self.pump_info[pump_id]['current_volume'] = dispensed_volume
                self.pump_info[pump_id]['is_dispensing'] = False
                self.pump_info[pump_id]['total_volume'] += dispensed_volume
                
                pump_name = get_pump_name(pump_id)
                logger.info(f"Stopped {pump_name}: {dispensed_volume}ml dispensed")
                return dispensed_volume
            except (IndexError, ValueError) as e:
                logger.error(f"Error parsing stop response: {e}")
        
        # Still try to update state even if parsing failed
        self.pump_info[pump_id]['is_dispensing'] = False
        return None
    
    def check_pump_status(self, pump_id):
        """Check current pump status and update volume"""
        if not validate_pump_id(pump_id):
            return False
        
        if not self.pump_info[pump_id]['is_dispensing']:
            return False
        
        # Get current dispensed volume
        response = self.send_command(pump_id, "R")
        
        if response:
            try:
                current_volume = float(response)
                self.pump_info[pump_id]['current_volume'] = current_volume
                self.pump_info[pump_id]['last_check'] = time.time()
                
                # Check if target reached (with small tolerance)
                target = self.pump_info[pump_id]['target_volume']
                if current_volume >= (target - 0.1):  # 0.1ml tolerance
                    self.pump_info[pump_id]['is_dispensing'] = False
                    self.pump_info[pump_id]['total_volume'] += current_volume
                    
                    pump_name = get_pump_name(pump_id)
                    logger.info(f"{pump_name} completed: {current_volume}ml/{target}ml")
                    return False  # Completed
                
                return True  # Still dispensing
            except ValueError:
                logger.warning(f"Invalid volume response from pump {pump_id}: {response}")
        
        return self.pump_info[pump_id]['is_dispensing']
    
    def calibrate_pump(self, pump_id, volume_ml):
        """Calibrate pump with actual dispensed volume"""
        if not validate_pump_id(pump_id):
            return False
        
        command = f"Cal,{volume_ml:.2f}"
        response = self.send_command(pump_id, command)
        
        if response is not None:
            self.pump_info[pump_id]['calibrated'] = True
            pump_name = get_pump_name(pump_id)
            logger.info(f"Calibrated {pump_name} with {volume_ml}ml")
            return True
        
        return False
    
    def get_pump_info(self, pump_id):
        """Get pump information"""
        if not validate_pump_id(pump_id):
            return None
        
        return self.pump_info[pump_id].copy()
    
    def get_all_pumps_status(self):
        """Get status of all pumps"""
        return {pump_id: info.copy() for pump_id, info in self.pump_info.items()}
    
    def emergency_stop(self):
        """Emergency stop all pumps"""
        logger.warning("Emergency stop - stopping all pumps")
        
        success = True
        for pump_id in PUMP_ADDRESSES.keys():
            if self.pump_info[pump_id]['is_dispensing']:
                try:
                    result = self.stop_dispense(pump_id)
                    if result is None:
                        success = False
                except Exception as e:
                    logger.error(f"Pump {pump_id} error: {e}")
                    success = False
        
        logger.info("All pumps stopped")
        return success
    
    def close(self):
        """Close I2C bus connection"""
        if self.bus:
            try:
                self.bus.close()
                self.bus = None
                logger.info("I2C bus closed")
            except Exception as e:
                logger.error(f"Error closing I2C bus: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.close()
        except:
            pass


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("EZO Pump Controller Test (Using config.py)")
    print("=" * 50)
    
    controller = EZOPumpController()
    
    print(f"I2C Bus: {I2C_BUS_NUMBER}")
    print(f"Available pumps: {get_available_pumps()}")
    print()
    
    # Show pump status
    print("Pump Status:")
    all_status = controller.get_all_pumps_status()
    for pump_id, info in all_status.items():
        pump_name = get_pump_name(pump_id)
        status = "Connected" if info['connected'] else "Disconnected"
        cal_status = "Calibrated" if info['calibrated'] else "Uncalibrated"
        print(f"  Pump {pump_id}: {pump_name:20s} | {status:12s} | {cal_status:12s} | {info['voltage']:.1f}V")
    
    # Test with first available connected pump
    connected_pumps = [pid for pid, info in all_status.items() if info['connected']]
    
    if connected_pumps:
        test_pump = connected_pumps[0]
        test_volume = 5.0
        
        print(f"\nTesting pump {test_pump} with {test_volume}ml...")
        
        if controller.start_dispense(test_pump, test_volume):
            print("Dispense started. Monitoring progress...")
            
            # Monitor for 30 seconds
            start_time = time.time()
            while time.time() - start_time < 30:
                still_running = controller.check_pump_status(test_pump)
                info = controller.get_pump_info(test_pump)
                
                print(f"  Progress: {info['current_volume']:.2f}/{info['target_volume']:.2f}ml")
                
                if not still_running:
                    print("  Dispense completed!")
                    break
                
                time.sleep(1)
            
            # Stop if still running
            if controller.pump_info[test_pump]['is_dispensing']:
                print("Stopping pump...")
                final_volume = controller.stop_dispense(test_pump)
                print(f"Final volume: {final_volume}ml")
        else:
            print("Failed to start dispense")
    else:
        print("No connected pumps available for testing")
    
    controller.close()
    print("Test completed")