#!/usr/bin/env python3
"""
Mock Hardware Controllers for Development and Testing
Provides realistic mock implementations for all hardware components
"""

import time
import logging
import random
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MockPumpController:
    """Mock EZO Pump Controller with realistic behavior"""
    
    def __init__(self, bus_number=1):
        self.bus_number = bus_number
        self.mock_mode = True
        
        # Mock pump information storage
        from config import PUMP_ADDRESSES, get_pump_name
        self.pump_info = {}
        for pump_id in PUMP_ADDRESSES.keys():
            self.pump_info[pump_id] = {
                'name': get_pump_name(pump_id),
                'address': PUMP_ADDRESSES[pump_id],
                'calibrated': True,  # Mock as calibrated
                'voltage': random.uniform(11.5, 12.5),  # Realistic voltage
                'total_volume': 0.0,
                'current_volume': 0.0,
                'target_volume': 0.0,
                'is_dispensing': False,
                'last_check': 0,
                'last_error': '',
                'connected': True,
                'dispense_start_time': None
            }
        
        logger.info(f"Mock pump controller initialized with {len(PUMP_ADDRESSES)} pumps")
    
    def initialize_bus(self):
        """Mock bus initialization"""
        return True
    
    def send_command(self, pump_id, command, delay=None):
        """Mock command sending with realistic responses"""
        from config import validate_pump_id, get_pump_name
        
        if not validate_pump_id(pump_id):
            logger.error(f"Invalid pump ID: {pump_id}")
            return None
        
        # Simulate command delay
        time.sleep(delay or 0.1)
        
        pump_name = get_pump_name(pump_id)
        
        # Simulate occasional failures (5% chance)
        if random.random() < 0.05:
            logger.warning(f"Mock pump {pump_id} simulated communication failure")
            self.pump_info[pump_id]['connected'] = False
            return None
        
        self.pump_info[pump_id]['connected'] = True
        
        # Handle different commands
        if command == "i":
            return f"?I,PMP,1.0"
        elif command == "Cal,?":
            return "?Cal,1"  # Mock as single-point calibrated
        elif command.startswith("Cal,"):
            return "OK"
        elif command == "PV,?":
            voltage = self.pump_info[pump_id]['voltage']
            return f"?PV,{voltage:.1f}"
        elif command == "Name,?":
            return f"?Name,{pump_name}"
        elif command.startswith("D,"):
            # Dispense command
            try:
                volume = float(command.split(",")[1])
                self.pump_info[pump_id]['target_volume'] = volume
                self.pump_info[pump_id]['current_volume'] = 0.0
                self.pump_info[pump_id]['is_dispensing'] = True
                self.pump_info[pump_id]['dispense_start_time'] = time.time()
                return "OK"
            except (IndexError, ValueError):
                return "ER"
        elif command == "X":
            # Stop command
            if self.pump_info[pump_id]['is_dispensing']:
                dispensed = self.pump_info[pump_id]['current_volume']
                self.pump_info[pump_id]['is_dispensing'] = False
                self.pump_info[pump_id]['total_volume'] += dispensed
                return f"*DONE,{dispensed:.2f}"
            return "OK"
        elif command == "R":
            # Read current volume
            if self.pump_info[pump_id]['is_dispensing']:
                return str(self.pump_info[pump_id]['current_volume'])
            return "0.00"
        else:
            return "OK"
    
    def initialize_pumps(self):
        """Mock pump initialization"""
        logger.info("Mock pumps initialized")
    
    def start_dispense(self, pump_id, volume_ml):
        """Mock dispense start"""
        from config import validate_pump_id, MIN_PUMP_VOLUME_ML, MAX_PUMP_VOLUME_ML
        
        if not validate_pump_id(pump_id):
            return False
        
        if not (MIN_PUMP_VOLUME_ML <= volume_ml <= MAX_PUMP_VOLUME_ML):
            logger.error(f"Volume {volume_ml}ml outside valid range")
            return False
        
        if self.pump_info[pump_id]['is_dispensing']:
            logger.warning(f"Pump {pump_id} is already dispensing")
            return False
        
        response = self.send_command(pump_id, f"D,{volume_ml:.2f}")
        return response == "OK"
    
    def stop_dispense(self, pump_id):
        """Mock dispense stop"""
        from config import validate_pump_id
        
        if not validate_pump_id(pump_id):
            return None
        
        response = self.send_command(pump_id, "X")
        if response and response.startswith("*DONE,"):
            try:
                volume_str = response.split(",")[1]
                return float(volume_str)
            except (IndexError, ValueError):
                pass
        return None
    
    def check_pump_status(self, pump_id):
        """Mock pump status check with realistic progression"""
        from config import validate_pump_id
        
        if not validate_pump_id(pump_id):
            return False
        
        if not self.pump_info[pump_id]['is_dispensing']:
            return False
        
        # Simulate realistic dispensing progression
        if self.pump_info[pump_id]['dispense_start_time']:
            elapsed = time.time() - self.pump_info[pump_id]['dispense_start_time']
            target = self.pump_info[pump_id]['target_volume']
            
            # Simulate dispensing at ~10ml/second
            progress = min(elapsed * 10.0, target)
            self.pump_info[pump_id]['current_volume'] = progress
            
            # Complete when target reached
            if progress >= target:
                self.pump_info[pump_id]['is_dispensing'] = False
                self.pump_info[pump_id]['total_volume'] += progress
                return False
        
        return True
    
    def get_pump_info(self, pump_id):
        """Get mock pump information"""
        from config import validate_pump_id
        
        if not validate_pump_id(pump_id):
            return None
        
        return self.pump_info[pump_id].copy()
    
    def get_all_pumps_status(self):
        """Get status of all mock pumps"""
        return {pump_id: info.copy() for pump_id, info in self.pump_info.items()}
    
    def emergency_stop(self):
        """Mock emergency stop"""
        logger.warning("Mock emergency stop - stopping all pumps")
        for pump_id in self.pump_info.keys():
            if self.pump_info[pump_id]['is_dispensing']:
                self.stop_dispense(pump_id)
        logger.info("All mock pumps stopped")
    
    def close(self):
        """Mock cleanup"""
        logger.info("Mock pump controller closed")

