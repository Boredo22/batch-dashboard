#!/usr/bin/env python3
"""
Atlas EZO Pump Physical Position Mapper
Tests each pump individually to identify physical positions,
then reassigns addresses so 11-18 go left to right on the wall.
"""

import smbus2
import time

def send_ezo_command(address, command, delay=0.3):
    """
    Send command to Atlas EZO pump using raw I2C method
    """
    try:
        bus = smbus2.SMBus(1)
        
        # Send command using raw I2C 
        msg = smbus2.i2c_msg.write(address, list(command.encode()))
        bus.i2c_rdwr(msg)
        
        time.sleep(delay)
        
        # Try to read response
        try:
            msg = smbus2.i2c_msg.read(address, 32)
            bus.i2c_rdwr(msg)
            data = list(msg)
            response_code = data[0]
            if response_code == 1:
                response_text = ''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip()
                return True, response_text
        except:
            pass
            
        bus.close()
        return True, "Command sent"
        
    except Exception as e:
        return False, str(e)

def verify_pump_at_address(address):
    """Check if a pump responds at the given address"""
    success, response = send_ezo_command(address, "i")
    return success and "PMP" in response

def dispense_test_amount(address, volume_ml=10):
    """Start dispensing test volume"""
    command = f"D,{volume_ml:.1f}"
    return send_ezo_command(address, command)

def stop_dispensing(address):
    """Stop dispensing"""
    return send_ezo_command(address, "X")

def get_valid_position_input():
    """Get valid position input from user (1-8)"""
    while True:
        try:
            pos = input("Which position is dispensing? (1-8, left to right): ").strip()
            position = int(pos)
            if 1 <= position <= 8:
                return position
            else:
                print("Please enter a number between 1 and 8")
        except ValueError:
            print("Please enter a valid number")

