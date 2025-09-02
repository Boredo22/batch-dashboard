#!/usr/bin/env python3
"""
Atlas EZO Pump I2C Address Reassignment Script
Reassigns 8 pumps to addresses 11-18

Current addresses from i2cdetect: 5, 8, 10, 11, 12, 13, 14, 103
Target addresses: 11-18
"""

import smbus2
import time

def send_ezo_command(address, command, delay=0.3):
    """
    Send command to Atlas EZO pump using raw I2C method
    (equivalent to Arduino Wire library)
    """
    try:
        bus = smbus2.SMBus(1)
        
        # Send command using raw I2C (like Arduino Wire)
        msg = smbus2.i2c_msg.write(address, list(command.encode()))
        bus.i2c_rdwr(msg)
        
        time.sleep(delay)
        
        # Try to read response (may not work after address change due to reboot)
        try:
            msg = smbus2.i2c_msg.read(address, 32)
            bus.i2c_rdwr(msg)
            data = list(msg)
            response_code = data[0]
            if response_code == 1:
                response_text = ''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip()
                return True, response_text
        except:
            # Expected behavior after address change - pump reboots
            pass
            
        bus.close()
        return True, "Command sent (pump rebooting)"
        
    except Exception as e:
        return False, str(e)

def verify_pump_at_address(address):
    """Check if a pump responds at the given address"""
    success, response = send_ezo_command(address, "i")
    return success and "PMP" in response

def main():
    # Current pump addresses (from your i2cdetect output)
    current_addresses = [5, 8, 10, 11, 12, 13, 14, 103]  # decimal values
    target_addresses = list(range(11, 19))  # 11-18
    
    print("Atlas EZO Pump Address Reassignment")
    print("=" * 40)
    print(f"Current addresses: {current_addresses}")
    print(f"Target addresses:  {target_addresses}")
    print()
    
    # First, verify all pumps are present
    print("Verifying current pumps...")
    verified_pumps = []
    for addr in current_addresses:
        if verify_pump_at_address(addr):
            print(f"✓ Pump found at address {addr}")
            verified_pumps.append(addr)
        else:
            print(f"✗ No pump response at address {addr}")
    
    if len(verified_pumps) != 8:
        print(f"\nWarning: Expected 8 pumps, found {len(verified_pumps)}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print(f"\nProceeding with {len(verified_pumps)} pumps")
    print()
    
    # Strategy: Reassign in order that avoids conflicts
    # Start with pumps that need to move to higher addresses
    reassignments = []
    for i, current_addr in enumerate(verified_pumps):
        new_addr = target_addresses[i]
        reassignments.append((current_addr, new_addr))
    
    # Sort to minimize conflicts (higher target addresses first when possible)
    reassignments.sort(key=lambda x: x[1], reverse=True)
    
    print("Reassignment plan:")
    for current, new in reassignments:
        print(f"  Address {current:3d} → {new:3d}")
    print()
    
    input("Press Enter to start reassignment...")
    print()
    
    # Perform reassignments
    success_count = 0
    for current_addr, new_addr in reassignments:
        print(f"Changing address {current_addr} to {new_addr}...")
        
        # Send I2C address change command
        success, response = send_ezo_command(current_addr, f"I2C,{new_addr}")
        
        if success:
            print(f"✓ Command sent successfully")
            success_count += 1
            
            # Give extra time for reboot
            print("  Waiting for pump to reboot...")
            time.sleep(2.0)
            
            # Try to verify at new address
            if verify_pump_at_address(new_addr):
                print(f"✓ Pump confirmed at new address {new_addr}")
            else:
                print(f"⚠ Could not verify pump at new address {new_addr}")
                print("  (This may be normal - try scanning again)")
        else:
            print(f"✗ Failed to send command: {response}")
        
        print()
    
    print("Reassignment Complete!")
    print("=" * 40)
    print(f"Successfully sent commands to {success_count}/{len(reassignments)} pumps")
    print()
    print("Recommended next steps:")
    print("1. Wait 30 seconds for all pumps to fully reboot")
    print("2. Run: sudo i2cdetect -y 1")
    print("3. Verify pumps appear at addresses 11-18")
    print()
    print("Note: If some pumps don't appear in i2cdetect, try:")
    print("python3 -c \"")
    print("import smbus2")
    print("bus = smbus2.SMBus(1)")
    print("for addr in range(11, 19):")
    print("    try:")
    print("        bus.read_byte(addr)")
    print("        print(f'Pump at address {addr}')")
    print("    except: pass")
    print("bus.close()\"")

if __name__ == "__main__":
    main()