#!/usr/bin/env python3
"""
I2C Troubleshooting Script for Raspberry Pi
Provides comprehensive diagnostics for I2C issues
"""

import time
import logging
import sys
import os
import subprocess
import re

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, check=False, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def check_system_i2c():
    """Check system I2C configuration"""
    results = []
    
    # Check if I2C device exists
    if os.path.exists('/dev/i2c-1'):
        results.append(("✓ I2C device file exists", True))
    else:
        results.append(("✗ I2C device file not found at /dev/i2c-1", False))
    
    # Check kernel modules
    stdout, _, _ = run_command("lsmod | grep i2c")
    if "i2c_bcm2708" in stdout or "i2c_bcm2835" in stdout:
        results.append(("✓ I2C kernel module loaded", True))
    else:
        results.append(("✗ I2C kernel module not loaded", False))
    
    # Check if enabled in config
    stdout, _, _ = run_command("raspi-config nonint get_i2c")
    if stdout.strip() == "0":
        results.append(("✓ I2C enabled in raspi-config", True))
    else:
        results.append(("✗ I2C not enabled in raspi-config", False))
    
    # Check permissions
    stdout, _, _ = run_command("ls -l /dev/i2c-1")
    if "crw-rw" in stdout:
        results.append(("✓ I2C device has correct permissions", True))
    else:
        results.append(("✗ I2C device may have permission issues", False))
    
    # Check i2cdetect tool
    stdout, stderr, returncode = run_command("which i2cdetect")
    if returncode == 0:
        results.append(("✓ i2cdetect tool available", True))
    else:
        results.append(("✗ i2cdetect tool not found (install i2c-tools)", False))
    
    return results

def run_i2cdetect():
    """Run i2cdetect tool"""
    print("\nRunning i2cdetect to scan the bus:")
    stdout, stderr, returncode = run_command("i2cdetect -y 1")
    
    if returncode == 0:
        print(stdout)
        # Check if any devices were detected
        if re.search(r'[0-9a-f][0-9a-f]', stdout):
            print("✓ i2cdetect found at least one device")
            return True
        else:
            print("✗ i2cdetect did not find any devices")
            return False
    else:
        print(f"✗ Error running i2cdetect: {stderr}")
        return False

def try_different_bus_speeds():
    """Try reading from I2C at different speeds"""
    results = []
    
    try:
        import smbus2 as smbus
    except ImportError:
        results.append(("✗ smbus2 not installed", False))
        return results
    
    speeds = {
        100: "Standard mode (100 kHz)",
        400: "Fast mode (400 kHz)",
        10: "Low speed (10 kHz)"
    }
    
    # We'll simulate different speeds by adding delays
    delays = {
        100: 0.01,  # Standard
        400: 0.001, # Fast
        10: 0.1     # Low
    }
    
    for speed, desc in speeds.items():
        try:
            bus = smbus.SMBus(1)
            delay = delays[speed]
            
            # Scan a few addresses with delay to simulate different speeds
            found = False
            for addr in range(1, 128):
                try:
                    # Add artificial delay to simulate lower bus speed
                    time.sleep(delay)
                    bus.read_byte(addr)
                    results.append((f"✓ Device found at address 0x{addr:02X} with {desc}", True))
                    found = True
                    break
                except:
                    continue
            
            if not found:
                results.append((f"✗ No devices found with {desc}", False))
                
            bus.close()
            
        except Exception as e:
            results.append((f"✗ Error testing {desc}: {e}", False))
    
    return results

def scan_i2c_addresses(bus_num=1, range_start=0x01, range_end=0x78):
    """Scan wider range of I2C addresses"""
    try:
        import smbus2 as smbus
        bus = smbus.SMBus(bus_num)
        found_devices = []
        
        print(f"\nScanning FULL I2C address range (0x{range_start:02X}-0x{range_end:02X}):")
        for addr in range(range_start, range_end + 1):
            try:
                bus.read_byte(addr)
                found_devices.append(addr)
                print(f"✓ Found device at address: 0x{addr:02X} ({addr})")
            except Exception:
                pass
                
        bus.close()
        
        if not found_devices:
            print("✗ No devices found in extended scan")
        
        return found_devices
        
    except Exception as e:
        print(f"✗ Error during extended scan: {e}")
        return []

def test_ezo_device(addr, bus_num=1):
    """Test specific EZO device address"""
    try:
        import smbus2 as smbus
    except ImportError:
        print("✗ smbus2 not installed")
        return False, "smbus2 not installed"
    
    try:
        bus = smbus.SMBus(bus_num)
        
        # First try reading a byte
        try:
            bus.read_byte(addr)
            print(f"✓ Basic read from 0x{addr:02X} succeeded")
        except Exception as e:
            print(f"✗ Basic read from 0x{addr:02X} failed: {e}")
            bus.close()
            return False, str(e)
        
        # Try sending "I" command to get device information
        print(f"  Sending 'I' command to 0x{addr:02X}...")
        command = "I"
        command_bytes = command.encode('utf-8')
        
        # Write command
        bus.write_i2c_block_data(addr, 0, list(command_bytes))
        
        # Wait for processing
        time.sleep(0.3)
        
        # Read response
        try:
            response_bytes = bus.read_i2c_block_data(addr, 0, 32)
            
            # Convert to string and clean up
            response = ''.join([chr(b) for b in response_bytes if b > 0 and b != 255]).strip()
            
            print(f"  → Response: {response}")
            return True, response
            
        except Exception as e:
            print(f"  → Error reading response: {e}")
            return False, str(e)
            
    except Exception as e:
        print(f"✗ Error communicating with device: {e}")
        return False, str(e)
    finally:
        try:
            bus.close()
        except:
            pass

