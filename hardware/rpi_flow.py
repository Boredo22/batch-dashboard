#!/usr/bin/env python3
"""
Flow Meter Control for Raspberry Pi
Updated to use centralized configuration from config.py
Works independently without hardware manager - compatible with simple_gui.py pattern
"""

import time
import logging
from config import (
    FLOW_METER_GPIO_PINS,
    FLOW_METER_NAMES,
    FLOW_METER_CALIBRATION,
    FLOW_METER_INTERRUPT_EDGE,
    MOCK_FLOW_PULSE_INTERVAL,
    MOCK_PULSES_PER_INTERVAL,
    get_flow_meter_name,
    get_available_flow_meters,
    validate_flow_meter_id
)

import platform

try:
    import lgpio
except ImportError:
    if platform.system() == 'Windows':
        print("Running on Windows - using mock lgpio")
        from .mock_hardware_libs import lgpio
    else:
        print("lgpio not installed. Install with: pip install lgpio")
        exit(1)

logger = logging.getLogger(__name__)

class FlowMeterController:
    def __init__(self):
        """Initialize flow meter control"""
        # Use flow meter mappings from config
        self.flow_pins_map = FLOW_METER_GPIO_PINS.copy()
        
        # Will store flow pins with callback info
        self.flow_pins = {}
        
        # Flow meter data
        self.flow_meters = {}
        for meter_id in self.flow_pins_map.keys():
            self.flow_meters[meter_id] = {
                'pulse_count': 0,
                'last_count': 0,
                'status': 0,  # 0=inactive, 1=active
                'target_gallons': 0,
                'current_gallons': 0,
                'pulses_per_gallon': FLOW_METER_CALIBRATION.get(meter_id, 220),
                'last_update': 0
            }
        
        # GPIO handle
        self.h = None
        
        # Setup GPIO
        self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for flow meters"""
        try:
            # Create an lgpio handle
            self.h = lgpio.gpiochip_open(0)
            
            # Setup flow meter pins with pull-up resistors
            for meter_id, pin in self.flow_pins_map.items():
                # Configure as input with pull-up
                lgpio.gpio_claim_input(self.h, pin, lgpio.SET_PULL_UP)
                
                # Determine interrupt edge
                edge = lgpio.FALLING_EDGE if FLOW_METER_INTERRUPT_EDGE == "FALLING" else lgpio.RISING_EDGE
                
                # Add callback for interrupt
                callback_id = lgpio.callback(self.h, pin, edge,
                                           lambda chip, gpio, level, tick, mid=meter_id: self.pulse_interrupt(mid))
                
                # Store the callback info
                self.flow_pins[meter_id] = {
                    'pin': pin,
                    'cb_id': callback_id,
                    'name': get_flow_meter_name(meter_id)
                }
                
                logger.debug(f"Flow meter {meter_id} ({get_flow_meter_name(meter_id)}) setup on GPIO {pin}")
                
            logger.info(f"Initialized {len(self.flow_pins)} flow meters")
            
        except Exception as e:
            logger.error(f"Failed to setup flow meter GPIO: {e}")
            raise
    
    def pulse_interrupt(self, meter_id):
        """Handle pulse interrupt from flow meter"""
        if meter_id in self.flow_meters:
            self.flow_meters[meter_id]['pulse_count'] += 1
            logger.debug(f"Pulse on {get_flow_meter_name(meter_id)}: {self.flow_meters[meter_id]['pulse_count']}")
    
    def start_flow(self, meter_id, target_gallons, pulses_per_gallon=None):
        """Start flow monitoring"""
        if not validate_flow_meter_id(meter_id):
            available = get_available_flow_meters()
            logger.error(f"Invalid flow meter ID: {meter_id} (available: {available})")
            return False
        
        if target_gallons <= 0:
            logger.error(f"Invalid target gallons: {target_gallons}")
            return False
        
        meter = self.flow_meters[meter_id]
        
        # Reset meter
        meter['pulse_count'] = 0
        meter['last_count'] = 0
        meter['current_gallons'] = 0
        meter['target_gallons'] = target_gallons
        meter['status'] = 1  # Active
        
        # Update calibration if provided
        if pulses_per_gallon is not None:
            meter['pulses_per_gallon'] = pulses_per_gallon
        
        meter['last_update'] = time.time()
        
        meter_name = get_flow_meter_name(meter_id)
        logger.info(f"Started {meter_name}: target {target_gallons} gallons, "
                   f"{meter['pulses_per_gallon']} pulses/gallon")
        return True
    
    def stop_flow(self, meter_id):
        """Stop flow monitoring"""
        if not validate_flow_meter_id(meter_id):
            return False
        
        meter = self.flow_meters[meter_id]
        meter['status'] = 0  # Inactive
        
        meter_name = get_flow_meter_name(meter_id)
        logger.info(f"Stopped {meter_name}")
        return True
    
    def update_flow_status(self, meter_id):
        """Update flow meter status and check for completion"""
        if not validate_flow_meter_id(meter_id):
            return False
        
        meter = self.flow_meters[meter_id]
        
        # Skip if meter is not active
        if meter['status'] == 0:
            return False
        
        # Check if pulse count has changed
        if meter['pulse_count'] != meter['last_count']:
            new_gallons = meter['pulse_count'] // meter['pulses_per_gallon']
            meter['last_count'] = meter['pulse_count']
            
            # Update if gallons changed
            if new_gallons != meter['current_gallons']:
                meter['current_gallons'] = new_gallons
                meter['last_update'] = time.time()
                
                meter_name = get_flow_meter_name(meter_id)
                logger.debug(f"{meter_name}: {meter['current_gallons']}/{meter['target_gallons']} gallons")
                
                # Check if target reached
                if meter['target_gallons'] <= meter['current_gallons']:
                    meter['status'] = 0  # Stop
                    logger.info(f"{meter_name} completed: {meter['current_gallons']} gallons")
                    return False  # Completed
        
        return meter['status'] == 1  # Still active
    
    def get_flow_status(self, meter_id):
        """Get flow meter status"""
        if not validate_flow_meter_id(meter_id):
            return None
        
        status = self.flow_meters[meter_id].copy()
        status['name'] = get_flow_meter_name(meter_id)
        return status
    
    def get_all_flow_status(self):
        """Get status of all flow meters"""
        status = {}
        for meter_id in self.flow_meters.keys():
            status[meter_id] = self.get_flow_status(meter_id)
        return status
    
    def calibrate_flow_meter(self, meter_id, pulses_per_gallon):
        """Set calibration for flow meter"""
        if not validate_flow_meter_id(meter_id):
            return False
        
        if pulses_per_gallon <= 0:
            return False
        
        self.flow_meters[meter_id]['pulses_per_gallon'] = pulses_per_gallon
        meter_name = get_flow_meter_name(meter_id)
        logger.info(f"Calibrated {meter_name}: {pulses_per_gallon} pulses/gallon")
        return True
    
    def reset_flow_meter(self, meter_id):
        """Reset flow meter counters"""
        if not validate_flow_meter_id(meter_id):
            return False
        
        meter = self.flow_meters[meter_id]
        meter['pulse_count'] = 0
        meter['last_count'] = 0
        meter['current_gallons'] = 0
        meter['target_gallons'] = 0
        meter['status'] = 0
        
        meter_name = get_flow_meter_name(meter_id)
        logger.info(f"Reset {meter_name}")
        return True
    
    def emergency_stop(self):
        """Stop all flow meters"""
        for meter_id in self.flow_meters:
            self.stop_flow(meter_id)
        logger.warning("Emergency stop - all flow meters stopped")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            self.emergency_stop()
            
            # Cancel callbacks and free GPIO pins
            for meter_info in self.flow_pins.values():
                try:
                    # Cancel the callback
                    lgpio.callback_cancel(meter_info['cb_id'])
                    # Free the GPIO pin
                    lgpio.gpio_free(self.h, meter_info['pin'])
                except:
                    pass  # Callback or pin might not exist
            
            # Close the GPIO chip
            if self.h is not None:
                lgpio.gpiochip_close(self.h)
                self.h = None
            
            logger.info("Flow meter cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during flow meter cleanup: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass


# Mock version for testing without actual hardware
class MockFlowMeterController(FlowMeterController):
    """Mock version for testing without actual hardware"""
    
    def __init__(self):
        # Use flow meter mappings from config
        self.flow_pins_map = FLOW_METER_GPIO_PINS.copy()
        self.flow_pins = {}
        self.flow_meters = {}
        
        for meter_id in self.flow_pins_map.keys():
            self.flow_meters[meter_id] = {
                'pulse_count': 0,
                'last_count': 0,
                'status': 0,
                'target_gallons': 0,
                'current_gallons': 0,
                'pulses_per_gallon': FLOW_METER_CALIBRATION.get(meter_id, 220),
                'last_update': 0
            }
            # Mock the flow_pins structure used by the real controller
            self.flow_pins[meter_id] = {
                'pin': self.flow_pins_map[meter_id],
                'cb_id': None,
                'name': get_flow_meter_name(meter_id)
            }
        
        self.last_mock_time = time.time()
        logger.info("Mock flow meter controller initialized")
    
    def setup_gpio(self):
        """Mock GPIO setup"""
        pass
    
    def cleanup(self):
        """Mock cleanup"""
        pass
    
    def update_mock_pulses(self):
        """Generate mock pulses for testing"""
        current_time = time.time()
        
        # Generate pulses at configured interval
        if current_time - self.last_mock_time >= MOCK_FLOW_PULSE_INTERVAL:
            self.last_mock_time = current_time
            
            # Add pulses to active flow meters
            for meter_id, meter in self.flow_meters.items():
                if meter['status'] == 1:
                    meter['pulse_count'] += MOCK_PULSES_PER_INTERVAL
    
    def update_flow_status(self, meter_id):
        """Update with mock pulse generation"""
        self.update_mock_pulses()
        return super().update_flow_status(meter_id)


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Use mock controller for testing without hardware
    controller = MockFlowMeterController()
    
    print("Flow Meter Controller Test (Using config.py)")
    print("=" * 50)
    print("Available flow meters:")
    
    for meter_id in get_available_flow_meters():
        status = controller.get_flow_status(meter_id)
        if status:
            gpio_pin = FLOW_METER_GPIO_PINS[meter_id]
            print(f"  {meter_id}. {status['name']:20s} (GPIO {gpio_pin}): {status['pulses_per_gallon']} PPG")
    
    print("\nTesting flow monitoring...")
    test_meter = get_available_flow_meters()[0] if get_available_flow_meters() else None
    
    if test_meter:
        meter_name = get_flow_meter_name(test_meter)
        print(f"Starting {meter_name} for 5 gallons...")
        
        if controller.start_flow(test_meter, 5):
            print("Flow monitoring started")
            
            # Monitor progress
            for i in range(30):  # 30 iterations
                still_running = controller.update_flow_status(test_meter)
                status = controller.get_flow_status(test_meter)
                print(f"  Progress: {status['current_gallons']}/{status['target_gallons']} gallons "
                      f"({status['pulse_count']} pulses)")
                
                if not still_running:
                    print("  Flow completed!")
                    break
                
                time.sleep(0.5)
        else:
            print("Failed to start flow monitoring")
    else:
        print("No flow meters available for testing")
    
    controller.cleanup()