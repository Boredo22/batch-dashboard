#!/usr/bin/env python3
"""
Test script to verify the refactored architecture
Tests that all components can be imported and initialized
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    logger.info("Testing imports...")

    try:
        from hardware.i2c_manager import get_i2c_manager
        logger.info("[OK] I2C manager import successful")
    except Exception as e:
        logger.error(f"[ERROR] I2C manager import failed: {e}")
        return False

    try:
        from hardware.rpi_pumps import EZOPumpController
        logger.info("[OK] Pump controller import successful")
    except Exception as e:
        logger.error(f"[ERROR] Pump controller import failed: {e}")
        return False

    try:
        from hardware.rpi_relays import RelayController
        logger.info("[OK] Relay controller import successful")
    except Exception as e:
        logger.error(f"[ERROR] Relay controller import failed: {e}")
        return False

    try:
        from hardware.rpi_flow import FlowMeterController
        logger.info("[OK] Flow meter controller import successful")
    except Exception as e:
        logger.error(f"[ERROR] Flow meter controller import failed: {e}")
        return False

    try:
        from hardware.rpi_ezo_sensors import EZOSensorController
        logger.info("[OK] EZO sensor controller import successful")
    except Exception as e:
        logger.error(f"[ERROR] EZO sensor controller import failed: {e}")
        return False

    try:
        from main import FeedControlSystem
        logger.info("[OK] FeedControlSystem import successful")
    except Exception as e:
        logger.error(f"[ERROR] FeedControlSystem import failed: {e}")
        return False

    try:
        from hardware.hardware_comms import get_hardware_comms
        logger.info("[OK] Hardware comms import successful")
    except Exception as e:
        logger.error(f"[ERROR] Hardware comms import failed: {e}")
        return False

    return True

def test_i2c_manager_singleton():
    """Test that I2C manager is a singleton"""
    logger.info("\nTesting I2C manager singleton pattern...")

    try:
        from hardware.i2c_manager import get_i2c_manager

        manager1 = get_i2c_manager()
        manager2 = get_i2c_manager()

        if manager1 is manager2:
            logger.info("[OK] I2C manager singleton working correctly")
            return True
        else:
            logger.error("[ERROR] I2C manager is not a singleton")
            return False
    except Exception as e:
        logger.error(f"[ERROR] I2C manager singleton test failed: {e}")
        return False

def test_configuration():
    """Test that configuration is correct"""
    logger.info("\nTesting configuration...")

    try:
        from config import (
            I2C_BUS_NUMBER,
            PH_SENSOR_ADDRESS,
            EC_SENSOR_ADDRESS,
            PUMP_ADDRESSES,
            get_available_pumps,
            get_available_relays,
            get_available_flow_meters
        )

        logger.info(f"  I2C Bus: {I2C_BUS_NUMBER}")
        logger.info(f"  pH Sensor: 0x{PH_SENSOR_ADDRESS:02X}")
        logger.info(f"  EC Sensor: 0x{EC_SENSOR_ADDRESS:02X}")
        logger.info(f"  Pumps: {get_available_pumps()}")
        logger.info(f"  Relays: {get_available_relays()}")
        logger.info(f"  Flow Meters: {get_available_flow_meters()}")

        logger.info("[OK] Configuration loaded successfully")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("  REFACTORING VERIFICATION TESTS")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    # Test 2: I2C Manager Singleton
    results.append(("I2C Manager Singleton", test_i2c_manager_singleton()))

    # Test 3: Configuration
    results.append(("Configuration", test_configuration()))

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:30s} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
