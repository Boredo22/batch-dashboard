#!/usr/bin/env python3
"""
Tank Mixing Integration Test (Mock Hardware)
Tests the complete Fill -> Mix -> Send workflow using mock hardware controllers.
Validates that all software logic flows correctly so any real-system issues
are likely hardware-related.
"""

import sys
import os
import time
import json
import logging
import threading

# Setup logging - show INFO level for test output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("tank_mixing_test")

# ============================================================================
# FORCE ALL MOCK SETTINGS BEFORE IMPORTING ANYTHING ELSE
# ============================================================================
import config
config.MOCK_SETTINGS = {
    "pumps": True,
    "relays": True,
    "flow_meters": True,
    "arduino": True,
    "tank_monitors": True
}

# Now import the system
from main import FeedControlSystem
from hardware.mock_controllers import MockPumpController, MockRelayController
from hardware.rpi_flow import MockFlowMeterController
from config import (
    TANKS, ROOMS, PUMP_NAMES, RELAY_GPIO_PINS,
    get_available_pumps, get_available_relays, get_available_flow_meters,
    get_pump_name, get_relay_name, get_flow_meter_name,
    FLOW_METER_CALIBRATION, MOCK_PULSES_PER_INTERVAL
)

# ============================================================================
# TEST HELPERS
# ============================================================================

class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def ok(self, msg):
        self.passed += 1
        self.details.append(f"  [PASS] {msg}")
        print(f"  [PASS] {msg}")

    def fail(self, msg):
        self.failed += 1
        self.details.append(f"  [FAIL] {msg}")
        print(f"  [FAIL] {msg}")

    def warn(self, msg):
        self.warnings += 1
        self.details.append(f"  [WARN] {msg}")
        print(f"  [WARN] {msg}")

    def info(self, msg):
        self.details.append(f"  [INFO] {msg}")
        print(f"  [INFO] {msg}")

    def summary(self):
        total = self.passed + self.failed
        status = "PASSED" if self.failed == 0 else "FAILED"
        return f"  {self.name}: {status} ({self.passed}/{total} checks, {self.warnings} warnings)"


class MockMessageCollector:
    """Collects system messages for verification"""
    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()

    def callback(self, message):
        with self.lock:
            self.messages.append({
                'time': time.time(),
                'message': message
            })

    def get_messages(self):
        with self.lock:
            return list(self.messages)

    def clear(self):
        with self.lock:
            self.messages.clear()

    def has_message_containing(self, text):
        with self.lock:
            return any(text in m['message'] for m in self.messages)


# ============================================================================
# BUG DETECTION: Check main.py mock controller wiring
# ============================================================================

def test_mock_controller_wiring(results):
    """Test that mock controllers are properly wired in main.py"""
    r = TestResult("Mock Controller Wiring")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 1: Mock Controller Wiring")
    print("=" * 60)

    # Create a FeedControlSystem with all mocks enabled
    system = FeedControlSystem(use_mock_flow=True)

    # Check pump controller
    if system.pump_controller is not None:
        r.ok("Pump controller is initialized in mock mode")
        if hasattr(system.pump_controller, 'mock_mode') and system.pump_controller.mock_mode:
            r.ok("Pump controller is using mock implementation")
        else:
            r.warn("Pump controller exists but may not be mock - check type")
    else:
        r.fail("BUG FOUND: pump_controller is None when MOCK_SETTINGS['pumps']=True")
        r.info("main.py:70-72 sets pump_controller=None instead of MockPumpController()")
        r.info("This means ALL pump commands silently fail in mock mode")

    # Check relay controller
    if system.relay_controller is not None:
        r.ok("Relay controller is initialized in mock mode")
        if hasattr(system.relay_controller, 'mock_mode') and system.relay_controller.mock_mode:
            r.ok("Relay controller is using mock implementation")
        else:
            r.warn("Relay controller exists but may not be mock - check type")
    else:
        r.fail("BUG FOUND: relay_controller is None when MOCK_SETTINGS['relays']=True")
        r.info("main.py:82-84 sets relay_controller=None instead of MockRelayController()")
        r.info("This means ALL relay commands silently fail in mock mode")

    # Check flow controller
    if system.flow_controller is not None:
        r.ok("Flow controller is initialized in mock mode")
        if isinstance(system.flow_controller, MockFlowMeterController):
            r.ok("Flow controller is using MockFlowMeterController")
        else:
            r.warn("Flow controller exists but is not MockFlowMeterController")
    else:
        r.fail("Flow controller is None in mock mode")

    # Check sensor controller
    if system.sensor_controller is None:
        r.info("Sensor controller is None (expected - no mock EC/pH sensor controller exists)")
    else:
        r.ok("Sensor controller is initialized")

    system.stop()
    return r


