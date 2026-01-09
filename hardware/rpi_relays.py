#!/usr/bin/env python3
"""
GPIO Relay Control for Raspberry Pi with ULN2803A Darlington Array
Uses centralized configuration from config.py
Works independently without hardware manager - compatible with simple_gui.py pattern
"""

import logging
import sys
from pathlib import Path
from config import (
    RELAY_GPIO_PINS,
    RELAY_NAMES,
    RELAY_ACTIVE_HIGH,
    get_relay_name,
    get_available_relays,
    validate_relay_id
)

import platform

# Add project root to path for state_manager import
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from state_manager import init_state_from_hardware, state
except ImportError:
    # Fallback if state_manager not available (for standalone testing)
    def init_state_from_hardware(*args, **kwargs):
        pass
    state = None

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

class RelayController:
    def __init__(self):
        """Initialize GPIO for relay control with ULN2803A"""
        
        # Use relay mappings from config
        self.relay_pins = RELAY_GPIO_PINS.copy()
        
        # Track relay states (True = ON, False = OFF)
        self.relay_states = {relay_id: False for relay_id in self.relay_pins.keys()}

        # GPIO handle
        self.h = None
        self._gpio_initialized = False
        self._initialization_attempts = 0
        self._max_init_attempts = 3

        # Don't setup GPIO immediately - use lazy initialization
        logger.debug("RelayController created with lazy GPIO initialization")
    
    def _cleanup_gpio_handle(self):
        """Clean up any existing GPIO handle before retry"""
        if self.h is not None:
            try:
                # Try to free all pins first
                for pin in self.relay_pins.values():
                    try:
                        lgpio.gpio_free(self.h, pin)
                    except Exception:
                        pass
                # Close the chip handle
                lgpio.gpiochip_close(self.h)
            except Exception as e:
                logger.debug(f"Error during GPIO handle cleanup: {e}")
            finally:
                self.h = None

    def _ensure_gpio_initialized(self):
        """Ensure GPIO is initialized with retry logic"""
        if self._gpio_initialized and self.h is not None:
            return True

        if self._initialization_attempts >= self._max_init_attempts:
            logger.error(f"GPIO initialization failed after {self._max_init_attempts} attempts")
            return False

        return self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for relays with ULN2803A

        IMPORTANT: This method reads the current GPIO pin state before claiming
        as output, allowing the system to preserve relay states across restarts.
        This is essential for maintaining system operations during development
        and redeployments without disrupting active processes.
        """
        self._initialization_attempts += 1

        # Clean up any existing handle before attempting initialization
        self._cleanup_gpio_handle()

        try:
            # Create an lgpio handle
            self.h = lgpio.gpiochip_open(0)

            # Setup each relay pin and read current state
            for relay_id, pin in self.relay_pins.items():
                # First, claim the pin as input to read current state
                lgpio.gpio_claim_input(self.h, pin)

                # Read the current GPIO pin state
                current_gpio_state = lgpio.gpio_read(self.h, pin)

                # Convert GPIO state to relay state based on active high/low
                if RELAY_ACTIVE_HIGH:
                    current_relay_state = (current_gpio_state == 1)  # HIGH = ON
                else:
                    current_relay_state = (current_gpio_state == 0)  # LOW = ON

                # Free the pin and reclaim as output
                lgpio.gpio_free(self.h, pin)
                lgpio.gpio_claim_output(self.h, pin)

                # Set the pin back to its current state (preserve existing state)
                lgpio.gpio_write(self.h, pin, current_gpio_state)

                # Track the relay state
                self.relay_states[relay_id] = current_relay_state

                state_str = "ON" if current_relay_state else "OFF"
                relay_name = get_relay_name(relay_id)
                logger.info(f"Relay {relay_id} ({relay_name}) initialized to {state_str} (GPIO {pin} = {current_gpio_state})")

            logger.info(f"Initialized {len(self.relay_pins)} relay pins with ULN2803A - preserved existing states")

            # Sync relay states to persistent storage
            init_state_from_hardware(self.relay_states)

            self._gpio_initialized = True
            self._initialization_attempts = 0  # Reset counter on success
            return True

        except Exception as e:
            logger.error(f"Failed to setup GPIO (attempt {self._initialization_attempts}): {e}")
            # Clean up on failure to release any partially acquired resources
            self._cleanup_gpio_handle()
            self._gpio_initialized = False

            # Add small delay before potential retry
            import time
            time.sleep(0.2)
            return False
    
    def set_relay(self, relay_id, is_on):
        """Set individual relay state

        Args:
            relay_id (int): Relay number
            is_on (bool): True = ON, False = OFF
        """
        if not validate_relay_id(relay_id):
            available = get_available_relays()
            logger.error(f"Invalid relay ID: {relay_id} (available: {available})")
            return False

        # Ensure GPIO is initialized before use
        if not self._ensure_gpio_initialized():
            logger.error(f"GPIO not initialized - cannot set relay {relay_id}")
            return False

        try:
            pin = self.relay_pins[relay_id]

            # Apply relay logic based on configuration
            if RELAY_ACTIVE_HIGH:
                gpio_state = 1 if is_on else 0  # HIGH = ON, LOW = OFF
            else:
                gpio_state = 0 if is_on else 1  # LOW = ON, HIGH = OFF

            lgpio.gpio_write(self.h, pin, gpio_state)

            # Update state tracking
            self.relay_states[relay_id] = is_on

            # Persist state to database (async to not block relay operation)
            if state is not None:
                import threading
                threading.Thread(target=state.set_relay, args=(relay_id, is_on), daemon=True).start()

            state_str = "ON" if is_on else "OFF"
            relay_name = get_relay_name(relay_id)
            logger.info(f"Relay {relay_id} ({relay_name}) set to {state_str}")
            return True

        except Exception as e:
            logger.error(f"Error setting relay {relay_id}: {e}")
            # If GPIO operation fails, mark as uninitialized to force retry
            self._gpio_initialized = False
            logger.warning(f"GPIO marked uninitialized, will retry (attempts: {self._initialization_attempts}/{self._max_init_attempts})")
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
        
        # Ensure GPIO is initialized before emergency stop
        if not self._ensure_gpio_initialized():
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