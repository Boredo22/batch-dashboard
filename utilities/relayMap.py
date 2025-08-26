#!/usr/bin/env python3
"""
Relay GPIO Mapper
Test each GPIO one by one and map which physical relay it controls
"""

import lgpio
import time
import json
from datetime import datetime

class RelayMapper:
    def __init__(self):
        """Initialize GPIO mapper"""
        # Your GPIO pins
        self.gpio_pins = [0, 5, 6, 9, 10, 11, 12, 13, 16, 19, 20, 21, 22, 26]
        self.gpio_pins.sort()  # Sort for easier testing
        
        # Store the mapping
        self.gpio_to_relay = {}
        self.relay_to_gpio = {}
        
        # GPIO handle
        self.h = None
        
    def setup_gpio(self):
        """Setup all GPIO pins"""
        try:
            self.h = lgpio.gpiochip_open(0)
            
            for pin in self.gpio_pins:
                lgpio.gpio_claim_output(self.h, pin)
                lgpio.gpio_write(self.h, pin, 0)  # Start with all OFF
                
            print(f"Initialized {len(self.gpio_pins)} GPIO pins")
            return True
            
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            return False
    
    def test_gpio(self, gpio_pin):
        """Test a single GPIO pin"""
        try:
            print(f"\nTesting GPIO {gpio_pin}")
            print("=" * 25)
            
            # Turn ON the GPIO
            print("Turning GPIO ON...")
            lgpio.gpio_write(self.h, gpio_pin, 1)
            
            print("Listen and watch for relay activation!")
            print("(LED should light up, relay should click)")
            
            # Wait for user to observe
            time.sleep(3)
            
            # Keep it on while user identifies
            input("Press Enter when you've identified which relay activated...")
            
            # Turn OFF
            print("Turning GPIO OFF...")
            lgpio.gpio_write(self.h, gpio_pin, 0)
            
            return True
            
        except Exception as e:
            print(f"Error testing GPIO {gpio_pin}: {e}")
            return False
    
    def get_relay_number(self, gpio_pin):
        """Get relay number from user"""
        while True:
            try:
                print(f"\nWhich relay number activated for GPIO {gpio_pin}?")
                print("Enter relay number (1-16) or:")
                print("'skip' - if no relay activated")
                print("'retry' - test this GPIO again")
                print("'quit' - exit mapper")
                
                response = input("Relay #: ").strip().lower()
                
                if response == 'skip':
                    return 'skip'
                elif response == 'retry':
                    return 'retry'
                elif response == 'quit':
                    return 'quit'
                else:
                    relay_num = int(response)
                    if 1 <= relay_num <= 16:
                        # Check if this relay is already mapped
                        if relay_num in self.relay_to_gpio:
                            existing_gpio = self.relay_to_gpio[relay_num]
                            print(f"WARNING: Relay {relay_num} is already mapped to GPIO {existing_gpio}")
                            overwrite = input("Overwrite? (y/n): ").lower()
                            if overwrite != 'y':
                                continue
                        return relay_num
                    else:
                        print("Please enter a number between 1 and 16")
                        
            except ValueError:
                print("Please enter a valid number")
    
    def save_mapping(self, filename="relay_mapping.json"):
        """Save the GPIO to relay mapping"""
        try:
            mapping_data = {
                "timestamp": datetime.now().isoformat(),
                "gpio_to_relay": self.gpio_to_relay,
                "relay_to_gpio": self.relay_to_gpio,
                "gpio_pins_used": self.gpio_pins
            }
            
            with open(filename, 'w') as f:
                json.dump(mapping_data, f, indent=2)
                
            print(f"Mapping saved to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving mapping: {e}")
            return False
    
    def load_mapping(self, filename="relay_mapping.json"):
        """Load existing mapping"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Convert string keys back to integers for relay_to_gpio
            self.gpio_to_relay = {int(k): v for k, v in data["gpio_to_relay"].items()}
            self.relay_to_gpio = {int(k): v for k, v in data["relay_to_gpio"].items()}
            
            print(f"Loaded existing mapping from {filename}")
            return True
            
        except FileNotFoundError:
            print("No existing mapping file found - starting fresh")
            return False
        except Exception as e:
            print(f"Error loading mapping: {e}")
            return False
    
    def show_mapping(self):
        """Display current mapping"""
        print("\nCURRENT RELAY MAPPING")
        print("=" * 40)
        
        if not self.gpio_to_relay:
            print("No mappings recorded yet")
            return
            
        print("GPIO -> Relay")
        print("-" * 15)
        for gpio in sorted(self.gpio_to_relay.keys()):
            relay = self.gpio_to_relay[gpio]
            print(f"  {gpio:2d} -> Relay {relay}")
        
        print(f"\nTotal mapped: {len(self.gpio_to_relay)}/{len(self.gpio_pins)}")
    
    def generate_code(self):
        """Generate the relay_pins dictionary for rpi_relays.py"""
        if not self.gpio_to_relay:
            print("No mappings to generate code from")
            return
            
        print("\nPYTHON CODE FOR rpi_relays.py")
        print("=" * 45)
        print("Copy this into your RelayController.__init__():")
        print()
        print("self.relay_pins = {")
        
        # Sort by relay number
        sorted_relays = sorted(self.relay_to_gpio.items())
        for relay_num, gpio_pin in sorted_relays:
            print(f"    {relay_num}: {gpio_pin},")
        
        print("}")
        print()
        print("# Relay names for reference:")
        for relay_num, gpio_pin in sorted_relays:
            print(f"# Relay {relay_num} = GPIO {gpio_pin}")
    
    def run_mapping(self):
        """Run the complete mapping process"""
        print("GPIO to Relay Mapper")
        print("=" * 30)
        print("This will test each GPIO pin and let you identify")
        print("which physical relay it controls.\n")
        
        # Try to load existing mapping
        self.load_mapping()
        
        # Show current mapping if any
        if self.gpio_to_relay:
            self.show_mapping()
            restart = input("\nContinue mapping remaining GPIOs? (y/n): ").lower()
            if restart != 'y':
                return
        
        # Setup GPIO
        if not self.setup_gpio():
            return
        
        try:
            # Test each GPIO pin
            for i, gpio_pin in enumerate(self.gpio_pins):
                
                # Skip if already mapped
                if gpio_pin in self.gpio_to_relay:
                    print(f"\nGPIO {gpio_pin} already mapped to Relay {self.gpio_to_relay[gpio_pin]} - skipping")
                    continue
                
                print(f"\nProgress: {i+1}/{len(self.gpio_pins)} GPIOs")
                
                while True:  # Loop for retry option
                    # Test the GPIO
                    if not self.test_gpio(gpio_pin):
                        break
                    
                    # Get relay number
                    relay_response = self.get_relay_number(gpio_pin)
                    
                    if relay_response == 'quit':
                        return
                    elif relay_response == 'retry':
                        continue  # Test this GPIO again
                    elif relay_response == 'skip':
                        print(f"Skipping GPIO {gpio_pin}")
                        break
                    else:
                        # Valid relay number
                        relay_num = relay_response
                        
                        # Remove old mapping if overwriting
                        if relay_num in self.relay_to_gpio:
                            old_gpio = self.relay_to_gpio[relay_num]
                            del self.gpio_to_relay[old_gpio]
                        
                        # Store mapping
                        self.gpio_to_relay[gpio_pin] = relay_num
                        self.relay_to_gpio[relay_num] = gpio_pin
                        
                        print(f"Mapped: GPIO {gpio_pin} -> Relay {relay_num}")
                        break
                
                # Save progress after each mapping
                self.save_mapping()
            
            # Show final results
            print("\nMAPPING COMPLETE!")
            self.show_mapping()
            self.generate_code()
            
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup GPIO"""
        try:
            if self.h:
                # Turn off all GPIOs
                for pin in self.gpio_pins:
                    try:
                        lgpio.gpio_write(self.h, pin, 0)
                        lgpio.gpio_free(self.h, pin)
                    except:
                        pass
                        
                lgpio.gpiochip_close(self.h)
                print("\nGPIO cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")

def main():
    """Main function"""
    mapper = RelayMapper()
    
    try:
        mapper.run_mapping()
    except KeyboardInterrupt:
        print("\n\nMapping interrupted")
    finally:
        mapper.cleanup()

if __name__ == "__main__":
    main()