#!/usr/bin/env python3
"""
GPIO Relay Control for Raspberry Pi
Simple replacement for Arduino Mega relay functionality
"""

import logging

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not installed. Install with: pip install RPi.GPIO")
    exit(1)

logger = logging.getLogger(__name__)

class RelayController:
    def __init__(self):
        """Initialize GPIO for relay control"""
        
        # Relay pin mappings (GPIO BCM numbering) - adjust these as needed
        self.relay_pins = {
            1: 4,   2: 17,  3: 27,  4: 22,   # Relays 1-4
            5: 5,   6: 6,   7: 13,  8: 19,   # Relays 5-8
            9: 26,  10: 14, 11: 15, 12: 18,  # Relays 9-12
            13: 23, 14: 24, 15: 25, 16: 8    # Relays 13-16
        }
        
        # Track relay states
        self.relay_states = {i: False for i in range(1, 17)}
        
        # Setup GPIO
        self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for relays"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup each relay pin
            for relay_id, pin in self.relay_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                # Start with relay OFF (active LOW, so HIGH = OFF)
                GPIO.output(pin, GPIO.HIGH)
                self.relay_states[relay_id] = False
                
            logger.info(f"Initialized {len(self.relay_pins)} relay pins")
            
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {e}")
            raise
    
    def set_relay(self, relay_id, state):
        """Set individual relay state"""
        if relay_id not in self.relay_pins:
            logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        try:
            pin = self.relay_pins[relay_id]
            
            # Relays are active LOW (LOW = ON, HIGH = OFF)
            gpio_state = GPIO.LOW if state else GPIO.HIGH
            GPIO.output(pin, gpio_state)
            
            # Update state tracking
            self.relay_states[relay_id] = state
            
            state_str = "ON" if state else "OFF"
            logger.debug(f"Relay {relay_id} set to {state_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting relay {relay_id}: {e}")
            return False
    
    def set_all_relays(self, state):
        """Set all relays to the same state"""
        success_count = 0
        
        for relay_id in self.relay_pins:
            if self.set_relay(relay_id, state):
                success_count += 1
        
        state_str = "ON" if state else "OFF"
        logger.info(f"Set {success_count}/{len(self.relay_pins)} relays to {state_str}")
        
        return success_count == len(self.relay_pins)
    
    def get_relay_state(self, relay_id):
        """Get current relay state"""
        return self.relay_states.get(relay_id, None)
    
    def get_all_relay_states(self):
        """Get states of all relays"""
        return self.relay_states.copy()
    
    def toggle_relay(self, relay_id):
        """Toggle relay state"""
        current_state = self.get_relay_state(relay_id)
        if current_state is not None:
            return self.set_relay(relay_id, not current_state)
        return False
    
    def emergency_stop(self):
        """Emergency stop - turn off all relays"""
        logger.warning("Emergency stop - turning off all relays")
        return self.set_all_relays(False)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            # Turn off all relays before cleanup
            self.emergency_stop()
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass


# Relay name mappings for easier identification
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
    11: "Room 2",
    12: "Room 3",
    13: "Tank Drain",
    14: "Spare 1",
    15: "Spare 2",
    16: "Spare 3"
}

def get_relay_name(relay_id):
    """Get descriptive name for relay"""
    return RELAY_NAMES.get(relay_id, f"Relay {relay_id}")


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    controller = RelayController()
    
    print("Relay Controller Test")
    print("Current relay states:")
    
    for relay_id in range(1, 17):
        state = controller.get_relay_state(relay_id)
        name = get_relay_name(relay_id)
        print(f"  {relay_id:2d}. {name}: {'ON' if state else 'OFF'}")
    
    print("\nTesting relay 1...")
    print("Turning ON...")
    controller.set_relay(1, True)
    
    import time
    time.sleep(2)
    
    print("Turning OFF...")
    controller.set_relay(1, False)
    
    print("\nTesting all relays OFF...")
    controller.set_all_relays(False)
    
    print("Test completed")
    controller.cleanup()