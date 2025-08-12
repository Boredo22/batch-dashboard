#!/usr/bin/env python3
"""
Simple Tkinter GUI for Testing Raspberry Pi Feed Control System
Provides easy interface to test all functionality
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime

from main import FeedControlSystem

class FeedControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi Feed Control System - Test GUI")
        self.root.geometry("1200x800")
        
        # Initialize system
        self.system = None
        self.system_running = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Start system in background
        self.start_system()
        
        # Update loop
        self.update_status()
    
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
        self.create_control_frames(main_frame)
        
        # Log frame
        self.create_log_frame(main_frame)
    
    def create_status_frame(self, parent):
        """Create system status display"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="System: Starting...", 
                                     font=('Arial', 12, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.ec_ph_label = ttk.Label(status_frame, text="EC: -- mS/cm, pH: --")
        self.ec_ph_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Emergency stop button
        emergency_btn = ttk.Button(status_frame, text="🚨 EMERGENCY STOP 🚨", 
                                  command=self.emergency_stop)
        emergency_btn.grid(row=0, column=2, sticky=tk.E, padx=(20, 0))
        
        status_frame.columnconfigure(1, weight=1)
    
    def create_control_frames(self, parent):
        """Create control panels"""
        
        # Left column - Pumps and Relays
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.rowconfigure(1, weight=1)
        
        # Right column - Flow meters and EC/pH
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.rowconfigure(1, weight=1)
        
        # Pump control
        self.create_pump_control(left_frame)
        
        # Relay control
        self.create_relay_control(left_frame)
        
        # Flow meter control
        self.create_flow_control(right_frame)
        
        # EC/pH control
        self.create_ecph_control(right_frame)
    
    def create_pump_control(self, parent):
        """Create pump control panel"""
        pump_frame = ttk.LabelFrame(parent, text="Pump Control", padding="10")
        pump_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Pump selection
        ttk.Label(pump_frame, text="Pump:").grid(row=0, column=0, sticky=tk.W)
        self.pump_var = tk.IntVar(value=1)
        pump_combo = ttk.Combobox(pump_frame, textvariable=self.pump_var, 
                                 values=list(range(1, 9)), state="readonly", width=5)
        pump_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Amount entry
        ttk.Label(pump_frame, text="Amount (ml):").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.amount_var = tk.StringVar(value="10.0")
        amount_entry = ttk.Entry(pump_frame, textvariable=self.amount_var, width=10)
        amount_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Buttons
        dispense_btn = ttk.Button(pump_frame, text="Dispense", command=self.dispense_pump)
        dispense_btn.grid(row=0, column=4, padx=(10, 0))
        
        stop_btn = ttk.Button(pump_frame, text="Stop", command=self.stop_pump)
        stop_btn.grid(row=0, column=5, padx=(5, 0))
        
        # Status display
        self.pump_status_label = ttk.Label(pump_frame, text="Status: Idle")
        self.pump_status_label.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(10, 0))
    
    def create_relay_control(self, parent):
        """Create relay control panel"""
        relay_frame = ttk.LabelFrame(parent, text="Relay Control", padding="10")
        relay_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
                                command=lambda: self.control_relay(0, False))
        all_off_btn.pack(fill=tk.X)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_flow_control(self, parent):
        """Create flow meter control panel"""
        flow_frame = ttk.LabelFrame(parent, text="Flow Meter Control", padding="10")
        flow_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Flow meter selection
        ttk.Label(flow_frame, text="Flow Meter:").grid(row=0, column=0, sticky=tk.W)
        self.flow_var = tk.IntVar(value=1)
        flow_combo = ttk.Combobox(flow_frame, textvariable=self.flow_var,
                                 values=[1, 2], state="readonly", width=5)
        flow_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Gallons entry
        ttk.Label(flow_frame, text="Gallons:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.gallons_var = tk.StringVar(value="5")
        gallons_entry = ttk.Entry(flow_frame, textvariable=self.gallons_var, width=10)
        gallons_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Buttons
        start_flow_btn = ttk.Button(flow_frame, text="Start Flow", command=self.start_flow)
        start_flow_btn.grid(row=0, column=4, padx=(10, 0))
        
        stop_flow_btn = ttk.Button(flow_frame, text="Stop Flow", command=self.stop_flow)
        stop_flow_btn.grid(row=0, column=5, padx=(5, 0))
        
        # Status display
        self.flow_status_label = ttk.Label(flow_frame, text="Status: Inactive")
        self.flow_status_label.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(10, 0))
    
    def create_ecph_control(self, parent):
        """Create EC/pH control panel"""
        ecph_frame = ttk.LabelFrame(parent, text="EC/pH Control", padding="10")
        ecph_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Monitoring buttons
        btn_frame = ttk.Frame(ecph_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        start_monitor_btn = ttk.Button(btn_frame, text="Start Monitoring", 
                                      command=self.start_ecph_monitoring)
        start_monitor_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        stop_monitor_btn = ttk.Button(btn_frame, text="Stop Monitoring", 
                                     command=self.stop_ecph_monitoring)
        stop_monitor_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Readings display
        readings_frame = ttk.Frame(ecph_frame)
        readings_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ec_reading_label = ttk.Label(readings_frame, text="EC: -- mS/cm", 
                                         font=('Arial', 14))
        self.ec_reading_label.pack(anchor=tk.W)
        
        self.ph_reading_label = ttk.Label(readings_frame, text="pH: --", 
                                         font=('Arial', 14))
        self.ph_reading_label.pack(anchor=tk.W)
        
        # Calibration section
        cal_frame = ttk.LabelFrame(ecph_frame, text="Calibration", padding="5")
        cal_frame.pack(fill=tk.X)
        
        # pH calibration
        ph_cal_frame = ttk.Frame(cal_frame)
        ph_cal_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(ph_cal_frame, text="pH Cal:").pack(side=tk.LEFT)
        
        ttk.Button(ph_cal_frame, text="pH 4", width=6,
                  command=lambda: self.calibrate_ph("low", "4.0")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ph_cal_frame, text="pH 7", width=6,
                  command=lambda: self.calibrate_ph("mid", "7.0")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ph_cal_frame, text="pH 10", width=6,
                  command=lambda: self.calibrate_ph("high", "10.0")).pack(side=tk.LEFT, padx=2)
        
        # EC calibration
        ec_cal_frame = ttk.Frame(cal_frame)
        ec_cal_frame.pack(fill=tk.X)
        
        ttk.Label(ec_cal_frame, text="EC Cal:").pack(side=tk.LEFT)
        
        ttk.Button(ec_cal_frame, text="Dry", width=6,
                  command=lambda: self.calibrate_ec("dry")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ec_cal_frame, text="1413", width=6,
                  command=lambda: self.calibrate_ec("single", "1413")).pack(side=tk.LEFT, padx=2)
    
    def create_log_frame(self, parent):
        """Create log display"""
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log control buttons
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        clear_log_btn = ttk.Button(log_btn_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.pack(side=tk.LEFT)
        
        save_log_btn = ttk.Button(log_btn_frame, text="Save Log", command=self.save_log)
        save_log_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    def start_system(self):
        """Start the feed control system in background thread"""
        def init_system():
            try:
                self.add_log("Initializing feed control system...")
                self.system = FeedControlSystem(use_mock_flow=True)  # Use mock for testing
                self.system.set_message_callback(self.system_message_callback)
                self.system.start()
                self.system_running = True
                self.add_log("✓ System started successfully")
            except Exception as e:
                self.add_log(f"✗ System startup failed: {e}")
                messagebox.showerror("System Error", f"Failed to start system:\n{e}")
        
        thread = threading.Thread(target=init_system, daemon=True)
        thread.start()
    
    def system_message_callback(self, message):
        """Handle messages from the system"""
        self.root.after(0, lambda: self.add_log(f"SYS: {message}"))
    
    def add_log(self, message):
        """Add message to log"""
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
        if self.system and self.system_running:
            try:
                # Update system status
                status = self.system.get_system_status()
                
                # Main status
                self.status_label.config(text="System: Running ✓", foreground="green")
                
                # EC/pH readings
                ec_ph = status.get('ec_ph', {})
                ec = ec_ph.get('ec', '--')
                ph = ec_ph.get('ph', '--')
                self.ec_ph_label.config(text=f"EC: {ec} mS/cm, pH: {ph}")
                
                # Update EC/pH display
                if ec != '--':
                    self.ec_reading_label.config(text=f"EC: {ec:.2f} mS/cm")
                if ph != '--':
                    self.ph_reading_label.config(text=f"pH: {ph:.2f}")
                
                # Update relay states
                relays = status.get('relays', {})
                for relay_id, state in relays.items():
                    if relay_id in self.relay_buttons:
                        status_text = "ON" if state else "OFF"
                        color = "green" if state else "red"
                        self.relay_buttons[relay_id]['status'].config(
                            text=status_text, foreground=color
                        )
                
                # Update pump status
                pumps = status.get('pumps', {})
                current_pump = self.pump_var.get()
                if current_pump in pumps:
                    pump_info = pumps[current_pump]
                    if pump_info and pump_info['is_dispensing']:
                        current = pump_info['current_volume']
                        target = pump_info['target_volume']
                        self.pump_status_label.config(
                            text=f"Status: Dispensing {current:.1f}/{target:.1f} ml",
                            foreground="orange"
                        )
                    else:
                        self.pump_status_label.config(
                            text="Status: Idle",
                            foreground="black"
                        )
                
                # Update flow status
                flows = status.get('flow_meters', {})
                current_flow = self.flow_var.get()
                if current_flow in flows:
                    flow_info = flows[current_flow]
                    if flow_info['status'] == 1:  # Active
                        current = flow_info['current_gallons']
                        target = flow_info['target_gallons']
                        self.flow_status_label.config(
                            text=f"Status: Active {current}/{target} gallons",
                            foreground="orange"
                        )
                    else:
                        self.flow_status_label.config(
                            text="Status: Inactive",
                            foreground="black"
                        )
            
            except Exception as e:
                self.add_log(f"Status update error: {e}")
        else:
            self.status_label.config(text="System: Not Running", foreground="red")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    # Control methods
    def control_relay(self, relay_id, state):
        """Control relay"""
        if not self.system:
            return
        
        state_str = "ON" if state else "OFF"
        command = f"Start;Relay;{relay_id};{state_str};end"
        success = self.system.send_command(command)
        
        if success:
            relay_name = "All relays" if relay_id == 0 else f"Relay {relay_id}"
            self.add_log(f"Command sent: {relay_name} {state_str}")
        else:
            self.add_log(f"Failed to send relay command")
    
    def dispense_pump(self):
        """Start pump dispense"""
        if not self.system:
            return
        
        try:
            pump_id = self.pump_var.get()
            amount = float(self.amount_var.get())
            
            command = f"Start;Dispense;{pump_id};{amount};end"
            success = self.system.send_command(command)
            
            if success:
                self.add_log(f"Dispensing {amount}ml from pump {pump_id}")
            else:
                self.add_log(f"Failed to start dispense")
        
        except ValueError:
            messagebox.showerror("Input Error", "Invalid amount value")
    
    def stop_pump(self):
        """Stop pump"""
        if not self.system:
            return
        
        pump_id = self.pump_var.get()
        command = f"Start;Pump;{pump_id};X;end"
        success = self.system.send_command(command)
        
        if success:
            self.add_log(f"Stopped pump {pump_id}")
    
    def start_flow(self):
        """Start flow monitoring"""
        if not self.system:
            return
        
        try:
            flow_id = self.flow_var.get()
            gallons = int(self.gallons_var.get())
            
            command = f"Start;StartFlow;{flow_id};{gallons};220;end"
            success = self.system.send_command(command)
            
            if success:
                self.add_log(f"Started flow meter {flow_id} for {gallons} gallons")
        
        except ValueError:
            messagebox.showerror("Input Error", "Invalid gallons value")
    
    def stop_flow(self):
        """Stop flow monitoring"""
        if not self.system:
            return
        
        flow_id = self.flow_var.get()
        command = f"Start;StartFlow;{flow_id};0;end"
        success = self.system.send_command(command)
        
        if success:
            self.add_log(f"Stopped flow meter {flow_id}")
    
    def start_ecph_monitoring(self):
        """Start EC/pH monitoring"""
        if not self.system:
            return
        
        command = "Start;EcPh;ON;end"
        success = self.system.send_command(command)
        
        if success:
            self.add_log("Started EC/pH monitoring")
    
    def stop_ecph_monitoring(self):
        """Stop EC/pH monitoring"""
        if not self.system:
            return
        
        command = "Start;EcPh;OFF;end"
        success = self.system.send_command(command)
        
        if success:
            self.add_log("Stopped EC/pH monitoring")
    
    def calibrate_ph(self, cal_type, value):
        """Calibrate pH sensor"""
        if not self.system or not self.system.uno_controller:
            self.add_log("Arduino Uno not available for pH calibration")
            return
        
        success = self.system.uno_controller.calibrate_ph(cal_type, value)
        if success:
            self.add_log(f"pH calibration: {cal_type} = {value}")
    
    def calibrate_ec(self, cal_type, value=None):
        """Calibrate EC sensor"""
        if not self.system or not self.system.uno_controller:
            self.add_log("Arduino Uno not available for EC calibration")
            return
        
        success = self.system.uno_controller.calibrate_ec(cal_type, value)
        if success:
            cal_str = f"{cal_type} = {value}" if value else cal_type
            self.add_log(f"EC calibration: {cal_str}")
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        if not self.system:
            return
        
        self.system.emergency_stop()
        self.add_log("🚨 EMERGENCY STOP ACTIVATED 🚨")
        messagebox.showwarning("Emergency Stop", "All operations have been stopped!")
    
    def on_closing(self):
        """Handle window closing"""
        if self.system:
            self.add_log("Shutting down system...")
            self.system.stop()
        
        self.root.destroy()


def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = FeedControlGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Start GUI
    root.mainloop()


if __name__ == "__main__":
    main()