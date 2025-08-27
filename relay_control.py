#!/usr/bin/env python3
"""
Simple Relay Control Utility
Control individual relays directly without mapping process
Updated with latest relay mappings from relay_mapping.json (2025-08-27)
"""

import lgpio
import time
import sys

# Updated relay mappings from latest mapping
RELAY_GPIO_PINS = {
    1: 22,   # Relay 1 on GPIO 22
    2: 26,   # Relay 2 on GPIO 26
    3: 20,   # Relay 3 on GPIO 20  
    4: 21,   # Relay 4 on GPIO 21
    5: 16,   # Relay 5 on GPIO 16
    6: 19,   # Relay 6 on GPIO 19
    7: 12,   # Relay 7 on GPIO 12
    8: 13,   # Relay 8 on GPIO 13
    9: 10,   # Relay 9 on GPIO 10
    10: 9,   # Relay 10 on GPIO 9
    12: 0,   # Relay 12 on GPIO 0
    13: 5,   # Relay 13 on GPIO 5
}

# Relay names (update these as needed)
RELAY_NAMES = {
    2: "Tank 2 Fill",
    3: "Tank 3 Fill", 
    4: "Tank 1 Nute Dispense",
    5: "Relay 5",
    6: "Tank 2 Nute Dispense",
    7: "Tank 1 Dispense Send",
    8: "Tank 2 Dispense Send",
    9: "Tank 3 Dispense Send",
    10: "Room 1",
    12: "Relay 12",
    13: "Relay 13",
}

# Relay logic settings (for ULN2803A)
RELAY_ACTIVE_HIGH = True  # GPIO HIGH = Relay ON

def get_relay_name(relay_id):
    """Get descriptive name for relay"""
    return RELAY_NAMES.get(relay_id, f"Relay {relay_id}")

def get_available_relays():
    """Get list of available relay IDs"""
    return list(RELAY_GPIO_PINS.keys())

def validate_relay_id(relay_id):
    """Check if relay ID is valid"""
    return relay_id in RELAY_GPIO_PINS

