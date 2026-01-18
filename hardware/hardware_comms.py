#!/usr/bin/env python3
"""
Hardware Communications Module
Extracted from working simple_gui.py patterns for reliable hardware control
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Union

# Import the proven working system
from main import FeedControlSystem
from config import (
    get_available_pumps, get_available_relays, get_available_flow_meters,
    get_pump_name, get_relay_name, get_flow_meter_name,
    MIN_PUMP_VOLUME_ML, MAX_PUMP_VOLUME_ML, MAX_FLOW_GALLONS,
    MOCK_SETTINGS
)

# Setup logging
logger = logging.getLogger(__name__)

class HardwareComms:
    """
    Hardware communications class using the exact same patterns as simple_gui.py
    This class encapsulates all the working hardware control logic
    """
    
    def __init__(self):
        self.system: Optional[FeedControlSystem] = None
        self.system_lock = threading.Lock()
        self._initialize_system()
    
    def _initialize_system(self) -> bool:
        """Initialize the FeedControlSystem exactly like simple_gui.py"""
        with self.system_lock:
            if self.system is not None:
                return True
                
            try:
                # Use same mock settings pattern as simple_gui
                use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
                self.system = FeedControlSystem(use_mock_flow=use_mock_flow)
                self.system.start()
                logger.info("✓ Feed control system started successfully")
                return True
            except Exception as e:
                logger.error(f"✗ Failed to start system: {e}")
                self.system = None
                return False
    
    def get_system(self) -> Optional[FeedControlSystem]:
        """Get the system instance, initializing if needed"""
        if self.system is None:
            self._initialize_system()
        return self.system
    
    def is_system_ready(self) -> bool:
        """Check if the system is ready for commands"""
        return self.system is not None
    
    # =========================================================================
    # RELAY CONTROL - Exact same patterns as simple_gui.py
    # =========================================================================
    
    def control_relay(self, relay_id: int, state: bool) -> bool:
        """
        Control relay using exact same validation and command as simple_gui.py
        
        Args:
            relay_id: Relay ID (0 = all relays)
            state: True = ON, False = OFF
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for relay control")
            return False
        
        # Same validation as simple_gui.py
        if relay_id != 0 and relay_id not in get_available_relays():
            logger.error(f"Invalid relay ID: {relay_id}")
            return False
        
        # Exact same command format as simple_gui.py
        state_str = "ON" if state else "OFF"
        command = f"Start;Relay;{relay_id};{state_str};end"
        
        try:
            success = sys.send_command(command)
            
            if success:
                relay_name = get_relay_name(relay_id) if relay_id != 0 else "All Relays"
                action = "turned on" if state else "turned off"
                logger.info(f"{relay_name} {action}")
            else:
                logger.error(f"Failed to control relay {relay_id}")
            
            return success
        except Exception as e:
            logger.error(f"Exception controlling relay {relay_id}: {e}")
            return False
    
    def all_relays_off(self) -> bool:
        """Turn all relays off using relay ID 0"""
        return self.control_relay(0, False)
    
    # =========================================================================
    # PUMP CONTROL - Exact same patterns as simple_gui.py  
    # =========================================================================
    
    def dispense_pump(self, pump_id: int, amount_ml: Union[int, float]) -> bool:
        """
        Dispense from pump using exact same pattern as simple_gui.py
        
        Args:
            pump_id: Pump ID
            amount_ml: Amount to dispense in milliliters
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for pump control")
            return False
        
        # Same validation as simple_gui.py
        if pump_id not in get_available_pumps():
            logger.error(f"Invalid pump ID: {pump_id}")
            return False
        
        try:
            amount = float(amount_ml)
            if not (MIN_PUMP_VOLUME_ML <= amount <= MAX_PUMP_VOLUME_ML):
                logger.error(f"Amount must be between {MIN_PUMP_VOLUME_ML} and {MAX_PUMP_VOLUME_ML}ml, got: {amount}")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid amount value: {amount_ml}")
            return False
        
        # Exact same command format as simple_gui.py
        command = f"Start;Dispense;{pump_id};{amount};end"
        
        try:
            success = sys.send_command(command)
            
            if success:
                pump_name = get_pump_name(pump_id)
                logger.info(f"Dispensing {amount}ml from {pump_name}")
            else:
                logger.error(f"Failed to start dispense from pump {pump_id}")
            
            return success
        except Exception as e:
            logger.error(f"Exception dispensing from pump {pump_id}: {e}")
            return False
    
    def stop_pump(self, pump_id: int) -> bool:
        """
        Stop pump using exact same command as simple_gui.py
        
        Args:
            pump_id: Pump ID
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for pump control")
            return False
        
        # Same validation
        if pump_id not in get_available_pumps():
            logger.error(f"Invalid pump ID: {pump_id}")
            return False
        
        # Exact same command format as simple_gui.py
        command = f"Start;Pump;{pump_id};X;end"
        
        try:
            success = sys.send_command(command)
            
            if success:
                pump_name = get_pump_name(pump_id)
                logger.info(f"Stopped {pump_name}")
            else:
                logger.error(f"Failed to stop pump {pump_id}")
            
            return success
        except Exception as e:
            logger.error(f"Exception stopping pump {pump_id}: {e}")
            return False
    
    def calibrate_pump(self, pump_id: int, actual_volume_ml: float) -> bool:
        """
        Calibrate EZO pump with actual dispensed volume
        
        Args:
            pump_id: Pump ID
            actual_volume_ml: The actual volume that was measured
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for calibration")
            return False
        
        try:
            # Use existing pump controller from main system
            success = sys.pump_controller.calibrate_pump(pump_id, actual_volume_ml)
            
            if success:
                pump_name = get_pump_name(pump_id)
                logger.info(f"Calibrated {pump_name} with {actual_volume_ml}ml")
            else:
                logger.error(f"Failed to calibrate pump {pump_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Exception calibrating pump {pump_id}: {e}")
            return False

    def clear_pump_calibration(self, pump_id: int) -> bool:
        """
        Clear EZO pump calibration data
        
        Args:
            pump_id: Pump ID
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for clearing calibration")
            return False
        
        try:
            # Send Cal,clear command using existing controller
            response = sys.pump_controller.send_command(pump_id, "Cal,clear")
            success = response is not None
            
            if success:
                # Update cached calibration status
                sys.pump_controller.calibration_status[pump_id] = 0
                sys.pump_controller.pump_info[pump_id]['calibrated'] = False
                pump_name = get_pump_name(pump_id)
                logger.info(f"Cleared calibration for {pump_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Exception clearing pump {pump_id} calibration: {e}")
            return False

    def check_pump_calibration_status(self, pump_id: int) -> dict:
        """
        Check EZO pump calibration status using live "Cal,?" command
        
        Args:
            pump_id: Pump ID
        
        Returns:
            dict: Calibration status info
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for checking calibration")
            return {
                'success': False,
                'pump_id': pump_id,
                'error': 'System not available'
            }
        
        try:
            # Send Cal,? command to get real-time calibration status
            cal_response = sys.pump_controller.send_command(pump_id, "Cal,?")
            logger.debug(f"Pump {pump_id}: Cal,? live response = '{cal_response}'")
            
            if cal_response:
                # Parse calibration status - EZO pump Cal,? returns ?CAL,n (uppercase) where n is calibration status
                if cal_response.startswith("?CAL,"):
                    try:
                        cal_status = int(cal_response.split(',')[1])
                        
                        # Update cached status
                        sys.pump_controller.calibration_status[pump_id] = cal_status
                        sys.pump_controller.pump_info[pump_id]['calibrated'] = cal_status > 0
                        
                        logger.info(f"Pump {pump_id}: Live calibration status {cal_status}")
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Pump {pump_id}: Failed to parse live calibration response '{cal_response}': {e}")
                        cal_status = 0
                elif cal_response.startswith("?Cal,"):
                    # Handle mixed case format too
                    try:
                        cal_status = int(cal_response.split(',')[1])
                        
                        # Update cached status
                        sys.pump_controller.calibration_status[pump_id] = cal_status
                        sys.pump_controller.pump_info[pump_id]['calibrated'] = cal_status > 0
                        
                        logger.info(f"Pump {pump_id}: Live calibration status {cal_status}")
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Pump {pump_id}: Failed to parse live calibration response '{cal_response}': {e}")
                        cal_status = 0
                else:
                    # Response doesn't match expected format
                    logger.warning(f"Pump {pump_id}: Unexpected live calibration response format: '{cal_response}'")
                    cal_status = 0
            else:
                cal_status = 0  # Default to uncalibrated if command failed
                logger.warning(f"Pump {pump_id}: No response to live Cal,? command")
            
            status_map = {
                0: "uncalibrated",
                1: "single_point",
                2: "volume_calibrated",
                3: "fully_calibrated"
            }
            
            return {
                'success': True,
                'pump_id': pump_id,
                'calibration_status': status_map.get(cal_status, "unknown"),
                'calibration_level': cal_status,
                'calibrated': cal_status > 0,
                'raw_response': cal_response
            }
            
        except Exception as e:
            logger.error(f"Exception checking pump {pump_id} calibration: {e}")
            return {
                'success': False,
                'pump_id': pump_id,
                'error': str(e)
            }

    def get_pump_status(self, pump_id: int = None) -> dict:
        """
        Get pump status using cached data from existing controller (no new initialization!)
        
        Args:
            pump_id: Pump ID or None for all pumps
        
        Returns:
            dict: Pump status information
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for getting pump status")
            return {'error': 'System not available'}
        
        try:
            pump_controller = sys.pump_controller  # Use existing controller - no new initialization!
            
            if pump_id:
                # Return single pump status using cached calibration
                pump_info = pump_controller.get_pump_info(pump_id)
                if pump_info:
                    result = {
                        'id': pump_id,
                        'name': pump_info.get('name', f'Pump {pump_id}'),
                        'voltage': pump_info.get('voltage', 0),
                        'calibrated': pump_controller.is_calibrated(pump_id),  # Use cached status
                        'status': 'ready' if pump_controller.is_calibrated(pump_id) else 'uncalibrated',
                        'connected': pump_info.get('connected', False),
                        'is_dispensing': pump_info.get('is_dispensing', False),
                        'current_volume': pump_info.get('current_volume', 0),
                        'target_volume': pump_info.get('target_volume', 0)
                    }
                else:
                    result = {
                        'id': pump_id,
                        'name': f'Pump {pump_id}',
                        'error': 'Pump not found'
                    }
            else:
                # Return all pump statuses using cached calibration
                result = {}
                for pid in get_available_pumps():
                    pump_info = pump_controller.get_pump_info(pid)
                    if pump_info:
                        result[pid] = {
                            'id': pid,
                            'name': pump_info.get('name', f'Pump {pid}'),
                            'voltage': pump_info.get('voltage', 0),
                            'calibrated': pump_controller.is_calibrated(pid),  # Use cached status
                            'status': 'ready' if pump_controller.is_calibrated(pid) else 'uncalibrated',
                            'connected': pump_info.get('connected', False),
                            'is_dispensing': pump_info.get('is_dispensing', False),
                            'current_volume': pump_info.get('current_volume', 0),
                            'target_volume': pump_info.get('target_volume', 0)
                        }
            
            return result
            
        except Exception as e:
            logger.error(f"Exception getting pump status: {e}")
            return {'error': str(e)}

    def refresh_pump_calibrations(self) -> bool:
        """
        Manually refresh calibration status for all pumps using existing controller
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for refreshing calibrations")
            return False
        
        try:
            # Use existing controller - this will update the cached calibration status
            sys.pump_controller._check_all_calibrations()
            logger.info("Pump calibration status refreshed")
            return True
            
        except Exception as e:
            logger.error(f"Exception refreshing calibrations: {e}")
            return False

    def pause_pump(self, pump_id: int) -> bool:
        """
        Pause EZO pump during dispensing using existing controller
        
        Args:
            pump_id: Pump ID
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for pausing pump")
            return False
        
        try:
            # Send P command to pause using existing controller
            response = sys.pump_controller.send_command(pump_id, "P")
            success = response is not None
            
            if success:
                pump_name = get_pump_name(pump_id)
                logger.info(f"Paused {pump_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Exception pausing pump {pump_id}: {e}")
            return False

    def get_pump_voltage(self, pump_id: int) -> dict:
        """
        Get EZO pump voltage using existing controller
        
        Args:
            pump_id: Pump ID
        
        Returns:
            dict: Voltage info
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for getting voltage")
            return {
                'success': False,
                'pump_id': pump_id,
                'error': 'System not available'
            }
        
        try:
            # First try to get cached voltage info
            pump_info = sys.pump_controller.get_pump_info(pump_id)
            if pump_info and pump_info.get('voltage', 0) > 0:
                return {
                    'success': True,
                    'pump_id': pump_id,
                    'voltage': pump_info['voltage'],
                    'cached': True
                }
            
            # If no cached voltage, get it fresh
            response = sys.pump_controller.send_command(pump_id, "PV,?")
            
            if response and response.startswith("?PV,"):
                voltage_str = response.split(",")[1] if "," in response else "0"
                try:
                    voltage = float(voltage_str)
                    # Update cached voltage
                    sys.pump_controller.pump_info[pump_id]['voltage'] = voltage
                    return {
                        'success': True,
                        'pump_id': pump_id,
                        'voltage': voltage,
                        'raw_response': response
                    }
                except ValueError:
                    pass
            
            return {
                'success': False,
                'pump_id': pump_id,
                'error': 'Failed to get voltage'
            }
            
        except Exception as e:
            logger.error(f"Exception getting pump {pump_id} voltage: {e}")
            return {
                'success': False,
                'pump_id': pump_id,
                'error': str(e)
            }

    def get_current_dispensed_volume(self, pump_id: int) -> dict:
        """
        Get current dispensed volume from EZO pump using existing controller
        
        Args:
            pump_id: Pump ID
        
        Returns:
            dict: Volume info
        """
        sys = self.get_system()
        if not sys or not sys.pump_controller:
            logger.error("System or pump controller not available for getting current volume")
            return {
                'success': False,
                'pump_id': pump_id,
                'error': 'System not available'
            }
        
        try:
            # First try to get cached volume info
            pump_info = sys.pump_controller.get_pump_info(pump_id)
            if pump_info and pump_info.get('is_dispensing', False):
                return {
                    'success': True,
                    'pump_id': pump_id,
                    'current_volume': pump_info.get('current_volume', 0),
                    'cached': True
                }
            
            # If not dispensing or no cached data, get it fresh
            response = sys.pump_controller.send_command(pump_id, "R")
            
            if response:
                try:
                    volume = float(response)
                    return {
                        'success': True,
                        'pump_id': pump_id,
                        'current_volume': volume,
                        'raw_response': response
                    }
                except ValueError:
                    pass
            
            return {
                'success': False,
                'pump_id': pump_id,
                'error': 'Failed to get current volume'
            }
            
        except Exception as e:
            logger.error(f"Exception getting pump {pump_id} current volume: {e}")
            return {
                'success': False,
                'pump_id': pump_id,
                'error': str(e)
            }
    
    # =========================================================================
    # FLOW CONTROL - Same patterns as simple_gui.py
    # =========================================================================
    
    def start_flow(self, flow_id: int, gallons: Union[int, float]) -> bool:
        """
        Start flow monitoring using same pattern as simple_gui.py
        
        Args:
            flow_id: Flow meter ID
            gallons: Target gallons
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for flow control")
            return False
        
        # Same validation as simple_gui.py
        if flow_id not in get_available_flow_meters():
            logger.error(f"Invalid flow meter ID: {flow_id}")
            return False
        
        try:
            gal = int(gallons)
            if not (1 <= gal <= MAX_FLOW_GALLONS):
                logger.error(f"Gallons must be between 1 and {MAX_FLOW_GALLONS}, got: {gal}")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid gallons value: {gallons}")
            return False
        
        # Same command format as simple_gui.py
        command = f"Start;StartFlow;{flow_id};{gal};220;end"
        
        try:
            success = sys.send_command(command)
            
            if success:
                meter_name = get_flow_meter_name(flow_id)
                logger.info(f"Started {meter_name} for {gal} gallons")
            else:
                logger.error(f"Failed to start flow meter {flow_id}")
            
            return success
        except Exception as e:
            logger.error(f"Exception starting flow meter {flow_id}: {e}")
            return False
    
    def stop_flow(self, flow_id: int) -> bool:
        """
        Stop flow monitoring
        
        Args:
            flow_id: Flow meter ID
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for flow control")
            return False
        
        if flow_id not in get_available_flow_meters():
            logger.error(f"Invalid flow meter ID: {flow_id}")
            return False
        
        # Stop flow by setting gallons to 0
        command = f"Start;StartFlow;{flow_id};0;end"
        
        try:
            success = sys.send_command(command)
            
            if success:
                meter_name = get_flow_meter_name(flow_id)
                logger.info(f"Stopped {meter_name}")
            else:
                logger.error(f"Failed to stop flow meter {flow_id}")
            
            return success
        except Exception as e:
            logger.error(f"Exception stopping flow meter {flow_id}: {e}")
            return False

    def get_flow_status(self, flow_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed status for a specific flow meter

        Args:
            flow_id: Flow meter ID

        Returns:
            dict: Flow meter status or None if not available
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for flow status")
            return None

        if flow_id not in get_available_flow_meters():
            logger.error(f"Invalid flow meter ID: {flow_id}")
            return None

        try:
            return sys.get_flow_status(flow_id)
        except Exception as e:
            logger.error(f"Exception getting flow status {flow_id}: {e}")
            return None

    def get_flow_controller(self):
        """
        Get the flow controller instance for low-level access

        Returns:
            FlowMeterController or None if not available
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for getting flow controller")
            return None

        return sys.flow_controller if hasattr(sys, 'flow_controller') else None

    # =========================================================================
    # EC/pH SENSOR CONTROL - Same patterns as simple_gui.py
    # =========================================================================
    
    def start_ec_ph(self) -> bool:
        """
        Start EC/pH monitoring using exact same command as simple_gui.py
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for EC/pH control")
            return False
        
        # Exact same command format as simple_gui.py
        command = "Start;EcPh;ON;end"
        
        try:
            success = sys.send_command(command)
            
            if success:
                logger.info("EC/pH monitoring started")
            else:
                logger.error("Failed to start EC/pH monitoring")
            
            return success
        except Exception as e:
            logger.error(f"Exception starting EC/pH monitoring: {e}")
            return False
    
    def stop_ec_ph(self) -> bool:
        """
        Stop EC/pH monitoring using exact same command as simple_gui.py

        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for EC/pH control")
            return False

        # Exact same command format as simple_gui.py
        command = "Start;EcPh;OFF;end"

        try:
            success = sys.send_command(command)

            if success:
                logger.info("EC/pH monitoring stopped")
            else:
                logger.error("Failed to stop EC/pH monitoring")

            return success
        except Exception as e:
            logger.error(f"Exception stopping EC/pH monitoring: {e}")
            return False

    def read_ec_ph_sensors(self) -> dict:
        """
        Read EC and pH sensor values directly via I2C

        Returns:
            dict: EC and pH readings with timestamp
        """
        sys = self.get_system()
        if not sys or not sys.sensor_controller:
            logger.error("Sensor controller not available")
            return {
                'success': False,
                'error': 'Sensor controller not available'
            }

        try:
            readings = sys.sensor_controller.read_sensors()
            return {
                'success': True,
                'ph': readings.get('ph'),
                'ec': readings.get('ec'),
                'timestamp': readings.get('timestamp')
            }
        except Exception as e:
            logger.error(f"Exception reading EC/pH sensors: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def calibrate_ph(self, point: str, value: float = None) -> bool:
        """
        Calibrate pH sensor

        Args:
            point: Calibration point ('mid', 'low', 'high', or 'clear')
            value: Optional pH value (uses defaults from config if None)

        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys or not sys.sensor_controller:
            logger.error("Sensor controller not available for pH calibration")
            return False

        try:
            if point == 'mid':
                return sys.sensor_controller.calibrate_ph_mid(value)
            elif point == 'low':
                return sys.sensor_controller.calibrate_ph_low(value)
            elif point == 'high':
                return sys.sensor_controller.calibrate_ph_high(value)
            elif point == 'clear':
                return sys.sensor_controller.clear_ph_calibration()
            else:
                logger.error(f"Invalid pH calibration point: {point}")
                return False
        except Exception as e:
            logger.error(f"Exception calibrating pH: {e}")
            return False

    def calibrate_ec(self, point: str, value: int = None) -> bool:
        """
        Calibrate EC sensor

        Args:
            point: Calibration point ('dry', 'single', 'low', 'high', or 'clear')
            value: Optional EC value in μS/cm (uses defaults from config if None)

        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys or not sys.sensor_controller:
            logger.error("Sensor controller not available for EC calibration")
            return False

        try:
            if point == 'dry':
                return sys.sensor_controller.calibrate_ec_dry()
            elif point == 'single':
                return sys.sensor_controller.calibrate_ec_single(value)
            elif point == 'low':
                return sys.sensor_controller.calibrate_ec_low(value)
            elif point == 'high':
                return sys.sensor_controller.calibrate_ec_high(value)
            elif point == 'clear':
                return sys.sensor_controller.clear_ec_calibration()
            else:
                logger.error(f"Invalid EC calibration point: {point}")
                return False
        except Exception as e:
            logger.error(f"Exception calibrating EC: {e}")
            return False

    def get_sensor_calibration_status(self) -> dict:
        """
        Get calibration status for both pH and EC sensors

        Returns:
            dict: Calibration status information
        """
        sys = self.get_system()
        if not sys or not sys.sensor_controller:
            logger.error("Sensor controller not available")
            return {
                'success': False,
                'error': 'Sensor controller not available'
            }

        try:
            ph_status = sys.sensor_controller.get_ph_calibration_status()
            ec_status = sys.sensor_controller.get_ec_calibration_status()

            return {
                'success': True,
                'ph': {
                    'calibration_points': ph_status,
                    'status': 'calibrated' if ph_status and ph_status > 0 else 'uncalibrated'
                },
                'ec': {
                    'calibration_state': ec_status,
                    'status': 'calibrated' if ec_status and ec_status > 0 else 'uncalibrated'
                }
            }
        except Exception as e:
            logger.error(f"Exception getting sensor calibration status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # =========================================================================
    # EMERGENCY CONTROLS - Same as simple_gui.py
    # =========================================================================
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop using same method as simple_gui.py
        
        Returns:
            bool: Success status
        """
        sys = self.get_system()
        if not sys:
            logger.error("System not available for emergency stop")
            return False
        
        try:
            sys.emergency_stop()
            logger.warning("🚨 EMERGENCY STOP ACTIVATED 🚨")
            return True
        except Exception as e:
            logger.error(f"Exception during emergency stop: {e}")
            return False
    
    # =========================================================================
    # STATUS AND MONITORING - Same as simple_gui.py
    # =========================================================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status using same method as simple_gui.py
        
        Returns:
            dict: System status information
        """
        sys = self.get_system()
        if not sys:
            return {
                'error': 'System not available',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system_ready': False
            }
        
        try:
            # Same status call as simple_gui.py
            status = sys.get_system_status()
            
            # Add timestamp and system ready flag
            status['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status['system_ready'] = True
            
            return status
        except Exception as e:
            logger.error(f"Exception getting system status: {e}")
            return {
                'error': f'Status error: {e}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system_ready': False
            }
    
    def get_available_hardware(self) -> Dict[str, Any]:
        """
        Get available hardware configuration
        
        Returns:
            dict: Available hardware information
        """
        return {
            'pumps': {
                'ids': list(get_available_pumps()),
                'names': {pid: get_pump_name(pid) for pid in get_available_pumps()},
                'volume_limits': {
                    'min_ml': MIN_PUMP_VOLUME_ML,
                    'max_ml': MAX_PUMP_VOLUME_ML
                }
            },
            'relays': {
                'ids': list(get_available_relays()),
                'names': {rid: get_relay_name(rid) for rid in get_available_relays()}
            },
            'flow_meters': {
                'ids': list(get_available_flow_meters()),
                'names': {fid: get_flow_meter_name(fid) for fid in get_available_flow_meters()},
                'max_gallons': MAX_FLOW_GALLONS
            },
            'mock_settings': MOCK_SETTINGS.copy()
        }
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    
    def cleanup(self):
        """Clean up system resources"""
        with self.system_lock:
            if self.system:
                try:
                    # Turn off all relays for safety
                    self.all_relays_off()
                    logger.info("All relays turned off during cleanup")
                except Exception as e:
                    logger.error(f"Error turning off relays during cleanup: {e}")
                
                try:
                    # Stop the system
                    self.system.stop()
                    logger.info("System stopped during cleanup")
                except Exception as e:
                    logger.error(f"Error stopping system during cleanup: {e}")
                
                self.system = None

# =============================================================================
# CONVENIENCE FUNCTIONS - For easy Flask integration
# =============================================================================

# Global instance for Flask app
_hardware_comms: Optional[HardwareComms] = None
_comms_lock = threading.Lock()

def get_hardware_comms() -> HardwareComms:
    """Get or create the global hardware communications instance"""
    global _hardware_comms
    with _comms_lock:
        if _hardware_comms is None:
            _hardware_comms = HardwareComms()
        return _hardware_comms

# Convenience functions that use the global instance
def control_relay(relay_id: int, state: bool) -> bool:
    """Control relay - convenience function"""
    return get_hardware_comms().control_relay(relay_id, state)

def dispense_pump(pump_id: int, amount_ml: Union[int, float]) -> bool:
    """Dispense from pump - convenience function"""
    return get_hardware_comms().dispense_pump(pump_id, amount_ml)

def stop_pump(pump_id: int) -> bool:
    """Stop pump - convenience function"""
    return get_hardware_comms().stop_pump(pump_id)

def start_flow(flow_id: int, gallons: Union[int, float]) -> bool:
    """Start flow - convenience function"""
    return get_hardware_comms().start_flow(flow_id, gallons)

def stop_flow(flow_id: int) -> bool:
    """Stop flow - convenience function"""  
    return get_hardware_comms().stop_flow(flow_id)

def emergency_stop() -> bool:
    """Emergency stop - convenience function"""
    return get_hardware_comms().emergency_stop()

def get_system_status() -> Dict[str, Any]:
    """Get system status - convenience function"""
    return get_hardware_comms().get_system_status()

def get_available_hardware() -> Dict[str, Any]:
    """Get available hardware - convenience function"""
    return get_hardware_comms().get_available_hardware()

def all_relays_off() -> bool:
    """Turn all relays off - convenience function"""
    return get_hardware_comms().all_relays_off()

def start_ec_ph() -> bool:
    """Start EC/pH monitoring - convenience function"""
    return get_hardware_comms().start_ec_ph()

def stop_ec_ph() -> bool:
    """Stop EC/pH monitoring - convenience function"""
    return get_hardware_comms().stop_ec_ph()

def calibrate_pump(pump_id: int, actual_volume_ml: float) -> bool:
    """Calibrate pump - convenience function"""
    return get_hardware_comms().calibrate_pump(pump_id, actual_volume_ml)

def clear_pump_calibration(pump_id: int) -> bool:
    """Clear pump calibration - convenience function"""
    return get_hardware_comms().clear_pump_calibration(pump_id)

def check_pump_calibration_status(pump_id: int) -> dict:
    """Check pump calibration status - convenience function"""
    return get_hardware_comms().check_pump_calibration_status(pump_id)

def pause_pump(pump_id: int) -> bool:
    """Pause pump - convenience function"""
    return get_hardware_comms().pause_pump(pump_id)

def get_pump_voltage(pump_id: int) -> dict:
    """Get pump voltage - convenience function"""
    return get_hardware_comms().get_pump_voltage(pump_id)

def get_current_dispensed_volume(pump_id: int) -> dict:
    """Get current dispensed volume - convenience function"""
    return get_hardware_comms().get_current_dispensed_volume(pump_id)

def get_pump_status(pump_id: int = None) -> dict:
    """Get pump status - convenience function"""
    return get_hardware_comms().get_pump_status(pump_id)

def refresh_pump_calibrations() -> bool:
    """Refresh pump calibrations - convenience function"""
    return get_hardware_comms().refresh_pump_calibrations()

def read_ec_ph_sensors() -> dict:
    """Read EC/pH sensors - convenience function"""
    return get_hardware_comms().read_ec_ph_sensors()

def calibrate_ph(point: str, value: float = None) -> bool:
    """Calibrate pH sensor - convenience function"""
    return get_hardware_comms().calibrate_ph(point, value)

def calibrate_ec(point: str, value: int = None) -> bool:
    """Calibrate EC sensor - convenience function"""
    return get_hardware_comms().calibrate_ec(point, value)

def get_sensor_calibration_status() -> dict:
    """Get sensor calibration status - convenience function"""
    return get_hardware_comms().get_sensor_calibration_status()

def get_flow_status(flow_id: int) -> Optional[Dict[str, Any]]:
    """Get flow status - convenience function"""
    return get_hardware_comms().get_flow_status(flow_id)

def get_flow_controller():
    """Get flow controller instance - convenience function"""
    return get_hardware_comms().get_flow_controller()

def cleanup_hardware():
    """Cleanup hardware resources - convenience function"""
    global _hardware_comms
    with _comms_lock:
        if _hardware_comms:
            _hardware_comms.cleanup()
            _hardware_comms = None

# Legacy export for backward compatibility
flow_controller = None  # Will be dynamically accessed via get_flow_controller()

# =============================================================================
# TESTING FUNCTIONS
# =============================================================================

def test_hardware_comms():
    """Test basic hardware communications"""
    print("Testing Hardware Communications...")
    
    # Get hardware info
    hardware = get_available_hardware()
    print(f"Available pumps: {hardware['pumps']['ids']}")
    print(f"Available relays: {hardware['relays']['ids']}")
    print(f"Available flow meters: {hardware['flow_meters']['ids']}")
    
    # Get system status
    status = get_system_status()
    print(f"System ready: {status.get('system_ready', False)}")
    print(f"Status timestamp: {status.get('timestamp', 'unknown')}")
    
    print("Hardware communications test complete.")

if __name__ == "__main__":
    test_hardware_comms()