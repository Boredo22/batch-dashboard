#!/usr/bin/env python3
"""
Basic I2C Hardware Debug - Step by step diagnosis
"""

import os
import subprocess
import time

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1

def check_basic_i2c():
    """Check the most basic I2C functionality"""
    print("=" * 60)
    print("BASIC I2C HARDWARE DIAGNOSIS")
    print("=" * 60)
    
    # 1. Check if we're on a Pi
    print("1. CHECKING RASPBERRY PI DETECTION:")
    if os.path.exists('/proc/device-tree/model'):
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip().replace('\x00', '')
            print(f"   ✓ Detected: {model}")
    else:
        print("   ✗ Not detected as Raspberry Pi")
        return False
    
    # 2. Check I2C device files
    print("\n2. CHECKING I2C DEVICE FILES:")
    for bus in [0, 1]:
        device = f"/dev/i2c-{bus}"
        if os.path.exists(device):
            print(f"   ✓ {device} exists")
            # Check permissions
            stat = os.stat(device)
            perms = oct(stat.st_mode)[-3:]
            print(f"     Permissions: {perms}")
        else:
            print(f"   ✗ {device} missing")
    
    # 3. Check kernel modules
    print("\n3. CHECKING KERNEL MODULES:")
    stdout, stderr, _ = run_cmd("lsmod | grep i2c")
    if stdout:
        print("   ✓ I2C modules loaded:")
        for line in stdout.split('\n'):
            if 'i2c' in line:
                print(f"     {line}")
    else:
        print("   ✗ No I2C modules found")
        print("   Trying to load modules...")
        run_cmd("sudo modprobe i2c-dev")
        run_cmd("sudo modprobe i2c-bcm2835")
        # Check again
        stdout, stderr, _ = run_cmd("lsmod | grep i2c")
        if stdout:
            print("   ✓ Modules loaded successfully")
        else:
            print("   ✗ Failed to load modules")
    
    # 4. Check raspi-config status
    print("\n4. CHECKING RASPI-CONFIG I2C STATUS:")
    stdout, stderr, code = run_cmd("sudo raspi-config nonint get_i2c")
    if code == 0:
        if stdout == "0":
            print("   ✓ I2C is enabled in raspi-config")
        else:
            print("   ✗ I2C is disabled in raspi-config")
            print("   Enabling I2C...")
            run_cmd("sudo raspi-config nonint do_i2c 0")
    else:
        print("   ? Could not check raspi-config status")
    
    # 5. Check config.txt
    print("\n5. CHECKING /boot/config.txt:")
    config_paths = ["/boot/config.txt", "/boot/firmware/config.txt"]
    config_found = False
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            config_found = True
            print(f"   Found config at: {config_path}")
            
            with open(config_path, 'r') as f:
                content = f.read()
                
            if "dtparam=i2c_arm=on" in content:
                print("   ✓ I2C enabled in config.txt")
            else:
                print("   ✗ I2C not enabled in config.txt")
                print("   This might be the issue!")
                
            if "i2c_baudrate" in content:
                import re
                match = re.search(r'i2c_baudrate=(\d+)', content)
                if match:
                    print(f"   ✓ I2C baudrate set to: {match.group(1)}")
            break
    
    if not config_found:
        print("   ✗ No config.txt found!")
    
    # 6. Check GPIO state
    print("\n6. CHECKING GPIO PINS (if gpiozero available):")
    try:
        import gpiozero
        from gpiozero import InputDevice
        
        try:
            sda = InputDevice(2, pull_up=None)  # GPIO 2 (SDA)
            scl = InputDevice(3, pull_up=None)  # GPIO 3 (SCL)
            
            print(f"   SDA (GPIO 2): {'HIGH' if sda.value else 'LOW'}")
            print(f"   SCL (GPIO 3): {'HIGH' if scl.value else 'LOW'}")
            
            if sda.value and scl.value:
                print("   ✓ Both lines HIGH (good idle state)")
            else:
                print("   ✗ One or both lines LOW (bad - check wiring)")
                
            sda.close()
            scl.close()
            
        except Exception as e:
            print(f"   ✗ Could not read GPIO: {e}")
            
    except ImportError:
        print("   ? gpiozero not available for GPIO check")
    
    # 7. Try i2cdetect on both buses
    print("\n7. TESTING i2cdetect ON BOTH BUSES:")
    
    # Check if i2cdetect is available
    stdout, stderr, code = run_cmd("which i2cdetect")
    if code != 0:
        print("   ✗ i2cdetect not found - installing...")
        run_cmd("sudo apt-get update && sudo apt-get install -y i2c-tools")
    
    for bus in [0, 1]:
        print(f"\n   Testing bus {bus}:")
        stdout, stderr, code = run_cmd(f"i2cdetect -y {bus}")
        
        if code == 0:
            print(f"   ✓ i2cdetect succeeded on bus {bus}")
            # Check if any devices found
            if any(c.isalnum() and c not in 'UU--' for c in stdout):
                print("   🎉 DEVICES FOUND!")
                print(stdout)
            else:
                print("   No devices detected")
                print(stdout[:200] + "..." if len(stdout) > 200 else stdout)
        else:
            print(f"   ✗ i2cdetect failed on bus {bus}: {stderr}")
    
    # 8. Check user permissions
    print("\n8. CHECKING USER PERMISSIONS:")
    import pwd
    import grp
    
    try:
        username = pwd.getpwuid(os.getuid()).pw_name
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        
        print(f"   Current user: {username}")
        print(f"   Groups: {', '.join(groups)}")
        
        required_groups = ['i2c', 'gpio']
        for group in required_groups:
            if group in groups:
                print(f"   ✓ In {group} group")
            else:
                print(f"   ✗ NOT in {group} group")
                print(f"     Run: sudo usermod -a -G {group} {username}")
                
    except Exception as e:
        print(f"   Error checking permissions: {e}")

