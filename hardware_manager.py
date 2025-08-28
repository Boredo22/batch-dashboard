#!/usr/bin/env python3
"""
Hardware Manager - Unified interface coordinating separate hardware files
Coordinates relay, pump, flow, and sensor controllers for tank operations
"""

import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum

# Import existing hardware controllers
from hardware.rpi_relays import RelayController
from hardware.rpi_pumps import EZOPumpController
from hardware.rpi_flow import FlowMeterController, MockFlowMeterController
from hardware.rpi_sensors import SensorController, MockSensorController
from hardware.mock_controllers import MockPumpController, MockRelayController, ConnectionManager

# Import configuration
from config import (
    TANKS, MOCK_SETTINGS, get_tank_info, validate_relay_id,
    validate_pump_id, validate_flow_meter_id
)

# Import models for logging
from models import get_database_manager, HardwareLog

logger = logging.getLogger(__name__)

class OperationResult(Enum):
    """Operation result enumeration"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    TIMEOUT = "timeout"

class HardwareManager:
    """Unified hardware interface coordinating all hardware controllers"""
    
    def __init__(self, use_mock_hardware: bool = None):
        """Initialize hardware manager with all controllers"""
        self.use_mock = use_mock_hardware if use_mock_hardware is not None else MOCK_SETTINGS
        
        # Use singleton database manager instead of creating new one
        self.db_manager = get_database_manager()
        self.hardware_log = HardwareLog(self.db_manager)
        
        # Initialize hardware controllers
        self.relay_controller = None
        self.pump_controller = None
        self.flow_controller = None
        self.sensor_controller = None
        
        # Track active operations
        self.active_operations = {}
        
        self._initialize_controllers()
    
    def _initialize_controllers(self):
        """Initialize all hardware controllers"""
        logger.info("Initializing hardware controllers...")
        
        # Initialize relay controller
        try:
            if self.use_mock.get('relays', False):
                self.relay_controller = MockRelayController()
                logger.info("✓ Mock relay controller initialized")
            else:
                self.relay_controller = RelayController()
                logger.info("✓ Relay controller initialized")
            self._log_hardware_action("relay", 0, "initialize", "success")
        except Exception as e:
            logger.error(f"✗ Relay controller failed: {e}")
            self._log_hardware_action("relay", 0, "initialize", "failed", str(e))
        
        # Initialize pump controller
        try:
            if self.use_mock.get('pumps', False):
                self.pump_controller = MockPumpController()
                logger.info("✓ Mock pump controller initialized")
            else:
                self.pump_controller = EZOPumpController()
                logger.info("✓ Pump controller initialized")
            self._log_hardware_action("pump", 0, "initialize", "success")
        except Exception as e:
            logger.error(f"✗ Pump controller failed: {e}")
            self._log_hardware_action("pump", 0, "initialize", "failed", str(e))
        
        # Initialize flow controller
        try:
            if self.use_mock.get('flow_meters', False):
                self.flow_controller = MockFlowMeterController()
                logger.info("✓ Mock flow controller initialized")
            else:
                self.flow_controller = FlowMeterController()
                logger.info("✓ Flow controller initialized")
            self._log_hardware_action("flow", 0, "initialize", "success")
        except Exception as e:
            logger.error(f"✗ Flow controller failed: {e}")
            self._log_hardware_action("flow", 0, "initialize", "failed", str(e))
        
        # Initialize sensor controller
        try:
            if self.use_mock.get('sensors', False):
                self.sensor_controller = MockSensorController()
                logger.info("✓ Mock sensor controller initialized")
            else:
                self.sensor_controller = SensorController()
                logger.info("✓ Sensor controller initialized")
            self._log_hardware_action("sensor", 0, "initialize", "success")
        except Exception as e:
            logger.error(f"✗ Sensor controller failed: {e}")
            self.sensor_controller = None
            self._log_hardware_action("sensor", 0, "initialize", "failed", str(e))
    
    def _log_hardware_action(self, component: str, component_id: int, action: str, 
                           result: str, error_message: str = None):
        """Log hardware action to database"""
        try:
            self.hardware_log.log_action(component, component_id, action, result, error_message)
        except Exception as e:
            logger.error(f"Failed to log hardware action: {e}")
    
    # =============================================================================
    # TANK OPERATIONS - High-level tank management
    # =============================================================================
    
    def fill_tank(self, tank_id: int, gallons: float) -> OperationResult:
        """Start filling a tank with specified gallons"""
        if not self._validate_tank_id(tank_id):
            return OperationResult.FAILED
        
        tank_info = get_tank_info(tank_id)
        fill_relay = tank_info.get('fill_relay')
        
        if not fill_relay:
            logger.error(f"Tank {tank_id} has no fill relay configured")
            return OperationResult.FAILED
        
        try:
            # Start flow monitoring
            if self.flow_controller:
                flow_meter_id = 1  # Assuming flow meter 1 for fill operations
                if self.flow_controller.start_flow(flow_meter_id, gallons):
                    logger.info(f"Started flow monitoring for {gallons} gallons")
                    self._log_hardware_action("flow", flow_meter_id, "start_fill", "success")
                else:
                    logger.error("Failed to start flow monitoring")
                    return OperationResult.FAILED
            
            # Turn on fill relay
            if self.relay_controller:
                if self.relay_controller.set_relay(fill_relay, True):
                    logger.info(f"Tank {tank_id} fill started: {gallons} gallons")
                    self._log_hardware_action("relay", fill_relay, "fill_start", "success")
                    
                    # Track operation
                    self.active_operations[f"fill_{tank_id}"] = {
                        'type': 'fill',
                        'tank_id': tank_id,
                        'target_gallons': gallons,
                        'start_time': time.time(),
                        'relay_id': fill_relay,
                        'flow_meter_id': flow_meter_id if self.flow_controller else None
                    }
                    
                    return OperationResult.IN_PROGRESS
                else:
                    logger.error(f"Failed to turn on fill relay {fill_relay}")
                    return OperationResult.FAILED
            
            return OperationResult.FAILED
            
        except Exception as e:
            logger.error(f"Error starting tank {tank_id} fill: {e}")
            self._log_hardware_action("tank", tank_id, "fill_start", "failed", str(e))
            return OperationResult.FAILED
    
    def mix_tank(self, tank_id: int, formula: Dict[str, float]) -> OperationResult:
        """Start mixing nutrients in a tank"""
        if not self._validate_tank_id(tank_id):
            return OperationResult.FAILED
        
        tank_info = get_tank_info(tank_id)
        mix_relays = tank_info.get('mix_relays', [])
        
        if not mix_relays:
            logger.error(f"Tank {tank_id} has no mix relays configured")
            return OperationResult.FAILED
        
        try:
            # Start circulation relays
            if self.relay_controller:
                for relay_id in mix_relays:
                    if not self.relay_controller.set_relay(relay_id, True):
                        logger.error(f"Failed to turn on mix relay {relay_id}")
                        return OperationResult.FAILED
                    self._log_hardware_action("relay", relay_id, "mix_start", "success")
            
            # Dispense nutrients according to formula
            if self.pump_controller and formula:
                for pump_name, amount_ml in formula.items():
                    # Find pump ID by name (would need mapping in config)
                    pump_id = self._get_pump_id_by_name(pump_name)
                    if pump_id and amount_ml > 0:
                        if self.pump_controller.start_dispense(pump_id, amount_ml):
                            logger.info(f"Started dispensing {amount_ml}ml from {pump_name}")
                            self._log_hardware_action("pump", pump_id, "dispense_start", "success")
                        else:
                            logger.error(f"Failed to start dispensing from {pump_name}")
            
            # Track operation
            self.active_operations[f"mix_{tank_id}"] = {
                'type': 'mix',
                'tank_id': tank_id,
                'formula': formula,
                'start_time': time.time(),
                'mix_relays': mix_relays
            }
            
            logger.info(f"Tank {tank_id} mixing started with formula: {formula}")
            return OperationResult.IN_PROGRESS
            
        except Exception as e:
            logger.error(f"Error starting tank {tank_id} mix: {e}")
            self._log_hardware_action("tank", tank_id, "mix_start", "failed", str(e))
            return OperationResult.FAILED
    
    def send_from_tank(self, tank_id: int, gallons: float) -> OperationResult:
        """Start sending solution from tank"""
        if not self._validate_tank_id(tank_id):
            return OperationResult.FAILED
        
        tank_info = get_tank_info(tank_id)
        send_relay = tank_info.get('send_relay')
        
        if not send_relay:
            logger.error(f"Tank {tank_id} has no send relay configured")
            return OperationResult.FAILED
        
        try:
            # Start flow monitoring for send
            if self.flow_controller:
                flow_meter_id = 2  # Assuming flow meter 2 for send operations
                if self.flow_controller.start_flow(flow_meter_id, gallons):
                    logger.info(f"Started send flow monitoring for {gallons} gallons")
                    self._log_hardware_action("flow", flow_meter_id, "start_send", "success")
                else:
                    logger.error("Failed to start send flow monitoring")
                    return OperationResult.FAILED
            
            # Turn on send relay
            if self.relay_controller:
                if self.relay_controller.set_relay(send_relay, True):
                    logger.info(f"Tank {tank_id} send started: {gallons} gallons")
                    self._log_hardware_action("relay", send_relay, "send_start", "success")
                    
                    # Track operation
                    self.active_operations[f"send_{tank_id}"] = {
                        'type': 'send',
                        'tank_id': tank_id,
                        'target_gallons': gallons,
                        'start_time': time.time(),
                        'relay_id': send_relay,
                        'flow_meter_id': flow_meter_id if self.flow_controller else None
                    }
                    
                    return OperationResult.IN_PROGRESS
                else:
                    logger.error(f"Failed to turn on send relay {send_relay}")
                    return OperationResult.FAILED
            
            return OperationResult.FAILED
            
        except Exception as e:
            logger.error(f"Error starting tank {tank_id} send: {e}")
            self._log_hardware_action("tank", tank_id, "send_start", "failed", str(e))
            return OperationResult.FAILED
    
    def stop_tank_operation(self, tank_id: int, operation_type: str = None) -> OperationResult:
        """Stop specific or all operations for a tank"""
        if not self._validate_tank_id(tank_id):
            return OperationResult.FAILED
        
        tank_info = get_tank_info(tank_id)
        stopped_operations = []
        
        try:
            # Stop specific operation or all operations for tank
            operations_to_stop = []
            for op_key, op_data in self.active_operations.items():
                if op_data['tank_id'] == tank_id:
                    if operation_type is None or op_data['type'] == operation_type:
                        operations_to_stop.append(op_key)
            
            for op_key in operations_to_stop:
                op_data = self.active_operations[op_key]
                op_type = op_data['type']
                
                if op_type == 'fill':
                    # Stop fill relay and flow meter
                    if self.relay_controller and 'relay_id' in op_data:
                        self.relay_controller.set_relay(op_data['relay_id'], False)
                        self._log_hardware_action("relay", op_data['relay_id'], "fill_stop", "success")
                    
                    if self.flow_controller and 'flow_meter_id' in op_data:
                        self.flow_controller.stop_flow(op_data['flow_meter_id'])
                        self._log_hardware_action("flow", op_data['flow_meter_id'], "fill_stop", "success")
                
                elif op_type == 'mix':
                    # Stop mix relays
                    if self.relay_controller and 'mix_relays' in op_data:
                        for relay_id in op_data['mix_relays']:
                            self.relay_controller.set_relay(relay_id, False)
                            self._log_hardware_action("relay", relay_id, "mix_stop", "success")
                
                elif op_type == 'send':
                    # Stop send relay and flow meter
                    if self.relay_controller and 'relay_id' in op_data:
                        self.relay_controller.set_relay(op_data['relay_id'], False)
                        self._log_hardware_action("relay", op_data['relay_id'], "send_stop", "success")
                    
                    if self.flow_controller and 'flow_meter_id' in op_data:
                        self.flow_controller.stop_flow(op_data['flow_meter_id'])
                        self._log_hardware_action("flow", op_data['flow_meter_id'], "send_stop", "success")
                
                # Remove from active operations
                del self.active_operations[op_key]
                stopped_operations.append(op_type)
            
            if stopped_operations:
                logger.info(f"Tank {tank_id} operations stopped: {stopped_operations}")
                return OperationResult.SUCCESS
            else:
                logger.warning(f"No active operations found for tank {tank_id}")
                return OperationResult.SUCCESS
                
        except Exception as e:
            logger.error(f"Error stopping tank {tank_id} operations: {e}")
            self._log_hardware_action("tank", tank_id, "stop_operations", "failed", str(e))
            return OperationResult.FAILED
    
    # =============================================================================
    # STATE QUERIES - System status and availability
    # =============================================================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'timestamp': time.time(),
            'controllers': {
                'relay': self.relay_controller is not None,
                'pump': self.pump_controller is not None,
                'flow': self.flow_controller is not None,
                'sensor': self.sensor_controller is not None
            },
            'tanks': {},
            'active_operations': self.active_operations.copy(),
            'hardware_status': {}
        }
        
        # Get tank statuses
        for tank_id in TANKS.keys():
            status['tanks'][tank_id] = self.get_tank_status(tank_id)
        
        # Get hardware statuses
        if self.relay_controller:
            status['hardware_status']['relays'] = self.relay_controller.get_all_relay_states()
        
        if self.pump_controller:
            status['hardware_status']['pumps'] = self.pump_controller.get_all_pumps_status()
        
        if self.flow_controller:
            status['hardware_status']['flow_meters'] = self.flow_controller.get_all_flow_status()
        
        if self.sensor_controller:
            status['hardware_status']['sensors'] = self.sensor_controller.get_sensor_status()
        
        return status
    
    def get_tank_status(self, tank_id: int) -> Dict[str, Any]:
        """Get status of specific tank"""
        if not self._validate_tank_id(tank_id):
            return {}
        
        tank_info = get_tank_info(tank_id)
        status = {
            'tank_id': tank_id,
            'name': tank_info.get('name', f'Tank {tank_id}'),
            'capacity': tank_info.get('capacity_gallons', 0),
            'available': self.is_tank_available(tank_id),
            'operations': {}
        }
        
        # Check for active operations
        for op_key, op_data in self.active_operations.items():
            if op_data['tank_id'] == tank_id:
                status['operations'][op_data['type']] = {
                    'active': True,
                    'start_time': op_data['start_time'],
                    'duration': time.time() - op_data['start_time']
                }
        
        return status
    
    def is_tank_available(self, tank_id: int) -> bool:
        """Check if tank is available for new operations"""
        if not self._validate_tank_id(tank_id):
            return False
        
        # Check if tank has any active operations
        for op_data in self.active_operations.values():
            if op_data['tank_id'] == tank_id:
                # Mixing and sending operations block the tank
                if op_data['type'] in ['mix', 'send']:
                    return False
        
        return True
    
    def update_operations(self) -> List[str]:
        """Update all active operations and return completed ones"""
        completed_operations = []
        
        for op_key, op_data in list(self.active_operations.items()):
            op_type = op_data['type']
            
            if op_type in ['fill', 'send'] and 'flow_meter_id' in op_data:
                # Check flow meter completion
                flow_meter_id = op_data['flow_meter_id']
                if self.flow_controller:
                    still_running = self.flow_controller.update_flow_status(flow_meter_id)
                    if not still_running:
                        # Operation completed
                        self.stop_tank_operation(op_data['tank_id'], op_type)
                        completed_operations.append(op_key)
                        logger.info(f"Operation {op_key} completed")
            
            elif op_type == 'mix':
                # Check if mixing should complete (time-based or sensor-based)
                mix_duration = time.time() - op_data['start_time']
                if mix_duration > 300:  # 5 minutes default mix time
                    self.stop_tank_operation(op_data['tank_id'], 'mix')
                    completed_operations.append(op_key)
                    logger.info(f"Mix operation {op_key} completed after {mix_duration:.1f}s")
        
        return completed_operations
    
    # =============================================================================
    # EMERGENCY AND CLEANUP
    # =============================================================================
    
    def emergency_stop_all(self) -> bool:
        """Stop ALL operations immediately"""
        logger.warning("EMERGENCY STOP ALL - Stopping ALL hardware operations immediately")
        success = True
        
        try:
            # Stop all relays
            if self.relay_controller:
                relay_success = self.relay_controller.set_all_relays(False)
                success &= relay_success
                self._log_hardware_action("relay", 0, "emergency_stop_all", "success" if relay_success else "failed")
            
            # Stop all pumps
            if self.pump_controller:
                pump_success = self.pump_controller.emergency_stop()
                success &= pump_success
                self._log_hardware_action("pump", 0, "emergency_stop_all", "success" if pump_success else "failed")
            
            # Stop all flow meters
            if self.flow_controller:
                try:
                    self.flow_controller.emergency_stop()
                    self._log_hardware_action("flow", 0, "emergency_stop_all", "success")
                except Exception as e:
                    logger.error(f"Flow controller emergency stop failed: {e}")
                    success = False
                    self._log_hardware_action("flow", 0, "emergency_stop_all", "failed", str(e))
            
            # Clear active operations
            self.active_operations.clear()
            
            logger.info(f"Emergency stop all completed - Success: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Critical error during emergency stop: {e}")
            self._log_hardware_action("system", 0, "emergency_stop_all", "failed", str(e))
            return False

    def emergency_stop(self) -> bool:
        """Emergency stop all operations (legacy method)"""
        return self.emergency_stop_all()
    
    def cleanup(self):
        """Clean up all hardware resources"""
        logger.info("Cleaning up hardware manager...")
        
        try:
            self.emergency_stop()
            
            if self.relay_controller:
                self.relay_controller.cleanup()
            
            if self.pump_controller:
                self.pump_controller.close()
            
            if self.flow_controller:
                self.flow_controller.cleanup()
            
            if self.sensor_controller:
                self.sensor_controller.close()
            
            logger.info("Hardware manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _validate_tank_id(self, tank_id: int) -> bool:
        """Validate tank ID"""
        if tank_id not in TANKS:
            logger.error(f"Invalid tank ID: {tank_id}")
            return False
        return True
    
    def _get_pump_id_by_name(self, pump_name: str) -> Optional[int]:
        """Get pump ID by name using config mapping"""
        from config import PUMP_NAME_TO_ID
        return PUMP_NAME_TO_ID.get(pump_name)

if __name__ == "__main__":
    # Test the hardware manager
    logging.basicConfig(level=logging.INFO)
    
    print("Hardware Manager Test")
    print("=" * 40)
    
    # Initialize with mock hardware
    manager = HardwareManager(use_mock_hardware={'relays': False, 'pumps': False, 'flow_meters': True, 'sensors': True})
    
    # Test system status
    status = manager.get_system_status()
    print(f"Controllers initialized: {status['controllers']}")
    print(f"Available tanks: {list(status['tanks'].keys())}")
    
    # Test tank operations
    print("\nTesting tank operations...")
    
    # Test fill operation
    result = manager.fill_tank(1, 50)
    print(f"Fill tank 1 (50 gal): {result}")
    
    # Check status
    tank_status = manager.get_tank_status(1)
    print(f"Tank 1 status: {tank_status}")
    
    # Update operations
    time.sleep(1)
    completed = manager.update_operations()
    print(f"Completed operations: {completed}")
    
    # Cleanup
    manager.cleanup()
    print("Test completed")