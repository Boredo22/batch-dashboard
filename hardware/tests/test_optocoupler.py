#!/usr/bin/env python3
"""
Quick test for optocoupler flow meter setup
Tests the 817 optocoupler module with VFS1001 flow meter
"""

import time
import sys

try:
    import lgpio
except ImportError:
    print("ERROR: lgpio not installed. Install with: pip install lgpio")
    sys.exit(1)

# Configuration
FLOW_GPIO = 24  # Flow meter 1 on GPIO 24
pulse_count = 0

def pulse_detected(chip, gpio, level, tick):
    """Callback for flow meter pulses"""
    global pulse_count
    pulse_count += 1

def main():
    global pulse_count

    print("=" * 60)
    print("Flow Meter Optocoupler Test")
    print("=" * 60)
    print(f"GPIO Pin: {FLOW_GPIO}")
    print("Edge Detection: FALLING (optocoupler inverts signal)")
    print("\nHardware setup:")
    print("  Flow meter 24V pulse → Optocoupler IN1")
    print("  Flow meter GND → Optocoupler input GND")
    print("  Pi 3.3V → Optocoupler middle jumper")
    print("  Optocoupler V1 → Pi GPIO 24")
    print("  Optocoupler output GND → Pi GND")
    print("\nExpected behavior:")
    print("  - Idle state: GPIO reads HIGH (pulled up)")
    print("  - Flow pulse: GPIO goes LOW (FALLING edge)")
    print("  - Optocoupler LED should flash with each pulse")
    print("=" * 60)
    print("\nRun water through the meter. Press Ctrl+C to stop.\n")

    # Setup GPIO
    h = None
    cb_id = None

    try:
        # Open GPIO chip
        h = lgpio.gpiochip_open(0)

        # Setup GPIO as input with pull-up
        lgpio.gpio_claim_input(h, FLOW_GPIO, lgpio.SET_PULL_UP)

        # Read initial state
        initial_state = lgpio.gpio_read(h, FLOW_GPIO)
        print(f"Initial GPIO state: {'HIGH' if initial_state else 'LOW'}")

        if initial_state == 0:
            print("⚠️  WARNING: GPIO is LOW when it should be HIGH!")
            print("   Check wiring and optocoupler power (3.3V jumper)")
        else:
            print("✓ GPIO is HIGH (correct idle state)")

        print()

        # Setup interrupt on FALLING edge
        cb_id = lgpio.callback(h, FLOW_GPIO, lgpio.FALLING_EDGE, pulse_detected)

        # Monitor for pulses
        last_count = 0
        last_time = time.time()

        while True:
            current_time = time.time()

            if pulse_count != last_count:
                # Calculate pulses per second
                time_diff = current_time - last_time
                pps = (pulse_count - last_count) / time_diff if time_diff > 0 else 0

                print(f"Pulses: {pulse_count:6d} (+{pulse_count - last_count:3d})  |  Rate: {pps:6.1f} pulses/sec")

                last_count = pulse_count
                last_time = current_time

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print(f"Test completed!")
        print(f"Total pulses detected: {pulse_count}")

        if pulse_count > 0:
            print("\n✓ SUCCESS: Pulses detected! Optocoupler is working correctly.")
            print("\nNext steps:")
            print("  1. Verify pulse count matches expected flow volume")
            print("  2. Check calibration (220 pulses/gallon for VFS1001)")
            print("  3. Test with main application")
        else:
            print("\n⚠️  No pulses detected. Troubleshooting:")
            print("  1. Check optocoupler LED - does it flash with water flow?")
            print("  2. Verify wiring connections")
            print("  3. Check flow meter 24V power supply")
            print("  4. Verify water is actually flowing through meter")
            print("  5. Check GPIO pin number matches config (GPIO 24)")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if cb_id is not None:
            try:
                lgpio.callback_cancel(cb_id)
            except:
                pass

        if h is not None:
            try:
                lgpio.gpio_free(h, FLOW_GPIO)
                lgpio.gpiochip_close(h)
            except:
                pass

if __name__ == "__main__":
    main()