# ============================================================================
# PATCHED SYSTEM: Wire in mock controllers properly for remaining tests
# ============================================================================

def create_patched_mock_system():
    """Create a FeedControlSystem with all mock controllers"""
    system = FeedControlSystem(use_mock_flow=True)

    # Verify mock controllers are properly wired (should be after fix)
    if system.pump_controller is None:
        system.pump_controller = MockPumpController()
        logger.warning("Had to patch MockPumpController - main.py fix may not be applied")

    if system.relay_controller is None:
        system.relay_controller = MockRelayController()
        logger.warning("Had to patch MockRelayController - main.py fix may not be applied")

    return system


# ============================================================================
# TEST: Command Parsing and Routing
# ============================================================================

def test_command_parsing(results):
    """Test that command strings are correctly parsed and routed"""
    r = TestResult("Command Parsing & Routing")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 2: Command Parsing & Routing")
    print("=" * 60)

    system = create_patched_mock_system()
    collector = MockMessageCollector()
    system.set_message_callback(collector.callback)
    system.start()
    time.sleep(0.5)  # Let worker thread start

    # Test valid relay command
    collector.clear()
    success = system.send_command("Start;Relay;1;ON;end")
    time.sleep(0.3)
    if success:
        r.ok("Valid relay ON command accepted by queue")
    else:
        r.fail("Valid relay ON command rejected by queue")

    if collector.has_message_containing("RelayResponse"):
        r.ok("Relay command produced RelayResponse message")
    else:
        r.warn("No RelayResponse message received (may need more time)")

    # Test valid pump dispense command
    collector.clear()
    success = system.send_command("Start;Dispense;1;10.0;end")
    time.sleep(0.3)
    if success:
        r.ok("Valid dispense command accepted by queue")
    else:
        r.fail("Valid dispense command rejected by queue")

    if collector.has_message_containing("NuteStat"):
        r.ok("Dispense command produced NuteStat message")
    else:
        r.warn("No NuteStat message received")

    # Test valid flow command
    collector.clear()
    success = system.send_command("Start;StartFlow;1;5;220;end")
    time.sleep(0.3)
    if success:
        r.ok("Valid flow command accepted by queue")
    else:
        r.fail("Valid flow command rejected by queue")

    if collector.has_message_containing("FlowStat"):
        r.ok("Flow command produced FlowStat message")
    else:
        r.warn("No FlowStat message received")

    # Test invalid command format
    collector.clear()
    success = system.send_command("BadCommand")
    time.sleep(0.3)
    if success:
        r.info("Invalid command was queued (expected - validation happens at execution)")

    # Test pump stop command
    collector.clear()
    success = system.send_command("Start;Pump;1;X;end")
    time.sleep(0.3)
    if success:
        r.ok("Pump stop command accepted")
    else:
        r.fail("Pump stop command rejected")

    system.stop()
    return r


# ============================================================================
# TEST: Full Tank Fill Workflow
# ============================================================================

