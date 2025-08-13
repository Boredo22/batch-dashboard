#!/usr/bin/env python3
"""
I2C Setup Script for Raspberry Pi
Installs and configures I2C kernel modules and dependencies
"""

import os
import sys
import subprocess
import time

def run_command(cmd, as_sudo=False):
    """Run a shell command and return output"""
    if as_sudo and os.geteuid() != 0:
        cmd = f"sudo {cmd}"
        
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=False, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def check_sudo():
    """Check if script has sudo privileges"""
    if os.geteuid() != 0:
        print("This script needs sudo privileges to install system packages and configure I2C.")
        print("Please run it with sudo:")
        print("sudo python3 setup_i2c.py")
        return False
    return True

def install_packages():
    """Install required packages"""
    print("\n===== Installing Required Packages =====")
    packages = [
        "i2c-tools",        # I2C utilities like i2cdetect
        "python3-smbus",    # Python SMBus interface
        "python3-pip",      # Python package manager
    ]
    
    return run_command(f"apt-get update && apt-get install -y {' '.join(packages)}")

def install_python_packages():
    """Install required Python packages"""
    print("\n===== Installing Python Packages =====")
    packages = [
        "smbus2",           # Improved SMBus interface
        "RPi.GPIO",         # GPIO access library
        "gpiozero",         # High-level GPIO interface
    ]
    
    return run_command(f"pip3 install {' '.join(packages)}")

def enable_i2c_in_config():
    """Enable I2C in Raspberry Pi configuration"""
    print("\n===== Enabling I2C in Raspberry Pi Configuration =====")
    
    # First, use raspi-config to enable I2C
    success = run_command("raspi-config nonint do_i2c 0")
    
    if not success:
        print("Could not enable I2C via raspi-config. Trying direct configuration...")
    
    # Ensure I2C is enabled in config.txt
    config_path = "/boot/config.txt"
    if not os.path.exists(config_path):
        config_path = "/boot/firmware/config.txt"  # For newer Pi OS
        
    if os.path.exists(config_path):
        # Check if dtparam=i2c_arm=on is in config.txt
        with open(config_path, 'r') as f:
            config_content = f.read()
            
        if "dtparam=i2c_arm=on" not in config_content:
            print(f"Adding I2C configuration to {config_path}")
            with open(config_path, 'a') as f:
                f.write("\n# Enable I2C\ndtparam=i2c_arm=on\n")
                f.write("dtparam=i2c_baudrate=10000\n")  # Lower baudrate for stability
    else:
        print(f"Warning: Could not find {config_path}")
        return False
    
    return True

def load_kernel_modules():
    """Load necessary kernel modules"""
    print("\n===== Loading I2C Kernel Modules =====")
    
    # Load modules
    modules = ["i2c-dev", "i2c-bcm2708", "i2c-bcm2835"]
    for module in modules:
        run_command(f"modprobe {module}")
    
    # Check if modules loaded
    result = run_command("lsmod | grep i2c")
    
    # Add modules to /etc/modules for loading at boot
    modules_file = "/etc/modules"
    if os.path.exists(modules_file):
        with open(modules_file, 'r') as f:
            content = f.read()
            
        with open(modules_file, 'a') as f:
            for module in modules:
                if module not in content:
                    f.write(f"{module}\n")
    
    return result

def configure_udev_rules():
    """Configure udev rules for I2C access without sudo"""
    print("\n===== Configuring udev Rules for I2C Access =====")
    
    udev_rule = """# I2C devices
KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0660"
"""
    
    # Create i2c group if it doesn't exist
    run_command("groupadd -f i2c")
    
    # Add current user to i2c group
    user = os.environ.get('SUDO_USER', os.environ.get('USER'))
    if user:
        run_command(f"usermod -aG i2c {user}")
    
    # Create udev rule
    rule_path = "/etc/udev/rules.d/99-i2c.rules"
    with open(rule_path, 'w') as f:
        f.write(udev_rule)
    
    # Reload udev rules
    return run_command("udevadm control --reload-rules && udevadm trigger")

def verify_i2c_setup():
    """Verify I2C setup"""
    print("\n===== Verifying I2C Setup =====")
    
    success = True
    
    # Check kernel modules
    if not run_command("lsmod | grep -q i2c"):
        print("✗ I2C kernel modules not loaded")
        success = False
    else:
        print("✓ I2C kernel modules loaded")
    
    # Check if I2C device exists
    if not os.path.exists("/dev/i2c-1"):
        print("✗ I2C device file not found at /dev/i2c-1")
        success = False
    else:
        print("✓ I2C device file exists at /dev/i2c-1")
    
    # Try to scan the I2C bus
    run_command("i2cdetect -y 1")
    
    return success

def main():
    """Main function"""
    print("=" * 60)
    print("I2C SETUP SCRIPT FOR RASPBERRY PI")
    print("=" * 60)
    
    if not check_sudo():
        sys.exit(1)
    
    steps = [
        ("Installing packages", install_packages),
        ("Installing Python packages", install_python_packages),
        ("Enabling I2C in configuration", enable_i2c_in_config),
        ("Loading kernel modules", load_kernel_modules),
        ("Configuring udev rules", configure_udev_rules),
        ("Verifying setup", verify_i2c_setup)
    ]
    
    all_success = True
    for description, func in steps:
        print(f"\n>> {description}...")
        if not func():
            print(f"✗ {description} failed")
            all_success = False
        else:
            print(f"✓ {description} completed")
    
    print("\n" + "=" * 60)
    if all_success:
        print("I2C SETUP COMPLETED SUCCESSFULLY")
        print("\nIMPORTANT: A system reboot is required for all changes to take effect.")
        print("Please run 'sudo reboot' to restart your Raspberry Pi.")
    else:
        print("I2C SETUP COMPLETED WITH ERRORS")
        print("Please review the output above for issues.")
        print("\nA system reboot may still resolve some issues.")
        print("After rebooting, run 'i2cdetect -y 1' to verify I2C is working.")
    print("=" * 60)

if __name__ == "__main__":
    main()