def main():
    print("Atlas EZO Pump Physical Position Mapper")
    print("=" * 50)
    print("This script will test each pump individually to map physical positions.")
    print("After mapping, addresses will be reassigned so 11-18 go left-to-right.")
    print()
    
    # Expected pump addresses from previous script
    pump_addresses = list(range(11, 19))  # 11-18
    
    # Verify all pumps are present
    print("Verifying pumps at addresses 11-18...")
    active_pumps = []
    for addr in pump_addresses:
        if verify_pump_at_address(addr):
            print(f"✓ Pump found at address {addr}")
            active_pumps.append(addr)
        else:
            print(f"✗ No pump at address {addr}")
    
    if len(active_pumps) != 8:
        print(f"\nError: Expected 8 pumps, found {len(active_pumps)}")
        print("Please ensure all pumps are connected and at addresses 11-18")
        return
    
    print(f"\nAll 8 pumps verified!")
    print()
    
    # Mapping phase
    address_to_position = {}  # Maps address -> physical position (1-8)
    position_to_address = {}  # Maps physical position -> current address
    
    print("=== MAPPING PHASE ===")
    print("Instructions:")
    print("- Each pump will dispense 10ml for identification")
    print("- Enter which physical position (1-8, counting left to right) is dispensing")
    print("- The pump will automatically stop after you enter the position")
    print()
    
    input("Press Enter when ready to start mapping...")
    print()
    
    for i, addr in enumerate(active_pumps, 1):
        print(f"Testing pump {i}/8 at address {addr}")
        print("-" * 30)
        
        # Start dispensing
        success, response = dispense_test_amount(addr, 10)
        if not success:
            print(f"✗ Failed to start dispensing on address {addr}: {response}")
            continue
        
        print(f"✓ Started 10ml dispense on address {addr}")
        print("Look at your pump array...")
        
        # Get user input for position
        position = get_valid_position_input()
        
        # Stop dispensing
        stop_success, stop_response = stop_dispensing(addr)
        if stop_success:
            print(f"✓ Stopped dispensing on address {addr}")
        else:
            print(f"⚠ Warning: Could not confirm stop on address {addr}")
        
        # Record mapping
        address_to_position[addr] = position
        position_to_address[position] = addr
        
        print(f"✓ Mapped: Address {addr} = Position {position}")
        print()
        
        # Small delay before next pump
        if i < len(active_pumps):
            time.sleep(1)
    
    # Display mapping results
    print("=== MAPPING RESULTS ===")
    print("Current Address -> Physical Position")
    for addr in sorted(address_to_position.keys()):
        pos = address_to_position[addr]
        print(f"    Address {addr:2d} -> Position {pos}")
    print()
    
    print("Physical Position -> Current Address")
    for pos in sorted(position_to_address.keys()):
        addr = position_to_address[pos]
        print(f"    Position {pos} -> Address {addr:2d}")
    print()
    
    # Calculate required reassignments
    print("=== REASSIGNMENT PLAN ===")
    target_addresses = list(range(11, 19))  # 11-18
    reassignments = []
    
    print("Target: Position -> Address")
    for pos in range(1, 9):
        target_addr = target_addresses[pos - 1]  # Position 1 -> Address 11, etc.
        current_addr = position_to_address[pos]
        print(f"    Position {pos} -> Address {target_addr}")
        
        if current_addr != target_addr:
            reassignments.append((current_addr, target_addr))
    
    print()
    if not reassignments:
        print("🎉 Perfect! All pumps are already in correct positions!")
        print("No reassignment needed.")
        return
    
    print("Required Address Changes:")
    for current, target in reassignments:
        current_pos = address_to_position[current]
        print(f"    Address {current:2d} (Position {current_pos}) -> Address {target:2d}")
    print()
    
    # Safety check for conflicts
    current_addresses = [addr for addr, _ in reassignments]
    target_addresses_needed = [addr for _, addr in reassignments]
    conflicts = set(current_addresses) & set(target_addresses_needed)
    
    if conflicts:
        print("⚠ Address conflicts detected. Using safe reassignment order...")
        # Sort by target address descending to minimize conflicts
        reassignments.sort(key=lambda x: x[1], reverse=True)
    
    # Confirm before proceeding
    print("This will reassign pump addresses so that:")
    print("Address 11 = Position 1 (leftmost)")
    print("Address 12 = Position 2")
    print("...")
    print("Address 18 = Position 8 (rightmost)")
    print()
    
    confirm = input("Proceed with reassignment? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Reassignment cancelled.")
        return
    
    print()
    print("=== REASSIGNMENT PHASE ===")
    
    # Perform reassignments
    for i, (current_addr, target_addr) in enumerate(reassignments, 1):
        current_pos = address_to_position[current_addr]
        print(f"Step {i}/{len(reassignments)}: Changing address {current_addr} (Position {current_pos}) to {target_addr}...")
        
        success, response = send_ezo_command(current_addr, f"I2C,{target_addr}")
        if success:
            print(f"✓ Command sent successfully")
            print("  Waiting for pump to reboot...")
            time.sleep(2.0)
            
            # Verify at new address  
            if verify_pump_at_address(target_addr):
                print(f"✓ Pump confirmed at new address {target_addr}")
            else:
                print(f"⚠ Could not immediately verify pump at address {target_addr}")
        else:
            print(f"✗ Failed to send command: {response}")
        
        print()
    
    print("=== REASSIGNMENT COMPLETE ===")
    print("Final address mapping should be:")
    for pos in range(1, 9):
        addr = 10 + pos  # Position 1 = Address 11, etc.
        print(f"  Position {pos} (left to right) = Address {addr}")
    
    print()
    print("Verification commands:")
    print("1. sudo i2cdetect -y 1")
    print("2. Test a pump: python3 -c \"")
    print("   import smbus2, time")
    print("   bus = smbus2.SMBus(1)")
    print("   msg = smbus2.i2c_msg.write(11, list(b'i'))  # Test address 11")
    print("   bus.i2c_rdwr(msg)")
    print("   time.sleep(0.3)")
    print("   msg = smbus2.i2c_msg.read(11, 32)")
    print("   bus.i2c_rdwr(msg)")
    print("   data = list(msg)")
    print("   if data[0] == 1: print(''.join([chr(x) for x in data[1:] if 32 <= x <= 126]).strip())")
    print("   bus.close()\"")

if __name__ == "__main__":
    main()