def test_tank_fill(results):
    """Test the tank fill workflow: relay ON -> flow monitor -> relay OFF"""
    r = TestResult("Tank Fill Workflow")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 3: Tank Fill Workflow (Tank 1, 5 gallons)")
    print("=" * 60)

    tank_id = 1
    tank = TANKS[tank_id]
    fill_relay = tank['fill_relay']
    target_gallons = 5

    r.info(f"Tank: {tank['name']}")
    r.info(f"Fill relay: {fill_relay} ({get_relay_name(fill_relay)})")
    r.info(f"Target: {target_gallons} gallons")

    system = create_patched_mock_system()
    collector = MockMessageCollector()
    system.set_message_callback(collector.callback)
    system.start()
    time.sleep(0.5)

    # Step 1: Turn on fill relay
    r.info("Step 1: Activating fill relay...")
    success = system.send_command(f"Start;Relay;{fill_relay};ON;end")
    time.sleep(0.3)

    if success:
        r.ok(f"Fill relay {fill_relay} command sent")
    else:
        r.fail(f"Failed to send fill relay {fill_relay} command")

    # Verify relay state
    if system.relay_controller:
        relay_state = system.relay_controller.get_relay_state(fill_relay)
        if relay_state:
            r.ok(f"Fill relay {fill_relay} confirmed ON")
        else:
            r.fail(f"Fill relay {fill_relay} is not ON after command")

    # Step 2: Start flow monitoring
    r.info("Step 2: Starting flow meter monitoring...")
    flow_meter_id = 1  # Tank Fill meter
    success = system.send_command(f"Start;StartFlow;{flow_meter_id};{target_gallons};220;end")
    time.sleep(0.3)

    if success:
        r.ok(f"Flow meter {flow_meter_id} started for {target_gallons} gallons")
    else:
        r.fail(f"Failed to start flow meter {flow_meter_id}")

    # Step 3: Monitor flow progress
    r.info("Step 3: Monitoring flow progress...")
    flow_completed = False
    max_iterations = 500  # Safety limit

    for i in range(max_iterations):
        if system.flow_controller:
            still_running = system.flow_controller.update_flow_status(flow_meter_id)
            status = system.flow_controller.get_flow_status(flow_meter_id)

            if status:
                current = status['current_gallons']
                target = status['target_gallons']
                pulses = status['pulse_count']

                # Log every 20 iterations
                if i % 20 == 0:
                    r.info(f"  Progress: {current}/{target} gallons ({pulses} pulses)")

                if not still_running and status['status'] == 2:
                    flow_completed = True
                    r.ok(f"Flow completed: {current}/{target} gallons ({pulses} pulses)")
                    break

        time.sleep(0.05)

    if not flow_completed:
        r.fail(f"Flow did not complete within {max_iterations} iterations")

    # Step 4: Turn off fill relay
    r.info("Step 4: Deactivating fill relay...")
    success = system.send_command(f"Start;Relay;{fill_relay};OFF;end")
    time.sleep(0.3)

    if success:
        r.ok(f"Fill relay {fill_relay} OFF command sent")
    else:
        r.fail(f"Failed to send fill relay {fill_relay} OFF command")

    if system.relay_controller:
        relay_state = system.relay_controller.get_relay_state(fill_relay)
        if not relay_state:
            r.ok(f"Fill relay {fill_relay} confirmed OFF")
        else:
            r.fail(f"Fill relay {fill_relay} is still ON after OFF command")

    system.stop()
    return r


# ============================================================================
# TEST: Full Mix Workflow (Nutrient Dispensing)
# ============================================================================

