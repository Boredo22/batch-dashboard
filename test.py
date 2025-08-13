#!/usr/bin/env python3
"""
Quick test script to diagnose GPIO issues in virtual environment
Updated for Raspberry Pi 5 compatibility using lgpio
"""

import sys
import os
import platform

print("=== GPIO Environment Test ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")
print(f"Running in venv: {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")
print()

# Test if we're on Raspberry Pi
print("=== Platform Detection ===")
try:
    with open('/proc/cpuinfo', 'r') as f:
        cpuinfo = f.read()
        is_pi = 'BCM' in cpuinfo and 'ARM' in cpuinfo
        print(f"Is Raspberry Pi: {is_pi}")
        if is_pi:
            # Extract Pi model info
            for line in cpuinfo.split('\n'):
                if 'Model' in line:
                    print(f"Model: {line}")
                elif 'Hardware' in line:
                    print(f"Hardware: {line}")
except Exception as e:
    print(f"Cannot read /proc/cpuinfo: {e}")

print()

# Test GPIO permissions
print("=== GPIO Permissions ===")
gpio_devices = ['/dev/gpiomem', '/dev/mem', '/dev/gpiochip0']  # Added gpiochip0 for Pi 5
for device in gpio_devices:
    if os.path.exists(device):
        try:
            with open(device, 'r+b') as f:
                print(f"✓ Can access {device}")
        except PermissionError:
            print(f"✗ Permission denied for {device}")
        except Exception as e:
            print(f"✗ Error accessing {device}: {e}")
    else:
        print(f"✗ {device} does not exist")

print()

# Test I2C
print("=== I2C Detection ===")
i2c_devices = ['/dev/i2c-0', '/dev/i2c-1']
for device in i2c_devices:
    if os.path.exists(device):
        try:
            with open(device, 'r+b') as f:
                print(f"✓ Can access {device}")
        except PermissionError:
            print(f"✗ Permission denied for {device}")
        except Exception as e:
            print(f"✗ Error accessing {device}: {e}")
    else:
        print(f"✗ {device} does not exist")

print()

# Test importing GPIO libraries
print("=== Library Import Test ===")
libraries = ['lgpio', 'smbus2', 'serial']

for lib in libraries:
    try:
        if lib == 'lgpio':
            import lgpio
            print(f"✓ {lib} imported successfully")
            
            # Test basic GPIO operations
            try:
                # Open GPIO chip
                h = lgpio.gpiochip_open(0)
                print(f"  ✓ GPIO chip opened successfully")
                
                # Test output pin
                pin = 18  # Use a safe pin
                lgpio.gpio_claim_output(h, pin)
                lgpio.gpio_write(h, pin, 0)  # Set low
                lgpio.gpio_write(h, pin, 1)  # Set high
                lgpio.gpio_free(h, pin)
                print(f"  ✓ GPIO output test passed")
                
                # Test input pin
                lgpio.gpio_claim_input(h, pin, lgpio.SET_PULL_UP)
                value = lgpio.gpio_read(h, pin)
                print(f"  ✓ GPIO input test passed, value: {value}")
                lgpio.gpio_free(h, pin)
                
                # Close GPIO chip
                lgpio.gpiochip_close(h)
                print(f"  ✓ GPIO chip closed successfully")
            except Exception as e:
                print(f"  ✗ GPIO test failed: {e}")
        elif lib == 'smbus2':
            import smbus2
            print(f"✓ {lib} imported successfully")
        elif lib == 'serial':
            import serial
            print(f"✓ {lib} imported successfully")
            
    except ImportError as e:
        print(f"✗ {lib} import failed: {e}")
    except Exception as e:
        print(f"✗ {lib} test failed: {e}")

print()

# Check user groups
print("=== User Groups ===")
import grp
import pwd

try:
    username = pwd.getpwuid(os.getuid()).pw_name
    groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
    print(f"User: {username}")
    print(f"Groups: {', '.join(groups)}")
    
    required_groups = ['gpio', 'i2c', 'spi']
    for group in required_groups:
        if group in groups:
            print(f"✓ In {group} group")
        else:
            print(f"✗ Not in {group} group")
            
except Exception as e:
    print(f"Error checking groups: {e}")

print()
print("=== Recommendations ===")

# Give specific recommendations
if not any(os.path.exists(dev) for dev in ['/dev/gpiomem', '/dev/gpiochip0']):
    print("❌ GPIO device not found - not running on Raspberry Pi")
    print("   Solution: Use mock hardware for development")
elif not any(os.access(dev, os.R_OK | os.W_OK) for dev in gpio_devices if os.path.exists(dev)):
    print("❌ GPIO permission denied")  
    print("   Solution 1: Add user to gpio group: sudo usermod -a -G gpio $USER")
    print("   Solution 2: Run with sudo (not recommended)")
    print("   Solution 3: Install GPIO libraries system-wide")
else:
    print("✓ Hardware access looks good")
    print("   Try installing lgpio in your venv: pip install lgpio")

print("\n=== Test Complete ===")