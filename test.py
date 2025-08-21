#!/usr/bin/env python3
"""
I2C Bus Diagnostic Tool
Diagnoses I2C issues like SCL reading 0.5V instead of 3.3V
"""

import lgpio
import time
import sys
import subprocess

class I2CDiagnostic:
    def __init__(self):
        """Initialize GPIO"""
        try:
            self.h = lgpio.gpiochip_open(0)
            print("✓ GPIO chip opened")
        except Exception as e:
            print(f"✗ Failed to open GPIO: {e}")
            sys.exit(1)
        
        self.claimed_pins = []
        self.sda_pin = 2  # GPIO 2
        self.scl_pin = 3  # GPIO 3
    
    def read_i2c_voltages(self):
        """Read actual voltages on I2C pins"""
        print("I2C PIN VOLTAGE DIAGNOSIS:")
        print("=" * 40)
        
        for pin, name in [(self.sda_pin, "SDA"), (self.scl_pin, "SCL")]:
            try:
                # Read with no pull resistor to see actual line state
                lgpio.gpio_claim_input(self.h, pin, lgpio.SET_PULL_NONE)
                self.claimed_pins.append(pin)
                time.sleep(0.1)
                
                state = lgpio.gpio_read(self.h, pin)
                voltage_digital = "3.3V" if state else "0.0V"
                
                print(f"{name} (Pin {pin}): Digital={voltage_digital}")
                
                if not state:
                    print(f"  ⚠️  {name} is being pulled LOW - this is the problem!")
                else:
                    print(f"  ✓  {name} reads HIGH digitally")
                
                lgpio.gpio_free(self.h, pin)
                self.claimed_pins.remove(pin)
                
            except Exception as e:
                print(f"{name} (Pin {pin}): Error - {e}")
        
        print(f"\nIf SCL shows LOW but you're measuring 0.5V with a multimeter:")
        print("This indicates a PARTIAL pull-down - something is wrong!")
    
    def diagnose_i2c_pullups(self):
        """Test pull-up resistor functionality"""
        print("\nI2C PULL-UP RESISTOR TEST:")
        print("=" * 30)
        
        for pin, name in [(self.sda_pin, "SDA"), (self.scl_pin, "SCL")]:
            try:
                # Test with Pi's internal pull-up
                lgpio.gpio_claim_input(self.h, pin, lgpio.SET_PULL_UP)
                self.claimed_pins.append(pin)
                time.sleep(0.1)
                
                state_with_pullup = lgpio.gpio_read(self.h, pin)
                
                lgpio.gpio_free(self.h, pin)
                self.claimed_pins.remove(pin)
                
                # Test without pull-up
                lgpio.gpio_claim_input(self.h, pin, lgpio.SET_PULL_NONE)
                self.claimed_pins.append(pin)
                time.sleep(0.1)
                
                state_no_pullup = lgpio.gpio_read(self.h, pin)
                
                print(f"{name}: With pull-up={state_with_pullup}, Without pull-up={state_no_pullup}")
                
                if state_with_pullup and not state_no_pullup:
                    print(f"  ✓ {name} pull-up working, but line is being pulled down")
                elif not state_with_pullup and not state_no_pullup:
                    print(f"  ⚠️  {name} stuck LOW - device or wiring issue!")
                elif state_with_pullup and state_no_pullup:
                    print(f"  ✓ {name} line is properly HIGH")
                
            except Exception as e:
                print(f"{name}: Error during pull-up test - {e}")
    
    def check_i2c_devices(self):
        """Check what devices are on the I2C bus"""
        print("\nI2C DEVICE SCAN:")
        print("=" * 20)
        
        try:
            # Run i2cdetect to see what's on the bus
            result = subprocess.run(['i2cdetect', '-y', '1'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("i2cdetect output:")
                print(result.stdout)
                
                # Look for devices
                lines = result.stdout.split('\n')
                devices_found = []
                
                for line in lines:
                    if ':' in line:
                        parts = line.split(':')[1].split()
                        for i, part in enumerate(parts):
                            if part != '--' and len(part) == 2:
                                addr = int(f"0x{part}", 16)
                                devices_found.append(addr)
                
                if devices_found:
                    print(f"Found devices at addresses: {[hex(addr) for addr in devices_found]}")
                    
                    # Check if these might be EZO pumps
                    ezo_addresses = [addr for addr in devices_found if 1 <= addr <= 8]
                    if ezo_addresses:
                        print(f"Possible EZO pumps at: {ezo_addresses}")
                else:
                    print("⚠️  No I2C devices detected!")
                    print("This suggests a bus problem if devices should be connected")
                    
            else:
                print("⚠️  i2cdetect failed - I2C may not be properly enabled")
                print("Error:", result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⚠️  i2cdetect timed out - I2C bus may be stuck")
        except FileNotFoundError:
            print("⚠️  i2cdetect not found - install i2c-tools")
            print("Run: sudo apt install i2c-tools")
        except Exception as e:
            print(f"Error scanning I2C: {e}")
    
    def test_i2c_communication(self):
        """Test basic I2C communication"""
        print("\nI2C COMMUNICATION TEST:")
        print("=" * 25)
        
        try:
            import smbus2
            bus = smbus2.SMBus(1)
            
            # Test reading from a few common addresses
            test_addresses = [1, 2, 3, 4, 5, 6, 7, 8]  # EZO pump range
            
            working_devices = []
            
            for addr in test_addresses:
                try:
                    # Try to read a byte
                    bus.read_byte(addr)
                    working_devices.append(addr)
                    print(f"✓ Device responds at address {addr}")
                except:
                    pass  # Device not present or not responding
            
            if working_devices:
                print(f"Communication successful with: {working_devices}")
            else:
                print("⚠️  No devices responding to I2C communication")
                print("This confirms there's a bus issue")
            
            bus.close()
            
        except ImportError:
            print("smbus2 not installed - cannot test communication")
            print("Install with: pip install smbus2")
        except Exception as e:
            print(f"I2C communication test failed: {e}")
    
    def diagnose_scl_low_issue(self):
        """Specific diagnosis for SCL reading 0.5V"""
        print("DIAGNOSING SCL @ 0.5V ISSUE:")
        print("=" * 35)
        print("Possible causes of SCL reading 0.5V instead of 3.3V:")
        print()
        
        print("1. DEVICE HOLDING SCL LOW:")
        print("   • One of your EZO pumps may be malfunctioning")
        print("   • Device may be stuck in a communication state")
        print("   • Try disconnecting devices one by one")
        
        print("\n2. INSUFFICIENT PULL-UP RESISTANCE:")
        print("   • Pi's internal pull-ups may be too weak")
        print("   • Try adding external 4.7kΩ pull-up resistors")
        print("   • Connect resistors from SDA/SCL to 3.3V")
        
        print("\n3. WIRING ISSUES:")
        print("   • Partial short to ground")
        print("   • Bad connection")
        print("   • Wrong pin connected")
        
        print("\n4. POWER ISSUES:")
        print("   • EZO pumps not getting proper 3.3V power")
        print("   • Check VCC connections to pumps")
        
        print("\n5. BUS CAPACITANCE:")
        print("   • Too many devices on bus")
        print("   • Wires too long")
        print("   • Poor quality connections")
    
    def provide_troubleshooting_steps(self):
        """Provide step-by-step troubleshooting"""
        print("\nTROUBLESHOOTING STEPS:")
        print("=" * 25)
        print("Try these steps in order:")
        print()
        print("STEP 1: Disconnect all I2C devices")
        print("   • Unplug all EZO pumps from I2C bus")
        print("   • Check if SCL returns to 3.3V")
        print("   • If yes: One device is faulty")
        
        print("\nSTEP 2: Check wiring")
        print("   • Verify SDA = GPIO 2 (Pin 3)")
        print("   • Verify SCL = GPIO 3 (Pin 5)")
        print("   • Check for loose connections")
        
        print("\nSTEP 3: Add external pull-ups")
        print("   • 4.7kΩ resistor from SDA to 3.3V")
        print("   • 4.7kΩ resistor from SCL to 3.3V")
        
        print("\nSTEP 4: Power check")
        print("   • Verify EZO pumps get 3.3V on VCC")
        print("   • Check ground connections")
        
        print("\nSTEP 5: Test one device at a time")
        print("   • Connect one EZO pump")
        print("   • Check if SCL stays at 3.3V")
        print("   • Test communication")
        print("   • Add devices one by one")
    
    def run_full_diagnosis(self):
        """Run complete I2C diagnosis"""
        print("I2C BUS FULL DIAGNOSTIC")
        print("=" * 30)
        print("Diagnosing SCL @ 0.5V issue...\n")
        
        self.read_i2c_voltages()
        self.diagnose_i2c_pullups()
        self.check_i2c_devices()
        self.test_i2c_communication()
        self.diagnose_scl_low_issue()
        self.provide_troubleshooting_steps()
    
    def cleanup(self):
        """Clean up GPIO"""
        for pin in self.claimed_pins:
            try:
                lgpio.gpio_free(self.h, pin)
            except:
                pass
        
        try:
            lgpio.gpiochip_close(self.h)
        except:
            pass

def main():
    """Main function"""
    diagnostic = I2CDiagnostic()
    
    try:
        diagnostic.run_full_diagnosis()
    except KeyboardInterrupt:
        print("\nDiagnostic interrupted")
    finally:
        diagnostic.cleanup()

if __name__ == "__main__":
    main()