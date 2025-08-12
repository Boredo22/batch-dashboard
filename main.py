#!/usr/bin/env python3
"""
Main Raspberry Pi Feed Control System
Coordinates pumps, relays, flow meters, and Arduino Uno EC/pH
"""

import time
import threading
import logging
import queue
from datetime import datetime

from rpi_pumps import EZOPumpController
from rpi_relays import RelayController, get_relay_name
from rpi_flow import FlowMeterController, MockFlowMeterController
from arduino_uno_comm import ArduinoUnoController, find_arduino_uno_port

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeedControlSystem:
    def __init__(self, uno_port=None, use_mock_flow=False):
        """Initialize the complete feed control system"""
        self.running = False
        self.command_queue = queue.Queue()
        self.worker_thread = None
        self.message_callback = None
        
        # Initialize controllers
        logger.info("Initializing controllers...")
        
        try:
            # Initialize pump controller
            self.pump_controller = EZOPumpController()
            logger.info("✓ Pump controller initialized")
        except Exception as e:
            logger.error(f"✗ Pump controller failed: {e}")
            self.pump_controller = None
        
        try:
            # Initialize relay controller
            self.relay_controller = RelayController()
            logger.info("✓ Relay controller initialized")
        except Exception as e:
            logger.error(f"✗ Relay controller failed: {e}")
            self.relay_controller = None
        
        try:
            # Initialize flow controller (mock for testing if needed)
            if use_mock_flow:
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
            command = self.command_queue.get_nowait()
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
        
        relay_no = int(parts[2])
        state = parts[3].upper() == "ON"
        
        if relay_no == 0:  # All relays
            success = self.relay_controller.set_all_relays(state)
        else:
            success = self.relay_controller.set_relay(relay_no, state)
        
        if success:
            state_str = "ON" if state else "OFF"
            self.send_message(f"Start;RelayResponse;{relay_no};{state_str};end")
    
    def _handle_dispense_command(self, parts):
        """Handle dispense commands: Start;Dispense;pump_addr;amount;end"""
        if len(parts) < 5 or not self.pump_controller:
            return
        
        pump_addr = int(parts[2])
        amount = float(parts[3])
        
        success = self.pump_controller.start_dispense(pump_addr, amount)
        if success:
            self.send_message(f"Start;Update;NuteStat;{pump_addr};ON;0.0;{amount:.2f};end")
    
    def _handle_pump_command(self, parts):
        """Handle raw pump commands: Start;Pump;pump_addr;command;end"""
        if len(parts) < 5 or not self.pump_controller:
            return
        
        pump_addr = int(parts[2])
        command = parts[3]
        
        response = self.pump_controller.send_command(pump_addr, command)
        self.send_message(f"Start;PumpResponse;{pump_addr};{response};end")
    
    def _handle_calibration_command(self, parts):
        """Handle calibration commands: Start;Cal;pump_addr;amount;end"""
        if len(parts) < 5 or not self.pump_controller:
            return
        
        pump_addr = int(parts[2])
        amount = parts[3]
        
        success = self.pump_controller.calibrate_pump(pump_addr, amount)
        if success:
            self.send_message(f"Start;Update;NuteStat;{pump_addr};Cal;{amount};end")
    
    def _handle_flow_command(self, parts):
        """Handle flow commands: Start;StartFlow;flow_no;gallons;[ppg];end"""
        if len(parts) < 5 or not self.flow_controller:
            return
        
        flow_no = int(parts[2])
        gallons = int(parts[3])
        ppg = int(parts[4]) if len(parts) > 5 and parts[4] != "end" else None
        
        if gallons == 0:
            success = self.flow_controller.stop_flow(flow_no)
        else:
            success = self.flow_controller.start_flow(flow_no, gallons, ppg)
        
        if success:
            self.send_message(f"Start;Update;StartFlow;{flow_no};{gallons};end")
    
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
        if current_time - self.last_pump_check >= 1.0:
            self.last_pump_check = current_time
            
            if self.pump_controller:
                for pump_addr in range(1, 9):
                    pump_info = self.pump_controller.get_pump_info(pump_addr)
                    if pump_info and pump_info['is_dispensing']:
                        still_running = self.pump_controller.check_pump_status(pump_addr)
                        
                        # Send status update
                        status_str = "ON" if still_running else "OFF"
                        current_vol = pump_info['current_volume']
                        target_vol = pump_info['target_volume']
                        
                        self.send_message(
                            f"Start;Update;NuteStat;{pump_addr};{status_str};"
                            f"{current_vol:.2f};{target_vol:.2f};end"
                        )
        
        # Update flow meters every 2 seconds
        if current_time - self.last_status_update >= 2.0:
            self.last_status_update = current_time
            
            if self.flow_controller:
                for meter_id in [1, 2]:
                    still_running = self.flow_controller.update_flow_status(meter_id)
                    status = self.flow_controller.get_flow_status(meter_id)
                    
                    if status and status['status'] == 1:  # Active
                        self.send_message(
                            f"Start;Update;FlowStat;{meter_id};"
                            f"{status['current_gallons']};{status['pulse_count']};end"
                        )
                    elif not still_running and status and status['current_gallons'] > 0:
                        # Flow completed
                        self.send_message(f"Start;Update;FlowComplete;{meter_id};end")
    
    def _print_system_info(self):
        """Print system startup information"""
        self.send_message("=" * 60)
        self.send_message("   Raspberry Pi Feed Control System v2.0")
        self.send_message("=" * 60)
        self.send_message("System Configuration:")
        self.send_message("- EZO Pumps: 8 units (I2C)")
        self.send_message("- Control Relays: 16 units (GPIO)")
        self.send_message("- Flow Meters: 2 units (GPIO interrupts)")
        self.send_message("- EC/pH Sensors: Arduino Uno (Serial)")
        self.send_message("")
        self.send_message("System Status:")
        
        # Show pump info
        if self.pump_controller:
            for pump_addr in range(1, 9):
                info = self.pump_controller.get_pump_info(pump_addr)
                if info:
                    status = "Calibrated" if info['calibrated'] else "Uncalibrated"
                    self.send_message(f"Pump {pump_addr}: {info['name']} ({status}, {info['voltage']:.1f}V)")
        
        self.send_message("")
        self.send_message("Ready to accept commands.")
        self.send_message("=" * 60)
    
    def send_command(self, command):
        """Queue a command for processing"""
        try:
            self.command_queue.put(command, timeout=1)
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
        
        self.send_message("Start;Update;EmergencyStop;Complete;end")
    
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
    
    print("Raspberry Pi Feed Control System")
    print("================================")
    
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
                print("  Start;Relay;1;ON;end        - Turn on relay 1")
                print("  Start;Relay;1;OFF;end       - Turn off relay 1")
                print("  Start;Dispense;1;10.0;end   - Dispense 10ml from pump 1")
                print("  Start;StartFlow;1;5;220;end - Start flow meter 1 for 5 gallons")
                print("  Start;EcPh;ON;end           - Start EC/pH monitoring")
                print("  emergency                   - Emergency stop all devices")
                print("  status                      - Show system status")
                print("  quit                        - Exit program")
            elif command.lower() == 'emergency':
                system.emergency_stop()
            elif command.lower() == 'status':
                status = system.get_system_status()
                print(f"\nSystem Status:")
                print(f"  Running: {status['running']}")
                print(f"  Active pumps: {sum(1 for p in status['pumps'].values() if p and p['is_dispensing'])}")
                print(f"  Active relays: {sum(1 for state in status['relays'].values() if state)}")
                print(f"  Active flows: {sum(1 for f in status['flow_meters'].values() if f['status'] == 1)}")
                
                if status['ec_ph']:
                    ec = status['ec_ph'].get('ec', 'No reading')
                    ph = status['ec_ph'].get('ph', 'No reading')
                    print(f"  EC: {ec} mS/cm, pH: {ph}")
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