def test_tank_mix(results):
    """Test the nutrient mixing workflow using veg formula"""
    r = TestResult("Tank Mix Workflow")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 4: Tank Mix Workflow (Veg Formula)")
    print("=" * 60)

    # Load nutrients config
    nutrients_path = os.path.join(os.path.dirname(__file__), 'nutrients.json')
    try:
        with open(nutrients_path, 'r') as f:
            nutrients = json.load(f)
        r.ok("Loaded nutrients.json")
    except Exception as e:
        r.fail(f"Failed to load nutrients.json: {e}")
        return r

    veg_formula = nutrients.get('veg_formula', {})
    pump_mapping = nutrients.get('pump_name_to_id', {})

    r.info(f"Veg formula: {veg_formula}")
    r.info(f"Pump mapping: {pump_mapping}")

    # Validate that all nutrients in formula have pump mappings
    for nutrient_name, amount_ml in veg_formula.items():
        if nutrient_name in pump_mapping:
            pump_id = pump_mapping[nutrient_name]
            if pump_id in get_available_pumps():
                r.ok(f"Nutrient '{nutrient_name}' -> Pump {pump_id} ({amount_ml}ml) - valid")
            else:
                r.fail(f"Nutrient '{nutrient_name}' mapped to pump {pump_id} which is not available")
        else:
            r.fail(f"Nutrient '{nutrient_name}' has no pump mapping in nutrients.json")

    # Create system and test dispensing
    tank_id = 1
    tank = TANKS[tank_id]
    mix_relays = tank['mix_relays']

    r.info(f"Tank: {tank['name']}")
    r.info(f"Mix relays: {mix_relays}")

    system = create_patched_mock_system()
    collector = MockMessageCollector()
    system.set_message_callback(collector.callback)
    system.start()
    time.sleep(0.5)

    # Step 1: Turn on mix relays (enables nutrient circulation path)
    r.info("Step 1: Activating mix relays...")
    for relay_id in mix_relays:
        success = system.send_command(f"Start;Relay;{relay_id};ON;end")
        time.sleep(0.2)
        if success:
            r.ok(f"Mix relay {relay_id} activated")
        else:
            r.fail(f"Failed to activate mix relay {relay_id}")

    # Verify relay states
    if system.relay_controller:
        for relay_id in mix_relays:
            state = system.relay_controller.get_relay_state(relay_id)
            if state:
                r.ok(f"Mix relay {relay_id} confirmed ON")
            else:
                r.fail(f"Mix relay {relay_id} is not ON")

    # Step 2: Dispense each nutrient
    r.info("Step 2: Dispensing nutrients...")
    dispense_results = {}

    for nutrient_name, amount_ml in veg_formula.items():
        pump_id = pump_mapping.get(nutrient_name)
        if pump_id is None:
            r.fail(f"No pump for {nutrient_name}")
            continue

        r.info(f"  Dispensing {amount_ml}ml of {nutrient_name} from pump {pump_id}...")
        collector.clear()

        success = system.send_command(f"Start;Dispense;{pump_id};{amount_ml};end")
        time.sleep(0.3)

        if success:
            r.ok(f"  Pump {pump_id} ({nutrient_name}) dispense command sent ({amount_ml}ml)")
        else:
            r.fail(f"  Failed to send dispense command for pump {pump_id}")
            continue

        # Wait for dispensing to complete (mock pumps dispense at ~10ml/sec)
        wait_time = max(amount_ml / 10.0, 0.5) + 1.0  # Add buffer
        r.info(f"  Waiting up to {wait_time:.1f}s for dispense to complete...")

        completed = False
        start_time = time.time()
        while time.time() - start_time < wait_time:
            if system.pump_controller:
                pump_info = system.pump_controller.get_pump_info(pump_id)
                if pump_info and not pump_info['is_dispensing']:
                    dispensed = pump_info['current_volume']
                    dispense_results[nutrient_name] = dispensed
                    r.ok(f"  Pump {pump_id} ({nutrient_name}) completed: {dispensed:.2f}ml dispensed")
                    completed = True
                    break
            time.sleep(0.2)

        if not completed:
            pump_info = system.pump_controller.get_pump_info(pump_id) if system.pump_controller else None
            if pump_info:
                r.fail(f"  Pump {pump_id} ({nutrient_name}) did not complete in time. "
                       f"Current: {pump_info['current_volume']:.2f}/{pump_info['target_volume']:.2f}ml")
            else:
                r.fail(f"  Pump {pump_id} ({nutrient_name}) did not complete and no status available")

    # Step 3: Verify all nutrients were dispensed
    r.info("Step 3: Verifying dispense results...")
    for nutrient_name, expected_ml in veg_formula.items():
        actual = dispense_results.get(nutrient_name, 0)
        if abs(actual - expected_ml) < 0.5:  # Allow small tolerance
            r.ok(f"  {nutrient_name}: expected {expected_ml}ml, got {actual:.2f}ml")
        else:
            r.fail(f"  {nutrient_name}: expected {expected_ml}ml, got {actual:.2f}ml")

    # Step 4: Turn off mix relays
    r.info("Step 4: Deactivating mix relays...")
    for relay_id in mix_relays:
        success = system.send_command(f"Start;Relay;{relay_id};OFF;end")
        time.sleep(0.2)
        if success:
            r.ok(f"Mix relay {relay_id} deactivated")
        else:
            r.fail(f"Failed to deactivate mix relay {relay_id}")

    system.stop()
    return r


