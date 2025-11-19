#!/usr/bin/env python3
"""
EZO pH and EC Controller for Raspberry Pi
Direct I2C communication with Atlas Scientific EZO circuits
Replaces Arduino Uno functionality
"""

import time
import logging
from smbus2 import SMBus

logger = logging.getLogger(__name__)


class EZOCircuit:
    """Base class for EZO circuit communication via I2C"""
    
    def __init__(self, bus_number, address, name):
        self.bus_number = bus_number
        self.address = address
        self.name = name
        self.bus = None
        
    def connect(self):
        """Open I2C bus connection"""
        try:
            self.bus = SMBus(self.bus_number)
            logger.info(f"Connected to {self.name} at address 0x{self.address:02X}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            return False
    
    def close(self):
        """Close I2C bus connection"""
        if self.bus:
            self.bus.close()
            self.bus = None
    
    def send_command(self, command, response_time=0.9):
        """
        Send command to EZO circuit and read response
        
        Args:
            command: Command string (e.g., "R" for read, "Cal,mid,7.00" for calibration)
            response_time: Time to wait for response in seconds (default 0.9s)
        
        Returns:
            Response string or None if error
        """
        if not self.bus:
            logger.error(f"{self.name}: Not connected")
            return None
        
        try:
            # Send command
            command_bytes = [ord(c) for c in command]
            self.bus.write_i2c_block_data(self.address, 0, command_bytes)
            
            # Wait for processing
            time.sleep(response_time)
            
            # Read response
            response_data = self.bus.read_i2c_block_data(self.address, 0, 31)
            
            # Parse response
            response_code = response_data[0]
            
            if response_code == 1:  # Success
                # Convert bytes to string, ignore null bytes
                response_string = ''.join([chr(b) for b in response_data[1:] if b != 0])
                logger.debug(f"{self.name} <- '{command}' -> '{response_string}'")
                return response_string.strip()
            
            elif response_code == 2:
                logger.error(f"{self.name}: Syntax error for command '{command}'")
                return None
            
            elif response_code == 254:
                logger.warning(f"{self.name}: Still processing command '{command}'")
                return None
            
            elif response_code == 255:
                logger.warning(f"{self.name}: No data available")
                return None
            
            else:
                logger.error(f"{self.name}: Unknown response code {response_code}")
                return None
                
        except Exception as e:
            logger.error(f"{self.name}: Error sending command '{command}': {e}")
            return None
    
    def read(self):
        """Read current value from sensor"""
        response = self.send_command("R")
        if response:
            try:
                return float(response)
            except ValueError:
                logger.error(f"{self.name}: Invalid reading '{response}'")
                return None
        return None
    
    def get_info(self):
        """Get device information"""
        return self.send_command("I")
    
    def get_status(self):
        """Get device status"""
        return self.send_command("Status")
    
    def set_led(self, state):
        """Turn LED on (1) or off (0)"""
        return self.send_command(f"L,{1 if state else 0}")
    
    def factory_reset(self):
        """Factory reset the device"""
        return self.send_command("Factory")


class EZOpH(EZOCircuit):
    """pH EZO Circuit Controller"""
    
    def __init__(self, bus_number=1, address=0x63):
        super().__init__(bus_number, address, "pH")
        
        # Standard calibration solutions
        self.cal_solutions = {
            'low': 4.0,
            'mid': 7.0,
            'high': 10.0
        }
    
    def calibrate_mid(self, value=None):
        """
        Calibrate at mid-point (typically pH 7.0)
        
        Args:
            value: Calibration solution pH value (default: 7.0)
        """
        if value is None:
            value = self.cal_solutions['mid']
        
        command = f"Cal,mid,{value:.2f}"
        response = self.send_command(command, response_time=0.9)
        
        if response is not None:
            logger.info(f"pH mid-point calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH mid-point calibration at {value:.2f}: Failed")
            return False
    
    def calibrate_low(self, value=None):
        """
        Calibrate at low-point (typically pH 4.0)
        
        Args:
            value: Calibration solution pH value (default: 4.0)
        """
        if value is None:
            value = self.cal_solutions['low']
        
        command = f"Cal,low,{value:.2f}"
        response = self.send_command(command, response_time=0.9)
        
        if response is not None:
            logger.info(f"pH low-point calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH low-point calibration at {value:.2f}: Failed")
            return False
    
    def calibrate_high(self, value=None):
        """
        Calibrate at high-point (typically pH 10.0)
        
        Args:
            value: Calibration solution pH value (default: 10.0)
        """
        if value is None:
            value = self.cal_solutions['high']
        
        command = f"Cal,high,{value:.2f}"
        response = self.send_command(command, response_time=0.9)
        
        if response is not None:
            logger.info(f"pH high-point calibration at {value:.2f}: Success")
            return True
        else:
            logger.error(f"pH high-point calibration at {value:.2f}: Failed")
            return False
    
    def clear_calibration(self):
        """Clear all calibration data"""
        response = self.send_command("Cal,clear", response_time=0.9)
        
        if response is not None:
            logger.info("pH calibration cleared")
            return True
        else:
            logger.error("Failed to clear pH calibration")
            return False
    
    def get_calibration_status(self):
        """
        Get calibration status
        Returns number of calibration points (0, 1, 2, or 3)
        """
        response = self.send_command("Cal,?")
        if response:
            try:
                # Response format: "?Cal,n" where n is number of points
                cal_count = int(response.split(',')[1])
                logger.debug(f"pH calibration points: {cal_count}")
                return cal_count
            except:
                logger.error(f"Invalid calibration status response: {response}")
                return None
        return None
    
    def set_temperature_compensation(self, temp_c):
        """
        Set temperature compensation value
        
        Args:
            temp_c: Temperature in Celsius (0-100)
        """
        if not 0 <= temp_c <= 100:
            logger.error(f"Invalid temperature: {temp_c}°C (must be 0-100)")
            return False
        
        command = f"T,{temp_c:.1f}"
        response = self.send_command(command)
        
        if response is not None:
            logger.info(f"pH temperature compensation set to {temp_c:.1f}°C")
            return True
        return False


class EZOEC(EZOCircuit):
    """EC EZO Circuit Controller"""
    
    def __init__(self, bus_number=1, address=0x64):
        super().__init__(bus_number, address, "EC")
        
        # Standard calibration solutions (μS/cm)
        self.cal_solutions = {
            'dry': 0,
            'single': 1413,
            'low': 84,
            'high': 1413
        }
        
        # Configure outputs on connection
        self._configured = False
    
    def connect(self):
        """Connect and configure EC circuit"""
        if super().connect():
            self._configure_outputs()
            return True
        return False
    
    def _configure_outputs(self):
        """Configure EC circuit to output only EC value"""
        if self._configured:
            return
        
        try:
            # Enable EC output
            self.send_command("O,EC,1")
            # Disable TDS output
            self.send_command("O,TDS,0")
            # Disable salinity output
            self.send_command("O,S,0")
            # Disable specific gravity output
            self.send_command("O,SG,0")
            
            self._configured = True
            logger.info("EC outputs configured (EC only)")
        except Exception as e:
            logger.error(f"Failed to configure EC outputs: {e}")
    
    def read(self):
        """
        Read EC value
        Returns EC in mS/cm (EZO returns μS/cm, we convert to mS/cm)
        """
        response = self.send_command("R")
        if response:
            try:
                # EZO returns μS/cm, convert to mS/cm
                ec_us = float(response)
                ec_ms = ec_us / 1000.0  # Convert μS/cm to mS/cm
                return ec_ms
            except ValueError:
                logger.error(f"EC: Invalid reading '{response}'")
                return None
        return None
    
    def calibrate_dry(self):
        """Calibrate dry (air) reading"""
        response = self.send_command("Cal,dry", response_time=0.9)
        
        if response is not None:
            logger.info("EC dry calibration: Success")
            return True
        else:
            logger.error("EC dry calibration: Failed")
            return False
    
    def calibrate_single(self, value=None):
        """
        Single point calibration
        
        Args:
            value: Calibration solution EC in μS/cm (default: 1413)
        """
        if value is None:
            value = self.cal_solutions['single']
        
        command = f"Cal,{value}"
        response = self.send_command(command, response_time=0.9)
        
        if response is not None:
            logger.info(f"EC single-point calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC single-point calibration at {value} μS/cm: Failed")
            return False
    
    def calibrate_low(self, value=None):
        """
        Two-point calibration - low point
        
        Args:
            value: Calibration solution EC in μS/cm (default: 84)
        """
        if value is None:
            value = self.cal_solutions['low']
        
        command = f"Cal,low,{value}"
        response = self.send_command(command, response_time=0.9)
        
        if response is not None:
            logger.info(f"EC low-point calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC low-point calibration at {value} μS/cm: Failed")
            return False
    
    def calibrate_high(self, value=None):
        """
        Two-point calibration - high point
        
        Args:
            value: Calibration solution EC in μS/cm (default: 1413)
        """
        if value is None:
            value = self.cal_solutions['high']
        
        command = f"Cal,high,{value}"
        response = self.send_command(command, response_time=0.9)
        
        if response is not None:
            logger.info(f"EC high-point calibration at {value} μS/cm: Success")
            return True
        else:
            logger.error(f"EC high-point calibration at {value} μS/cm: Failed")
            return False
    
    def clear_calibration(self):
        """Clear all calibration data"""
        response = self.send_command("Cal,clear", response_time=0.9)
        
        if response is not None:
            logger.info("EC calibration cleared")
            return True
        else:
            logger.error("Failed to clear EC calibration")
            return False
    
    def get_calibration_status(self):
        """
        Get calibration status
        Returns calibration state (0=uncalibrated, 1=single, 2=dual)
        """
        response = self.send_command("Cal,?")
        if response:
            try:
                # Response format: "?Cal,n" where n is calibration state
                cal_state = int(response.split(',')[1])
                logger.debug(f"EC calibration state: {cal_state}")
                return cal_state
            except:
                logger.error(f"Invalid calibration status response: {response}")
                return None
        return None
    
    def set_probe_type(self, k_value):
        """
        Set EC probe K value
        
        Args:
            k_value: K constant (0.1, 1.0, or 10.0)
        """
        if k_value not in [0.1, 1.0, 10.0]:
            logger.error(f"Invalid K value: {k_value} (must be 0.1, 1.0, or 10.0)")
            return False
        
        command = f"K,{k_value}"
        response = self.send_command(command)
        
        if response is not None:
            logger.info(f"EC probe K value set to {k_value}")
            return True
        return False
    
    def set_temperature_compensation(self, temp_c):
        """
        Set temperature compensation value
        
        Args:
            temp_c: Temperature in Celsius (0-100)
        """
        if not 0 <= temp_c <= 100:
            logger.error(f"Invalid temperature: {temp_c}°C (must be 0-100)")
            return False
        
        command = f"T,{temp_c:.1f}"
        response = self.send_command(command)
        
        if response is not None:
            logger.info(f"EC temperature compensation set to {temp_c:.1f}°C")
            return True
        return False


class PHECController:
    """Combined pH and EC controller for easy management"""
    
    def __init__(self, bus_number=1, ph_address=0x63, ec_address=0x64):
        self.ph = EZOpH(bus_number, ph_address)
        self.ec = EZOEC(bus_number, ec_address)
        
        self.latest_readings = {
            'ph': None,
            'ec': None,
            'last_update': 0
        }
    
    def connect(self):
        """Connect to both pH and EC circuits"""
        ph_ok = self.ph.connect()
        ec_ok = self.ec.connect()
        
        if ph_ok and ec_ok:
            logger.info("✓ Both pH and EC sensors connected")
            return True
        elif ph_ok:
            logger.warning("⚠ Only pH sensor connected")
            return True
        elif ec_ok:
            logger.warning("⚠ Only EC sensor connected")
            return True
        else:
            logger.error("✗ Failed to connect to pH/EC sensors")
            return False
    
    def close(self):
        """Close both connections"""
        self.ph.close()
        self.ec.close()
    
    def read_sensors(self):
        """Read both pH and EC sensors and update latest readings"""
        ph_value = self.ph.read()
        ec_value = self.ec.read()
        
        if ph_value is not None:
            self.latest_readings['ph'] = ph_value
        
        if ec_value is not None:
            self.latest_readings['ec'] = ec_value
        
        if ph_value is not None or ec_value is not None:
            self.latest_readings['last_update'] = time.time()
        
        return {
            'ph': ph_value,
            'ec': ec_value,
            'timestamp': time.time()
        }
    
    def get_latest_readings(self):
        """Get the latest cached readings"""
        return self.latest_readings.copy()
    
    def get_status(self):
        """Get status of both sensors"""
        return {
            'ph': {
                'info': self.ph.get_info(),
                'calibration': self.ph.get_calibration_status()
            },
            'ec': {
                'info': self.ec.get_info(),
                'calibration': self.ec.get_calibration_status()
            }
        }


# ============================================================================
# TEST/DEMO CODE
# ============================================================================

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Atlas Scientific EZO pH/EC Controller")
    print("Direct I2C Communication on Raspberry Pi")
    print("=" * 60)
    print()
    
    # Create controller
    controller = PHECController(bus_number=1, ph_address=0x63, ec_address=0x64)
    
    # Connect to sensors
    print("Connecting to sensors...")
    if not controller.connect():
        print("✗ Failed to connect to sensors")
        print("  Make sure:")
        print("  - Atlas Scientific isolation shield is connected")
        print("  - pH sensor is at I2C address 0x63")
        print("  - EC sensor is at I2C address 0x64")
        print("  - I2C is enabled on your Pi")
        exit(1)
    
    print()
    
    # Get sensor info
    print("Sensor Information:")
    print("-" * 60)
    status = controller.get_status()
    print(f"pH Sensor: {status['ph']['info']}")
    print(f"pH Calibration Points: {status['ph']['calibration']}")
    print(f"EC Sensor: {status['ec']['info']}")
    print(f"EC Calibration State: {status['ec']['calibration']}")
    print()
    
    # Simple menu for testing
    print("Commands:")
    print("  1. Read sensors")
    print("  2. pH calibration menu")
    print("  3. EC calibration menu")
    print("  4. Continuous monitoring")
    print("  q. Quit")
    print()
    
    try:
        while True:
            choice = input("Enter command: ").strip()
            
            if choice == '1':
                # Read sensors
                print("\nReading sensors...")
                readings = controller.read_sensors()
                if readings['ph'] is not None:
                    print(f"  pH: {readings['ph']:.2f}")
                else:
                    print("  pH: Error reading")
                
                if readings['ec'] is not None:
                    print(f"  EC: {readings['ec']:.2f} mS/cm")
                else:
                    print("  EC: Error reading")
                print()
            
            elif choice == '2':
                # pH calibration menu
                print("\npH Calibration Menu:")
                print("  1. Mid-point (7.0)")
                print("  2. Low-point (4.0)")
                print("  3. High-point (10.0)")
                print("  4. Clear calibration")
                print("  5. Check calibration status")
                cal_choice = input("Enter choice: ").strip()
                
                if cal_choice == '1':
                    controller.ph.calibrate_mid()
                elif cal_choice == '2':
                    controller.ph.calibrate_low()
                elif cal_choice == '3':
                    controller.ph.calibrate_high()
                elif cal_choice == '4':
                    controller.ph.clear_calibration()
                elif cal_choice == '5':
                    points = controller.ph.get_calibration_status()
                    print(f"  Calibration points: {points}")
                print()
            
            elif choice == '3':
                # EC calibration menu
                print("\nEC Calibration Menu:")
                print("  1. Dry calibration")
                print("  2. Single-point (1413 μS/cm)")
                print("  3. Low-point (84 μS/cm)")
                print("  4. High-point (1413 μS/cm)")
                print("  5. Clear calibration")
                print("  6. Check calibration status")
                cal_choice = input("Enter choice: ").strip()
                
                if cal_choice == '1':
                    controller.ec.calibrate_dry()
                elif cal_choice == '2':
                    controller.ec.calibrate_single()
                elif cal_choice == '3':
                    controller.ec.calibrate_low()
                elif cal_choice == '4':
                    controller.ec.calibrate_high()
                elif cal_choice == '5':
                    controller.ec.clear_calibration()
                elif cal_choice == '6':
                    state = controller.ec.get_calibration_status()
                    state_names = {0: "Uncalibrated", 1: "Single-point", 2: "Two-point"}
                    print(f"  Calibration state: {state_names.get(state, 'Unknown')}")
                print()
            
            elif choice == '4':
                # Continuous monitoring
                print("\nContinuous Monitoring (Ctrl+C to stop)")
                print("Reading every 2 seconds...")
                print()
                try:
                    while True:
                        readings = controller.read_sensors()
                        ph_str = f"{readings['ph']:.2f}" if readings['ph'] else "---"
                        ec_str = f"{readings['ec']:.2f}" if readings['ec'] else "---"
                        print(f"pH: {ph_str}  |  EC: {ec_str} mS/cm", end='\r')
                        time.sleep(2)
                except KeyboardInterrupt:
                    print("\nStopped monitoring")
                    print()
            
            elif choice.lower() == 'q':
                break
            
            else:
                print("Invalid choice\n")
    
    finally:
        print("\nClosing connections...")
        controller.close()
        print("Done!")
