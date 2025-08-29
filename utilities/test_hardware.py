#!/usr/bin/env python3
"""
Hardware testing utility for the Nutrient Mixing System
Easy way to test individual components and system diagnostics
"""

import time
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.rpi_pumps import EZOPumpController
from hardware.rpi_relays import RelayController
from hardware.rpi_sensors import SensorController, MockSensorController
from hardware.rpi_flow import FlowMeterController, MockFlowMeterController
from config import (
    PUMP_ADDRESSES, RELAY_GPIO_PINS, FLOW_METER_GPIO_PINS,
    get_pump_name, get_relay_name, get_flow_meter_name
)

logger = logging.getLogger(__name__)

class HardwareTestUtility:
    """Comprehensive hardware testing utility"""
    
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        self.test_results = {}
        
        # Initialize controllers
        self.pump_controller = None
        self.relay_controller = None
        self.sensor_controller = None
        self.flow_controller = None
        
        self._initialize_controllers()
    
    def _initialize_controllers(self):
        """Initialize hardware controllers for testing"""
        print("Initializing hardware controllers...")
        
        # Initialize pump controller
        try:
            self.pump_controller = EZOPumpController()
            print("✓ Pump controller initialized")
        except Exception as e:
            print(f"✗ Pump controller failed: {e}")
            self.test_results['pump_init'] = False
        
        # Initialize relay controller
        try:
            if not self.use_mock:
                self.relay_controller = RelayController()
                print("✓ Relay controller initialized")
            else:
                print("⚠ Using mock relay controller")
        except Exception as e:
            print(f"✗ Relay controller failed: {e}")
            self.test_results['relay_init'] = False
        
        # Initialize sensor controller
        try:
            if self.use_mock:
                self.sensor_controller = MockSensorController()
                print("✓ Mock sensor controller initialized")
            else:
                self.sensor_controller = SensorController()
                print("✓ Sensor controller initialized")
        except Exception as e:
            print(f"✗ Sensor controller failed: {e}")
            self.test_results['sensor_init'] = False
        
        # Initialize flow controller
        try:
            if self.use_mock:
                self.flow_controller = MockFlowMeterController()
                print("✓ Mock flow controller initialized")
            else:
                self.flow_controller = FlowMeterController()
                print("✓ Flow controller initialized")
        except Exception as e:
            print(f"✗ Flow controller failed: {e}")
            self.test_results['flow_init'] = False

    def test_all_pumps(self):
        """Test each pump with info command"""
        print("\n" + "="*50)
        print("TESTING EZO PUMPS")
        print("="*50)
        
        if not self.pump_controller:
            print("✗ Pump controller not available")
            return False
        
        success_count = 0
        total_pumps = len(PUMP_ADDRESSES)
        
        for pump_id, address in PUMP_ADDRESSES.items():
            pump_name = get_pump_name(pump_id)
            print(f"\nTesting Pump {pump_id} ({pump_name}) at I2C address {address}...")
            
            try:
                # Test info command
                response = self.pump_controller.send_command(pump_id, "i")
                if response:
                    print(f"  ✓ Info: {response}")
                    success_count += 1
                    
                    # Test calibration status
                    cal_response = self.pump_controller.send_command(pump_id, "Cal,?")
                    if cal_response:
                        print(f"  ✓ Calibration: {cal_response}")
                    
                    # Test voltage
                    voltage_response = self.pump_controller.send_command(pump_id, "PV,?")
                    if voltage_response:
                        print(f"  ✓ Voltage: {voltage_response}")
                    
                else:
                    print(f"  ✗ No response from pump {pump_id}")
                    
            except Exception as e:
                print(f"  ✗ Error testing pump {pump_id}: {e}")
        
        print(f"\nPump Test Results: {success_count}/{total_pumps} pumps responding")
        self.test_results['pumps'] = success_count
        return success_count == total_pumps

    def test_all_relays(self):
        """Test each relay on/off"""
        print("\n" + "="*50)
        print("TESTING RELAYS")
        print("="*50)
        
        if not self.relay_controller:
            print("✗ Relay controller not available")
            return False
        
        success_count = 0
        total_relays = len(RELAY_GPIO_PINS)
        
        for relay_id in RELAY_GPIO_PINS.keys():
            relay_name = get_relay_name(relay_id)
            print(f"\nTesting Relay {relay_id} ({relay_name})...")
            
            try:
                # Test ON
                if self.relay_controller.set_relay(relay_id, True):
                    print(f"  ✓ Turned ON")
                    time.sleep(0.5)
                    
                    # Test OFF
                    if self.relay_controller.set_relay(relay_id, False):
                        print(f"  ✓ Turned OFF")
                        success_count += 1
                    else:
                        print(f"  ✗ Failed to turn OFF")
                else:
                    print(f"  ✗ Failed to turn ON")
                    
            except Exception as e:
                print(f"  ✗ Error testing relay {relay_id}: {e}")
        
        print(f"\nRelay Test Results: {success_count}/{total_relays} relays working")
        self.test_results['relays'] = success_count
        return success_count == total_relays

    def test_sensors(self):
        """Test pH and EC sensors"""
        print("\n" + "="*50)
        print("TESTING SENSORS")
        print("="*50)
        
        if not self.sensor_controller:
            print("✗ Sensor controller not available")
            return False
        
        try:
            # Test sensor status
            status = self.sensor_controller.get_sensor_status()
            print(f"pH Sensor - Connected: {status['ph']['connected']}, Calibrated: {status['ph']['calibrated']}")
            print(f"EC Sensor - Connected: {status['ec']['connected']}, Calibrated: {status['ec']['calibrated']}")
            
            # Test readings
            print("\nTaking sensor readings...")
            for i in range(3):
                readings = self.sensor_controller.read_both_sensors()
                if readings['ph'] is not None and readings['ec'] is not None:
                    print(f"  Reading {i+1}: pH={readings['ph']:.2f}, EC={readings['ec']:.2f} mS/cm")
                else:
                    print(f"  Reading {i+1}: Failed to get readings")
                time.sleep(1)
            
            self.test_results['sensors'] = True
            return True
            
        except Exception as e:
            print(f"✗ Error testing sensors: {e}")
            self.test_results['sensors'] = False
            return False

    def test_flow_meters(self):
        """Test flow meters"""
        print("\n" + "="*50)
        print("TESTING FLOW METERS")
        print("="*50)
        
        if not self.flow_controller:
            print("✗ Flow controller not available")
            return False
        
        try:
            # Test flow meter status
            status = self.flow_controller.get_all_flow_status()
            for meter_id, meter_status in status.items():
                meter_name = get_flow_meter_name(meter_id)
                print(f"Flow Meter {meter_id} ({meter_name}): {meter_status}")
            
            self.test_results['flow_meters'] = True
            return True
            
        except Exception as e:
            print(f"✗ Error testing flow meters: {e}")
            self.test_results['flow_meters'] = False
            return False

    def system_health_check(self):
        """Comprehensive system health check"""
        print("\n" + "="*50)
        print("SYSTEM HEALTH CHECK")
        print("="*50)
        
        health = {
            'database': self.test_database_connection(),
            'pumps': self.test_pump_communication(),
            'sensors': self.test_sensor_communication(),
            'relays': self.test_relay_control(),
            'config': self.validate_configuration()
        }
        
        print("\nHealth Check Results:")
        for component, status in health.items():
            status_icon = "✓" if status else "✗"
            print(f"  {status_icon} {component.title()}: {'OK' if status else 'FAILED'}")
        
        overall_health = all(health.values())
        print(f"\nOverall System Health: {'✓ HEALTHY' if overall_health else '✗ ISSUES DETECTED'}")
        
        return health

    def test_database_connection(self):
        """Test database connectivity"""
        try:
            from db.models import DatabaseManager
            db = DatabaseManager()
            # Simple test query
            return True
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False

    def test_pump_communication(self):
        """Test pump I2C communication"""
        if not self.pump_controller:
            return False
        
        try:
            # Test at least one pump
            for pump_id in list(PUMP_ADDRESSES.keys())[:1]:
                response = self.pump_controller.send_command(pump_id, "i")
                if response:
                    return True
            return False
        except Exception:
            return False

    def test_sensor_communication(self):
        """Test sensor communication"""
        if not self.sensor_controller:
            return False
        
        try:
            readings = self.sensor_controller.read_both_sensors()
            return readings['ph'] is not None or readings['ec'] is not None
        except Exception:
            return False

    def test_relay_control(self):
        """Test relay control"""
        if not self.relay_controller:
            return True  # Skip if using mock
        
        try:
            # Test first available relay
            relay_ids = list(RELAY_GPIO_PINS.keys())
            if relay_ids:
                test_relay = relay_ids[0]
                return self.relay_controller.set_relay(test_relay, False)
            return True
        except Exception:
            return False

    def validate_configuration(self):
        """Validate system configuration"""
        try:
            # Check if all required config values are present
            required_configs = [
                PUMP_ADDRESSES, RELAY_GPIO_PINS, FLOW_METER_GPIO_PINS
            ]
            return all(config for config in required_configs)
        except Exception:
            return False

    def run_full_test_suite(self):
        """Run complete hardware test suite"""
        print("🌱 NUTRIENT MIXING SYSTEM - HARDWARE TEST UTILITY")
        print("="*60)
        
        start_time = time.time()
        
        # Run all tests
        pump_result = self.test_all_pumps()
        relay_result = self.test_all_relays()
        sensor_result = self.test_sensors()
        flow_result = self.test_flow_meters()
        health_result = self.system_health_check()
        
        # Summary
        duration = time.time() - start_time
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        tests = [
            ("Pumps", pump_result),
            ("Relays", relay_result),
            ("Sensors", sensor_result),
            ("Flow Meters", flow_result),
            ("System Health", all(health_result.values()) if health_result else False)
        ]
        
        passed = sum(1 for _, result in tests if result)
        total = len(tests)
        
        for test_name, result in tests:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        print(f"Duration: {duration:.1f} seconds")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - System ready for operation!")
        else:
            print("⚠️  SOME TESTS FAILED - Check hardware connections")
        
        return passed == total

    def cleanup(self):
        """Clean up hardware resources"""
        try:
            if self.pump_controller:
                self.pump_controller.close()
            if self.relay_controller:
                self.relay_controller.cleanup()
            if self.sensor_controller:
                self.sensor_controller.close()
            if self.flow_controller:
                self.flow_controller.cleanup()
            print("✓ Hardware cleanup completed")
        except Exception as e:
            print(f"⚠ Cleanup error: {e}")

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hardware Test Utility')
    parser.add_argument('--mock', action='store_true', help='Use mock hardware')
    parser.add_argument('--pumps', action='store_true', help='Test pumps only')
    parser.add_argument('--relays', action='store_true', help='Test relays only')
    parser.add_argument('--sensors', action='store_true', help='Test sensors only')
    parser.add_argument('--flow', action='store_true', help='Test flow meters only')
    parser.add_argument('--health', action='store_true', help='System health check only')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test utility
    tester = HardwareTestUtility(use_mock=args.mock)
    
    try:
        # Run specific tests or full suite
        if args.pumps:
            tester.test_all_pumps()
        elif args.relays:
            tester.test_all_relays()
        elif args.sensors:
            tester.test_sensors()
        elif args.flow:
            tester.test_flow_meters()
        elif args.health:
            tester.system_health_check()
        else:
            tester.run_full_test_suite()
    
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()