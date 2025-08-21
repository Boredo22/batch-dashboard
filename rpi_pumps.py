#!/usr/bin/env python3
"""
Raspberry Pi 5 I2C Bus Scanner
Pi 5 has multiple I2C buses - scan them all
"""

import subprocess
import time
import os

def run_cmd(cmd, timeout=10):
    """Run command with timeout"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, 
                              text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

def scan_all_i2c_buses():
    """Scan all available I2C buses"""
    print("=" * 60)
    print("RASPBERRY PI 5 I2C BUS SCANNER")
    print("=" * 60)
    
    # Find all I2C device files
    i2c_devices = []
    for i in range(10):  # Check i2c-0 through i2c-9
        device = f"/dev/i2c-{i}"
        if os.path.exists(device):
            i2c_devices.append(i)
            print(f"Found I2C device: {device}")
    
    if not i2c_devices:
        print("❌ No I2C device files found!")
        return
    
    print(f"\nScanning {len(i2c_devices)} I2C bus(es)...")
    
    for bus_num in i2c_devices:
        print(f"\n🔍 Scanning I2C bus {bus_num} (/dev/i2c-{bus_num}):")
        
        # Try with timeout
        stdout, stderr, code = run_cmd(f"timeout 5 i2cdetect -y {bus_num}")
        
        if code == 0 and stdout:
            print(f"✅ Bus {bus_num} scan completed:")
            
            # Check if any devices found
            lines = stdout.strip().split('\n')
            found_devices = False
            devices = []
            
            for line in lines[1:]:  # Skip header
                for char in line.split()[1:]:  # Skip address column
                    if char not in ['--', 'UU'] and len(char) == 2:
                        try:
                            addr = int(char, 16)
                            devices.append(addr)
                            found_devices = True
                        except:
                            pass
            
            if found_devices:
                print(f"🎉 DEVICES FOUND on bus {bus_num}:")
                for addr in devices:
                    print(f"   Device at address: 0x{addr:02X} ({addr})")
                print("\nBus scan output:")
                print(stdout)
                
                # Try to identify EZO devices
                print(f"\n🔬 Testing devices on bus {bus_num} for EZO compatibility:")
                test_ezo_devices(bus_num, devices)
            else:
                print(f"   No devices found on bus {bus_num}")
                
        elif "TIMEOUT" in stderr:
            print(f"⏰ Bus {bus_num} scan timed out (possible hardware issue)")
        else:
            print(f"❌ Bus {bus_num} scan failed: {stderr}")

def test_ezo_devices(bus_num, addresses):
    """Test if devices respond to EZO commands"""
    try:
        import smbus2 as smbus
        
        bus = smbus.SMBus(bus_num)
        
        for addr in addresses:
            try:
                print(f"   Testing 0x{addr:02X}...")
                
                # Send "I" command to get device info
                bus.write_i2c_block_data(addr, 0, list("I".encode()))
                time.sleep(0.3)
                
                # Read response
                response_bytes = bus.read_i2c_block_data(addr, 0, 32)
                response = ''.join([chr(b) for b in response_bytes if 32 <= b <= 126]).strip()
                
                if response:
                    print(f"     ✅ EZO Response: {response}")
                else:
                    print(f"     ❓ Device responds but not EZO-compatible")
                    
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
        bus.close()
        
    except ImportError:
        print("   ⚠️  smbus2 not available for detailed testing")
    except Exception as e:
        print(f"   ❌ Bus {bus_num} test error: {e}")

def check_pi5_specific():
    """Check Pi 5 specific I2C configuration"""
    print(f"\n" + "=" * 60)
    print("RASPBERRY PI 5 SPECIFIC CHECKS")
    print("=" * 60)
    
    # Check what's actually in the device tree
    print("1. Checking device tree I2C configuration:")
    stdout, stderr, code = run_cmd("dtparam -l | grep i2c")
    if stdout:
        print("   I2C parameters:")
        for line in stdout.strip().split('\n'):
            print(f"     {line}")
    else:
        print("   No I2C parameters found in device tree")
    
    # Check which I2C buses are enabled
    print("\n2. Checking enabled I2C interfaces:")
    for i in range(10):
        if os.path.exists(f"/sys/bus/i2c/devices/i2c-{i}"):
            print(f"   ✅ I2C bus {i} is enabled")
            
            # Try to get more info about this bus
            try:
                with open(f"/sys/bus/i2c/devices/i2c-{i}/name", 'r') as f:
                    name = f.read().strip()
                    print(f"      Name: {name}")
            except:
                pass
    
    # Check GPIO alternative functions
    print("\n3. Checking GPIO pin functions:")
    stdout, stderr, code = run_cmd("raspi-gpio get 2-3")
    if stdout:
        print("   GPIO 2-3 status:")
        print(f"     {stdout.strip()}")
    
    # Check for additional I2C configs
    print("\n4. Checking additional I2C overlays:")
    stdout, stderr, code = run_cmd("grep -i i2c /boot/config.txt")
    if stdout:
        print("   I2C config lines:")
        for line in stdout.strip().split('\n'):
            print(f"     {line}")

def main():
    print("Scanning all I2C buses on Raspberry Pi 5...")
    
    # Install i2c-tools if needed
    if subprocess.run(["which", "i2cdetect"], capture_output=True).returncode != 0:
        print("Installing i2c-tools...")
        run_cmd("sudo apt-get update && sudo apt-get install -y i2c-tools")
    
    scan_all_i2c_buses()
    check_pi5_specific()
    
    print(f"\n" + "=" * 60)
    print("RASPBERRY PI 5 I2C TROUBLESHOOTING GUIDE")
    print("=" * 60)