class SimpleRelayController:
    def __init__(self):
        """Initialize simple relay controller"""
        self.h = None
        self.relay_states = {}
        self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for relays"""
        try:
            self.h = lgpio.gpiochip_open(0)
            
            # Setup each relay pin
            for relay_id, pin in RELAY_GPIO_PINS.items():
                lgpio.gpio_claim_output(self.h, pin)
                
                # Start with all relays OFF
                initial_state = 0 if not RELAY_ACTIVE_HIGH else 0
                lgpio.gpio_write(self.h, pin, initial_state)
                self.relay_states[relay_id] = False
            
            print(f"Initialized {len(RELAY_GPIO_PINS)} relays")
            
        except Exception as e:
            print(f"Failed to setup GPIO: {e}")
            raise
    
    def set_relay(self, relay_id, state):
        """Set individual relay state"""
        if not validate_relay_id(relay_id):
            print(f"Invalid relay ID: {relay_id}")
            return False
        
        try:
            pin = RELAY_GPIO_PINS[relay_id]
            
            # Apply relay logic
            if RELAY_ACTIVE_HIGH:
                gpio_state = 1 if state else 0
            else:
                gpio_state = 0 if state else 1
            
            lgpio.gpio_write(self.h, pin, gpio_state)
            self.relay_states[relay_id] = state
            
            state_str = "ON" if state else "OFF"
            relay_name = get_relay_name(relay_id)
            print(f"Relay {relay_id} ({relay_name}) set to {state_str}")
            return True
            
        except Exception as e:
            print(f"Error setting relay {relay_id}: {e}")
            return False
    
    def get_relay_state(self, relay_id):
        """Get current relay state"""
        return self.relay_states.get(relay_id, None)
    
    def show_status(self):
        """Show current status of all relays"""
        print("\nCurrent Relay Status:")
        print("=" * 60)
        for relay_id in sorted(RELAY_GPIO_PINS.keys()):
            state = self.get_relay_state(relay_id)
            status = "ON" if state else "OFF"
            gpio_pin = RELAY_GPIO_PINS[relay_id]
            relay_name = get_relay_name(relay_id)
            print(f"  {relay_id:2d}. {relay_name:25s} (GPIO {gpio_pin:2d}): {status}")
    
    def all_relays_off(self):
        """Turn all relays OFF"""
        print("Turning all relays OFF...")
        success_count = 0
        for relay_id in RELAY_GPIO_PINS.keys():
            if self.set_relay(relay_id, False):
                success_count += 1
        print(f"Turned OFF {success_count}/{len(RELAY_GPIO_PINS)} relays")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            # Turn off all relays
            for relay_id in RELAY_GPIO_PINS.keys():
                try:
                    self.set_relay(relay_id, False)
                except:
                    pass
            
            # Release GPIO pins
            for pin in RELAY_GPIO_PINS.values():
                try:
                    lgpio.gpio_free(self.h, pin)
                except:
                    pass
            
            # Close GPIO chip
            if self.h is not None:
                lgpio.gpiochip_close(self.h)
                self.h = None
            
            print("GPIO cleanup completed")
            
        except Exception as e:
            print(f"Cleanup error: {e}")

def show_menu():
    """Show main menu"""
    print("\nRelay Control Utility")
    print("=" * 30)
    print("Commands:")
    print("  <relay_id> on   - Turn relay ON (e.g., '2 on')")
    print("  <relay_id> off  - Turn relay OFF (e.g., '2 off')")
    print("  list            - Show available relays")
    print("  status          - Show current relay states")
    print("  all off         - Turn all relays OFF")
    print("  help            - Show this menu")
    print("  quit            - Exit program")
    
def show_available_relays():
    """Show available relays"""
    print("\nAvailable Relays:")
    print("=" * 50)
    for relay_id in sorted(RELAY_GPIO_PINS.keys()):
        gpio_pin = RELAY_GPIO_PINS[relay_id]
        relay_name = get_relay_name(relay_id)
        print(f"  {relay_id:2d}. {relay_name:25s} (GPIO {gpio_pin:2d})")

def parse_command(command_str, controller):
    """Parse and execute command"""
    parts = command_str.strip().lower().split()
    
    if not parts:
        return True
    
    cmd = parts[0]
    
    # Quit commands
    if cmd in ['quit', 'exit', 'q']:
        return False
    
    # Help command
    elif cmd == 'help':
        show_menu()
    
    # List relays
    elif cmd == 'list':
        show_available_relays()
    
    # Show status
    elif cmd == 'status':
        controller.show_status()
    
    # All relays off
    elif cmd == 'all' and len(parts) > 1 and parts[1] == 'off':
        controller.all_relays_off()
    
    # Individual relay control
    elif cmd.isdigit():
        relay_id = int(cmd)
        
        if not validate_relay_id(relay_id):
            print(f"Invalid relay ID: {relay_id}")
            print("Valid relay IDs:", sorted(RELAY_GPIO_PINS.keys()))
            return True
        
        if len(parts) < 2:
            print(f"Missing command for relay {relay_id}. Use 'on' or 'off'")
            return True
        
        action = parts[1]
        if action == 'on':
            controller.set_relay(relay_id, True)
        elif action == 'off':
            controller.set_relay(relay_id, False)
        else:
            print(f"Invalid action '{action}'. Use 'on' or 'off'")
    
    # Unknown command
    else:
        print(f"Unknown command: {command_str}")
        print("Type 'help' for available commands")
    
    return True

def main():
    """Main function"""
    print("Simple Relay Control Utility")
    print("Using updated relay mappings")
    print("=" * 45)
    
    try:
        # Initialize controller
        controller = SimpleRelayController()
        
        # Show available relays
        show_available_relays()
        
        # Show menu
        show_menu()
        
        # Main command loop
        while True:
            try:
                command = input("\nrelay> ").strip()
                
                if not command:
                    continue
                
                # Parse and execute command
                if not parse_command(command, controller):
                    break
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except EOFError:
                print("\nEOF received")
                break
        
        print("Shutting down...")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Cleanup
        try:
            controller.cleanup()
        except:
            pass
    
    print("Goodbye!")

if __name__ == "__main__":
    main()