#!/usr/bin/env python3
"""
Main Raspberry Pi Feed Control System
Updated to use centralized configuration from config.py
"""

import time
import threading
import logging
import queue
from datetime import datetime

# Import updated controllers
from hardware.rpi_pumps import EZOPumpController
from hardware.rpi_relays import RelayController
from hardware.rpi_flow import FlowMeterController, MockFlowMeterController
from hardware.rpi_unoComm import ArduinoUnoController, find_arduino_uno_port

# Import configuration
from config import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_LEVELS,
    STATUS_UPDATE_INTERVAL,
    PUMP_CHECK_INTERVAL,
    COMMAND_TIMEOUT,
    USE_MOCK_HARDWARE,
    MOCK_SETTINGS,
    MESSAGE_FORMATS,
    get_available_pumps,
    get_available_relays,
    get_available_flow_meters,
    get_relay_name,
    get_pump_name,
    get_flow_meter_name
)

# Setup logging with configuration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Set component-specific log levels
for component, level in LOG_LEVELS.items():
    component_logger = logging.getLogger(component)
    component_logger.setLevel(getattr(logging, level))

class FeedControlSystem:
    def __init__(self, uno_port=None, use_mock_flow=None):
        """Initialize the complete feed control system"""
        self.running = False
        self.command_queue = queue.Queue()
        self.worker_thread = None
        self.message_callback = None
        
        # Use config for mock settings
        if use_mock_flow is None:
            use_mock_flow = MOCK_SETTINGS.get('flow_meters', False)
        
        # Initialize controllers
        logger.info("Initializing feed control system with config.py...")
        
        try:
            # Initialize pump controller
            if MOCK_SETTINGS.get('pumps', False):
                logger.info("Using mock pump controller")
                self.pump_controller = None  # Would implement mock pump controller
            else:
                self.pump_controller = EZOPumpController()
                logger.info("✓ EZO pump controller initialized")
        except Exception as e:
            logger.error(f"✗ Pump controller failed: {e}")
            self.pump_controller = None
        
        try:
            # Initialize relay controller
            if MOCK_SETTINGS.get('relays', False):
                logger.info("Using mock relay controller")
                self.relay_controller = None  # Would implement mock relay controller
            else:
                self.relay_controller = RelayController()
                logger.info("✓ Relay controller initialized")
        except Exception as e:
            logger.error(f"✗ Relay controller failed: {e}")
            self.relay_controller = None
        
        try:
            # Initialize flow controller
            if use_mock_flow or MOCK_SETTINGS.get('flow_meters', False):
                self.flow_controller = MockFlowMeterController()
                logger.info("✓ Mock flow controller initialized")
            else:
                self.flow_controller = FlowMeterController()
                logger.info("✓ Flow controller initialized")
        except Exception as e:
            logger.error(f"✗ Flow controller failed: {e}")
            self.flow_controller = None
        
        try:
            # Initialize Arduino Uno controller
            if MOCK_SETTINGS.get('arduino', False):
                logger.info("Using mock Arduino controller")
                self.uno_controller = None  # Would implement mock Arduino controller
            else:
                if uno_port is None:
                    uno_port = find_arduino_uno_port()
                
                if uno_port:
                    self.uno_controller = ArduinoUnoController(port=uno_port)
                    logger.info(f"✓ Arduino Uno controller initialized on {uno_port}")
                else:
                    logger.warning("✗ Arduino Uno port not found")
                    self.uno_controller = None
        except Exception as e:
            logger.error(f"✗ Arduino Uno controller failed: {e}")
            self.uno_controller = None
        
        # Timing for status updates
        self.last_status_update = 0
        self.last_pump_check = 0
    
    def set_message_callback(self, callback):
        """Set callback for system messages"""
        self.message_callback = callback
        
        # Set callback for Arduino Uno messages too
        if self.uno_controller:
            self.uno_controller.set_message_callback(callback)
    
    def send_message(self, message):
        """Send a message via callback"""
        if self.message_callback:
            self.message_callback(message)
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {message}")
    
    def start(self):
        """Start the feed control system"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Start EC/pH monitoring if available
        if self.uno_controller:
            self.uno_controller.start_monitoring()
        
        # Print system info
        self._print_system_info()
        
        logger.info("Feed control system started")
    
    def stop(self):
        """Stop the feed control system"""
        if not self.running:
            return
        
        logger.info("Stopping feed control system...")
        
        self.running = False
        
        # Stop worker thread
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        # Emergency stop all devices
        self.emergency_stop()
        
        # Close all controllers
        if self.pump_controller:
            self.pump_controller.close()
        if self.relay_controller:
            self.relay_controller.cleanup()
        if self.flow_controller:
            self.flow_controller.cleanup()
        if self.uno_controller:
            self.uno_controller.close()
        
        logger.info("Feed control system stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                # Process commands
                self._process_commands()
                
                # Update device statuses
                self._update_devices()
                
                time.sleep(0.01)  # Small delay
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)
    
    def _process_commands(self):
        """Process queued commands"""
        try:
            command = self.command_queue.get(timeout=0.001)  # Very short timeout
            self._execute_command(command)
        except queue.Empty:
            pass
    
    def _execute_command(self, command_str):
        """Execute a command string"""
        logger.debug(f"Executing command: {command_str}")
        
        # Parse command: Start;Type;Param1;Param2;...;end
        parts = command_str.strip().split(';')
        
        if len(parts) < 3 or parts[0] != "Start" or parts[-1] != "end":
            logger.error(f"Invalid command format: {command_str}")
            return
        
        cmd_type = parts[1]
        
        try:
            if cmd_type == "Relay":
                self._handle_relay_command(parts)
            elif cmd_type == "Dispense":
                self._handle_dispense_command(parts)
            elif cmd_type == "Pump":
                self._handle_pump_command(parts)
            elif cmd_type == "Cal":
                self._handle_calibration_command(parts)
            elif cmd_type == "StartFlow":
                self._handle_flow_command(parts)
            elif cmd_type == "EcPh":
                self._handle_ecph_command(parts)
            else:
                logger.warning(f"Unknown command type: {cmd_type}")
        
        except Exception as e:
            logger.error(f"Error executing {cmd_type} command: {e}")
    
    def _handle_relay_command(self, parts):
        """Handle relay commands: Start;Relay;relay_no;state;end"""
        if len(parts) < 5 or not self.relay_controller:
            return
        
        try:
            relay_no = int(parts[2])
            state = parts[3].upper() == "ON"
            
            if relay_no == 0:  # All relays
                success = self.relay_controller.set_all_relays(state)
            else:
                success = self.relay_controller.set_relay(relay_no, state)
            
            if success:
                state_str = "ON" if state else "OFF"
                message = MESSAGE_FORMATS["relay_response"].format(
                    relay_id=relay_no, state=state_str
                )
                self.send_message(message)
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid relay command: {e}")
    
    def _handle_dispense_command(self, parts):
        """Handle dispense commands: Start;Dispense;pump_addr;amount;end"""
        if len(parts) < 5 or not self.pump_controller:
            return
        
        try:
            pump_addr = int(parts[2])
            amount = float(parts[3])
            
            success = self.pump_controller.start_dispense(pump_addr, amount)
            if success:
                message = MESSAGE_FORMATS["nute_status"].format(
                    pump_id=pump_addr, status="ON", current=0.0, target=amount
                )
                self.send_message(message)
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid dispense command: {e}")
    
    def _handle_pump_command(self, parts):
        """Handle raw pump commands: Start;Pump;pump_addr;command;end"""
        if len(parts) < 5 or not self.pump_controller:
            return
        
        try:
            pump_addr = int(parts[2])
            command = parts[3]
            
            response = self.pump_controller.send_command(pump_addr, command)
            message = MESSAGE_FORMATS["pump_response"].format(
                pump_id=pump_addr, response=response or "ERROR"
            )
            self.send_message(message)
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid pump command: {e}")
    
    def _handle_calibration_command(self, parts):
        """Handle calibration commands: Start;Cal;pump_addr;amount;end"""
        if len(parts) < 5 or not self.pump_controller:
            return
        
        try:
            pump_addr = int(parts[2])
            amount = float(parts[3])
            
            success = self.pump_controller.calibrate_pump(pump_addr, amount)
            if success:
                message = MESSAGE_FORMATS["nute_status"].format(
                    pump_id=pump_addr, status="Cal", current=amount, target=0
                )
                self.send_message(message)
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid calibration command: {e}")
    
    def _handle_flow_command(self, parts):
        """Handle flow commands: Start;StartFlow;flow_no;gallons;[ppg];end"""
        if len(parts) < 5 or not self.flow_controller:
            return
        
        try:
            flow_no = int(parts[2])
            gallons = int(parts[3])
            ppg = int(parts[4]) if len(parts) > 5 and parts[4] != "end" else None
            
            if gallons == 0:
                success = self.flow_controller.stop_flow(flow_no)
            else:
                success = self.flow_controller.start_flow(flow_no, gallons, ppg)
            
            if success:
                message = MESSAGE_FORMATS["flow_status"].format(
                    flow_id=flow_no, gallons=gallons, pulses=0
                )
                self.send_message(message)
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid flow command: {e}")
    
    def _handle_ecph_command(self, parts):
        """Handle EC/pH commands: Start;EcPh;command;end"""
        if len(parts) < 4 or not self.uno_controller:
            return
        
        command = parts[2].upper()
        
        if command == "ON":
            self.uno_controller.start_monitoring()
        elif command == "OFF":
            self.uno_controller.stop_monitoring()
        
        self.send_message(f"Start;Update;EcPhStatus;{command};end")
    
    def _update_devices(self):
        """Update all device statuses"""
        current_time = time.time()
        
        # Update pumps every second
        if current_time - self.last_pump_check >= PUMP_CHECK_INTERVAL:
            self.last_pump_check = current_time
            
            if self.pump_controller:
                for pump_addr in get_available_pumps():
                    pump_info = self.pump_controller.get_pump_info(pump_addr)
                    if pump_info and pump_info['is_dispensing']:
                        still_running = self.pump_controller.check_pump_status(pump_addr)
                        
                        # Send status update
                        status_str = "ON" if still_running else "OFF"
                        current_vol = pump_info['current_volume']
                        target_vol = pump_info['target_volume']
                        
                        message = MESSAGE_FORMATS["nute_status"].format(
                            pump_id=pump_addr, status=status_str,
                            current=f"{current_vol:.2f}", target=f"{target_vol:.2f}"
                        )
                        self.send_message(message)
        
        # Update flow meters every 2 seconds
        if current_time - self.last_status_update >= STATUS_UPDATE_INTERVAL:
            self.last_status_update = current_time
            
            if self.flow_controller:
                for meter_id in get_available_flow_meters():
                    still_running = self.flow_controller.update_flow_status(meter_id)
                    status = self.flow_controller.get_flow_status(meter_id)
                    
                    if status and status['status'] == 1:  # Active
                        message = MESSAGE_FORMATS["flow_status"].format(
                            flow_id=meter_id,
                            gallons=status['current_gallons'],
                            pulses=status['pulse_count']
                        )
                        self.send_message(message)
                    elif not still_running and status and status['current_gallons'] > 0:
                        # Flow completed
                        message = MESSAGE_FORMATS["flow_complete"].format(flow_id=meter_id)
                        self.send_message(message)
    
    def _print_system_info(self):
        """Print system startup information"""
        self.send_message("=" * 60)
        self.send_message("   Raspberry Pi Feed Control System v2.0")
        self.send_message("=" * 60)
        self.send_message("System Configuration (from config.py):")
        
        # Show available components
        pumps = get_available_pumps()
        relays = get_available_relays()
        flow_meters = get_available_flow_meters()
        
        self.send_message(f"- EZO Pumps: {len(pumps)} units (I2C)")
        self.send_message(f"- Control Relays: {len(relays)} units (GPIO)")
        self.send_message(f"- Flow Meters: {len(flow_meters)} units (GPIO interrupts)")
        self.send_message("- EC/pH Sensors: Arduino Uno (Serial)")
        self.send_message("")
        self.send_message("System Status:")
        
        # Show pump info
        if self.pump_controller:
            all_pumps = self.pump_controller.get_all_pumps_status()
            for pump_id, info in all_pumps.items():
                if info['connected']:
                    pump_name = get_pump_name(pump_id)
                    status = "Calibrated" if info['calibrated'] else "Uncalibrated"
                    self.send_message(f"Pump {pump_id}: {pump_name} ({status}, {info['voltage']:.1f}V)")
        
        # Show relay info
        if self.relay_controller:
            for relay_id in relays:
                relay_name = get_relay_name(relay_id)
                self.send_message(f"Relay {relay_id}: {relay_name}")
        
        # Show flow meter info
        if self.flow_controller:
            for meter_id in flow_meters:
                meter_name = get_flow_meter_name(meter_id)
                self.send_message(f"Flow {meter_id}: {meter_name}")
        
        self.send_message("")
        self.send_message("Ready to accept commands.")
        self.send_message("=" * 60)
    
    def send_command(self, command):
        """Queue a command for processing"""
        try:
            self.command_queue.put(command, timeout=COMMAND_TIMEOUT)
            return True
        except queue.Full:
            logger.error("Command queue is full")
            return False
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        logger.warning("EMERGENCY STOP")
        
        # Stop all pumps
        if self.pump_controller:
            self.pump_controller.emergency_stop()
        
        # Turn off all relays
        if self.relay_controller:
            self.relay_controller.emergency_stop()
        
        # Stop all flow meters
        if self.flow_controller:
            self.flow_controller.emergency_stop()
        
        self.send_message(MESSAGE_FORMATS["emergency_stop"])
    
    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            'running': self.running,
            'pumps': {},
            'relays': {},
            'flow_meters': {},
            'ec_ph': {}
        }
        
        # Get pump statuses
        if self.pump_controller:
            status['pumps'] = self.pump_controller.get_all_pumps_status()
        
        # Get relay statuses
        if self.relay_controller:
            status['relays'] = self.relay_controller.get_all_relay_states()
        
        # Get flow meter statuses
        if self.flow_controller:
            status['flow_meters'] = self.flow_controller.get_all_flow_status()
        
        # Get EC/pH status
        if self.uno_controller:
            status['ec_ph'] = self.uno_controller.get_latest_readings()
        
        return status


# Simple command-line interface
def main():
    """Main entry point"""
    import sys
    import signal
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Raspberry Pi Feed Control System (Using config.py)")
    print("=" * 55)
    
    # Check command line arguments
    use_mock_flow = "--mock-flow" in sys.argv
    uno_port = None
    
    for i, arg in enumerate(sys.argv):
        if arg == "--uno-port" and i + 1 < len(sys.argv):
            uno_port = sys.argv[i + 1]
    
    # Create and start system
    system = FeedControlSystem(uno_port=uno_port, use_mock_flow=use_mock_flow)
    system.start()
    
    # Interactive command loop
    print("\nEnter commands (or 'help' for options, 'quit' to exit):")
    
    while system.running:
        try:
            command = input("feed> ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
            elif command.lower() == 'help':
                print("\nAvailable commands:")
                print("  Start;Relay;1;ON;end        - Turn on relay")
                print("  Start;Relay;1;OFF;end       - Turn off relay")
                print("  Start;Dispense;1;10.0;end   - Dispense 10ml from pump 1")
                print("  Start;StartFlow;1;5;220;end - Start flow meter 1 for 5 gallons")
                print("  Start;EcPh;ON;end           - Start EC/pH monitoring")
                print("  emergency                   - Emergency stop all devices")
                print("  status                      - Show system status")
                print("  config                      - Show configuration")
                print("  quit                        - Exit program")
            elif command.lower() == 'emergency':
                system.emergency_stop()
            elif command.lower() == 'status':
                status = system.get_system_status()
                print(f"\nSystem Status:")
                print(f"  Running: {status['running']}")
                print(f"  Active pumps: {sum(1 for p in status['pumps'].values() if p and p.get('is_dispensing', False))}")
                print(f"  Active relays: {sum(1 for state in status['relays'].values() if state)}")
                print(f"  Active flows: {sum(1 for f in status['flow_meters'].values() if f and f.get('status') == 1)}")
                
                if status['ec_ph']:
                    ec = status['ec_ph'].get('ec', 'No reading')
                    ph = status['ec_ph'].get('ph', 'No reading')
                    print(f"  EC: {ec} mS/cm, pH: {ph}")
            elif command.lower() == 'config':
                print(f"\nSystem Configuration:")
                print(f"  Available Pumps: {get_available_pumps()}")
                print(f"  Available Relays: {get_available_relays()}")
                print(f"  Available Flow Meters: {get_available_flow_meters()}")
                print(f"  Mock Hardware: {MOCK_SETTINGS}")
            elif command.startswith('Start;'):
                success = system.send_command(command)
                if success:
                    print("✓ Command sent")
                else:
                    print("✗ Failed to send command")
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    
    system.stop()
    print("Goodbye!")


if __name__ == "__main__":
    main()