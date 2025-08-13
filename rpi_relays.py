#!/usr/bin/env python3
"""
GPIO Relay Control for Raspberry Pi
Simple replacement for Arduino Mega relay functionality
"""

import logging

try:
    import lgpio
except ImportError:
    print("lgpio not installed. Install with: pip install lgpio")
    exit(1)

logger = logging.getLogger(__name__)

class RelayController:
    def __init__(self):
        """Initialize GPIO for relay control"""
        
        # Relay pin mappings (GPIO BCM numbering) - adjust these as needed
        self.relay_pins = {
            1: 23,   2: 21,  3: 18,  4: 26,   # Relays 1-4
            5: 15,   6: 19,  7: 14,  8: 13,   # Relays 5-8
            9: 22,  10: 6,  11: 27, 12: 0,   # Relays 9-12
            13: 4, 14: 16, 15: 5, 16: 14    # Relays 13-16
        }
        
        # Track relay states
        self.relay_states = {i: False for i in range(1, 17)}
        
        # Setup GPIO
        self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for relays"""
        try:
            # Create an lgpio handle
            self.h = lgpio.gpiochip_open(0)
            
            # Setup each relay pin
            for relay_id, pin in self.relay_pins.items():
                lgpio.gpio_claim_output(self.h, pin)
                # Start with relay OFF (active LOW, so HIGH = OFF)
                lgpio.gpio_write(self.h, pin, 1)  # 1 = HIGH = OFF
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
            gpio_state = 0 if state else 1  # 0 = LOW = ON, 1 = HIGH = OFF
            lgpio.gpio_write(self.h, pin, gpio_state)
            
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
            
            # Release GPIO pins
            for pin in self.relay_pins.values():
                try:
                    lgpio.gpio_free(self.h, pin)
                except:
                    pass
            
            # Close the GPIO chip
            lgpio.gpiochip_close(self.h)
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