# ============================================================================
# TEST: Full Send Workflow
# ============================================================================

def test_tank_send(results):
    """Test the send-to-room workflow"""
    r = TestResult("Tank Send Workflow")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 5: Tank Send Workflow (Tank 1 -> Room 1, 5 gallons)")
    print("=" * 60)

    tank_id = 1
    tank = TANKS[tank_id]
    send_relay = tank['send_relay']
    room_id = 1
    room = ROOMS.get(room_id, {})
    room_relay = room.get('relay')
    target_gallons = 5

    r.info(f"Tank: {tank['name']}")
    r.info(f"Send relay: {send_relay}")
    r.info(f"Room relay: {room_relay}")
    r.info(f"Target: {target_gallons} gallons")

    # Validate relay IDs exist in config
    if send_relay in RELAY_GPIO_PINS:
        r.ok(f"Send relay {send_relay} exists in RELAY_GPIO_PINS")
    else:
        r.fail(f"Send relay {send_relay} NOT in RELAY_GPIO_PINS - tank config error!")

    if room_relay and room_relay in RELAY_GPIO_PINS:
        r.ok(f"Room relay {room_relay} exists in RELAY_GPIO_PINS")
    elif room_relay:
        r.fail(f"Room relay {room_relay} NOT in RELAY_GPIO_PINS")
    else:
        r.fail("Room 1 has no relay configured")

    system = create_patched_mock_system()
    collector = MockMessageCollector()
    system.set_message_callback(collector.callback)
    system.start()
    time.sleep(0.5)

    # Step 1: Turn on send relay
    r.info("Step 1: Activating send relay...")
    success = system.send_command(f"Start;Relay;{send_relay};ON;end")
    time.sleep(0.3)

    if success:
        r.ok(f"Send relay {send_relay} command sent")
    else:
        r.fail(f"Failed to send relay {send_relay} command")

    # Also turn on room relay if different from send relay
    if room_relay and room_relay != send_relay:
        r.info(f"  Also activating room relay {room_relay}...")
        success = system.send_command(f"Start;Relay;{room_relay};ON;end")
        time.sleep(0.3)
        if success:
            r.ok(f"Room relay {room_relay} activated")
        else:
            r.fail(f"Failed to activate room relay {room_relay}")

    # Step 2: Start flow meter (use meter 2 for sending)
    r.info("Step 2: Starting send flow meter...")
    flow_meter_id = 2  # Tank Send meter
    success = system.send_command(f"Start;StartFlow;{flow_meter_id};{target_gallons};220;end")
    time.sleep(0.3)

    if success:
        r.ok(f"Flow meter {flow_meter_id} (Tank Send) started")
    else:
        r.fail(f"Failed to start flow meter {flow_meter_id}")

    # Step 3: Monitor send progress
    r.info("Step 3: Monitoring send progress...")
    flow_completed = False
    max_iterations = 200

    for i in range(max_iterations):
        if system.flow_controller:
            still_running = system.flow_controller.update_flow_status(flow_meter_id)
            status = system.flow_controller.get_flow_status(flow_meter_id)

            if status:
                current = status['current_gallons']
                target = status['target_gallons']

                if i % 20 == 0:
                    r.info(f"  Progress: {current}/{target} gallons")

                if not still_running and status['status'] == 2:
                    flow_completed = True
                    r.ok(f"Send completed: {current}/{target} gallons")
                    break

        time.sleep(0.05)

    if not flow_completed:
        r.fail("Send flow did not complete")

    # Step 4: Turn off relays
    r.info("Step 4: Deactivating send relays...")
    system.send_command(f"Start;Relay;{send_relay};OFF;end")
    time.sleep(0.2)
    if room_relay and room_relay != send_relay:
        system.send_command(f"Start;Relay;{room_relay};OFF;end")
        time.sleep(0.2)

    if system.relay_controller:
        send_state = system.relay_controller.get_relay_state(send_relay)
        if not send_state:
            r.ok(f"Send relay {send_relay} confirmed OFF")
        else:
            r.fail(f"Send relay {send_relay} still ON after OFF command")

    system.stop()
    return r


