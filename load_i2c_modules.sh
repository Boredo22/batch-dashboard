#!/bin/bash
# Simple script to load I2C kernel modules

echo "===== Loading I2C Kernel Modules ====="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root (sudo). Try: sudo bash load_i2c_modules.sh"
  exit 1
fi

# Install i2c-tools if not already installed
echo "Checking for i2c-tools..."
if ! command -v i2cdetect &> /dev/null; then
    echo "Installing i2c-tools..."
    apt-get update && apt-get install -y i2c-tools python3-smbus
fi

# Load the necessary modules
echo "Loading I2C kernel modules..."
modprobe i2c-dev
modprobe i2c-bcm2708
modprobe i2c-bcm2835

# Check if modules were loaded
echo "Checking if modules are loaded:"
lsmod | grep i2c

# Enable I2C in config if it's not already enabled
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt && ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "Enabling I2C in boot config..."
    if [ -f "/boot/config.txt" ]; then
        echo "dtparam=i2c_arm=on" >> /boot/config.txt
        echo "dtparam=i2c_baudrate=10000" >> /boot/config.txt
    elif [ -f "/boot/firmware/config.txt" ]; then
        echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
        echo "dtparam=i2c_baudrate=10000" >> /boot/firmware/config.txt
    fi
    echo "I2C enabled in config. A reboot is required for this to take effect."
fi

# Check I2C device file
if [ -e "/dev/i2c-1" ]; then
    echo "I2C device file exists: /dev/i2c-1"
else
    echo "I2C device file not found. A reboot may be required."
fi

# Try to run i2cdetect
echo "Running i2cdetect to scan for devices:"
i2cdetect -y 1

echo ""
echo "If you don't see any errors above and modules are loaded, I2C should be working."
echo "If i2cdetect shows a grid with no devices, your I2C modules are loaded but no devices are detected."
echo "This could be due to wiring issues or device power problems."
echo ""
echo "For a complete setup, run: sudo python3 setup_i2c.py"
echo "You may need to reboot after running that script: sudo reboot"