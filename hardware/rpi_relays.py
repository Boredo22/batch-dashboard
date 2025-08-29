#!/usr/bin/env python3
"""
GPIO Relay Control for Raspberry Pi with ULN2803A Darlington Array
Uses centralized configuration from config.py
Works independently without hardware manager - compatible with simple_gui.py pattern
"""

import logging
from config import (
    RELAY_GPIO_PINS,
    RELAY_NAMES,
    RELAY_ACTIVE_HIGH,
    get_relay_name,
    get_available_relays,
    validate_relay_id
)

try:
    import lgpio
except ImportError:
    print("lgpio not installed. Install with: pip install lgpio")
    exit(1)

logger = logging.getLogger(__name__)

class RelayController:
    def __init__(self):
        """Initialize GPIO for relay control with ULN2803A"""
        
        # Use relay mappings from config
        self.relay_pins = RELAY_GPIO_PINS.copy()
        
        # Track relay states (True = ON, False = OFF)
        self.relay_states = {relay_id: False for relay_id in self.relay_pins.keys()}

        # GPIO handle
        self.h = None

        # Setup GPIO
        self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for relays with ULN2803A"""
        try:
            # Create an lgpio handle
            self.h = lgpio.gpiochip_open(0)
            
            # Setup each relay pin
            for relay_id, pin in self.relay_pins.items():
                lgpio.gpio_claim_output(self.h, pin)
                
                # Start with all relays OFF
                initial_state = 0 if not RELAY_ACTIVE_HIGH else 0  # Always start OFF
                lgpio.gpio_write(self.h, pin, initial_state)
                self.relay_states[relay_id] = False
                
                logger.debug(f"Relay {relay_id} setup on GPIO {pin} ({get_relay_name(relay_id)})")
                
            logger.info(f"Initialized {len(self.relay_pins)} relay pins with ULN2803A")
            
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {e}")
            self.h = None
            # Don't re-raise the exception to allow graceful degradation
    
    def set_relay(self, relay_id, state):
        """Set individual relay state
        
        Args:
            relay_id (int): Relay number
            state (bool): True = ON, False = OFF
        """
        if not validate_relay_id(relay_id):
            available = get_available_relays()
            logger.error(f"Invalid relay ID: {relay_id} (available: {available})")
            return False
        
        if self.h is None:
            logger.error(f"GPIO not initialized - cannot set relay {relay_id}")
            return False
        
        try:
            pin = self.relay_pins[relay_id]
            
            # Apply relay logic based on configuration
            if RELAY_ACTIVE_HIGH:
                gpio_state = 1 if state else 0  # HIGH = ON, LOW = OFF
            else:
                gpio_state = 0 if state else 1  # LOW = ON, HIGH = OFF
            
            lgpio.gpio_write(self.h, pin, gpio_state)
            
            # Update state tracking
            self.relay_states[relay_id] = state
            
            state_str = "ON" if state else "OFF"
            relay_name = get_relay_name(relay_id)
            logger.debug(f"Relay {relay_id} ({relay_name}) set to {state_str}")
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
        if not validate_relay_id(relay_id):
            return False
            
        current_state = self.get_relay_state(relay_id)
        if current_state is not None:
            return self.set_relay(relay_id, not current_state)
        return False
    
    def emergency_stop(self):
        """Emergency stop - turn off all relays"""
        logger.warning("Emergency stop - turning off all relays")
        if self.h is None:
            logger.error("GPIO not initialized - cannot perform emergency stop")
            return False
        return self.set_all_relays(False)
    
    def get_available_relays(self):
        """Get list of available relay IDs"""
        return get_available_relays()
    
    def get_relay_info(self, relay_id):
        """Get relay information"""
        if not validate_relay_id(relay_id):
            return None
            
        return {
            "id": relay_id,
            "name": get_relay_name(relay_id),
            "gpio_pin": self.relay_pins[relay_id],
            "state": self.relay_states[relay_id],
            "active_high": RELAY_ACTIVE_HIGH
        }
    
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
            if self.h is not None:
                lgpio.gpiochip_close(self.h)
                self.h = None
            
            logger.info("GPIO cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    controller = RelayController()
    
    print("Relay Controller Test (Using config.py)")
    print("=" * 45)
    print("Available relays and their current states:")
    
    for relay_id in controller.get_available_relays():
        info = controller.get_relay_info(relay_id)
        if info:
            print(f"  {info['id']:2d}. {info['name']:25s} (GPIO {info['gpio_pin']:2d}): {'ON' if info['state'] else 'OFF'}")
    
    print(f"\nTesting first available relay...")
    available_relays = controller.get_available_relays()
    if available_relays:
        test_relay = available_relays[0]
        print(f"🔊 Listen for relay {test_relay} clicking sounds...")
        
        import time
        
        print("Turning ON...")
        controller.set_relay(test_relay, True)
        time.sleep(2)
        
        print("Turning OFF...")
        controller.set_relay(test_relay, False)
        
        print("\nTesting all relays OFF...")
        controller.set_all_relays(False)
        
        print(f"\nRelay Logic: {'Active HIGH' if RELAY_ACTIVE_HIGH else 'Active LOW'}")
        print("Test completed")
    else:
        print("No relays available for testing")
    
    controller.cleanup()