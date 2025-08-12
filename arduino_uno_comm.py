#!/usr/bin/env python3
"""
Arduino Uno Communication for EC/pH Sensors
Handles serial communication with Arduino Uno running EC/pH monitoring
"""

import serial
import time
import threading
import logging
import re
from queue import Queue, Empty

logger = logging.getLogger(__name__)

class ArduinoUnoController:
    def __init__(self, port="/dev/ttyACM1", baudrate=115200):
        """Initialize Arduino Uno serial communication"""
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.reader_thread = None
        
        # Data storage
        self.latest_readings = {
            'ec': None,
            'ph': None,
            'last_update': 0
        }
        
        # Message queue for callbacks
        self.message_queue = Queue()
        self.message_callback = None
        
        # Connect to Arduino
        self.connect()
    
    def connect(self):
        """Connect to Arduino Uno"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            
            # Wait for connection to stabilize
            time.sleep(2)
            self.serial_conn.reset_input_buffer()
            
            logger.info(f"Connected to Arduino Uno on {self.port}")
            
            # Start reader thread
            self.running = True
            self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self.reader_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Arduino Uno: {e}")
            return False
    
    def _reader_loop(self):
        """Continuously read from Arduino Uno"""
        while self.running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        logger.debug(f"Uno: {line}")
                        self._parse_message(line)
                        
                        # Queue message for callback
                        if self.message_callback:
                            self.message_queue.put(line)
                            
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Error reading from Arduino Uno: {e}")
                time.sleep(1)
            
            time.sleep(0.05)  # Small delay to prevent CPU hogging
    
    def _parse_message(self, message):
        """Parse messages from Arduino Uno"""
        # EC reading: Start;Update;Ec;value;end
        ec_match = re.search(r'Start;Update;Ec;([0-9.]+);end', message)
        if ec_match:
            try:
                ec_value = float(ec_match.group(1))
                self.latest_readings['ec'] = ec_value
                self.latest_readings['last_update'] = time.time()
                logger.debug(f"EC reading: {ec_value} mS/cm")
            except ValueError:
                logger.warning(f"Invalid EC value: {ec_match.group(1)}")
        
        # pH reading: Start;Update;Ph;value;end
        ph_match = re.search(r'Start;Update;Ph;([0-9.]+);end', message)
        if ph_match:
            try:
                ph_value = float(ph_match.group(1))
                self.latest_readings['ph'] = ph_value
                self.latest_readings['last_update'] = time.time()
                logger.debug(f"pH reading: {ph_value}")
            except ValueError:
                logger.warning(f"Invalid pH value: {ph_match.group(1)}")
    
    def send_command(self, command):
        """Send command to Arduino Uno"""
        if not self.serial_conn:
            logger.error("Arduino Uno not connected")
            return False
        
        try:
            # Add line ending if not present
            if not command.endswith('\n'):
                command += '\n'
            
            self.serial_conn.write(command.encode())
            self.serial_conn.flush()
            
            logger.debug(f"Sent to Uno: {command.strip()}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending command to Arduino Uno: {e}")
            return False
    
    def start_monitoring(self):
        """Start EC/pH monitoring"""
        return self.send_command("Start;EcPh;ON;end")
    
    def stop_monitoring(self):
        """Stop EC/pH monitoring"""
        return self.send_command("Start;EcPh;OFF;end")
    
    def calibrate_ph(self, cal_type, value=None):
        """Calibrate pH sensor"""
        if cal_type in ['mid', 'low', 'high'] and value:
            command = f"Start;PhCal;{cal_type};{value};end"
        elif cal_type == 'clear':
            command = f"Start;PhCal;clear;;end"
        else:
            logger.error(f"Invalid pH calibration type: {cal_type}")
            return False
        
        return self.send_command(command)
    
    def calibrate_ec(self, cal_type, value=None):
        """Calibrate EC sensor"""
        if cal_type == 'dry':
            command = "Start;EcCal;dry;;end"
        elif cal_type in ['low', 'one', 'single'] and value:
            command = f"Start;EcCal;{cal_type};{value};end"
        elif cal_type == 'clear':
            command = "Start;EcCal;clear;;end"
        else:
            logger.error(f"Invalid EC calibration type: {cal_type}")
            return False
        
        return self.send_command(command)
    
    def get_latest_readings(self):
        """Get latest EC/pH readings"""
        return self.latest_readings.copy()
    
    def get_ec_reading(self):
        """Get latest EC reading"""
        return self.latest_readings.get('ec')
    
    def get_ph_reading(self):
        """Get latest pH reading"""
        return self.latest_readings.get('ph')
    
    def is_connected(self):
        """Check if Arduino Uno is connected"""
        return self.serial_conn is not None and not self.serial_conn.closed
    
    def set_message_callback(self, callback):
        """Set callback for incoming messages"""
        self.message_callback = callback
    
    def get_queued_messages(self):
        """Get all queued messages"""
        messages = []
        try:
            while True:
                messages.append(self.message_queue.get_nowait())
        except Empty:
            pass
        return messages
    
    def get_connection_status(self):
        """Get connection status info"""
        return {
            "connected": self.is_connected(),
            "port": self.port,
            "running": self.running,
            "latest_readings": self.latest_readings
        }
    
    def close(self):
        """Close connection to Arduino Uno"""
        logger.info("Closing Arduino Uno connection...")
        
        # Stop monitoring first
        if self.is_connected():
            self.stop_monitoring()
            time.sleep(0.5)
        
        # Stop reader thread
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2)
        
        # Close serial connection
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None
        
        logger.info("Arduino Uno connection closed")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.close()
        except:
            pass


# Auto-detect Arduino Uno port
def find_arduino_uno_port():
    """Try to automatically find Arduino Uno port"""
    import serial.tools.list_ports
    
    # Look for common Arduino patterns
    for port in serial.tools.list_ports.comports():
        port_desc = str(port.description).lower()
        port_hwid = getattr(port, 'hwid', '')
        
        # Look for Arduino Uno patterns
        if ('arduino' in port_desc and 'uno' in port_desc) or 'VID:PID=2341:0043' in port_hwid:
            return port.device
    
    # Fallback to common ports
    common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    for port in common_ports:
        try:
            # Try to open the port briefly
            test_serial = serial.Serial(port, 115200, timeout=0.5)
            test_serial.close()
            return port
        except:
            continue
    
    return None


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Try to find Arduino Uno port automatically
    uno_port = find_arduino_uno_port()
    if not uno_port:
        print("Arduino Uno not found. Using default port /dev/ttyACM1")
        uno_port = "/dev/ttyACM1"
    
    print(f"Arduino Uno EC/pH Controller Test")
    print(f"Attempting to connect to: {uno_port}")
    
    controller = ArduinoUnoController(port=uno_port)
    
    if controller.is_connected():
        print("✓ Connected to Arduino Uno")
        
        # Set up message callback
        def message_handler(message):
            print(f"Message: {message}")
        
        controller.set_message_callback(message_handler)
        
        print("\n1. Starting EC/pH monitoring...")
        controller.start_monitoring()
        
        print("2. Reading values for 30 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 30:
            readings = controller.get_latest_readings()
            
            ec = readings.get('ec', 'No reading')
            ph = readings.get('ph', 'No reading')
            last_update = readings.get('last_update', 0)
            
            age = time.time() - last_update if last_update > 0 else 999
            
            print(f"  EC: {ec} mS/cm, pH: {ph} (age: {age:.1f}s)")
            
            # Process any queued messages
            messages = controller.get_queued_messages()
            for msg in messages:
                print(f"  Raw: {msg}")
            
            time.sleep(2)
        
        print("\n3. Stopping monitoring...")
        controller.stop_monitoring()
        
        print("4. Final readings:")
        final_readings = controller.get_latest_readings()
        print(f"  EC: {final_readings.get('ec')} mS/cm")
        print(f"  pH: {final_readings.get('ph')}")
        
    else:
        print("✗ Failed to connect to Arduino Uno")
        print("Check:")
        print("  - Arduino Uno is connected")
        print("  - Correct port in code")
        print("  - User has permission to access serial port")
        print(f"  - Try: sudo usermod -a -G dialout $USER")
    
    controller.close()
    print("Test completed")