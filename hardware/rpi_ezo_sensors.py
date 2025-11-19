#!/usr/bin/env python3
"""
EZO pH/EC Sensor Controller for Batch Dashboard
Direct I2C communication with Atlas Scientific EZO circuits on Raspberry Pi
Replaces Arduino Uno - same interface, native Pi control

Compatible with existing batch-dashboard architecture
Follows patterns from rpi_p1umps.py and rpi_relays.py
"""

import time
import logging
import sys
from pathlib import Path
from smbus2 import SMBus

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from config import (
    I2C_BUS_NUMBER,
    EZO_PH_ADDRESS,
    EZO_EC_ADDRESS,
    PH_CALIBRATION_SOLUTIONS,
    EC_CALIBRATION_SOLUTIONS,
    EZO_COMMAND_DELAY
)

logger = logging.getLogger(__name__)


class EZOSensorController:
    """
    EZO pH and EC sensor controller using I2C
    Replaces ArduinoUnoController with direct I2C communication
    Compatible with existing FeedControlSystem patterns
    """

    def __init__(self):
        self.bus = None
        self.connected = False
        self.monitoring_active = False

        self.latest_readings = {
            'ph': None,
            'ec': None,
            'last_update': 0
        }

    def connect(self):
        """Connect to I2C bus and configure sensors"""
        try:
            self.bus = SMBus(I2C_BUS_NUMBER)
            self.connected = True

            # Configure EC sensor outputs (EC only, disable other readings)
            self._send_command(EZO_EC_ADDRESS, "O,EC,1")   # Enable EC
            self._send_command(EZO_EC_ADDRESS, "O,TDS,0")  # Disable TDS
            self._send_command(EZO_EC_ADDRESS, "O,S,0")    # Disable salinity
            self._send_command(EZO_EC_ADDRESS, "O,SG,0")   # Disable specific gravity

            logger.info("✓ Connected to EZO pH/EC sensors via I2C")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to EZO pH/EC sensors: {e}")
            self.connected = False
            return False
    
    def close(self):
        """Close I2C connection"""
        if self.bus:
            self.bus.close()
            self.bus = None
        self.connected = False
    
    def _send_command(self, address, command, response_time=0.9):
        """
        Send command to EZO circuit and read response

        Args:
            address: I2C address
            command: Command string
            response_time: Time to wait for response in seconds

        Returns:
            Response string or None if error
        """
        if not self.connected or not self.bus:
            logger.warning(f"Cannot send command - not connected to I2C bus")
            return None

        try:
            # Send command
            command_bytes = [ord(c) for c in command]
            self.bus.write_i2c_block_data(address, 0, command_bytes)

            # Wait for processing
            time.sleep(response_time)

            # Read response
            response_data = self.bus.read_i2c_block_data(address, 0, 31)
            response_code = response_data[0]

            if response_code == 1:  # Success
                response_string = ''.join([chr(b) for b in response_data[1:] if b != 0])
                logger.debug(f"EZO 0x{address:02X} <- '{command}' -> '{response_string.strip()}'")
                return response_string.strip()
            elif response_code == 2:
                logger.error(f"EZO 0x{address:02X}: Syntax error for command '{command}'")
            elif response_code == 254:
                logger.warning(f"EZO 0x{address:02X}: Still processing command '{command}'")
            elif response_code == 255:
                logger.warning(f"EZO 0x{address:02X}: No data available")
            else:
                logger.error(f"EZO 0x{address:02X}: Unknown response code {response_code}")

            return None

        except Exception as e:
            logger.error(f"Error communicating with EZO sensor at 0x{address:02X}: {e}")
            return None
    
    def start_monitoring(self):
        """Start EC/pH monitoring (for compatibility with Arduino pattern)"""
        self.monitoring_active = True
        logger.info("EZO pH/EC monitoring started")
        return True

    def stop_monitoring(self):
        """Stop EC/pH monitoring (for compatibility with Arduino pattern)"""
        self.monitoring_active = False
        logger.info("EZO pH/EC monitoring stopped")
        return True

    def read_ph(self):
        """Read pH value"""
        response = self._send_command(EZO_PH_ADDRESS, "R")
        if response:
            try:
                value = float(response)
                self.latest_readings['ph'] = value
                self.latest_readings['last_update'] = time.time()
                return value
            except ValueError:
                logger.error(f"Invalid pH reading: {response}")
                return None
        return None
    
    def read_ec(self):
        """Read EC value (returns mS/cm)"""
        response = self._send_command(EZO_EC_ADDRESS, "R")
        if response:
            try:
                # EZO returns μS/cm, convert to mS/cm
                ec_us = float(response)
                ec_ms = ec_us / 1000.0
                self.latest_readings['ec'] = ec_ms
                self.latest_readings['last_update'] = time.time()
                return ec_ms
            except ValueError:
                logger.error(f"Invalid EC reading: {response}")
                return None
        return None
    
    def read_sensors(self):
        """Read both sensors and return dict"""
        ph = self.read_ph()
        time.sleep(0.3)  # Small delay between readings
        ec = self.read_ec()
        
        return {
            'ph': ph,
            'ec': ec,
            'timestamp': time.time()
        }
    
    def get_latest_readings(self):
        """Get cached latest readings"""
        return self.latest_readings.copy()
    
    # ========================================================================
    # pH Calibration Methods
    # ========================================================================
    
    def calibrate_ph_mid(self, value=None):
        """Calibrate pH mid-point (typically 7.0)"""
        if value is None:
            value = PH_CALIBRATION_SOLUTIONS['mid']

        command = f"Cal,mid,{value:.2f}"
        response = self._send_command(EZO_PH_ADDRESS, command)
        
        if response is not None:
            logger.info(f"pH mid calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH mid calibration at {value:.2f}: Failed")
            return False
    
    def calibrate_ph_low(self, value=None):
        """Calibrate pH low-point (typically 4.0)"""
        if value is None:
            value = PH_CALIBRATION_SOLUTIONS['low']

        command = f"Cal,low,{value:.2f}"
        response = self._send_command(EZO_PH_ADDRESS, command)

        if response is not None:
            logger.info(f"pH low calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH low calibration at {value:.2f}: Failed")
            return False

    def calibrate_ph_high(self, value=None):
        """Calibrate pH high-point (typically 10.0)"""
        if value is None:
            value = PH_CALIBRATION_SOLUTIONS['high']

        command = f"Cal,high,{value:.2f}"
        response = self._send_command(EZO_PH_ADDRESS, command)

        if response is not None:
            logger.info(f"pH high calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH high calibration at {value:.2f}: Failed")
            return False

    def clear_ph_calibration(self):
        """Clear all pH calibration"""
        response = self._send_command(EZO_PH_ADDRESS, "Cal,clear")

        if response is not None:
            logger.info("pH calibration cleared")
            return True
        else:
            logger.error("Failed to clear pH calibration")
            return False

    def get_ph_calibration_status(self):
        """Get number of pH calibration points (0-3)"""
        response = self._send_command(EZO_PH_ADDRESS, "Cal,?")
        if response:
            try:
                return int(response.split(',')[1])
            except:
                return None
        return None
    
    # ========================================================================
    # EC Calibration Methods
    # ========================================================================
    
    def calibrate_ec_dry(self):
        """Calibrate EC dry (in air)"""
        response = self._send_command(EZO_EC_ADDRESS, "Cal,dry")
        
        if response is not None:
            logger.info("EC dry calibration: Success")
            return True
        else:
            logger.error("EC dry calibration: Failed")
            return False
    
    def calibrate_ec_single(self, value=None):
        """Single-point EC calibration (typically 1413 μS/cm)"""
        if value is None:
            value = EC_CALIBRATION_SOLUTIONS['single']

        command = f"Cal,{value}"
        response = self._send_command(EZO_EC_ADDRESS, command)

        if response is not None:
            logger.info(f"EC single calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC single calibration at {value} μS/cm: Failed")
            return False

    def calibrate_ec_low(self, value=None):
        """Two-point EC calibration - low (typically 84 μS/cm)"""
        if value is None:
            value = EC_CALIBRATION_SOLUTIONS['low']

        command = f"Cal,low,{value}"
        response = self._send_command(EZO_EC_ADDRESS, command)

        if response is not None:
            logger.info(f"EC low calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC low calibration at {value} μS/cm: Failed")
            return False

    def calibrate_ec_high(self, value=None):
        """Two-point EC calibration - high (typically 1413 μS/cm)"""
        if value is None:
            value = EC_CALIBRATION_SOLUTIONS['high']

        command = f"Cal,high,{value}"
        response = self._send_command(EZO_EC_ADDRESS, command)

        if response is not None:
            logger.info(f"EC high calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC high calibration at {value} μS/cm: Failed")
            return False

    def clear_ec_calibration(self):
        """Clear all EC calibration"""
        response = self._send_command(EZO_EC_ADDRESS, "Cal,clear")

        if response is not None:
            logger.info("EC calibration cleared")
            return True
        else:
            logger.error("Failed to clear EC calibration")
            return False

    def get_ec_calibration_status(self):
        """Get EC calibration state (0=none, 1=single, 2=dual)"""
        response = self._send_command(EZO_EC_ADDRESS, "Cal,?")
        if response:
            try:
                return int(response.split(',')[1])
            except:
                return None
        return None
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def is_connected(self):
        """Check if connected to sensors"""
        return self.connected
    
    def get_sensor_info(self):
        """Get information about both sensors"""
        ph_info = self._send_command(EZO_PH_ADDRESS, "I")
        ec_info = self._send_command(EZO_EC_ADDRESS, "I")
        
        return {
            'ph': {
                'info': ph_info,
                'calibration': self.get_ph_calibration_status()
            },
            'ec': {
                'info': ec_info,
                'calibration': self.get_ec_calibration_status()
            }
        }


