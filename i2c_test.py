#!/usr/bin/env python3
"""
I2C Test Script for Raspberry Pi
Tests if I2C is working properly and detects connected EZO devices
"""

import time
import logging
import sys

try:
    import smbus2 as smbus
except ImportError:
    print("smbus2 not installed. Install with: pip install smbus2")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scan_i2c_bus(bus_num=1):
    """Scan the I2C bus for connected devices"""
    logger.info(f"Scanning I2C bus {bus_num} for devices...")
    
    try:
        bus = smbus.SMBus(bus_num)
        found_devices = []
        
        # Scan address range (0x08-0x77 is standard I2C range)
        # EZO devices typically use addresses 1-8 (0x01-0x08)
        # We'll scan a wider range to be safe
        for addr in range(0x01, 0x78):
            try:
                # Try to read a byte to see if device exists
                # Use a command that should be safe for most devices
                bus.read_byte(addr)
                found_devices.append(addr)
                logger.info(f"Found device at address: 0x{addr:02X} ({addr})")
            except Exception:
                # No device at this address
                pass
                
        bus.close()
        return found_devices
        
    except Exception as e:
        logger.error(f"Error accessing I2C bus {bus_num}: {e}")
        return []

def test_ezo_device(addr, bus_num=1):
    """Test communication with an EZO device"""
    logger.info(f"Testing communication with device at address: 0x{addr:02X} ({addr})")
    
    try:
        bus = smbus.SMBus(bus_num)
        
        # Send "I" command to get device information
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
            
            logger.info(f"Response from device 0x{addr:02X}: {response}")
            return True, response
            
        except Exception as e:
            logger.warning(f"Could read from device, but no valid response: {e}")
            return False, str(e)
            
    except Exception as e:
        logger.error(f"Error communicating with device: {e}")
        return False, str(e)
    finally:
        try:
            bus.close()
        except:
            pass

def main():
    """Main test function"""
    print("=" * 50)
    print("I2C CONNECTION TEST")
    print("=" * 50)
    
    # Check for I2C capability
    try:
        import os
        if os.path.exists('/dev/i2c-1'):
            print("✓ I2C bus 1 is available at /dev/i2c-1")
        else:
            print("✗ I2C bus 1 device file not found!")
            print("  → Check if I2C is enabled in raspi-config")
    except:
        print("Could not check for I2C device file")
    
    print("\n1. Scanning for I2C devices...")
    devices = scan_i2c_bus()
    
    if not devices:
        print("✗ No I2C devices found!")
        print("  → Check connections and device power")
        print("  → Verify I2C is enabled in raspi-config")
        print("  → Try running 'i2cdetect -y 1' to confirm")
        return
    
    print(f"✓ Found {len(devices)} I2C device(s) at addresses: {', '.join([f'0x{addr:02X}' for addr in devices])}\n")
    
    print("2. Testing communication with each device...")
    for addr in devices:
        print(f"\nTesting device at address 0x{addr:02X} ({addr}):")
        success, response = test_ezo_device(addr)
        
        if success:
            print(f"✓ Successfully communicated with device 0x{addr:02X}")
            print(f"  → Response: {response}")
        else:
            print(f"✗ Communication failed with device 0x{addr:02X}")
            print(f"  → Error: {response}")
    
    print("\n" + "=" * 50)
    if devices:
        print("I2C TEST SUMMARY: I2C bus is working!")
        if any(1 <= addr <= 8 for addr in devices):
            print("EZO pump devices detected. Your I2C configuration appears correct.")
        else:
            print("Devices detected, but none in EZO pump address range (1-8).")
            print("Check if pumps are powered and properly connected.")
    else:
        print("I2C TEST SUMMARY: No I2C devices detected!")
        print("Check connections and I2C configuration.")
    print("=" * 50)

if __name__ == "__main__":
    main()