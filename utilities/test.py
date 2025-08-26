#!/usr/bin/env python3
"""
Simple Relay Test - GPIO 26 through ULN2803A
Quick test to verify your relay setup is working
"""

import lgpio
import time
import sys

def test_relay():
    """Test relay connected to GPIO 26"""
    gpio_pin = 26
    
    print("🔧 Simple Relay Test")
    print("=" * 25)
    print(f"Testing GPIO {gpio_pin} → ULN2803A → Relay")
    print("🔊 Listen for relay clicking sounds...")
    print()
    
    try:
        # Open GPIO
        h = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(h, gpio_pin)
        
        print("⚡ Starting with relay OFF...")
        lgpio.gpio_write(h, gpio_pin, 0)  # LOW = OFF with ULN2803A
        time.sleep(2)
        
        # Test cycle
        for cycle in range(3):
            print(f"🔄 Test cycle {cycle + 1}/3")
            
            print("   🟢 Turning relay ON (GPIO HIGH)")
            lgpio.gpio_write(h, gpio_pin, 1)  # HIGH = ON with ULN2803A
            print("      🔊 You should hear a CLICK now!")
            time.sleep(3)
            
            print("   🔴 Turning relay OFF (GPIO LOW)")
            lgpio.gpio_write(h, gpio_pin, 0)  # LOW = OFF with ULN2803A
            print("      🔊 You should hear another CLICK now!")
            time.sleep(2)
            print()
        
        print("✅ Test completed successfully!")
        print("If you heard clicking sounds, your setup is working!")
        
        # Cleanup
        lgpio.gpio_free(h, gpio_pin)
        lgpio.gpiochip_close(h)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        print("Check your connections and try again.")
        return False

def manual_control():
    """Manual relay control"""
    gpio_pin = 26
    
    print("🎮 Manual Relay Control")
    print("=" * 25)
    print("Commands:")
    print("  'on' or '1'  - Turn relay ON")
    print("  'off' or '0' - Turn relay OFF") 
    print("  'quit' or 'q' - Exit")
    print()
    
    try:
        # Open GPIO
        h = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(h, gpio_pin)
        
        # Start with relay OFF
        lgpio.gpio_write(h, gpio_pin, 0)
        relay_state = False
        print(f"🔴 Relay is OFF (GPIO {gpio_pin} = LOW)")
        
        while True:
            try:
                command = input("\nEnter command: ").lower().strip()
                
                if command in ['quit', 'q', 'exit']:
                    break
                elif command in ['on', '1']:
                    lgpio.gpio_write(h, gpio_pin, 1)
                    relay_state = True
                    print(f"🟢 Relay is ON (GPIO {gpio_pin} = HIGH)")
                elif command in ['off', '0']:
                    lgpio.gpio_write(h, gpio_pin, 0)
                    relay_state = False
                    print(f"🔴 Relay is OFF (GPIO {gpio_pin} = LOW)")
                else:
                    print("❓ Unknown command. Use: on/off/quit")
                    
            except KeyboardInterrupt:
                break
        
        # Ensure relay is OFF before exit
        print("\n🔴 Turning relay OFF before exit...")
        lgpio.gpio_write(h, gpio_pin, 0)
        
        # Cleanup
        lgpio.gpio_free(h, gpio_pin)
        lgpio.gpiochip_close(h)
        
        print("✅ Manual control ended")
        return True
        
    except Exception as e:
        print(f"❌ Error in manual control: {e}")
        return False

def check_setup():
    """Check basic setup"""
    print("🔍 Setup Verification")
    print("=" * 20)
    print("Before testing, verify these connections:")
    print()
    print("📋 Checklist:")
    print("  ✅ ULN2803A Pin 9 (GND) → Pi GND")
    print("  ✅ ULN2803A Pin 10 (VCC) → External 5V supply")
    print("  ✅ Pi GPIO 26 → ULN2803A input pin")
    print("  ✅ ULN2803A output pin → Relay IN")
    print("  ✅ Relay board VCC → External 5V supply")
    print("  ✅ Relay board GND → Common ground")
    print("  ✅ External 5V supply is ON")
    print()
    
    response = input("All connections verified? (y/n): ").lower()
    return response == 'y'

def main():
    """Main test menu"""
    print("🧪 GPIO 26 Relay Test Utility")
    print("=" * 30)
    
    if not check_setup():
        print("❌ Please verify connections before testing")
        return
    
    while True:
        print("\nChoose test mode:")
        print("1. Automatic Test (3 on/off cycles)")
        print("2. Manual Control (you control on/off)")
        print("3. Quit")
        
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                success = test_relay()
                if success:
                    print("\n🎉 Your relay setup is working!")
                else:
                    print("\n⚠️  Check your wiring if you didn't hear clicks")
                    
            elif choice == "2":
                manual_control()
                
            elif choice == "3":
                print("👋 Goodbye!")
                break
                
            else:
                print("❓ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n\n👋 Test interrupted")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()