class MockRelayController:
    """Mock Relay Controller with realistic behavior"""
    
    def __init__(self):
        from config import RELAY_GPIO_PINS, get_relay_name
        
        self.mock_mode = True
        self.relay_pins = RELAY_GPIO_PINS.copy()
        self.relay_states = {relay_id: False for relay_id in self.relay_pins.keys()}
        
        logger.info(f"Mock relay controller initialized with {len(self.relay_pins)} relays")
    
    def setup_gpio(self):
        """Mock GPIO setup"""
        return True
    
    def set_relay(self, relay_id, state):
        """Mock relay control with realistic behavior"""
        from config import validate_relay_id, get_relay_name
        
        if not validate_relay_id(relay_id):
            logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        # Simulate occasional failures (2% chance)
        if random.random() < 0.02:
            logger.warning(f"Mock relay {relay_id} simulated failure")
            return False
        
        # Simulate relay switching delay
        time.sleep(0.01)
        
        self.relay_states[relay_id] = state
        relay_name = get_relay_name(relay_id)
        state_str = "ON" if state else "OFF"
        logger.debug(f"Mock relay {relay_id} ({relay_name}) set to {state_str}")
        return True
    
    def set_all_relays(self, state):
        """Mock set all relays"""
        success_count = 0
        for relay_id in self.relay_pins:
            if self.set_relay(relay_id, state):
                success_count += 1
        
        state_str = "ON" if state else "OFF"
        logger.info(f"Mock set {success_count}/{len(self.relay_pins)} relays to {state_str}")
        return success_count == len(self.relay_pins)
    
    def get_relay_state(self, relay_id):
        """Get mock relay state"""
        return self.relay_states.get(relay_id, None)
    
    def get_all_relay_states(self):
        """Get all mock relay states"""
        return self.relay_states.copy()
    
    def toggle_relay(self, relay_id):
        """Mock toggle relay"""
        from config import validate_relay_id
        
        if not validate_relay_id(relay_id):
            return False
        
        current_state = self.get_relay_state(relay_id)
        if current_state is not None:
            return self.set_relay(relay_id, not current_state)
        return False
    
    def emergency_stop(self):
        """Mock emergency stop"""
        logger.warning("Mock emergency stop - turning off all relays")
        return self.set_all_relays(False)
    
    def get_available_relays(self):
        """Get available mock relays"""
        from config import get_available_relays
        return get_available_relays()
    
    def get_relay_info(self, relay_id):
        """Get mock relay information"""
        from config import validate_relay_id, get_relay_name, RELAY_ACTIVE_HIGH
        
        if not validate_relay_id(relay_id):
            return None
        
        return {
            "id": relay_id,
            "name": get_relay_name(relay_id),
            "gpio_pin": self.relay_pins[relay_id],
            "state": self.relay_states[relay_id],
            "active_high": RELAY_ACTIVE_HIGH,
            "mock": True
        }
    
    def cleanup(self):
        """Mock cleanup"""
        self.emergency_stop()
        logger.info("Mock relay controller cleanup completed")