def check_gpio_state():
    """Check GPIO state if gpiozero is available"""
    try:
        from gpiozero import InputDevice
        from gpiozero.pins.mock import MockFactory
        from gpiozero import Device
        
        # Check if we're on a Pi and have access to real GPIO
        try:
            # Try to get I2C pins
            sda = InputDevice(2)  # GPIO 2 (SDA)
            scl = InputDevice(3)  # GPIO 3 (SCL)
            
            print(f"SDA (GPIO 2) state: {'HIGH' if sda.value else 'LOW'}")
            print(f"SCL (GPIO 3) state: {'HIGH' if scl.value else 'LOW'}")
            
            # Both should be pulled high when idle
            if sda.value and scl.value:
                print("✓ Both I2C lines are HIGH (correct idle state)")
            else:
                print("✗ One or both I2C lines are LOW (should be HIGH when idle)")
                print("  This suggests a wiring issue or missing pull-up resistors")
            
            sda.close()
            scl.close()
            return True
            
        except Exception as e:
            print(f"✗ Could not check GPIO state: {e}")
            return False
            
    except ImportError:
        print("✗ gpiozero not installed, cannot check GPIO state")
        return False

def print_wiring_diagram():
    """Print a visual wiring guide"""
    print("\nI2C WIRING DIAGRAM:")
    print("""
    Raspberry Pi          EZO Pump
    -------------        ----------
    3.3V (Pin 1) -------- VCC (Red)
    SDA (Pin 3/GPIO 2) -- SDA (Blue/Yellow)
    SCL (Pin 5/GPIO 3) -- SCL (White)
    GND (Pin 9) --------- GND (Black)
    
    IMPORTANT:
    1. Double-check that SDA and SCL are not swapped
    2. Verify you're using GPIO 2 and 3 (pins 3 and 5)
    3. Make sure all connections are secure
    4. EZO pumps typically use 3.3V (not 5V) for logic levels
    """)

def main():
    """Main troubleshooting function"""
    print("=" * 60)
    print("I2C COMPREHENSIVE TROUBLESHOOTING")
    print("=" * 60)
    
    # 1. Check for smbus2
    try:
        import smbus2 as smbus
        print("✓ smbus2 module is installed")
    except ImportError:
        print("✗ smbus2 module not installed!")
        print("  → Install with: pip install smbus2")
        return
    
    # 2. Check system I2C configuration
    print("\nCHECKING SYSTEM I2C CONFIGURATION:")
    sys_checks = check_system_i2c()
    for msg, status in sys_checks:
        print(msg)
    
    # 3. Run i2cdetect
    i2cdetect_found_devices = run_i2cdetect()
    
    # 4. Try to read I2C with different bus speeds
    print("\nTRYING DIFFERENT I2C BUS SPEEDS:")
    speed_results = try_different_bus_speeds()
    for msg, status in speed_results:
        print(msg)
    
    # 5. Run extended scan for unusual addresses
    extended_devices = scan_i2c_addresses(1, 0x01, 0x78)
    
    # 6. If any devices found, try to communicate with them
    if extended_devices:
        print("\nTESTING COMMUNICATION WITH FOUND DEVICES:")
        for addr in extended_devices:
            print(f"\nTesting device at address 0x{addr:02X} ({addr}):")
            test_ezo_device(addr)
    
    # 7. If still no devices, try direct GPIO checking
    if not extended_devices and not i2cdetect_found_devices:
        print("\nCHECKING GPIO PIN STATES:")
        check_gpio_state()
    
    # 8. Print wiring diagram and troubleshooting suggestions
    print_wiring_diagram()
    
    print("\nTROUBLESHOOTING SUGGESTIONS:")
    print("""
1. Check physical connections:
   - Ensure wires are firmly connected and not loose
   - Verify wire connections match the diagram above
   - Try using different wires to rule out broken wires

2. Check power to EZO pumps:
   - Confirm pumps have power (LED indicators)
   - Measure voltage at VCC/GND on the pump side (should be 3.3V)

3. Check pull-up resistors:
   - I2C requires pull-up resistors on SDA and SCL
   - Raspberry Pi has built-in pull-ups, but they may be too weak
   - Try adding external 4.7kΩ pull-up resistors to both SDA and SCL

4. Check for bus conflicts:
   - Disconnect other I2C devices if present
   - Try using a shorter cable (under 20cm)

5. Check EZO pump configuration:
   - Verify if pumps need a specific initialization
   - Check if they have non-standard I2C addresses
   - Try factory reset procedure if available

6. Try lower-level tools:
   - Run: 'sudo apt-get install -y i2c-tools python3-smbus2'
   - Then: 'i2cdetect -y 1' to scan the bus

7. Try forcing I2C baudrate:
   - Edit /boot/config.txt and add: dtparam=i2c_baudrate=10000
   - Then reboot and try again

8. Additional software checks:
   - Run: 'sudo raspi-config' and ensure I2C is enabled
   - Run: 'lsmod | grep i2c' to verify modules are loaded
   - If modules missing: 'sudo modprobe i2c-dev i2c-bcm2835'
   
9. Check pump is in I2C mode (not UART):
   - Some devices have different communication modes
   - Check device documentation for mode selection
    """)
    
    print("=" * 60)

if __name__ == "__main__":
    main()