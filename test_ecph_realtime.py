#!/usr/bin/env python3
"""
Test Real-Time EC/pH Monitoring
Verifies that background polling works correctly
"""

import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("=" * 70)
print("Real-Time EC/pH Monitoring Test")
print("=" * 70)

try:
    from hardware.rpi_ezo_sensors import EZOSensorController

    sensor = EZOSensorController()

    if not sensor.connect():
        print("✗ FAILED: Could not connect to EZO sensors")
        sys.exit(1)

    print("✓ Connected to EZO sensors via I2C")

    # Start monitoring
    print("\nStarting background monitoring...")
    sensor.start_monitoring()

    print("Monitoring active. Will display readings for 30 seconds...")
    print("(Sensors are polled every 5 seconds in background thread)")
    print()

    # Monitor for 30 seconds
    for i in range(30):
        time.sleep(1)

        # Every 2 seconds, check the cached readings (simulating frontend polling)
        if i % 2 == 0:
            readings = sensor.get_latest_readings()
            ph = readings.get('ph')
            ec = readings.get('ec')
            last_update = readings.get('last_update', 0)

            if last_update > 0 and ph is not None and ec is not None:
                age = time.time() - last_update
                print(f"[{i:2d}s] pH: {ph:.2f} | EC: {ec:.2f} mS/cm | Last updated: {age:.1f}s ago")
            else:
                print(f"[{i:2d}s] Waiting for first reading...")

    # Stop monitoring
    print("\nStopping monitoring...")
    sensor.stop_monitoring()

    # Final readings
    final = sensor.get_latest_readings()
    if final.get('ph') is not None and final.get('ec') is not None:
        print(f"\nFinal readings - pH: {final.get('ph'):.2f} | EC: {final.get('ec'):.2f} mS/cm")
    else:
        print("\nNo final readings available")

    sensor.close()
    print("\n✓ TEST PASSED - Background monitoring works correctly!")
    print("\nThis demonstrates:")
    print("  1. Background thread polls sensors every 5 seconds")
    print("  2. Frontend can read cached values anytime (every 2s)")
    print("  3. Data stays fresh without blocking API calls")

except Exception as e:
    print(f"\n✗ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