# ============================================================================
# TEST: Emergency Stop
# ============================================================================

def test_emergency_stop(results):
    """Test emergency stop kills all operations"""
    r = TestResult("Emergency Stop")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 6: Emergency Stop")
    print("=" * 60)

    system = create_patched_mock_system()
    system.start()
    time.sleep(0.5)

    # Start some operations
    system.send_command("Start;Relay;1;ON;end")
    system.send_command("Start;Relay;4;ON;end")
    system.send_command("Start;Dispense;1;100.0;end")
    system.send_command("Start;StartFlow;1;25;220;end")
    time.sleep(0.5)

    # Verify things are running
    r.info("Started relay 1, relay 4, pump 1 dispense, flow meter 1...")

    if system.relay_controller:
        r1 = system.relay_controller.get_relay_state(1)
        r4 = system.relay_controller.get_relay_state(4)
        if r1 and r4:
            r.ok("Relays confirmed active before emergency stop")
        else:
            r.warn(f"Relay states before e-stop: relay1={r1}, relay4={r4}")

    # Emergency stop
    r.info("Triggering emergency stop...")
    system.emergency_stop()
    time.sleep(0.5)

    # Verify everything is off
    if system.relay_controller:
        all_states = system.relay_controller.get_all_relay_states()
        any_on = any(state for state in all_states.values())
        if not any_on:
            r.ok("All relays OFF after emergency stop")
        else:
            on_relays = [rid for rid, state in all_states.items() if state]
            r.fail(f"Relays still ON after emergency stop: {on_relays}")

    if system.pump_controller:
        all_pumps = system.pump_controller.get_all_pumps_status()
        any_dispensing = any(p['is_dispensing'] for p in all_pumps.values())
        if not any_dispensing:
            r.ok("All pumps stopped after emergency stop")
        else:
            active = [pid for pid, p in all_pumps.items() if p['is_dispensing']]
            r.fail(f"Pumps still dispensing after emergency stop: {active}")

    if system.flow_controller:
        all_flow = system.flow_controller.get_all_flow_status()
        any_active = any(f['status'] == 1 for f in all_flow.values())
        if not any_active:
            r.ok("All flow meters stopped after emergency stop")
        else:
            active = [fid for fid, f in all_flow.items() if f['status'] == 1]
            r.fail(f"Flow meters still active after emergency stop: {active}")

    system.stop()
    return r


# ============================================================================
# TEST: Tank Config Validation
# ============================================================================

def test_tank_config_validation(results):
    """Validate that tank configs reference valid relays and hardware"""
    r = TestResult("Tank Config Validation")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 7: Tank Configuration Validation")
    print("=" * 60)

    available_relays = get_available_relays()

    for tank_id, tank in TANKS.items():
        r.info(f"Validating Tank {tank_id}: {tank['name']}")

        # Check fill relay
        fill = tank.get('fill_relay')
        if fill in available_relays:
            r.ok(f"  Fill relay {fill} is valid")
        else:
            r.fail(f"  Fill relay {fill} NOT in available relays {available_relays}")

        # Check mix relays
        for relay in tank.get('mix_relays', []):
            if relay in available_relays:
                r.ok(f"  Mix relay {relay} is valid")
            else:
                r.fail(f"  Mix relay {relay} NOT in available relays {available_relays}")

        # Check send relay
        send = tank.get('send_relay')
        if send in available_relays:
            r.ok(f"  Send relay {send} is valid")
        else:
            r.fail(f"  Send relay {send} NOT in available relays {available_relays}")

    # Check room relays
    for room_id, room in ROOMS.items():
        relay = room.get('relay')
        r.info(f"Validating Room {room_id}: {room['name']}")
        if relay in available_relays:
            r.ok(f"  Room relay {relay} is valid")
        else:
            r.fail(f"  Room relay {relay} NOT in available relays {available_relays}")

    # Check nutrient pump mappings
    nutrients_path = os.path.join(os.path.dirname(__file__), 'nutrients.json')
    try:
        with open(nutrients_path, 'r') as f:
            nutrients = json.load(f)

        pump_mapping = nutrients.get('pump_name_to_id', {})
        available_pumps = get_available_pumps()

        r.info("Validating nutrient pump mappings...")
        for name, pump_id in pump_mapping.items():
            if pump_id in available_pumps:
                r.ok(f"  '{name}' -> Pump {pump_id} is valid")
            else:
                r.fail(f"  '{name}' -> Pump {pump_id} NOT in available pumps {available_pumps}")
    except Exception as e:
        r.fail(f"Failed to load nutrients.json: {e}")

    return r


