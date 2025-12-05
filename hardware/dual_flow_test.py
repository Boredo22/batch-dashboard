#!/usr/bin/env python3
"""
Dual Flow Meter Pulse Counter Test
Tests both flow meters simultaneously with live LED and pulse count feedback
Run this script to verify pulses are coming in from both flow meters

Usage:
  python dual_flow_test.py [duration_seconds]

Example:
  python dual_flow_test.py 30    # Run for 30 seconds
"""

import sys
import time
import signal
import platform
from datetime import datetime

# Setup import paths
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import lgpio
    MOCK_MODE = False
except ImportError:
    if platform.system() == 'Windows':
        print("Running on Windows - using mock mode for testing")
        from hardware.mock_hardware_libs import lgpio
        MOCK_MODE = True
    else:
        print("lgpio not installed. Install with: pip install lgpio")
        sys.exit(1)

from config import FLOW_METER_GPIO_PINS, FLOW_METER_NAMES, FLOW_METER_CALIBRATION

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

# GPIO handle
h = None

# Pulse counters for each flow meter
pulse_counts = {
    1: 0,
    2: 0
}

# Test control
running = True
start_time = None

# =============================================================================
# PULSE INTERRUPT HANDLERS
# =============================================================================

def pulse_callback_meter_1(chip, gpio, level, tick):
    """Callback for flow meter 1 pulses"""
    global pulse_counts
    pulse_counts[1] += 1
    elapsed = time.time() - start_time
    print(f"💧 METER 1: Pulse #{pulse_counts[1]:4d} | {elapsed:6.1f}s | {FLOW_METER_NAMES[1]}")

def pulse_callback_meter_2(chip, gpio, level, tick):
    """Callback for flow meter 2 pulses"""
    global pulse_counts
    pulse_counts[2] += 1
    elapsed = time.time() - start_time
    print(f"🌊 METER 2: Pulse #{pulse_counts[2]:4d} | {elapsed:6.1f}s | {FLOW_METER_NAMES[2]}")

# =============================================================================
# GPIO SETUP & CLEANUP
# =============================================================================

def setup_gpio():
    """Initialize GPIO pins and callbacks for both flow meters"""
    global h

    try:
        # Open GPIO chip
        h = lgpio.gpiochip_open(0)
        print(f"✅ GPIO chip opened")

        # Setup Flow Meter 1
        pin1 = FLOW_METER_GPIO_PINS[1]
        lgpio.gpio_claim_input(h, pin1, lgpio.SET_PULL_UP)
        cb1 = lgpio.callback(h, pin1, lgpio.RISING_EDGE, pulse_callback_meter_1)
        print(f"✅ Flow Meter 1 ({FLOW_METER_NAMES[1]}) configured on GPIO {pin1}")

        # Setup Flow Meter 2
        pin2 = FLOW_METER_GPIO_PINS[2]
        lgpio.gpio_claim_input(h, pin2, lgpio.SET_PULL_UP)
        cb2 = lgpio.callback(h, pin2, lgpio.RISING_EDGE, pulse_callback_meter_2)
        print(f"✅ Flow Meter 2 ({FLOW_METER_NAMES[2]}) configured on GPIO {pin2}")

        return cb1, cb2

    except Exception as e:
        print(f"❌ Error setting up GPIO: {e}")
        cleanup()
        sys.exit(1)

def cleanup():
    """Clean up GPIO resources"""
    global h

    print("\n🛑 Cleaning up GPIO...")

    if h is not None:
        try:
            # Free both GPIO pins
            for meter_id in FLOW_METER_GPIO_PINS:
                pin = FLOW_METER_GPIO_PINS[meter_id]
                try:
                    lgpio.gpio_free(h, pin)
                except:
                    pass

            # Close GPIO chip
            lgpio.gpiochip_close(h)
            h = None
            print("✅ GPIO cleanup complete")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\n⚠️ Interrupt received...")
    running = False

# =============================================================================
# DISPLAY & CALCULATIONS
# =============================================================================

