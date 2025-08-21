#!/bin/bash
# Raspberry Pi 5 I2C Fix Script

echo "=== Raspberry Pi 5 I2C Troubleshooting ==="

# 1. Check all available I2C devices
echo "1. Available I2C devices:"
ls -la /dev/i2c* 2>/dev/null || echo "No I2C devices found"

# 2. Check which I2C buses exist in sysfs
echo -e "\n2. I2C buses in system:"
for i in {0..10}; do
    if [ -d "/sys/bus/i2c/devices/i2c-$i" ]; then
        echo "  i2c-$i exists"
        if [ -f "/sys/bus/i2c/devices/i2c-$i/name" ]; then
            name=$(cat /sys/bus/i2c/devices/i2c-$i/name)
            echo "    Name: $name"
        fi
    fi
done

# 3. Reset I2C modules
echo -e "\n3. Resetting I2C modules..."
sudo rmmod i2c_bcm2835 2>/dev/null
sudo rmmod i2c_dev 2>/dev/null
sleep 1
sudo modprobe i2c_dev
sudo modprobe i2c_bcm2835
echo "Modules reloaded"

# 4. Try scanning each available bus with timeout
echo -e "\n4. Scanning each I2C bus (with timeout):"
for i in {0..5}; do
    if [ -c "/dev/i2c-$i" ]; then
        echo "  Scanning bus $i:"
        timeout 5 sudo i2cdetect -y $i 2>/dev/null
        if [ $? -eq 124 ]; then
            echo "    Bus $i timed out"
        elif [ $? -eq 0 ]; then
            echo "    Bus $i scan completed"
        else
            echo "    Bus $i scan failed"
        fi
    fi
done

# 5. Check GPIO pin assignments
echo -e "\n5. Checking GPIO pin assignments:"
if [ -f "/sys/kernel/debug/pinctrl/pinctrl-rp1/pinmux-pins" ]; then
    echo "  GPIO 2 (SDA):"
    sudo cat /sys/kernel/debug/pinctrl/pinctrl-rp1/pinmux-pins | grep "pin 2 " || echo "    No info"
    echo "  GPIO 3 (SCL):"
    sudo cat /sys/kernel/debug/pinctrl/pinctrl-rp1/pinmux-pins | grep "pin 3 " || echo "    No info"
fi

# 6. Check device tree overlays
echo -e "\n6. Active device tree overlays:"
if [ -d "/proc/device-tree/chosen/overlays" ]; then
    ls /proc/device-tree/chosen/overlays/ | grep i2c || echo "  No I2C overlays found"
fi

# 7. Show current I2C configuration
echo -e "\n7. Current I2C configuration in /boot/config.txt:"
grep -E "i2c|I2C" /boot/config.txt | grep -v "^#" || echo "  No I2C config found"

echo -e "\n=== Recommendations ==="
echo "If all buses timeout or fail:"
echo "  1. Check physical wiring (SDA=Pin3, SCL=Pin5)"
echo "  2. Try lower speed: dtparam=i2c_baudrate=1000"
echo "  3. Add external pull-up resistors (4.7kΩ)"
echo "  4. Check if devices are in UART mode instead of I2C"
echo "  5. Try different I2C overlay: dtoverlay=i2c1,pins_2_3"