# ============================================================================
# TEST: Full End-to-End Workflow
# ============================================================================

def test_full_workflow(results):
    """Test complete Fill -> Mix -> Send workflow on Tank 1"""
    r = TestResult("Full End-to-End Workflow")
    results.append(r)

    print("\n" + "=" * 60)
    print("TEST 8: Full End-to-End Workflow (Fill -> Mix -> Send)")
    print("=" * 60)

    tank_id = 1
    tank = TANKS[tank_id]
    target_gallons = 5

    r.info(f"Tank: {tank['name']}")
    r.info(f"Target: {target_gallons} gallons")
    r.info(f"Recipe: veg_formula")

    system = create_patched_mock_system()
    collector = MockMessageCollector()
    system.set_message_callback(collector.callback)
    system.start()
    time.sleep(0.5)

    # ---- PHASE 1: FILL ----
    r.info("\n--- PHASE 1: FILL ---")
    fill_relay = tank['fill_relay']

    # Turn on fill relay
    system.send_command(f"Start;Relay;{fill_relay};ON;end")
    time.sleep(0.2)

    # Start flow meter 1
    system.send_command("Start;StartFlow;1;{};220;end".format(target_gallons))
    time.sleep(0.2)

    # Wait for fill to complete
    fill_done = False
    for i in range(500):
        if system.flow_controller:
            system.flow_controller.update_flow_status(1)
            status = system.flow_controller.get_flow_status(1)
            if status and status['status'] == 2:
                fill_done = True
                break
        time.sleep(0.05)

    # Turn off fill relay
    system.send_command(f"Start;Relay;{fill_relay};OFF;end")
    time.sleep(0.2)

    if fill_done:
        r.ok("FILL phase completed successfully")
    else:
        r.fail("FILL phase did not complete")

    # ---- PHASE 2: MIX ----
    r.info("\n--- PHASE 2: MIX ---")
    mix_relays = tank['mix_relays']

    # Turn on mix relays
    for relay_id in mix_relays:
        system.send_command(f"Start;Relay;{relay_id};ON;end")
        time.sleep(0.1)

    # Load and dispense nutrients
    nutrients_path = os.path.join(os.path.dirname(__file__), 'nutrients.json')
    with open(nutrients_path, 'r') as f:
        nutrients = json.load(f)

    veg_formula = nutrients['veg_formula']
    pump_mapping = nutrients['pump_name_to_id']

    all_dispensed = True
    for nutrient_name, amount_ml in veg_formula.items():
        pump_id = pump_mapping[nutrient_name]
        system.send_command(f"Start;Dispense;{pump_id};{amount_ml};end")
        time.sleep(0.1)

        # Wait for this dispense to complete
        wait_time = max(amount_ml / 10.0, 0.5) + 1.0
        completed = False
        start = time.time()
        while time.time() - start < wait_time:
            if system.pump_controller:
                info = system.pump_controller.get_pump_info(pump_id)
                if info and not info['is_dispensing']:
                    completed = True
                    break
            # Also need to trigger status checks
            if system.pump_controller:
                system.pump_controller.check_pump_status(pump_id)
            time.sleep(0.1)

        if not completed:
            all_dispensed = False
            r.fail(f"  Pump {pump_id} ({nutrient_name}) did not complete")

    # Turn off mix relays
    for relay_id in mix_relays:
        system.send_command(f"Start;Relay;{relay_id};OFF;end")
        time.sleep(0.1)

    if all_dispensed:
        r.ok("MIX phase completed - all nutrients dispensed")
    else:
        r.fail("MIX phase incomplete - some nutrients not dispensed")

    # ---- PHASE 3: SEND ----
    r.info("\n--- PHASE 3: SEND ---")
    send_relay = tank['send_relay']
    room_relay = ROOMS[1]['relay']

    # Turn on send relay and room relay
    system.send_command(f"Start;Relay;{send_relay};ON;end")
    time.sleep(0.1)
    if room_relay != send_relay:
        system.send_command(f"Start;Relay;{room_relay};ON;end")
        time.sleep(0.1)

    # Start flow meter 2 for sending
    system.send_command(f"Start;StartFlow;2;{target_gallons};220;end")
    time.sleep(0.2)

    # Wait for send to complete
    send_done = False
    for i in range(500):
        if system.flow_controller:
            system.flow_controller.update_flow_status(2)
            status = system.flow_controller.get_flow_status(2)
            if status and status['status'] == 2:
                send_done = True
                break
        time.sleep(0.05)

    # Turn off relays
    system.send_command(f"Start;Relay;{send_relay};OFF;end")
    time.sleep(0.1)
    if room_relay != send_relay:
        system.send_command(f"Start;Relay;{room_relay};OFF;end")
        time.sleep(0.1)

    if send_done:
        r.ok("SEND phase completed successfully")
    else:
        r.fail("SEND phase did not complete")

    # ---- FINAL CHECK ----
    r.info("\n--- FINAL CHECK ---")

    # Verify all relays are off
    if system.relay_controller:
        all_states = system.relay_controller.get_all_relay_states()
        any_on = any(state for state in all_states.values())
        if not any_on:
            r.ok("All relays OFF at end of workflow")
        else:
            on_relays = [rid for rid, s in all_states.items() if s]
            r.fail(f"Relays still ON: {on_relays}")

    # Verify no pumps dispensing
    if system.pump_controller:
        all_pumps = system.pump_controller.get_all_pumps_status()
        any_active = any(p['is_dispensing'] for p in all_pumps.values())
        if not any_active:
            r.ok("No pumps dispensing at end of workflow")
        else:
            r.fail("Some pumps still active at end of workflow")

    if fill_done and all_dispensed and send_done:
        r.ok("FULL WORKFLOW COMPLETED SUCCESSFULLY")
    else:
        r.fail("FULL WORKFLOW HAD FAILURES")

    system.stop()
    return r


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("  TANK MIXING INTEGRATION TEST (Mock Hardware)")
    print("  Tests complete Fill -> Mix -> Send workflow")
    print("=" * 60)
    print(f"  Mock Settings: {config.MOCK_SETTINGS}")
    print(f"  Tanks: {list(TANKS.keys())}")
    print(f"  Pumps: {list(PUMP_NAMES.values())}")
    print(f"  Relays: {list(RELAY_GPIO_PINS.keys())}")
    print(f"  Flow Meters: {list(get_available_flow_meters())}")
    print()

    results = []

    # Run all tests
    test_mock_controller_wiring(results)
    test_command_parsing(results)
    test_tank_fill(results)
    test_tank_mix(results)
    test_tank_send(results)
    test_emergency_stop(results)
    test_tank_config_validation(results)
    test_full_workflow(results)

    # Print summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    total_passed = 0
    total_failed = 0
    total_warnings = 0

    for r in results:
        print(r.summary())
        total_passed += r.passed
        total_failed += r.failed
        total_warnings += r.warnings

    print()
    print(f"  Total: {total_passed} passed, {total_failed} failed, {total_warnings} warnings")

    if total_failed > 0:
        print("\n  BUGS FOUND - Issues that need fixing:")
        for r in results:
            for detail in r.details:
                if "[FAIL]" in detail:
                    print(f"    {r.name}: {detail.strip()}")
        print()
        print("  If these bugs are fixed in software, any remaining issues")
        print("  on the real system are LIKELY HARDWARE-RELATED.")
    else:
        print("\n  ALL TESTS PASSED!")
        print("  Software logic is verified correct with mock hardware.")
        print("  Any issues on the real system are LIKELY HARDWARE-RELATED.")

    print("=" * 60)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