# ============================================================================
# Simple test script (like your simple_gui.py pattern)
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("pH/EC Sensor Test - Batch Dashboard")
    print("=" * 60)

    # Create sensor controller
    sensor = EZOSensorController()
    
    # Connect
    if not sensor.connect():
        print("\n✗ Failed to connect to sensors")
        print("  Make sure I2C is enabled and sensors are connected")
        exit(1)
    
    print("\n✓ Connected to pH/EC sensors")
    
    # Show sensor info
    info = sensor.get_sensor_info()
    print(f"\npH Sensor: {info['ph']['info']}")
    print(f"pH Calibration Points: {info['ph']['calibration']}")
    print(f"\nEC Sensor: {info['ec']['info']}")
    print(f"EC Calibration State: {info['ec']['calibration']}")
    
    # Menu
    print("\n" + "=" * 60)
    print("Commands:")
    print("  1. Read sensors once")
    print("  2. Continuous monitoring")
    print("  3. pH calibration")
    print("  4. EC calibration")
    print("  q. Quit")
    print("=" * 60)
    
    try:
        while True:
            choice = input("\nEnter command: ").strip()
            
            if choice == '1':
                print("\nReading sensors...")
                readings = sensor.read_sensors()
                ph_str = f"{readings['ph']:.2f}" if readings['ph'] is not None else "---"
                ec_str = f"{readings['ec']:.2f}" if readings['ec'] is not None else "---"
                print(f"  pH: {ph_str}")
                print(f"  EC: {ec_str} mS/cm")
            
            elif choice == '2':
                print("\nContinuous monitoring (Ctrl+C to stop)")
                try:
                    while True:
                        readings = sensor.read_sensors()
                        ph_str = f"{readings['ph']:.2f}" if readings['ph'] is not None else "---"
                        ec_str = f"{readings['ec']:.2f}" if readings['ec'] is not None else "---"
                        print(f"pH: {ph_str}  |  EC: {ec_str} mS/cm", end='\r')
                        time.sleep(2)
                except KeyboardInterrupt:
                    print("\nStopped")
            
            elif choice == '3':
                print("\npH Calibration:")
                print("  1. Mid (7.0)")
                print("  2. Low (4.0)")
                print("  3. High (10.0)")
                print("  4. Clear")
                print("  5. Status")
                
                cal = input("Choice: ").strip()
                if cal == '1':
                    sensor.calibrate_ph_mid()
                elif cal == '2':
                    sensor.calibrate_ph_low()
                elif cal == '3':
                    sensor.calibrate_ph_high()
                elif cal == '4':
                    sensor.clear_ph_calibration()
                elif cal == '5':
                    points = sensor.get_ph_calibration_status()
                    print(f"Calibration points: {points}")
            
            elif choice == '4':
                print("\nEC Calibration:")
                print("  1. Dry")
                print("  2. Single (1413 μS/cm)")
                print("  3. Low (84 μS/cm)")
                print("  4. High (1413 μS/cm)")
                print("  5. Clear")
                print("  6. Status")
                
                cal = input("Choice: ").strip()
                if cal == '1':
                    sensor.calibrate_ec_dry()
                elif cal == '2':
                    sensor.calibrate_ec_single()
                elif cal == '3':
                    sensor.calibrate_ec_low()
                elif cal == '4':
                    sensor.calibrate_ec_high()
                elif cal == '5':
                    sensor.clear_ec_calibration()
                elif cal == '6':
                    state = sensor.get_ec_calibration_status()
                    states = {0: "Uncalibrated", 1: "Single-point", 2: "Two-point"}
                    print(f"State: {states.get(state, 'Unknown')}")
            
            elif choice.lower() == 'q':
                break
    
    finally:
        sensor.close()
        print("\nDone!")
