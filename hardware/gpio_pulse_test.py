#!/usr/bin/env python3
"""
Simple GPIO Pulse Detection Test
Tests basic GPIO input and pulse detection functionality

This script will help debug optocoupler connections and GPIO setup
"""

import time
import signal
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import lgpio
    MOCK_MODE = False
    print("✓ Using real lgpio library")
except ImportError:
    print("⚠️  lgpio not available - using mock mode")
    from hardware.mock_hardware_libs import lgpio
    MOCK_MODE = True

from config import FLOW_METER_GPIO_PINS, FLOW_METER_NAMES

# Global variables
h = None
running = True
pulse_counts = {}
last_pulse_times = {}

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running, h
    print("\n🛑 Stopping GPIO test...")
    running = False
    cleanup_gpio()
    sys.exit(0)

def pulse_callback(chip, gpio, level, tick, meter_id):
    """Callback for GPIO pulse detection"""
    global pulse_counts, last_pulse_times
    
    current_time = time.time()
    
    if meter_id not in pulse_counts:
        pulse_counts[meter_id] = 0
    
    pulse_counts[meter_id] += 1
    
    # Calculate time since last pulse
    time_diff = 0
    if meter_id in last_pulse_times:
        time_diff = current_time - last_pulse_times[meter_id]
    
    last_pulse_times[meter_id] = current_time
    
    meter_name = FLOW_METER_NAMES.get(meter_id, f"Meter {meter_id}")
    
    print(f"🌊 PULSE! {meter_name} (GPIO {gpio}): Count={pulse_counts[meter_id]}, "
          f"Level={level}, Time since last={time_diff:.3f}s")

def cleanup_gpio():
    """Clean up GPIO resources"""
    global h
    if h is not None:
        try:
            # Close the GPIO chip
            lgpio.gpiochip_close(h)
            h = None
            print("✓ GPIO cleanup completed")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def test_gpio_basic_read(gpio_pin):
    """Test basic GPIO pin reading"""
    global h
    
    if h is None:
        return False
        
    try:
        # Read current level
        level = lgpio.gpio_read(h, gpio_pin)
        return level
    except Exception as e:
        print(f"❌ Error reading GPIO {gpio_pin}: {e}")
        return None

def main():
    global h, running, pulse_counts
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("🧪 GPIO PULSE DETECTION TEST")
    print(f"   Mode: {'MOCK HARDWARE' if MOCK_MODE else 'REAL HARDWARE'}")
    print("=" * 70)
    print()
    
    if MOCK_MODE:
        print("⚠️  Running in mock mode - no real GPIO testing possible")
        print("   Install lgpio with: pip install lgpio")
        return
    
    try:
        # Initialize GPIO
        print("🔧 Initializing GPIO...")
        h = lgpio.gpiochip_open(0)
        print("✓ GPIO chip opened successfully")
        
        # Configure and test each flow meter GPIO pin
        callbacks = {}
        
        for meter_id, gpio_pin in FLOW_METER_GPIO_PINS.items():
            meter_name = FLOW_METER_NAMES.get(meter_id, f"Meter {meter_id}")
            
            print(f"\n📍 Setting up {meter_name} on GPIO {gpio_pin}...")
            
            try:
                # Configure as input with pull-up resistor
                lgpio.gpio_claim_input(h, gpio_pin, lgpio.SET_PULL_UP)
                print(f"  ✓ GPIO {gpio_pin} configured as input with pull-up")
                
                # Test basic reading
                initial_level = test_gpio_basic_read(gpio_pin)
                if initial_level is not None:
                    print(f"  ✓ Initial level: {initial_level} ({'HIGH' if initial_level else 'LOW'})")
                else:
                    print(f"  ❌ Cannot read GPIO {gpio_pin}")
                    continue
                
                # Setup interrupt callback for FALLING edge (typical for optocouplers)
                callback_id = lgpio.callback(h, gpio_pin, lgpio.FALLING_EDGE,
                                           lambda chip, gpio, level, tick, mid=meter_id: pulse_callback(chip, gpio, level, tick, mid))
                
                callbacks[meter_id] = callback_id
                pulse_counts[meter_id] = 0
                
                print(f"  ✓ Interrupt callback setup for FALLING edge")
                
            except Exception as e:
                print(f"  ❌ Error setting up GPIO {gpio_pin}: {e}")
                continue
        
        if not callbacks:
            print("\n❌ No GPIO pins configured successfully!")
            return
        
        print(f"\n✓ Successfully configured {len(callbacks)} flow meter GPIO pins")
        print("\n" + "=" * 70)
        print("💡 TESTING INSTRUCTIONS:")
        print("   1. Turn on water flow through your flow meters")
        print("   2. Watch for pulse messages above")
        print("   3. Check that optocoupler LED is blinking")
        print("   4. Verify GPIO levels change with flow")
        print("   5. Press Ctrl+C to stop")
        print("=" * 70)
        print()
        
        # Main monitoring loop
        last_status_time = time.time()
        
        while running:
            current_time = time.time()
            
            # Print status every 5 seconds
            if current_time - last_status_time >= 5.0:
                print(f"\n📊 STATUS UPDATE - {time.strftime('%H:%M:%S')}")
                
                for meter_id, gpio_pin in FLOW_METER_GPIO_PINS.items():
                    meter_name = FLOW_METER_NAMES.get(meter_id, f"Meter {meter_id}")
                    count = pulse_counts.get(meter_id, 0)
                    
                    # Read current GPIO level
                    current_level = test_gpio_basic_read(gpio_pin)
                    level_str = "HIGH" if current_level else "LOW" if current_level is not None else "ERROR"
                    
                    print(f"  {meter_name:15s} (GPIO {gpio_pin:2d}): {count:4d} pulses, Level: {level_str}")
                
                last_status_time = current_time
                print()
            
            time.sleep(0.1)  # Small delay
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        cleanup_gpio()
        sys.exit(1)

if __name__ == "__main__":
    main()