class ConnectionManager:
    """Connection management and retry logic for hardware controllers"""
    
    def __init__(self, max_connections=5):
        self.connection_pool = {}
        self.max_connections = max_connections
        self.max_retries = 3
        self.retry_delay = 0.1
        
    def get_connection(self, bus_id):
        """Get pooled I2C connection"""
        if bus_id not in self.connection_pool:
            try:
                import smbus2
                self.connection_pool[bus_id] = smbus2.SMBus(bus_id)
                logger.debug(f"Created new I2C connection for bus {bus_id}")
            except Exception as e:
                logger.error(f"Failed to create I2C connection for bus {bus_id}: {e}")
                return None
        
        return self.connection_pool[bus_id]
    
    def retry_on_failure(self, func, *args, **kwargs):
        """Decorator for auto-retry logic"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.debug(f"Retry {attempt + 1}/{self.max_retries} for {func.__name__}: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed after {self.max_retries} retries: {e}")
                    raise
        return None
    
    def close_all_connections(self):
        """Close all pooled connections"""
        for bus_id, connection in self.connection_pool.items():
            try:
                connection.close()
                logger.debug(f"Closed I2C connection for bus {bus_id}")
            except Exception as e:
                logger.error(f"Error closing I2C connection for bus {bus_id}: {e}")
        
        self.connection_pool.clear()

# Factory functions for creating mock controllers
def create_mock_pump_controller():
    """Create mock pump controller"""
    return MockPumpController()

def create_mock_relay_controller():
    """Create mock relay controller"""
    return MockRelayController()

def create_connection_manager():
    """Create connection manager"""
    return ConnectionManager()

if __name__ == "__main__":
    # Test mock controllers
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Mock Controllers")
    print("=" * 40)
    
    # Test mock pump controller
    print("\nTesting Mock Pump Controller...")
    pump_controller = MockPumpController()
    
    # Test pump info
    status = pump_controller.get_all_pumps_status()
    print(f"Mock pumps initialized: {len(status)}")
    
    # Test dispense
    if pump_controller.start_dispense(1, 10.0):
        print("Mock dispense started")
        for i in range(3):
            still_running = pump_controller.check_pump_status(1)
            info = pump_controller.get_pump_info(1)
            print(f"  Progress: {info['current_volume']:.1f}/{info['target_volume']:.1f}ml")
            if not still_running:
                break
            time.sleep(0.5)
    
    # Test mock relay controller
    print("\nTesting Mock Relay Controller...")
    relay_controller = MockRelayController()
    
    # Test relay control
    if relay_controller.set_relay(1, True):
        print("Mock relay turned ON")
        time.sleep(0.1)
        if relay_controller.set_relay(1, False):
            print("Mock relay turned OFF")
    
    # Cleanup
    pump_controller.close()
    relay_controller.cleanup()
    print("\nMock controller tests completed")