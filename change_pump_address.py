#!/usr/bin/env python3
"""
Simple script to change EZO pump I2C address from 103 to 17
Sends "I2C,17" command to pump at address 103
"""

import time
import logging
import platform

# Import I2C library with fallback for Windows testing
try:
    import smbus2
except ImportError:
    if platform.system() == 'Windows':
        print("Running on Windows - I2C functionality will be limited")
        smbus2 = None
    else:
        print("smbus2 not installed. Install with: pip install smbus2")
        exit(1)

# Configuration
OLD_PUMP_ADDRESS = 103
NEW_PUMP_ADDRESS = 17
I2C_BUS_NUMBER = 1  # Default I2C bus for Raspberry Pi
COMMAND_DELAY = 1.0  # Delay after sending command
MAX_RETRIES = 3
RETRY_DELAY = 0.5

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_i2c_command(bus, address, command, delay=COMMAND_DELAY):
    """
    Send command to EZO device via I2C
    
    Args:
        bus: SMBus instance
        address: I2C address of the device
        command: Command string to send
        delay: Delay after sending command
    
    Returns:
        str or None: Response from device or None if failed
    """
    if not smbus2:
        logger.error("smbus2 not available - cannot send I2C commands")
        return None
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Send command using raw I2C
            logger.info(f"Sending command '{command}' to address {address}")
            msg = smbus2.i2c_msg.write(address, list(command.encode()))
            bus.i2c_rdwr(msg)
            
            # Wait for processing
            time.sleep(delay)
            
            # Read response
            msg = smbus2.i2c_msg.read(address, 32)
            bus.i2c_rdwr(msg)
            
            data = list(msg)
            
            # Parse response
            if len(data) > 0:
                response_code = data[0]
                
                if response_code == 1:  # Success
                    response_text = ''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip()
                    logger.info(f"Command successful. Response: '{response_text}'")
                    return response_text
                elif response_code == 254:  # Still processing
                    retries += 1
                    logger.warning(f"Device still processing, retry {retries}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY)
                    continue
                elif response_code == 255:  # No data
                    logger.warning("No data response from device")
                    return "NO_DATA"
                elif response_code == 2:  # Syntax error
                    logger.error("Syntax error in command")
                    return None
                else:
                    logger.error(f"Unknown response code: {response_code}")
                    return None
            else:
                logger.warning("No response data received")
                return None
                
        except Exception as e:
            retries += 1
            logger.warning(f"Attempt {retries}/{MAX_RETRIES} failed: {e}")
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY * retries)
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed")
    
    return None

def change_pump_address():
    """
    Change EZO pump address from 103 to 17
    """
    if not smbus2:
        logger.error("Cannot proceed - smbus2 not available")
        return False
    
    try:
        # Initialize I2C bus
        logger.info(f"Initializing I2C bus {I2C_BUS_NUMBER}")
        bus = smbus2.SMBus(I2C_BUS_NUMBER)
        
        # First, verify the pump is responding at the old address
        logger.info(f"Checking if pump responds at current address {OLD_PUMP_ADDRESS}")
        info_response = send_i2c_command(bus, OLD_PUMP_ADDRESS, "i", 1.0)
        
        if info_response is None:
            logger.error(f"Pump not responding at address {OLD_PUMP_ADDRESS}")
            logger.error("Make sure:")
            logger.error("1. Pump is connected and powered")
            logger.error("2. I2C is enabled on your Raspberry Pi")
            logger.error("3. Pump is actually at address 103")
            bus.close()
            return False
        
        logger.info(f"Pump info: {info_response}")
        
        # Send the address change command
        logger.info(f"Changing pump address from {OLD_PUMP_ADDRESS} to {NEW_PUMP_ADDRESS}")
        address_cmd = f"I2C,{NEW_PUMP_ADDRESS}"
        response = send_i2c_command(bus, OLD_PUMP_ADDRESS, address_cmd, 2.0)
        
        if response is None:
            logger.error("Failed to send address change command")
            bus.close()
            return False
        
        logger.info("Address change command sent successfully!")
        
        # Wait a moment for the address change to take effect
        logger.info("Waiting for address change to take effect...")
        time.sleep(3)
        
        # Try to verify the pump now responds at the new address
        logger.info(f"Verifying pump now responds at new address {NEW_PUMP_ADDRESS}")
        try:
            verify_response = send_i2c_command(bus, NEW_PUMP_ADDRESS, "i", 1.0)
            if verify_response:
                logger.info(f"SUCCESS! Pump now responding at address {NEW_PUMP_ADDRESS}")
                logger.info(f"New pump info: {verify_response}")
            else:
                logger.warning("Could not verify pump at new address (this may be normal)")
                logger.warning("The address change command was sent successfully")
        except Exception as e:
            logger.warning(f"Could not verify new address: {e}")
            logger.warning("The address change command was sent successfully")
        
        # Close I2C bus
        bus.close()
        logger.info("I2C bus closed")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during address change: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("EZO Pump Address Change Utility")
    print("=" * 60)
    print(f"Old address: {OLD_PUMP_ADDRESS}")
    print(f"New address: {NEW_PUMP_ADDRESS}")
    print(f"Command: I2C,{NEW_PUMP_ADDRESS}")
    print("=" * 60)
    
    # Confirm before proceeding
    if platform.system() != 'Windows':
        confirm = input(f"Change pump address from {OLD_PUMP_ADDRESS} to {NEW_PUMP_ADDRESS}? (y/N): ")
        if confirm.lower() != 'y':
            print("Address change cancelled")
            return
    
    # Perform the address change
    success = change_pump_address()
    
    print("=" * 60)
    if success:
        print("✓ Address change completed successfully!")
        print(f"✓ Pump should now be at address {NEW_PUMP_ADDRESS}")
        print("✓ Update your configuration to use the new address")
    else:
        print("✗ Address change failed")
        print("✗ Check the logs above for error details")
    print("=" * 60)

if __name__ == "__main__":
    main()