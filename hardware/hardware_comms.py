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

def cleanup_hardware():
    """Cleanup hardware resources - convenience function"""
    global _hardware_comms
    with _comms_lock:
        if _hardware_comms:
            _hardware_comms.cleanup()
            _hardware_comms = None

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