def test_manual_gpio():
    """Test GPIO pins manually if possible"""
    print("\n" + "=" * 60)
    print("MANUAL GPIO TEST (if lgpio available)")
    print("=" * 60)
    
    try:
        import lgpio
        
        # Open GPIO chip
        h = lgpio.gpiochip_open(0)

        
        
        # Test SDA and SCL pins
        sda_pin = 2
        scl_pin = 3
        
        print(f"Testing GPIO {sda_pin} (SDA) and {scl_pin} (SCL)...")
        
        # Set as inputs with pull-ups
        lgpio.gpio_claim_input(h, sda_pin, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(h, scl_pin, lgpio.SET_PULL_UP)
        
        time.sleep(0.1)
        
        sda_val = lgpio.gpio_read(h, sda_pin)
        scl_val = lgpio.gpio_read(h, scl_pin)
        
        print(f"SDA value: {sda_val} ({'HIGH' if sda_val else 'LOW'})")
        print(f"SCL value: {scl_val} ({'HIGH' if scl_val else 'LOW'})")
        
        if sda_val == 1 and scl_val == 1:
            print("✓ Both pins are HIGH - good for I2C")
        else:
            print("✗ One or both pins are LOW - check wiring/pull-ups")
        
        # Cleanup
        lgpio.gpio_free(h, sda_pin)
        lgpio.gpio_free(h, scl_pin)
        lgpio.gpiochip_close(h)
        
        return True
        
    except ImportError:
        print("lgpio not available")
        return False
    except Exception as e:
        print(f"GPIO test failed: {e}")
        return False

def main():
    print("Starting comprehensive I2C diagnosis...")
    
    # Run basic checks
    check_basic_i2c()
    
    # Test GPIO manually
    test_manual_gpio()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("""
    Based on the output above:
    
    1. If NO /dev/i2c-* files exist:
       - I2C is not properly enabled
       - Run: sudo raspi-config -> Interface Options -> I2C -> Enable
       - Reboot
    
    2. If files exist but i2cdetect fails:
       - Check user permissions (add to i2c group)
       - Try with sudo: sudo i2cdetect -y 1
    
    3. If i2cdetect works but finds nothing:
       - Hardware wiring issue
       - Wrong device mode (UART vs I2C)
       - Need pull-up resistors
       - Try different I2C bus speed
    
    4. If GPIO pins are LOW:
       - Check physical wiring
       - Ensure SDA=GPIO2/Pin3, SCL=GPIO3/Pin5
       - Add 4.7kΩ pull-up resistors
       
    5. Force enable I2C if needed:
       - Add these lines to /boot/config.txt:
         dtparam=i2c_arm=on
         dtparam=i2c1=on
         dtparam=i2c_baudrate=10000
       - Reboot
    """)

if __name__ == "__main__":
    main()