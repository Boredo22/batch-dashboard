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
import threading
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from config import (
    I2C_BUS_NUMBER,
    PH_SENSOR_ADDRESS,
    EC_SENSOR_ADDRESS,
    PH_CALIBRATION_SOLUTIONS,
    EC_CALIBRATION_SOLUTIONS,
    EZO_COMMAND_DELAY
)

from hardware.i2c_manager import get_i2c_manager

logger = logging.getLogger(__name__)


class EZOSensorController:
    """
    EZO pH and EC sensor controller using I2C
    Replaces ArduinoUnoController with direct I2C communication
    Compatible with existing FeedControlSystem patterns
    """

    def __init__(self):
        # Use shared I2C manager
        self.i2c = get_i2c_manager()
        self.connected = True
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 5.0  # Read sensors every 5 seconds

        self.latest_readings = {
            'ph': None,
            'ec': None,
            'last_update': 0
        }

        # Configure sensors on initialization
        try:
            # Configure EC sensor outputs (EC only, disable other readings)
            self._send_command(EC_SENSOR_ADDRESS, "O,EC,1")   # Enable EC
            self._send_command(EC_SENSOR_ADDRESS, "O,TDS,0")  # Disable TDS
            self._send_command(EC_SENSOR_ADDRESS, "O,S,0")    # Disable salinity
            self._send_command(EC_SENSOR_ADDRESS, "O,SG,0")   # Disable specific gravity

            logger.info("✓ EZO pH/EC sensors initialized via shared I2C manager")
        except Exception as e:
            logger.error(f"Failed to configure EZO pH/EC sensors: {e}")
            self.connected = False

    def connect(self):
        """Compatibility method - already connected via shared I2C manager"""
        return self.connected

    def close(self):
        """Close sensor controller and stop monitoring"""
        # Stop monitoring thread first
        if self.monitoring_active:
            self.stop_monitoring()

        # Shared I2C manager handles bus lifecycle
        logger.debug("Sensor controller cleanup (I2C bus managed by shared manager)")
        self.connected = False
    
    def _send_command(self, address, command, response_time=0.9):
        """
        Send command to EZO circuit and read response using shared I2C manager

        Args:
            address: I2C address
            command: Command string
            response_time: Time to wait for response in seconds

        Returns:
            Response string or None if error
        """
        if not self.connected:
            logger.warning(f"Cannot send command - sensor controller not connected")
            return None

        # Use shared I2C manager
        success, response_code, response_text = self.i2c.send_command(address, command, response_time)

        if success:
            logger.debug(f"EZO 0x{address:02X} <- '{command}' -> '{response_text}'")
            return response_text
        elif response_code == 2:
            logger.error(f"EZO 0x{address:02X}: Syntax error for command '{command}'")
        elif response_code == 254:
            logger.warning(f"EZO 0x{address:02X}: Still processing (may need longer delay)")
        elif response_code == 255:
            logger.warning(f"EZO 0x{address:02X}: No data available")
        else:
            logger.error(f"EZO 0x{address:02X}: Unknown response code {response_code}")

        return None
    
    def _monitoring_loop(self):
        """Background thread that continuously reads sensors when monitoring is active"""
        logger.info("Sensor monitoring loop started")

        while self.monitoring_active:
            try:
                # Read both sensors
                readings = self.read_sensors()
                if readings['ph'] is not None or readings['ec'] is not None:
                    logger.debug(f"Sensor readings - pH: {readings['ph']}, EC: {readings['ec']}")
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Sleep for the monitoring interval
            time.sleep(self.monitoring_interval)

        logger.info("Sensor monitoring loop stopped")

    def start_monitoring(self):
        """Start EC/pH monitoring with background polling"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return True

        self.monitoring_active = True

        # Start background monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="EZO-Monitoring"
        )
        self.monitoring_thread.start()

        logger.info(f"EZO pH/EC monitoring started (polling every {self.monitoring_interval}s)")
        return True

    def stop_monitoring(self):
        """Stop EC/pH monitoring and background polling"""
        if not self.monitoring_active:
            logger.warning("Monitoring already stopped")
            return True

        self.monitoring_active = False

        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

        logger.info("EZO pH/EC monitoring stopped")
        return True

    def read_ph(self):
        """Read pH value"""
        response = self._send_command(PH_SENSOR_ADDRESS, "R")
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
        response = self._send_command(EC_SENSOR_ADDRESS, "R")
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
        response = self._send_command(PH_SENSOR_ADDRESS, command)
        
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
        response = self._send_command(PH_SENSOR_ADDRESS, command)

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
        response = self._send_command(PH_SENSOR_ADDRESS, command)

        if response is not None:
            logger.info(f"pH high calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH high calibration at {value:.2f}: Failed")
            return False

    def clear_ph_calibration(self):
        """Clear all pH calibration"""
        response = self._send_command(PH_SENSOR_ADDRESS, "Cal,clear")

        if response is not None:
            logger.info("pH calibration cleared")
            return True
        else:
            logger.error("Failed to clear pH calibration")
            return False

    def get_ph_calibration_status(self):
        """Get number of pH calibration points (0-3)"""
        response = self._send_command(PH_SENSOR_ADDRESS, "Cal,?")
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
        response = self._send_command(EC_SENSOR_ADDRESS, "Cal,dry")
        
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
        response = self._send_command(EC_SENSOR_ADDRESS, command)

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
        response = self._send_command(EC_SENSOR_ADDRESS, command)

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
        response = self._send_command(EC_SENSOR_ADDRESS, command)

        if response is not None:
            logger.info(f"EC high calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC high calibration at {value} μS/cm: Failed")
            return False

    def clear_ec_calibration(self):
        """Clear all EC calibration"""
        response = self._send_command(EC_SENSOR_ADDRESS, "Cal,clear")

        if response is not None:
            logger.info("EC calibration cleared")
            return True
        else:
            logger.error("Failed to clear EC calibration")
            return False

    def get_ec_calibration_status(self):
        """Get EC calibration state (0=none, 1=single, 2=dual)"""
        response = self._send_command(EC_SENSOR_ADDRESS, "Cal,?")
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
        ph_info = self._send_command(PH_SENSOR_ADDRESS, "I")
        ec_info = self._send_command(EC_SENSOR_ADDRESS, "I")
        
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
