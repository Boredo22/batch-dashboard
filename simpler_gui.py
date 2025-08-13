#!/usr/bin/env python3
"""
Simpler Tkinter GUI for Testing Raspberry Pi Components
Focuses only on relays, flow meters and Arduino Uno connection
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import logging

# Import the specific controllers
from rpi_relays import RelayController
from rpi_flow import FlowMeterController, MockFlowMeterController
from arduino_uno_comm import ArduinoUnoController, find_arduino_uno_port

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimplerGUI")

class SimplerTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi Component Tester")
        self.root.geometry("1000x750")
        
        # Initialize controller components
        self.relay_controller = None
        self.flow_controller = None
        self.arduino_controller = None
        
        self.system_running = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Schedule system start after main loop begins
        self.root.after(100, self.initialize_controllers)
        
        # Schedule status updates
        self.root.after(500, self.update_status)
        
        # Set up proper closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # System status frame
        self.create_status_frame(main_frame)
        
        # Control frames
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Relay control on left
        self.create_relay_control(left_frame)
        
        # Flow meter control on right top
        self.create_flow_control(right_frame)
        
        # Arduino control on right bottom
        self.create_arduino_control(right_frame)
        
        # Log frame at bottom
        self.create_log_frame(main_frame)
    
    def create_status_frame(self, parent):
        """Create system status display"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="System: Initializing...", 
                                      font=('Arial', 12, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Component status
        self.components_label = ttk.Label(status_frame, 
                                         text="Relays: Not Connected | Flow: Not Connected | Arduino: Not Connected")
        self.components_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Emergency stop button
        emergency_btn = ttk.Button(status_frame, text="🚨 EMERGENCY STOP 🚨", 
                                  command=self.emergency_stop)
        emergency_btn.grid(row=0, column=2, sticky=tk.E, padx=(20, 0))
        
        status_frame.columnconfigure(1, weight=1)
    
    def create_relay_control(self, parent):
        """Create relay control panel"""
        relay_frame = ttk.LabelFrame(parent, text="Relay Control", padding="10")
        relay_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for relays
        canvas = tk.Canvas(relay_frame)
        scrollbar = ttk.Scrollbar(relay_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Relay buttons
        relay_names = {
            1: "Tank 1 Fill", 2: "Tank 2 Fill", 3: "Tank 3 Fill",
            4: "Tank 1 Nute", 5: "Tank 2 Nute", 6: "Tank 3 Nute",
            7: "Tank 1 Send", 8: "Tank 2 Send", 9: "Tank 3 Send",
            10: "Room 1", 11: "Room 2", 12: "Room 3",
            13: "Tank Drain", 14: "Spare 1", 15: "Spare 2", 16: "Spare 3"
        }
        
        self.relay_buttons = {}
        
        for i in range(1, 17):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            
            name = relay_names.get(i, f"Relay {i}")
            label = ttk.Label(frame, text=f"{i:2d}. {name}:", width=20, anchor="w")
            label.pack(side=tk.LEFT)
            
            on_btn = ttk.Button(frame, text="ON", width=6,
                               command=lambda r=i: self.control_relay(r, True))
            on_btn.pack(side=tk.LEFT, padx=(5, 2))
            
            off_btn = ttk.Button(frame, text="OFF", width=6,
                                command=lambda r=i: self.control_relay(r, False))
            off_btn.pack(side=tk.LEFT, padx=(2, 5))
            
            status_label = ttk.Label(frame, text="OFF", width=6, anchor="center")
            status_label.pack(side=tk.LEFT, padx=(5, 0))
            
            self.relay_buttons[i] = {
                'on': on_btn,
                'off': off_btn,
                'status': status_label
            }
        
        # All relays off button
        all_off_frame = ttk.Frame(scrollable_frame)
        all_off_frame.pack(fill=tk.X, pady=(10, 0))
        all_off_btn = ttk.Button(all_off_frame, text="ALL RELAYS OFF", 
                                command=self.all_relays_off)
        all_off_btn.pack(fill=tk.X)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_flow_control(self, parent):
        """Create flow meter control panel"""
        flow_frame = ttk.LabelFrame(parent, text="Flow Meter Control", padding="10")
        flow_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Flow meter selection
        control_frame = ttk.Frame(flow_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Flow Meter:").grid(row=0, column=0, sticky=tk.W)
        self.flow_var = tk.IntVar(value=1)
        flow_combo = ttk.Combobox(control_frame, textvariable=self.flow_var,
                                  values=[1, 2], state="readonly", width=5)
        flow_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Gallons entry
        ttk.Label(control_frame, text="Gallons:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.gallons_var = tk.StringVar(value="5")
        gallons_entry = ttk.Entry(control_frame, textvariable=self.gallons_var, width=10)
        gallons_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Buttons
        start_flow_btn = ttk.Button(control_frame, text="Start Flow", command=self.start_flow)
        start_flow_btn.grid(row=0, column=4, padx=(10, 0))
        
        stop_flow_btn = ttk.Button(control_frame, text="Stop Flow", command=self.stop_flow)
        stop_flow_btn.grid(row=0, column=5, padx=(5, 0))
        
        # Status frame
        status_frame = ttk.Frame(flow_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Status display for each flow meter
        self.flow_status_labels = {}
        
        for i in [1, 2]:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)
            
            label = ttk.Label(frame, text=f"Flow {i}:")
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            status = ttk.Label(frame, text="Inactive")
            status.pack(side=tk.LEFT)
            
            self.flow_status_labels[i] = status
    
    def create_arduino_control(self, parent):
        """Create Arduino Uno control panel"""
        arduino_frame = ttk.LabelFrame(parent, text="Arduino Uno Control", padding="10")
        arduino_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection details
        conn_frame = ttk.Frame(arduino_frame)
        conn_frame.pack(fill=tk.X, pady=5)
        
        self.arduino_port_label = ttk.Label(conn_frame, text="Port: Not connected")
        self.arduino_port_label.pack(side=tk.LEFT)
        
        self.arduino_status_label = ttk.Label(conn_frame, text="Status: Disconnected")
        self.arduino_status_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Control buttons
        btn_frame = ttk.Frame(arduino_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        connect_btn = ttk.Button(btn_frame, text="Connect", command=self.connect_arduino)
        connect_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        start_monitor_btn = ttk.Button(btn_frame, text="Start Monitoring", 
                                      command=self.start_arduino_monitoring)
        start_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        stop_monitor_btn = ttk.Button(btn_frame, text="Stop Monitoring", 
                                     command=self.stop_arduino_monitoring)
        stop_monitor_btn.pack(side=tk.LEFT, padx=5)
        
        # EC/pH readings
        readings_frame = ttk.LabelFrame(arduino_frame, text="Sensor Readings", padding="5")
        readings_frame.pack(fill=tk.X, pady=5)
        
        self.ec_reading_label = ttk.Label(readings_frame, text="EC: -- mS/cm", font=('Arial', 12))
        self.ec_reading_label.pack(anchor=tk.W)
        
        self.ph_reading_label = ttk.Label(readings_frame, text="pH: --", font=('Arial', 12))
        self.ph_reading_label.pack(anchor=tk.W)
    
    def create_log_frame(self, parent):
        """Create log display"""
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log control buttons
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        clear_log_btn = ttk.Button(log_btn_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.pack(side=tk.LEFT)
        
        save_log_btn = ttk.Button(log_btn_frame, text="Save Log", command=self.save_log)
        save_log_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    def initialize_controllers(self):
        """Initialize hardware controllers"""
        self.add_log("Initializing controllers...")
        
        def init_thread():
            try:
                # Initialize relay controller
                try:
                    self.relay_controller = RelayController()
                    self.root.after(0, lambda: self.add_log("✓ Relay controller initialized"))
                except Exception as e:
                    self.root.after(0, lambda: self.add_log(f"✗ Relay controller failed: {e}"))
                
                # Initialize flow meter controller (use mock for testing if needed)
                try:
                    use_mock = True  # Set to False for real hardware
                    if use_mock:
                        self.flow_controller = MockFlowMeterController()
                        self.root.after(0, lambda: self.add_log("✓ Mock flow meter controller initialized"))
                    else:
                        self.flow_controller = FlowMeterController()
                        self.root.after(0, lambda: self.add_log("✓ Flow meter controller initialized"))
                except Exception as e:
                    self.root.after(0, lambda: self.add_log(f"✗ Flow meter controller failed: {e}"))
                
                # Try to auto-detect Arduino Uno
                try:
                    uno_port = find_arduino_uno_port()
                    if uno_port:
                        self.root.after(0, lambda: self.add_log(f"✓ Arduino Uno found on {uno_port}"))
                        try:
                            self.arduino_controller = ArduinoUnoController(port=uno_port)
                            self.arduino_controller.set_message_callback(self.arduino_message_callback)
                            if self.arduino_controller.is_connected():
                                self.root.after(0, lambda: self.add_log("✓ Arduino Uno connected successfully"))
                            else:
                                self.root.after(0, lambda: self.add_log("✗ Arduino Uno connection failed"))
                        except Exception as e:
                            self.root.after(0, lambda: self.add_log(f"✗ Arduino Uno controller failed: {e}"))
                    else:
                        self.root.after(0, lambda: self.add_log("✗ Arduino Uno not found"))
                except Exception as e:
                    self.root.after(0, lambda: self.add_log(f"✗ Arduino Uno detection failed: {e}"))
                
                # Set system status
                self.system_running = True
                self.root.after(0, lambda: self.add_log("System initialization complete"))
                
            except Exception as e:
                error_msg = f"System initialization failed: {e}"
                self.root.after(0, lambda: self.add_log(f"✗ {error_msg}"))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("System Error", msg))
        
        # Start initialization in a separate thread
        threading.Thread(target=init_thread, daemon=True).start()
    
    def arduino_message_callback(self, message):
        """Handle messages from Arduino Uno"""
        self.root.after(0, lambda: self.add_log(f"Arduino: {message}"))
    
    def add_log(self, message):
        """Add message to log"""
        # Check if we're in the main thread
        if threading.current_thread() is threading.main_thread():
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            self.log_text.insert(tk.END, formatted_message + "\n")
            self.log_text.see(tk.END)
        else:
            # Schedule update on the main thread
            self.root.after(0, lambda msg=message: self.add_log_main_thread(msg))
    
    def add_log_main_thread(self, message):
        """Add log message from the main thread"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Save log to file"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.add_log(f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save log:\n{e}")
    
    def update_status(self):
        """Update system status display"""
        if self.system_running:
            # Update main status
            self.status_label.config(text="System: Running ✓", foreground="green")
            
            # Update component statuses
            relay_status = "Connected ✓" if self.relay_controller else "Not Connected ✗"
            flow_status = "Connected ✓" if self.flow_controller else "Not Connected ✗"
            arduino_status = "Connected ✓" if self.arduino_controller and self.arduino_controller.is_connected() else "Not Connected ✗"
            
            self.components_label.config(text=f"Relays: {relay_status} | Flow: {flow_status} | Arduino: {arduino_status}")
            
            # Update relay states
            if self.relay_controller:
                relay_states = self.relay_controller.get_all_relay_states()
                for relay_id, state in relay_states.items():
                    if relay_id in self.relay_buttons:
                        status_text = "ON" if state else "OFF"
                        color = "green" if state else "red"
                        self.relay_buttons[relay_id]['status'].config(
                            text=status_text, foreground=color
                        )
            
            # Update flow status
            if self.flow_controller:
                for meter_id in [1, 2]:
                    status = self.flow_controller.get_flow_status(meter_id)
                    if status:
                        if status['status'] == 1:
                            self.flow_status_labels[meter_id].config(
                                text=f"Active: {status['current_gallons']}/{status['target_gallons']} gallons",
                                foreground="green"
                            )
                        else:
                            self.flow_status_labels[meter_id].config(
                                text="Inactive", foreground="black"
                            )
            
            # Update Arduino status
            if self.arduino_controller and self.arduino_controller.is_connected():
                # Update port
                status = self.arduino_controller.get_connection_status()
                self.arduino_port_label.config(text=f"Port: {status['port']}")
                
                # Update connection status
                if status['connected']:
                    self.arduino_status_label.config(text="Status: Connected", foreground="green")
                else:
                    self.arduino_status_label.config(text="Status: Disconnected", foreground="red")
                
                # Update readings
                readings = self.arduino_controller.get_latest_readings()
                
                ec = readings.get('ec')
                if ec is not None:
                    self.ec_reading_label.config(text=f"EC: {ec:.2f} mS/cm")
                
                ph = readings.get('ph')
                if ph is not None:
                    self.ph_reading_label.config(text=f"pH: {ph:.2f}")
                
                # Process any queued messages
                messages = self.arduino_controller.get_queued_messages()
                for message in messages:
                    self.add_log(f"Arduino: {message}")
                
            else:
                self.arduino_port_label.config(text="Port: Not connected")
                self.arduino_status_label.config(text="Status: Disconnected", foreground="red")
                
        else:
            self.status_label.config(text="System: Not Running", foreground="red")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    # Relay control methods
    def control_relay(self, relay_id, state):
        """Control individual relay"""
        if not self.relay_controller:
            self.add_log("Relay controller not initialized")
            return
        
        state_str = "ON" if state else "OFF"
        success = self.relay_controller.set_relay(relay_id, state)
        
        if success:
            self.add_log(f"Relay {relay_id} set to {state_str}")
        else:
            self.add_log(f"Failed to set relay {relay_id}")
    
    def all_relays_off(self):
        """Turn all relays off"""
        if not self.relay_controller:
            self.add_log("Relay controller not initialized")
            return
        
        success = self.relay_controller.set_all_relays(False)
        
        if success:
            self.add_log("All relays turned OFF")
        else:
            self.add_log("Failed to turn off all relays")
    
    # Flow meter control methods
    def start_flow(self):
        """Start flow monitoring"""
        if not self.flow_controller:
            self.add_log("Flow controller not initialized")
            return
        
        try:
            flow_id = self.flow_var.get()
            gallons = int(self.gallons_var.get())
            
            if gallons <= 0:
                messagebox.showerror("Input Error", "Gallons must be greater than 0")
                return
            
            success = self.flow_controller.start_flow(flow_id, gallons)
            
            if success:
                self.add_log(f"Started flow meter {flow_id} for {gallons} gallons")
            else:
                self.add_log(f"Failed to start flow meter {flow_id}")
                
        except ValueError:
            messagebox.showerror("Input Error", "Invalid gallons value")
    
    def stop_flow(self):
        """Stop flow monitoring"""
        if not self.flow_controller:
            self.add_log("Flow controller not initialized")
            return
        
        flow_id = self.flow_var.get()
        success = self.flow_controller.stop_flow(flow_id)
        
        if success:
            self.add_log(f"Stopped flow meter {flow_id}")
        else:
            self.add_log(f"Failed to stop flow meter {flow_id}")
    
    # Arduino control methods
    def connect_arduino(self):
        """Connect to Arduino Uno"""
        if self.arduino_controller and self.arduino_controller.is_connected():
            self.add_log("Arduino already connected")
            return
        
        # Try to auto-detect Arduino Uno
        uno_port = find_arduino_uno_port()
        if not uno_port:
            self.add_log("Arduino Uno not found")
            uno_port = messagebox.askstring("Arduino Port", "Enter Arduino port:")
            if not uno_port:
                return
        
        self.add_log(f"Connecting to Arduino on {uno_port}...")
        
        try:
            # Close existing connection if any
            if self.arduino_controller:
                self.arduino_controller.close()
            
            # Create new connection
            self.arduino_controller = ArduinoUnoController(port=uno_port)
            self.arduino_controller.set_message_callback(self.arduino_message_callback)
            
            if self.arduino_controller.is_connected():
                self.add_log("Arduino Uno connected successfully")
            else:
                self.add_log("Arduino Uno connection failed")
                
        except Exception as e:
            self.add_log(f"Arduino connection error: {e}")
    
    def start_arduino_monitoring(self):
        """Start EC/pH monitoring"""
        if not self.arduino_controller or not self.arduino_controller.is_connected():
            self.add_log("Arduino not connected")
            return
        
        success = self.arduino_controller.start_monitoring()
        
        if success:
            self.add_log("Started EC/pH monitoring")
        else:
            self.add_log("Failed to start EC/pH monitoring")
    
    def stop_arduino_monitoring(self):
        """Stop EC/pH monitoring"""
        if not self.arduino_controller or not self.arduino_controller.is_connected():
            self.add_log("Arduino not connected")
            return
        
        success = self.arduino_controller.stop_monitoring()
        
        if success:
            self.add_log("Stopped EC/pH monitoring")
        else:
            self.add_log("Failed to stop EC/pH monitoring")
    
    # System control methods
    def emergency_stop(self):
        """Emergency stop - turn off all components"""
        self.add_log("EMERGENCY STOP initiated")
        
        # Stop flow meters
        if self.flow_controller:
            self.flow_controller.emergency_stop()
            self.add_log("Flow meters stopped")
        
        # Turn off all relays
        if self.relay_controller:
            self.relay_controller.emergency_stop()
            self.add_log("All relays turned OFF")
        
        # Stop Arduino monitoring
        if self.arduino_controller and self.arduino_controller.is_connected():
            self.arduino_controller.stop_monitoring()
            self.add_log("Arduino monitoring stopped")
        
        self.add_log("Emergency stop completed")
    
    def on_closing(self):
        """Cleanup on window close"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.add_log("Shutting down...")
            
            # Cleanup components
            if self.relay_controller:
                try:
                    self.relay_controller.cleanup()
                except:
                    pass
            
            if self.flow_controller:
                try:
                    self.flow_controller.cleanup()
                except:
                    pass
            
            if self.arduino_controller:
                try:
                    self.arduino_controller.close()
                except:
                    pass
            
            self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = SimplerTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()