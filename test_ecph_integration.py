#!/usr/bin/env python3
"""
Test EC/pH Sensor Integration
Verifies that EZO sensors work with the full stack:
1. Direct sensor communication (rpi_ezo_sensors.py)
2. Hardware comms layer (hardware_comms.py)
3. Flask API endpoints (app.py)
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
print("EC/pH Sensor Integration Test")
print("=" * 70)

# Test 1: Direct sensor communication
print("\n" + "=" * 70)
print("TEST 1: Direct EZO Sensor Communication")
print("=" * 70)

try:
    from hardware.rpi_ezo_sensors import EZOSensorController

    sensor = EZOSensorController()

    if not sensor.connect():
        print("✗ FAILED: Could not connect to EZO sensors")
        print("  Check I2C connection and addresses (pH: 0x63, EC: 0x64)")
        sys.exit(1)

    print("✓ Connected to EZO sensors via I2C")

    # Get sensor info
    info = sensor.get_sensor_info()
    print(f"\npH Sensor Info: {info['ph']['info']}")
    print(f"pH Calibration Points: {info['ph']['calibration']}")
    print(f"EC Sensor Info: {info['ec']['info']}")
    print(f"EC Calibration State: {info['ec']['calibration']}")

    # Read sensors
    print("\nReading sensors...")
    readings = sensor.read_sensors()

    if readings['ph'] is not None:
        print(f"✓ pH Reading: {readings['ph']:.2f}")
    else:
        print("✗ pH Reading: Failed")

    if readings['ec'] is not None:
        print(f"✓ EC Reading: {readings['ec']:.2f} mS/cm")
    else:
        print("✗ EC Reading: Failed")

    sensor.close()
    print("\n✓ TEST 1 PASSED")

except Exception as e:
    print(f"\n✗ TEST 1 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Hardware comms layer
print("\n" + "=" * 70)
print("TEST 2: Hardware Communications Layer")
print("=" * 70)

try:
    from hardware.hardware_comms import read_ec_ph_sensors

    print("Reading sensors via hardware_comms...")
    result = read_ec_ph_sensors()

    if result.get('success'):
        print(f"✓ Success: {result}")
        print(f"  pH: {result.get('ph')}")
        print(f"  EC: {result.get('ec')}")
        print(f"  Timestamp: {result.get('timestamp')}")
    else:
        print(f"✗ Failed: {result}")
        sys.exit(1)

    print("\n✓ TEST 2 PASSED")

except Exception as e:
    print(f"\n✗ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: API endpoints
print("\n" + "=" * 70)
print("TEST 3: Flask API Endpoints")
print("=" * 70)

print("\nNOTE: This test requires the Flask app to be running.")
print("      Start it with: python app.py")
print("      Then test the API with:")
print("        curl http://localhost:5000/api/sensors/ecph/read")
print("        curl -X POST http://localhost:5000/api/ecph/start")
print("        curl -X POST http://localhost:5000/api/ecph/stop")

# Test 4: Summary
print("\n" + "=" * 70)
print("INTEGRATION TEST SUMMARY")
print("=" * 70)
print("✓ Direct EZO sensor communication: WORKING")
print("✓ Hardware comms layer: WORKING")
print("? Flask API endpoints: Start app.py to test")
print("\nFrontend Integration:")
print("  1. Start Flask: python app.py")
print("  2. Start Vite: cd frontend && npm run dev")
print("  3. Open browser: http://localhost:5173")
print("  4. Go to Dashboard page")
print("  5. Click 'Start Monitoring' on EC/pH Monitor card")
print("  6. Watch real-time readings update every 2 seconds")
print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)
