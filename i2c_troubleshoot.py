#!/usr/bin/env python3
"""
Stuck EZO Pump Reset Tool
Fixes pumps that always return to blinking green after power cycle
"""

import time
import sys

try:
    import smbus2 as smbus
except ImportError:
    print("smbus2 not installed. Install with: pip install smbus2")
    sys.exit(1)

class StuckPumpReset:
    def __init__(self):
        """Initialize I2C"""
        self.bus = None
        
    def open_bus(self):
        """Try to open I2C bus"""
        try:
            self.bus = smbus.SMBus(1)
            return True
        except Exception as e:
            print(f"Failed to open I2C bus: {e}")
            return False
    
    def send_command_with_retry(self, address, command, max_retries=3):
        """Send command with retries"""
        for attempt in range(max_retries):
            try:
                if not self.bus:
                    if not self.open_bus():
                        continue
                
                print(f"  Sending: {command}")
                
                # Send command
                cmd_bytes = command.encode('utf-8')
                self.bus.write_i2c_block_data(address, 0, list(cmd_bytes))
                
                # Wait for processing (EZO needs 300ms)
                time.sleep(0.4)
                
                # Try to read response
                try:
                    response_bytes = self.bus.read_i2c_block_data(address, 0, 32)
                    response = ''.join([chr(b) for b in response_bytes if b > 0 and b != 255]).strip()
                    print(f"  Response: {response}")
                    return True, response
                except:
                    print(f"  Command sent (no response expected)")
                    return True, "No response"
                    
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}")
                # Close and reopen bus
                try:
                    if self.bus:
                        self.bus.close()
                        self.bus = None
                    time.sleep(0.5)
                except:
                    pass
                    
        return False, "All attempts failed"
    
    def factory_reset_pump(self, address):
        """Factory reset the problematic pump"""
        print(f"FACTORY RESET for pump at address {address}:")
        print("=" * 45)
        
        # Commands to try in order
        reset_commands = [
            "X",           # Stop any current operation
            "Sleep",       # Put to sleep first
            "Factory",     # Factory reset - this should fix it!
        ]
        
        for cmd in reset_commands:
            success, response = self.send_command_with_retry(address, cmd)
            if not success:
                print(f"  ⚠️  Failed to send {cmd}")
            time.sleep(1)
        
        print("\n  Factory reset sent! Pump should reboot...")
        print("  Wait 5 seconds then check LED color")
        time.sleep(5)
    
    def check_startup_dispense_mode(self, address):
        """Check if pump is in startup dispense mode"""
        print(f"\nCHECKING STARTUP DISPENSE MODE:")
        print("=" * 35)
        
        # Check if pump has a startup dispense command
        success, response = self.send_command_with_retry(address, "Dstart,?")
        
        if success and "Dstart" in response:
            print(f"  Found startup mode: {response}")
            print("  This could be causing the green LED!")
            
            # Disable startup dispense
            print("  Disabling startup dispense...")
            self.send_command_with_retry(address, "Dstart,off")
            return True
        else:
            print("  No startup dispense mode found")
            return False
    
    def check_continuous_mode(self, address):
        """Check if pump is stuck in continuous dispensing"""
        print(f"\nCHECKING CONTINUOUS DISPENSE MODE:")
        print("=" * 37)
        
        # Check dispense status
        success, response = self.send_command_with_retry(address, "D,?")
        
        if success and response and response != "No response":
            print(f"  Dispense status: {response}")
            if "*" in response or "1" in response:
                print("  Pump may be in continuous mode!")
                
                # Stop dispensing
                print("  Sending stop command...")
                self.send_command_with_retry(address, "X")
                return True
        
        print("  No continuous dispensing detected")
        return False
    
    def check_pump_configuration(self, address):
        """Check various pump settings that could cause issues"""
        print(f"\nCHECKING PUMP CONFIGURATION:")
        print("=" * 32)
        
        # Check various settings
        check_commands = {
            "L,?": "LED status",
            "O,?": "Output parameters", 
            "Plock,?": "Protocol lock",
            "i": "Device info"
        }
        
        for cmd, description in check_commands.items():
            print(f"\n{description}:")
            success, response = self.send_command_with_retry(address, cmd)
            if success:
                print(f"  {response}")
    
    def comprehensive_reset(self, address):
        """Perform comprehensive reset of stuck pump"""
        print(f"COMPREHENSIVE RESET for address {address}")
        print("=" * 50)
        
        # Step 1: Try to communicate first
        print("STEP 1: Testing communication...")
        success, response = self.send_command_with_retry(address, "i")
        if not success:
            print("  ⚠️  Cannot communicate with pump - check wiring/address")
            return False
        else:
            print(f"  ✓ Communication OK: {response}")
        
        # Step 2: Stop any current operations
        print("\nSTEP 2: Stopping current operations...")
        for cmd in ["X", "Sleep"]:
            self.send_command_with_retry(address, cmd)
            time.sleep(0.5)
        
        # Step 3: Check and fix startup modes
        print("\nSTEP 3: Checking startup configurations...")
        self.check_startup_dispense_mode(address)
        self.check_continuous_mode(address)
        
        # Step 4: Factory reset
        print("\nSTEP 4: Factory reset...")
        success, response = self.send_command_with_retry(address, "Factory")
        if success:
            print("  ✓ Factory reset sent - pump should reboot")
            print("  Wait 10 seconds for reboot...")
            time.sleep(10)
        
        # Step 5: Verify reset
        print("\nSTEP 5: Verifying reset...")
        success, response = self.send_command_with_retry(address, "i")
        if success:
            print(f"  ✓ Pump responsive after reset: {response}")
            print("  Check LED - should be BLUE now!")
            return True
        else:
            print("  ⚠️  Pump not responding after reset")
            return False
    
    def scan_for_problem_pump(self):
        """Scan for the pump that might be causing issues"""
        print("SCANNING FOR PROBLEM PUMP:")
        print("=" * 30)
        
        # Common EZO pump addresses
        test_addresses = [1, 2, 3, 4, 5, 6, 7, 8, 103]  # 103 is default EZO address
        
        responsive_pumps = []
        
        for addr in test_addresses:
            try:
                if not self.bus:
                    if not self.open_bus():
                        continue
                        
                # Try to get device info
                self.bus.write_i2c_block_data(addr, 0, list(b'i'))
                time.sleep(0.4)
                
                response_bytes = self.bus.read_i2c_block_data(addr, 0, 32)
                response = ''.join([chr(b) for b in response_bytes if b > 0 and b != 255]).strip()
                
                if response and len(response) > 2:
                    responsive_pumps.append(addr)
                    print(f"  Address {addr}: {response}")
                    
            except:
                pass  # No pump at this address
        
        if responsive_pumps:
            print(f"\nFound pumps at addresses: {responsive_pumps}")
            return responsive_pumps
        else:
            print("  No pumps responding - I2C bus may still be stuck")
            return []
    
    def close(self):
        """Close I2C bus"""
        try:
            if self.bus:
                self.bus.close()
        except:
            pass

def main():
    """Main function"""
    reset_tool = StuckPumpReset()
    
    try:
        if len(sys.argv) > 1:
            # Reset specific pump
            try:
                address = int(sys.argv[1])
                print(f"Resetting pump at address {address}...")
                reset_tool.comprehensive_reset(address)
            except ValueError:
                print("Usage: python stuck_pump_reset.py [address]")
                print("Example: python stuck_pump_reset.py 103")
        else:
            # Scan and show options
            pumps = reset_tool.scan_for_problem_pump()
            
            if pumps:
                print(f"\nTo reset a specific pump, run:")
                for addr in pumps:
                    print(f"  python stuck_pump_reset.py {addr}")
            else:
                print("\nTrying broadcast reset to common addresses...")
                for addr in [1, 2, 3, 4, 5, 6, 7, 8, 103]:
                    print(f"\nTrying address {addr}...")
                    reset_tool.comprehensive_reset(addr)
                    
    except KeyboardInterrupt:
        print("\nReset interrupted")
    finally:
        reset_tool.close()

if __name__ == "__main__":
    main()