def print_header():
    """Print test header"""
    print("=" * 80)
    print("🌊 DUAL FLOW METER PULSE COUNTER TEST")
    print("=" * 80)
    print(f"Mode: {'MOCK' if MOCK_MODE else 'REAL HARDWARE'}")
    print()
    print(f"Flow Meter 1: {FLOW_METER_NAMES[1]:20s} | GPIO {FLOW_METER_GPIO_PINS[1]:2d} | {FLOW_METER_CALIBRATION[1]} PPG")
    print(f"Flow Meter 2: {FLOW_METER_NAMES[2]:20s} | GPIO {FLOW_METER_GPIO_PINS[2]:2d} | {FLOW_METER_CALIBRATION[2]} PPG")
    print()
    print("💡 Both flow meters are being monitored simultaneously")
    print("💡 LEDs should blink on each pulse (if connected)")
    print("💡 Press Ctrl+C to stop")
    print("=" * 80)
    print()

def print_status(elapsed_time):
    """Print current pulse counts and statistics"""
    print("\n" + "=" * 80)
    print(f"📊 TEST RESULTS - {elapsed_time:.1f} seconds elapsed")
    print("=" * 80)

    for meter_id in [1, 2]:
        pulses = pulse_counts[meter_id]
        ppg = FLOW_METER_CALIBRATION[meter_id]
        gallons = pulses / ppg

        # Calculate flow rate (gallons per minute)
        gpm = (gallons / elapsed_time * 60) if elapsed_time > 0 else 0

        # Calculate pulse rate (pulses per minute)
        ppm = (pulses / elapsed_time * 60) if elapsed_time > 0 else 0

        print(f"\nFlow Meter {meter_id} ({FLOW_METER_NAMES[meter_id]}):")
        print(f"  Total Pulses:     {pulses:6d}")
        print(f"  Total Volume:     {gallons:6.3f} gallons")
        print(f"  Flow Rate:        {gpm:6.2f} GPM")
        print(f"  Pulse Rate:       {ppm:6.1f} pulses/min")

    # Summary
    total_pulses = pulse_counts[1] + pulse_counts[2]
    print(f"\nTotal Pulses (both meters): {total_pulses:6d}")

    # Diagnostics
    if total_pulses == 0:
        print("\n⚠️ WARNING: No pulses detected on either meter!")
        print("   Troubleshooting:")
        print("   1. Check that water is flowing through the meters")
        print("   2. Verify voltage divider connections (24V → 3.3V)")
        print("   3. Check GPIO wiring (GPIO 24 and GPIO 23)")
        print("   4. Verify LEDs are blinking (visual confirmation)")
        print("   5. Check flow meter power supply (24V)")
    elif pulse_counts[1] == 0:
        print(f"\n⚠️ WARNING: No pulses on Meter 1 ({FLOW_METER_NAMES[1]})")
    elif pulse_counts[2] == 0:
        print(f"\n⚠️ WARNING: No pulses on Meter 2 ({FLOW_METER_NAMES[2]})")
    else:
        print("\n✅ SUCCESS! Both flow meters are detecting pulses!")

    print("=" * 80)

# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

def main():
    """Main test function"""
    global running, start_time

    # Get test duration from command line
    duration = 30  # Default 30 seconds
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("❌ Error: Duration must be a number")
            sys.exit(1)

    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Print header
    print_header()

    # Setup GPIO
    print("🔧 Initializing GPIO pins...")
    callbacks = setup_gpio()
    print()

    # Start test
    print(f"🚀 Starting {duration} second test...")
    print(f"⏰ Test will automatically stop at {datetime.now().strftime('%H:%M:%S')}")
    print()
    print("📋 LIVE PULSE LOG (newest first):")
    print("-" * 80)

    start_time = time.time()

    try:
        # Main monitoring loop
        while running and (time.time() - start_time) < duration:
            time.sleep(0.1)  # Small delay to prevent CPU spinning

        # Test complete
        elapsed_time = time.time() - start_time

        # Print final results
        print("\n" + "-" * 80)
        print_status(elapsed_time)

    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
