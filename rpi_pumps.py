#!/usr/bin/env python3
"""
EZO Pump I2C Control for Raspberry Pi
Simple replacement for Arduino Mega pump functionality
"""

import time
import logging

try:
    import smbus2 as smbus
except ImportError:
    print("smbus2 not installed. Install with: pip install smbus2")
    exit(1)

logger = logging.getLogger(__name__)

class EZOPumpController:
    def __init__(self, i2c_bus=1):
        """Initialize I2C bus for EZO pumps"""
        self.i2c_bus = smbus.SMBus(i2c_bus)
        self.pumps = {}
        
        # Initialize pump tracking
        for addr in range(1, 9):  # Pumps 1-8
            self.pumps[addr] = {
                'name': f'Pump {addr}',
                'status': 0,  # 0=idle, 1=active
                'current_volume': 0.0,
                'target_volume': 0.0,
                'is_dispensing': False,
                'voltage': 0.0,
                'calibrated': False,
                'last_check': 0
            }
    
    def send_command(self, pump_addr, command):
        """Send command to EZO pump via I2C"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Send command
                command_bytes = command.encode('utf-8')
                self.i2c_bus.write_i2c_block_data(pump_addr, 0, list(command_bytes))
                
                # Wait for processing
                time.sleep(0.3)
                
                # Read response
                response_bytes = self.i2c_bus.read_i2c_block_data(pump_addr, 0, 32)
                
                # Convert to string and clean up
                response = ''.join([chr(b) for b in response_bytes if b > 0 and b != 255]).strip()
                
                logger.debug(f"Pump {pump_addr} response: {response}")
                return response
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"I2C retry {retry_count}/{max_retries} for pump {pump_addr}: {e}")
                # Space out retries by a few seconds
                time.sleep(2.0 * retry_count)  # Increasing delay with each retry
                
        logger.error(f"I2C communication failed after {max_retries} retries for pump {pump_addr}")
        return "ERROR"
    
    def parse_volume(self, response):
        """Parse volume from EZO pump response"""
        # Clean up the response - remove non-numeric chars except decimal and minus
        cleaned = ''.join(c for c in response.strip() if c.isdigit() or c in '.-')
        
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0
    
    def start_dispense(self, pump_addr, amount):
        """Start dispensing from pump"""
        if pump_addr not in self.pumps or amount <= 0:
            return False
            
        pump = self.pumps[pump_addr]
        
        # Check if already dispensing
        if pump['is_dispensing']:
            logger.warning(f"Pump {pump_addr} already dispensing")
            return False
        
        # Send dispense command
        command = f"D,{amount}"
        response = self.send_command(pump_addr, command)
        
        if response != "ERROR":
            pump['status'] = 1
            pump['is_dispensing'] = True
            pump['target_volume'] = amount
            pump['current_volume'] = 0.0
            pump['last_check'] = time.time()
            
            logger.info(f"Started dispensing {amount}ml from pump {pump_addr}")
            return True
        
        return False
    
    def stop_pump(self, pump_addr):
        """Stop pump operation"""
        if pump_addr not in self.pumps:
            return False
            
        response = self.send_command(pump_addr, "X")
        
        if response != "ERROR":
            pump = self.pumps[pump_addr]
            pump['status'] = 0
            pump['is_dispensing'] = False
            pump['target_volume'] = 0
            pump['current_volume'] = 0
            
            logger.info(f"Stopped pump {pump_addr}")
            return True
        
        return False
    
    def get_volume(self, pump_addr):
        """Get current dispensed volume"""
        if pump_addr not in self.pumps:
            return 0.0
            
        response = self.send_command(pump_addr, "R")
        if response != "ERROR":
            return self.parse_volume(response)
        
        return 0.0
    
    def check_pump_status(self, pump_addr):
        """Check if pump has finished dispensing"""
        if pump_addr not in self.pumps:
            return False
            
        pump = self.pumps[pump_addr]
        
        if not pump['is_dispensing']:
            return False
            
        # Get current volume
        current_volume = self.get_volume(pump_addr)
        pump['current_volume'] = current_volume
        
        # Check if finished (within tolerance)
        tolerance = 0.1
        finished = (current_volume + tolerance) >= pump['target_volume']
        
        if finished:
            self.stop_pump(pump_addr)
            logger.info(f"Pump {pump_addr} finished: {current_volume}/{pump['target_volume']} ml")
            
        return not finished  # Return True if still dispensing
    
    def calibrate_pump(self, pump_addr, amount):
        """Calibrate pump"""
        if pump_addr not in self.pumps:
            return False
            
        command = f"Cal,{amount}"
        response = self.send_command(pump_addr, command)
        
        if response != "ERROR":
            self.pumps[pump_addr]['calibrated'] = True
            logger.info(f"Calibrated pump {pump_addr} with {amount}ml")
            return True
        
        return False
    
    def get_pump_info(self, pump_addr):
        """Get pump information"""
        if pump_addr not in self.pumps:
            return None
            
        pump = self.pumps[pump_addr]
        
        # Get voltage if pump is idle
        if not pump['is_dispensing']:
            response = self.send_command(pump_addr, "PV,?")
            if response != "ERROR" and "," in response:
                try:
                    pump['voltage'] = float(response.split(",")[1])
                except:
                    pass
        
        return pump.copy()
    
    def get_all_pumps_status(self):
        """Get status of all pumps"""
        return {addr: self.get_pump_info(addr) for addr in self.pumps}
    
    def emergency_stop(self):
        """Stop all pumps immediately"""
        for pump_addr in self.pumps:
            self.stop_pump(pump_addr)
        logger.warning("Emergency stop - all pumps stopped")
    
    def close(self):
        """Close I2C bus"""
        try:
            self.emergency_stop()
            self.i2c_bus.close()
        except:
            pass


# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    controller = EZOPumpController()
    
    print("EZO Pump Controller Test")
    print("1. Testing pump communication...")
    
    for pump_addr in range(1, 9):
        info = controller.get_pump_info(pump_addr)
        print(f"Pump {pump_addr}: {info}")
    
    print("\n2. Test dispense (pump 1, 5ml)...")
    if controller.start_dispense(1, 5.0):
        print("Dispense started")
        
        # Monitor progress
        for i in range(10):
            still_running = controller.check_pump_status(1)
            info = controller.get_pump_info(1)
            print(f"  Progress: {info['current_volume']:.2f}/{info['target_volume']:.2f} ml")
            
            if not still_running:
                print("  Dispense completed!")
                break
                
            time.sleep(1)
    else:
        print("Failed to start dispense")
    
    controller.close()