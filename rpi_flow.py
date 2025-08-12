#!/usr/bin/env python3
"""
Flow Meter Control for Raspberry Pi
Simple replacement for Arduino Mega flow meter functionality
"""

import time
import logging

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not installed. Install with: pip install RPi.GPIO")
    exit(1)

logger = logging.getLogger(__name__)

class FlowMeterController:
    def __init__(self):
        """Initialize flow meter control"""
        
        # Flow meter pin mappings (GPIO BCM numbering)
        self.flow_pins = {
            1: 3,  # Flow meter 1 on GPIO 3
            2: 2   # Flow meter 2 on GPIO 2
        }
        
        # Flow meter data
        self.flow_meters = {}
        for meter_id in self.flow_pins:
            self.flow_meters[meter_id] = {
                'pulse_count': 0,
                'last_count': 0,
                'status': 0,  # 0=inactive, 1=active
                'target_gallons': 0,
                'current_gallons': 0,
                'pulses_per_gallon': 220,  # Default calibration
                'last_update': 0
            }
        
        # Setup GPIO
        self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for flow meters"""
        try:
            # GPIO should already be set to BCM mode by relay controller
            # But set it here too in case this runs standalone
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup flow meter pins with pull-up resistors
            for meter_id, pin in self.flow_pins.items():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
                # Add interrupt detection for falling edge
                GPIO.add_event_detect(
                    pin, 
                    GPIO.FALLING, 
                    callback=lambda channel, mid=meter_id: self.pulse_interrupt(mid),
                    bouncetime=2  # 2ms debounce
                )
                
                logger.debug(f"Flow meter {meter_id} setup on GPIO {pin}")
                
            logger.info(f"Initialized {len(self.flow_pins)} flow meters")
            
        except Exception as e:
            logger.error(f"Failed to setup flow meter GPIO: {e}")
            raise
    
    def pulse_interrupt(self, meter_id):
        """Handle pulse interrupt from flow meter"""
        if meter_id in self.flow_meters:
            self.flow_meters[meter_id]['pulse_count'] += 1
            logger.debug(f"Pulse on flow meter {meter_id}: {self.flow_meters[meter_id]['pulse_count']}")
    
    def start_flow(self, meter_id, target_gallons, pulses_per_gallon=None):
        """Start flow monitoring"""
        if meter_id not in self.flow_meters:
            logger.error(f"Invalid flow meter ID: {meter_id}")
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
        
        if pulses_per_gallon is not None:
            meter['pulses_per_gallon'] = pulses_per_gallon
        
        meter['last_update'] = time.time()
        
        logger.info(f"Started flow meter {meter_id}: target {target_gallons} gallons, "
                   f"{meter['pulses_per_gallon']} pulses/gallon")
        return True
    
    def stop_flow(self, meter_id):
        """Stop flow monitoring"""
        if meter_id not in self.flow_meters:
            return False
        
        meter = self.flow_meters[meter_id]
        meter['status'] = 0  # Inactive
        
        logger.info(f"Stopped flow meter {meter_id}")
        return True
    
    def update_flow_status(self, meter_id):
        """Update flow meter status and check for completion"""
        if meter_id not in self.flow_meters:
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
                
                logger.debug(f"Flow meter {meter_id}: {meter['current_gallons']}/{meter['target_gallons']} gallons")
                
                # Check if target reached
                if meter['target_gallons'] <= meter['current_gallons']:
                    meter['status'] = 0  # Stop
                    logger.info(f"Flow meter {meter_id} completed: {meter['current_gallons']} gallons")
                    return False  # Completed
        
        return meter['status'] == 1  # Still active
    
    def get_flow_status(self, meter_id):
        """Get flow meter status"""
        if meter_id not in self.flow_meters:
            return None
        
        return self.flow_meters[meter_id].copy()
    
    def get_all_flow_status(self):
        """Get status of all flow meters"""
        return {meter_id: meter.copy() for meter_id, meter in self.flow_meters.items()}
    
    def calibrate_flow_meter(self, meter_id, pulses_per_gallon):
        """Set calibration for flow meter"""
        if meter_id not in self.flow_meters:
            return False
        
        if pulses_per_gallon <= 0:
            return False
        
        self.flow_meters[meter_id]['pulses_per_gallon'] = pulses_per_gallon
        logger.info(f"Calibrated flow meter {meter_id}: {pulses_per_gallon} pulses/gallon")
        return True
    
    def reset_flow_meter(self, meter_id):
        """Reset flow meter counters"""
        if meter_id not in self.flow_meters:
            return False
        
        meter = self.flow_meters[meter_id]
        meter['pulse_count'] = 0
        meter['last_count'] = 0
        meter['current_gallons'] = 0
        meter['target_gallons'] = 0
        meter['status'] = 0
        
        logger.info(f"Reset flow meter {meter_id}")
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
            
            # Remove GPIO event detection
            for pin in self.flow_pins.values():
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass  # Pin might not have event detection
            
            logger.info("Flow meter cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during flow meter cleanup: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass


# Test code with mock pulses for testing
class MockFlowMeterController(FlowMeterController):
    """Mock version for testing without actual hardware"""
    
    def __init__(self):
        self.flow_pins = {1: 3, 2: 2}
        self.flow_meters = {}
        for meter_id in self.flow_pins:
            self.flow_meters[meter_id] = {
                'pulse_count': 0,
                'last_count': 0,
                'status': 0,
                'target_gallons': 0,
                'current_gallons': 0,
                'pulses_per_gallon': 220,
                'last_update': 0
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
        
        # Generate pulses every 50ms for smooth simulation
        if current_time - self.last_mock_time >= 0.05:
            self.last_mock_time = current_time
            
            # Add pulses to active flow meters
            for meter_id, meter in self.flow_meters.items():
                if meter['status'] == 1:
                    # Simulate ~10 gallons/minute = 2200 pulses/minute at 220 pulses/gallon
                    # That's ~37 pulses/second, so add ~2 pulses every 50ms
                    meter['pulse_count'] += 2
    
    def update_flow_status(self, meter_id):
        """Update with mock pulse generation"""
        self.update_mock_pulses()
        return super().update_flow_status(meter_id)


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Use mock controller for testing without hardware
    controller = MockFlowMeterController()
    
    print("Flow Meter Controller Test")
    print("1. Testing flow meter setup...")
    
    for meter_id in [1, 2]:
        status = controller.get_flow_status(meter_id)
        print(f"Flow meter {meter_id}: {status}")
    
    print("\n2. Test flow monitoring (meter 1, 5 gallons)...")
    if controller.start_flow(1, 5, 220):
        print("Flow monitoring started")
        
        # Monitor progress
        for i in range(30):  # 30 iterations
            still_running = controller.update_flow_status(1)
            status = controller.get_flow_status(1)
            print(f"  Progress: {status['current_gallons']}/{status['target_gallons']} gallons "
                  f"({status['pulse_count']} pulses)")
            
            if not still_running:
                print("  Flow completed!")
                break
            
            time.sleep(0.5)
    else:
        print("Failed to start flow monitoring")
    
    controller.cleanup()