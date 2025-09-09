#!/usr/bin/env python3
"""
Flow Meter Pulse Test Script
Tests GPIO 24 for flow meter pulses using voltage divider
"""

import lgpio
import time
import signal
import sys

# Configuration
GPIO_PIN = 24  # Your flow meter GPIO pin
TEST_DURATION = 30  # Test for 30 seconds

# Global variables
h = None
pulse_count = 0
start_time = None

def pulse_callback(chip, gpio, level, tick):
    """Callback function for each pulse"""
    global pulse_count, start_time
    pulse_count += 1
    
    # Calculate time since start
    elapsed = time.time() - start_time
    
    print(f"💧 PULSE #{pulse_count} detected! ({elapsed:.1f}s elapsed)")

def cleanup(signum=None, frame=None):
    """Clean up GPIO resources"""
    global h
    print("\n🛑 Cleaning up...")
    
    if h is not None:
        try:
            lgpio.gpio_free(h, GPIO_PIN)
            lgpio.gpiochip_close(h)
        except:
            pass
    
    print("✅ Cleanup complete")
    sys.exit(0)

def test_gpio_level():
    """Test current GPIO level"""
    try:
        level = lgpio.gpio_read(h, GPIO_PIN)
        voltage = "~3V (HIGH)" if level == 1 else "~0V (LOW)"
        print(f"📊 Current GPIO {GPIO_PIN} level: {level} ({voltage})")
        return level
    except Exception as e:
        print(f"❌ Error reading GPIO: {e}")
        return None

def main():
    """Main test function"""
    global h, start_time
    
    print("🌊 Flow Meter Pulse Test")
    print("=" * 40)
    print(f"📍 GPIO Pin: {GPIO_PIN}")
    print(f"⏱️  Test Duration: {TEST_DURATION} seconds")
    print(f"🔧 Setup: 24V → Voltage Divider → GPIO {GPIO_PIN}")
    print()
    
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Initialize GPIO
        print("🔌 Initializing GPIO...")
        h = lgpio.gpiochip_open(0)
        
        # Configure GPIO as input with pull-up
        lgpio.gpio_claim_input(h, GPIO_PIN, lgpio.SET_PULL_UP)
        print(f"✅ GPIO {GPIO_PIN} configured as input with pull-up")
        
        # Test current level
        print("\n🔍 Testing current GPIO state...")
        initial_level = test_gpio_level()
        
        if initial_level is None:
            print("❌ Cannot read GPIO level - check connections!")
            cleanup()
            return
        
        # Set up interrupt callback for FALLING edge (pulse detection)
        print(f"\n⚡ Setting up interrupt on FALLING edge...")
        callback_id = lgpio.callback(h, GPIO_PIN, lgpio.FALLING_EDGE, pulse_callback)
        print(f"✅ Interrupt callback registered")
        
        print(f"\n🎯 STARTING PULSE DETECTION...")
        print(f"💡 Expectations:")
        print(f"   • Idle state: GPIO reads HIGH (~3V)")
        print(f"   • Pulse state: GPIO reads LOW (~0V)")
        print(f"   • Trigger: FALLING edge (HIGH → LOW)")
        print()
        print(f"🚰 Now test your flow meter:")
        print(f"   • Turn on water/pump")
        print(f"   • Manually spin the impeller")
        print(f"   • Tap the sensor gently")
        print()
        
        start_time = time.time()
        
        # Monitor for pulses
        for seconds in range(TEST_DURATION):
            remaining = TEST_DURATION - seconds
            print(f"\r⏳ Monitoring... {remaining:2d}s remaining | Pulses: {pulse_count:4d}", end="", flush=True)
            
            # Check GPIO level every 5 seconds
            if seconds % 5 == 0 and seconds > 0:
                print()  # New line
                test_gpio_level()
            
            time.sleep(1)
        
        print()  # Final newline
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        print("🔧 Check your wiring:")
        print("   • GPIO 24 connected to voltage divider junction?")
        print("   • Ground shared between Pi and power supply?")
        print("   • Flow meter signal connected to voltage divider?")
    
    finally:
        # Final results
        elapsed_time = time.time() - start_time if start_time else 0
        print(f"\n📈 TEST RESULTS:")
        print(f"   • Total Pulses: {pulse_count}")
        print(f"   • Test Duration: {elapsed_time:.1f} seconds")
        if pulse_count > 0 and elapsed_time > 0:
            rate = pulse_count / elapsed_time * 60  # pulses per minute
            gallons_per_minute = rate / 220  # assuming 220 pulses/gallon
            print(f"   • Pulse Rate: {rate:.1f} pulses/minute")
            print(f"   • Flow Rate: {gallons_per_minute:.2f} gallons/minute")
        
        if pulse_count == 0:
            print("\n🤔 No pulses detected. Troubleshooting:")
            print("   1. Check voltage at junction point (should be ~3V)")
            print("   2. Manually test flow sensor (spin/tap)")
            print("   3. Verify wiring connections")
            print("   4. Check if flow meter is powered")
        else:
            print(f"\n🎉 SUCCESS! Flow meter is working!")
        
        cleanup()

if __name__ == "__main__":
    main()